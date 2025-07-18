#!/usr/bin/env python3

# usage: hny-column-cleanup.py [-h] -k API_KEY -d DATASET [-m {hidden,spammy,date}] --date YYYY-MM-DD
# Honeycomb Dataset Column Cleanup tool
# arguments:
#   -h, --help              show this help message and exit
#   -k, --api-key           Honeycomb API key
#   -a, --api-host          Honeycomb API hostname (defaults to api.honeycomb.io)
#   -d, --dataset           Honeycomb Dataset
#   -m, --mode {hidden,spammy,date,last_written_before,regex_pattern}
#                           Type of columns to clean up. `date` targets the `created_at` date.
#                           `last_written_before` targets columns with no writes since date.
#   --date YYYY/MM/DD       ISO8601 date to be used with --mode date
#   --regex_pattern         Regular expression to match on column names
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
import email.utils
from datetime import date
from datetime import datetime

SPAMMY_STRINGS = [
    'oastify', 'burp', 'xml', 'jndi', 'ldap', # pentester
    '%','{', '(', '*', '!', '?', '<', '..', '|', '&', '"', '\'', '\r', '\n','`','--','u0','\\','@'
]

def fetch_all_columns(dataset, api_key, api_url):
    """
    Fetch all columns in a dataset and return them all as json
    """
    url = api_url + 'columns/' + dataset
    response = requests.get(url, headers={"X-Honeycomb-Team": api_key})
    if response.status_code != 200:
        print('Failure: Unable to list columns:' + response.text)
        return
    return response.json()


def list_hidden_columns(dataset, api_key, api_url):
    """
    List hidden columns in a dataset and return the list as an array of column IDs
    """
    all_columns = fetch_all_columns(dataset, api_key, api_url)
    hidden_column_ids = {}
    for column in all_columns:
        if column['hidden']:
            hidden_column_ids[column['id']] = column['key_name']
    return hidden_column_ids


def list_spammy_columns(dataset, api_key, api_url):
    """
    List spammy columns in a dataset and return the list as an array of column IDs
    """
    all_columns = fetch_all_columns(dataset, api_key, api_url)
    spammy_column_ids = {}
    for column in all_columns:
        for spammy_string in SPAMMY_STRINGS:
            if spammy_string in column['key_name']:
                spammy_column_ids[column['id']] = column['key_name']
                break  # end the inner loop in case there's multiple matches in the same string
    return spammy_column_ids

def match_columns(dataset, api_key, api_url, regex_pattern):
    """
    List columns in a dataset that match a regular expression and return the list as an array of column IDs
    """
    all_columns = fetch_all_columns(dataset, api_key, api_url)
    pattern = re.compile(regex_pattern)
    matched_column_ids = {}
    for column in all_columns:
        if pattern.match(column['key_name']):
            matched_column_ids[column['id']] = column['key_name']
    return matched_column_ids

def list_columns_by_date(dataset, api_key, api_url, date):
    """
    List columns by date in a dataset and return the list as an array of column IDs. The created date is set in `column_created_date_string` for now.
    """
    all_columns = fetch_all_columns(dataset, api_key, api_url)
    matched_column_ids = {}
    for column in all_columns:
        created_at_date = datetime.fromisoformat(column['created_at']).date()
        if date == created_at_date:
            matched_column_ids[column['id']] = column['key_name']
    return matched_column_ids

def list_columns_last_written_before(dataset, api_key, api_url, date):
    """
    List columns in a dataset where last_written is before specified date.
    Returns a dictionary where key is id and value is key_name.
    """
    all_columns = fetch_all_columns(dataset, api_key, api_url)

    return dict(
        [
            (column['id'], column['key_name'])
            for column in all_columns
            if datetime.fromisoformat(column['last_written'].replace("Z", "+00:00")).date() < date
        ]
    )

def parse_retry_after(retry_after):
    """
    Parse the Retry-After header as an HTTP date (e.g., "Fri, 31 Dec 1999 23:59:59 GMT")
    Returns the number of seconds to wait
    """
    try:
        # Parse as an HTTP date format
        retry_date = email.utils.parsedate_to_datetime(retry_after)
        now = datetime.now(retry_date.tzinfo)
        delta = retry_date - now
        # Add 1 second buffer to account for processing time
        return max(1, int(delta.total_seconds()) + 1)
    except (ValueError, TypeError):
        # If parsing fails, return default of 30 seconds
        return 30

def delete_columns(dataset, api_key, api_url, is_dry_run, column_ids):
    """
    Delete hidden columns in a dataset from a provided array of column IDs
    """
    url = api_url + 'columns/' + dataset
    headers = {"X-Honeycomb-Team": api_key}
    for id in column_ids.keys():
        if is_dry_run:
            print('Dry run: would delete column ID: ' + id +
                  ' Name: ' + column_ids[id] + '...')
        else:
            print('Deleting column ID: ' + id +
                  ' Name: ' + column_ids[id] + '...')

        if not is_dry_run:
            while True:
                response = requests.delete(url + '/' + id, headers=headers)

                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '30')
                    wait_seconds = parse_retry_after(retry_after)
                    print(f'Rate limited. Contact support for higher limits. Waiting {wait_seconds} seconds before retrying...')
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
        parser.add_argument('-a', '--api-host', default='api.honeycomb.io',
                            help='Honeycomb API hostname (defaults to api.honeycomb.io)')
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

        # Construct the full API URL from the hostname
        api_url = f'https://{args.api_host}/1/'

        columns_to_delete = {}

        if args.mode == 'hidden':
            columns_to_delete = list_hidden_columns(args.dataset, args.api_key, api_url)
        elif args.mode == 'spammy':
            columns_to_delete = list_spammy_columns(args.dataset, args.api_key, api_url)
        elif args.mode == 'regex_pattern':
            columns_to_delete = match_columns(args.dataset, args.api_key, api_url, args.regex_pattern)
        elif (args.mode == 'date' and args.date is not None):
            columns_to_delete = list_columns_by_date(args.dataset, args.api_key, api_url, args.date)
        elif (args.mode == 'last_written_before' and args.date is not None):
            columns_to_delete = list_columns_last_written_before(args.dataset, args.api_key, api_url, args.date)
        else:
            parser.error('--date YYYY-MM-DD is required when using --mode ' + args.mode)

        if len(columns_to_delete.keys()) > 0:
            if not args.dry_run:
                print("WARNING: Dry run disabled - this will delete live columns!")
            delete_columns(args.dataset, args.api_key, api_url,
                           args.dry_run, columns_to_delete)
            if args.dry_run:
                print('Dry run completed: Would have deleted ' + str(len(columns_to_delete.keys())) +
                      ' ' + args.mode + ' columns!')
            else:
                print('Deleted ' + str(len(columns_to_delete.keys())) +
                      ' ' + args.mode + ' columns! Enjoy your clean dataset!')

    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        print('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
