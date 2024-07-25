#!/usr/bin/env python3

# usage: slo_report
#
# Prerequisites:
#   - Python 3.11+
#   - Requests module
#   - A Honeycomb API key with the "Manage Queries and Columns" permission

import argparse
import os, sys, signal
from itertools import batched, groupby

from lib.fetchers import HoneycombFetcher

BATCH_SIZE = 10

api_key = None
DEBUG = True if os.environ.get('DEBUG') else False




# expected output:
# {
#     "slo_id": "sdfsdfs",
#     "slo_name": "SLO Name",
#     "sli_name": "SLI Name",
#     "sli_expression": "IF(AND(CONTAINS($service.name, \"FOO\"), EQUALS($service. role_type, \"prod\*), EQUALS(Scloud. region, \"ap-southeast-2\"), EXISTS($http.status_code)), LT(Shttp. status_code, 500))",
#     "dataset": "prod",
#     "sli_event_count": 65659,
#     "sli_service_count" : 2,
#     "sli_values": {
#         "true": 65659
#     }，
#     "region": "prod",
#     "count_date" : "2024-07-09"
# }


# simplified query specs from original:

# COUNT, COUNT_DISTINCT(service.name) WHERE <sli> exists [24 hours] |
# COUNT WHERE <sli> exists GROUP BY <sli> [24 hours] |
# COUNT WHERE <sli> = true [7 days] |
# COUNT WHERE <sli> exists GROUP BY <sli> [7 days]
# COUNT WHERE <sli> exists GROUP BY <sli> [7 days]

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

        fetcher = HoneycombFetcher(api_key, debug=DEBUG)

        # fetch all SLOs
        auth_info = fetcher.fetch_auth_info()
        print('Fetching all SLOs for ' + auth_info + "\n\n")

        all_slos = fetcher.fetch_all_slos()
        if all_slos is None:
            sys.exit(1)

        # group all SLOs by dataset
        for dataset, slos_group in groupby(all_slos, key=lambda slo: slo['dataset']):
            print (f"Running batches for Dataset: {dataset}")
            # take batches of 10 SLOs and fetch SLI data for them
            for slo_batch in batched(slos_group, BATCH_SIZE):
                slo_names = [slo['name'] for slo in slo_batch]
                print(slo_names)
                sli_data = fetcher.fetch_sli_service_values_counts(slo_batch, dataset)

    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        print('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
