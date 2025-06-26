#!/usr/bin/env python3

# usage: hny-dataset-cleanup.py [-h] -k API_KEY [-m {spammy,date}] --date YYYY-MM-DD
# Honeycomb Dataset Cleanup tool for Environments
# This differs from hny_column_cleanup.py as it is targeted at Environments that may have datasets created by pentesters
#
# arguments:
#   -h, --help              show this help message and exit
#   -k API_KEY, --api-key   API_KEY
#                           Honeycomb API key for your Environment, with Create Dataset permission
#   -m {spammy,date,lastwritten} --mode {spammy,date,lastwritten}
#                           Type of datasets to clean up. `date` targets the `created_at` date.
#                           `lastwritten` targets datasets with no writes since date.
#   --date YYYY/MM/DD       ISO8601 date to be used with --mode date
#   --dry-run               Will print out the datasets it would delete without deleting them
#
# Prerequisites:
#   - Python 3.11+
#   - Requests module
#   - A Honeycomb API key with the "Create Dataset" permission

import argparse
import requests
import sys
import signal
import time
import json
import email.utils
from datetime import date
from datetime import datetime

HONEYCOMB_API = 'https://api.honeycomb.io/1/'  # /columns/dataset_slug
SPAMMY_STRINGS = [
                 'oastify', 'burp', 'xml', 'jndi', 'ldap', 'lol' # pentester
		         '%','{', '(', '*', '!', '?', '<', '..', '|', '&', '"', '\'', '\r', '\n','`','--','u0','\\','@','\ufffd'
]

def fetch_all_datasets(api_key):
    """
    Fetch all datasets in an environment and return them all as json
    """
    url = HONEYCOMB_API + 'datasets'
    response = requests.get(url, headers={"X-Honeycomb-Team": api_key})
    if response.status_code != 200:
        print('Failure: Unable to list datasets:' + response.text)
        return
    return response.json()

def list_spammy_datasets(api_key):
    """
    List spammy datasets and return the list as an array of dataset IDs
    """
    all_datasets = fetch_all_datasets(api_key)
    spammy_dataset_slugs = {}
    for dataset in all_datasets:
        for spammy_string in SPAMMY_STRINGS:
            if spammy_string in dataset['name']:
                spammy_dataset_slugs[dataset['slug']] = dataset['slug']
                break  # end the inner loop in case there's multiple matches in the same string
    return spammy_dataset_slugs

def list_datasets_by_date(api_key, date):
     """
     List datasets by date in a Environment and return the list as an array of dataset slugs. The created date is set in `dataset_created_date_string` for now.
     """
     all_datasets = fetch_all_datasets(api_key)
     matched_dataset_slugs = {}
     for dataset in all_datasets:
         created_at_date = datetime.fromisoformat(dataset['created_at']).date()
         if date == created_at_date:
            matched_dataset_slugs[dataset['slug']] = dataset['slug']
     return matched_dataset_slugs

def list_datasets_by_last_written_at(api_key, date):
     """
     List datasets by date in a Environment and return the list as an array of dataset slugs. The created date is set in `dataset_created_date_string` for now.
     """
     all_datasets = fetch_all_datasets(api_key)
     matched_dataset_slugs = {}
     for dataset in all_datasets:
         last_written_at_date = datetime.fromisoformat(dataset['last_written_at']).date()
         if date > last_written_at_date:
            matched_dataset_slugs[dataset['slug']] = dataset['slug']
     return matched_dataset_slugs

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

def handle_response(response, slug, action):
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After', '30')
        wait_seconds = parse_retry_after(retry_after)
        print(f'Rate limited. Contact support for higher limits. Waiting {wait_seconds} seconds before retrying...')
        time.sleep(wait_seconds)
        return True
    elif response.status_code in [500, 502, 503, 504]:
        print('Received a retryable error ' + str(response.status_code) + ' sleeping and retrying...')
        time.sleep(30)
        return True
    elif response.status_code != 200 and response.status_code != 202:
        print('Failed: Unable to ' + action + ' dataset slug ' + slug + ': ' + response.text)
        print('Moving on to the next dataset...')
    return False

def remove_delete_protection(api_key, is_dry_run, dataset_slugs):
    url = HONEYCOMB_API + 'datasets'
    headers = {"X-Honeycomb-Team": api_key}
    payload = '{"settings": {"delete_protected": false}}'
    for slug in dataset_slugs.keys():
        print('Removing delete protection from dataset slug: ' + slug + '...')
        if not is_dry_run:
            while True:
                response = requests.put(url + '/' + slug, headers=headers, data=payload)
                if not handle_response(response, slug, 'remove delete protection from'):
                    break

def delete_datasets(api_key, is_dry_run, dataset_slugs):
    url = HONEYCOMB_API + 'datasets'
    headers = {"X-Honeycomb-Team": api_key}
    for slug in dataset_slugs.keys():
        print('Deleting dataset slug: ' + slug + '...')
        if not is_dry_run:
            while True:
                response = requests.delete(url + '/' + slug, headers=headers)
                if not handle_response(response, slug, 'delete'):
                    break

if __name__ == "__main__":
    try:
        # parse command line arguments
        parser = argparse.ArgumentParser(
            description='Honeycomb Dataset Cleanup tool for Environments')
        parser.add_argument('-k', '--api-key',
                            help='Honeycomb API key', required=True)
        parser.add_argument('-m', '--mode', default='spammy',
                            choices=['spammy', 'date', 'lastwritten'], help='Type of datasets to clean up')
        parser.add_argument('--dry-run', default=False,
                            action=argparse.BooleanOptionalAction, help='Will print out the datasets it would delete without deleting them')
        parser.add_argument('--date', type=date.fromisoformat, default=None,
                            help='Search for datasets to clean up created on date (YYYY-MM-DD)')
        args = parser.parse_args()

        datasets_to_delete = {}

        if args.mode == 'spammy':
            datasets_to_delete = list_spammy_datasets(args.api_key)
        elif (args.mode == 'date' and args.date is not None):
            datasets_to_delete = list_datasets_by_date(args.api_key, args.date)
        elif (args.mode == 'lastwritten' and args.date is not None):
            datasets_to_delete = list_datasets_by_last_written_at(args.api_key, args.date)
        else:
            parser.error('--date YYYY-MM-DD is required when using --mode date')

        if len(datasets_to_delete.keys()) > 0:
            remove_delete_protection(args.api_key,
                                       args.dry_run, datasets_to_delete)
            print('Removed delete protection for ' + str(len(datasets_to_delete.keys())) +
                  ' ' + args.mode + ' datasets.')
            delete_datasets(args.api_key,
                           args.dry_run, datasets_to_delete)
            print('Deleted ' + str(len(datasets_to_delete.keys())) +
                  ' ' + args.mode + ' datasets! Enjoy your clean environment!')

    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        print('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
