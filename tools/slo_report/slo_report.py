#!/usr/bin/env python3

# usage: slo_report
#
# Prerequisites:
#   - Python 3.11+
#   - Requests module
#   - A Honeycomb API key with the "Manage Queries and Columns" permission

import argparse
import requests
import os
import sys
import signal
import json
from lib.hnyapi import hnyapi_request, query_factory, craft_query_body

api_key = None
DEBUG = True if os.environ.get('DEBUG') else False

def fetch_auth_info():
    """
    Fetch the auth info for the current user
    """
    response = hnyapi_request('auth', api_key)
    return f"Current team: {response['team']['name']}, environment: {response['environment']['name']}"

def fetch_all_datasets():
    """
    Fetch all datasets in a team and return them as a list of dataset IDs
    """
    response = hnyapi_request('datasets', api_key)

    all_datasets = []
    for dataset in response:
        all_datasets.append(dataset['name'])

    return all_datasets

# Use the get all SLOs API: https://docs.honeycomb.io/api/tag/SLOs#operation/listSlos [docs.honeycomb.io]
def fetch_all_slos_for_dataset(dataset):
    """
    Fetch all SLOs in a dataset and return them all as json
    """
    print(f"fetching SLOs for dataset: {dataset}") if DEBUG else None
    endpoint = 'slos/' + dataset
    response = hnyapi_request(endpoint, api_key)

    all_slos = []
    for slo in response:
        print(f"  slo {slo['name']} : {slo['id']}") if DEBUG else None
        all_slos.append(slo)

    return all_slos

# Get the burn alert data: https://docs.honeycomb.io/api/tag/Burn-Alerts#operation/listBurnAlertsBySlo [docs.honeycomb.io]
def fetch_burn_alerts_for_slo(dataset, slo_id):
    """
    Fetch all burn alerts for a SLO and return them all as json
    """
    endpoint = 'burn_alerts/' + dataset + '?slo_id=' + slo_id
    response = hnyapi_request(endpoint, api_key)

    all_burn_alerts = []
    for burn_alert in response:
        all_burn_alerts.append(burn_alert)

    return all_burn_alerts

def fetch_all_slos():
    all_datasets = fetch_all_datasets()
    if all_datasets is None:
        print('No datasets found')
        sys.exit(1)

    all_slos = []
    for dataset in all_datasets:
        slos_for_dataset = fetch_all_slos_for_dataset(dataset)
        for slo in slos_for_dataset:
            slo['dataset'] = dataset
            slo['burn_alerts'] = fetch_burn_alerts_for_slo(dataset, slo['id'])
            all_slos.append(slo)

    return all_slos

# Run a query data api query where the SLI exists, once for a count and once for group by service name, and possibly one more time for where value = true?
# using
def fetch_sli_data(sli, dataset):
    """
    Fetch SLI data for a SLO and return it as json
    """
    query = craft_query_body(time_range=3600, breakdowns=[sli, "service.name"], calculations=[{"op": "COUNT"}])
    query_result = query_factory(dataset, query, api_key)

    return query_result


# The output of this is a production readiness check that tells you Service & SLO quality:



# Does a service have a SLO - x referenced from ServiceNow / cmdb?
# Is the SLI scoped to too many events
# Is the SLI scoped to too few events
# Are all events succeeding
# Are none of the events succeeding
# Is the SLO burning uncontrollably
# Is a burn alert configured

if __name__ == "__main__":
    try:
        # parse command line arguments
        parser = argparse.ArgumentParser(
            description='Honeycomb SLO report tool')
        parser.add_argument('-k', '--api-key',
                            help='Honeycomb API key', required=False)
        args = parser.parse_args()

        columns_to_delete = {}

        # try to get api_key from env var, if not use args.api_key
        if args.api_key is not None:
            api_key = args.api_key
        elif 'HONEYCOMB_API_KEY' in os.environ:
            api_key = os.environ['HONEYCOMB_API_KEY']
        else:
            print('You must provide an API key via the -k flag or the HONEYCOMB_API_KEY environment variable')
            sys.exit(1)

        # fetch all SLOs
        auth_info = fetch_auth_info()
        print('Fetching all SLOs for ' + auth_info + "\n\n")

        all_slos = fetch_all_slos()
        if all_slos is None:
            sys.exit(1)

        for slo in all_slos:
            print(f"Dataset: {slo['dataset']}, SLO: {slo['name']}, ID: {slo['id']}, SLI: {slo['sli']['alias']}")
            for burn_alert in slo['burn_alerts']:
                print(f"  Burn alert: {burn_alert['alert_type']}, ID: {burn_alert['id']}")

            print("Fetching SLI data ...")
            fetch_sli_data(slo['sli']['alias'], slo['dataset'])


    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        print('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
