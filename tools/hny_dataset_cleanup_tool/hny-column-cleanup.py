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
import re
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

def match_columns(dataset, api_key, regex_pattern):
    """
    List columns in a dataset that match a regular expression and return the list as an array of column IDs
    """
    all_columns = fetch_all_columns(dataset, api_key)
    pattern = re.compile(regex_pattern)
    matched_column_ids = {}
    for column in all_columns:
        if pattern.match(column['key_name']):
            matched_column_ids[column['id']] = column['key_name']
    return matched_column_ids

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
            if datetime.fromisoformat(column['last_written'].replace("Z", "+00:00")).date() < date
        ]
    )

def parse_retry_after(retry_after):
    """
    Parse the Retry-After header which can be either:
    - A number of seconds
    - An ISO 8601 date (e.g., "2025-02-27T15:38:09Z")
    Returns the number of seconds to wait
    """
    try:
        # First try to parse as a number of seconds
        return int(retry_after)
    except ValueError:
        try:
            # If that fails, try to parse as an ISO 8601 date
            retry_date = datetime.fromisoformat(retry_after.replace('Z', '+00:00'))
            now = datetime.now(retry_date.tzinfo)
            delta = retry_date - now
            return max(0, int(delta.total_seconds()))
        except ValueError:
            # If both parsing attempts fail, return default of 30 seconds
            return 30

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
            while True:
                response = requests.delete(url + '/' + id, headers=headers)

                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '30')
                    wait_seconds = parse_retry_after(retry_after)
                    print(f'Rate limited. Waiting {wait_seconds} seconds before retrying...')
                    time.sleep(wait_seconds)
                    continue
                elif response.status_code in [500, 502, 503, 504]:
                    print('Received a retryable error ' +
                          str(response.status_code) + ' sleeping and retrying...')
                    time.sleep(30)
                    continue
                elif response.status_code != 204:
                    print('Failed: Unable to delete column ID ' +
                          id + ': ' + response.text)
                    print('Moving on to the next column...')
                break  # Exit the retry loop on success or non-retryable error


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
                            choices=['hidden', 'spammy', 'date', 'last_written_before', 'regex_pattern'], help='Type of columns to clean up')
        parser.add_argument('--dry-run', default=False,
                            action=argparse.BooleanOptionalAction, help='Will print out the columns it would delete without deleting them')
        parser.add_argument('--date', type=date.fromisoformat, default=None,
                            help='Date filter to use with date and last_written_before modes (YYYY-MM-DD)')
        parser.add_argument('--regex_pattern',
                            help='Regular expression to match on column names')
        args = parser.parse_args()

        columns_to_delete = {}

        if args.mode == 'hidden':
            columns_to_delete = list_hidden_columns(args.dataset, args.api_key)
        elif args.mode == 'spammy':
            columns_to_delete = list_spammy_columns(args.dataset, args.api_key)
        elif args.mode == 'regex_pattern':
            columns_to_delete = match_columns(args.dataset, args.api_key, args.regex_pattern)
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
