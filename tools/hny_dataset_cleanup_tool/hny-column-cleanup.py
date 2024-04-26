#!/usr/bin/env python3

# usage: hny-column-cleanup.py [-h] -k API_KEY -d DATASET [-m {hidden,spammy,date}] --date YYYY-MM-DD
# Honeycomb Dataset Column Cleanup tool
# arguments:
#   -h, --help              show this help message and exit
#   -k API_KEY, --api-key   API_KEY
#                           Honeycomb API key
#   -d DATASET, --dataset   DATASET
#                           Honeycomb Dataset
#   -m {hidden,spammy,date} --mode {hidden,spammy,date}
#                           Type of columns to clean up. `date` targets the `created_at` date.
#   --date YYYY/MM/DD       ISO8601 date to be used with --mode date
#   --dry-run               Will print out the columns it would delete without deleting them
#
# Prerequisites:
#   - Python 3.11+
#   - Requests module
#   - A Honeycomb API key with the "Manage Queries and Columns" permission

import argparse
import requests
import sys
import signal
import time
from datetime import date
from datetime import datetime

HONEYCOMB_API = 'https://api.honeycomb.io/1/'  # /columns/dataset_slug
SPAMMY_STRINGS = [
    'oastify', 'burp', 'xml', 'jndi', 'ldap', # pentester
    '%','{', '(', '*', '!', '?', '<', '..', '|', '&', '"', '\'', '\r', '\n','`','--','u0','\\','@'
]

def fetch_all_columns(dataset, api_key):
    """
    Fetch all columns in a dataset and return them all as json
    """
    url = HONEYCOMB_API + 'columns/' + dataset
    response = requests.get(url, headers={"X-Honeycomb-Team": api_key})
    if response.status_code != 200:
        print('Failure: Unable to list columns:' + response.text)
        return
    return response.json()


def list_hidden_columns(dataset, api_key):
    """
    List hidden columns in a dataset and return the list as an array of column IDs
    """
    all_columns = fetch_all_columns(dataset, api_key)
    hidden_column_ids = {}
    for column in all_columns:
        if column['hidden']:
            hidden_column_ids[column['id']] = column['key_name']
    return hidden_column_ids


def list_spammy_columns(dataset, api_key):
    """
    List spammy columns in a dataset and return the list as an array of column IDs
    """
    all_columns = fetch_all_columns(dataset, api_key)
    spammy_column_ids = {}
    for column in all_columns:
        for spammy_string in SPAMMY_STRINGS:
            if spammy_string in column['key_name']:
                spammy_column_ids[column['id']] = column['key_name']
                break  # end the inner loop in case there's multiple matches in the same string
    return spammy_column_ids

def list_columns_by_date(dataset, api_key, date):
    """
    List columns by date in a dataset and return the list as an array of column IDs. The created date is set in `column_created_date_string` for now.
    """
    all_columns = fetch_all_columns(dataset, api_key)
    matched_column_ids = {}
    for column in all_columns:
        created_at_date = datetime.fromisoformat(column['created_at']).date()
        if date == created_at_date:
            matched_column_ids[column['id']] = column['key_name']
    return matched_column_ids

def list_columns_last_written_before(dataset, api_key, date):
    """
    List columns in a dataset where last_written is before specified date.
    Returns a dictionary where key is id and value is key_name.
    """
    all_columns = fetch_all_columns(dataset, api_key)

    return dict(
        [
            (column['id'], column['key_name'])
            for column in all_columns
            if datetime.fromisoformat(column['last_written']).date() < date
        ]
    )

def delete_columns(dataset, api_key, is_dry_run, column_ids):
    """
    Delete hidden columns in a dataset from a provided array of column IDs
    """
    url = HONEYCOMB_API + 'columns/' + dataset
    headers = {"X-Honeycomb-Team": api_key}
    for id in column_ids.keys():
        print('Deleting column ID: ' + id +
              ' Name: ' + column_ids[id] + '...')

        if not is_dry_run:
            response = requests.delete(url + '/' + id, headers=headers)

            # A tiny bit of error handling
            if response.status_code in [429, 500, 502, 503, 504]:
                print('Received a retryable error ' +
                      response.status_code + ' sleeping and retrying...')
                # Put a long-ish sleep here to cope with the default rate limit of 10 requests per minute
                time.sleep(30)
                response = requests.delete(url + '/' + id, headers=headers)
            elif response.status_code != 204:
                print('Failed: Unable to delete column ID' +
                      id + ': ' + response.text)
                print('Moving on to the next column...')


if __name__ == "__main__":
    try:
        # parse command line arguments
        parser = argparse.ArgumentParser(
            description='Honeycomb Dataset Column Cleanup tool')
        parser.add_argument('-k', '--api-key',
                            help='Honeycomb API key', required=True)
        parser.add_argument('-d', '--dataset',
                            help='Honeycomb Dataset', required=True)
        parser.add_argument('-m', '--mode', default='hidden',
                            choices=['hidden', 'spammy', 'date', 'last_written_before'], help='Type of columns to clean up')
        parser.add_argument('--dry-run', default=False,
                            action=argparse.BooleanOptionalAction, help='Will print out the columns it would delete without deleting them')
        parser.add_argument('--date', type=date.fromisoformat, default=None,
                            help='Date filter to use with date and last_written_before modes (YYYY-MM-DD)')
        args = parser.parse_args()

        columns_to_delete = {}

        if args.mode == 'hidden':
            columns_to_delete = list_hidden_columns(args.dataset, args.api_key)
        elif args.mode == 'spammy':
            columns_to_delete = list_spammy_columns(args.dataset, args.api_key)
        elif (args.mode == 'date' and args.date is not None):
            columns_to_delete = list_columns_by_date(args.dataset, args.api_key, args.date)
        elif (args.mode == 'last_written_before' and args.date is not None):
            columns_to_delete = list_columns_last_written_before(args.dataset, args.api_key, args.date)
        else:
            parser.error('--date YYYY-MM-DD is required when using --mode ' + args.mode)

        if len(columns_to_delete.keys()) > 0:
            delete_columns(args.dataset, args.api_key,
                           args.dry_run, columns_to_delete)
            print('Deleted ' + str(len(columns_to_delete.keys())) +
                  ' ' + args.mode + ' columns! Enjoy your clean dataset!')

    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        print('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
