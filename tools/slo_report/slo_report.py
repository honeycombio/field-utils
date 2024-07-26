#!/usr/bin/env python3

# usage: slo_report
#
# Prerequisites:
#   - Python 3.10+
#   - Requests module
#   - A Honeycomb API key with the "Run Queries and Manage SLOs" permission

import argparse, json, logging, os, signal, sys
from itertools import batched, groupby

from lib.fetchers import HoneycombFetcher

logger = logging.getLogger(__name__)

def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description='Honeycomb SLO report tool')
    parser.add_argument('-k', '--api-key',
                        help='Honeycomb API key', required=False)
    parser.add_argument('-l', '--log-level',
                        default="info", choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='Log level. Use warning or higher to only log the JSON output of this tool', required=False)
    parser.add_argument('-b', '--batch-size', type=int, default=10, required=False)
    args = parser.parse_args()

    logging.basicConfig(
        format="{asctime} {levelname} {message}",
        style="{",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        level=getattr(logging, args.log_level.upper())
    )

    # try to get api_key from env var, if not use args.api_key
    api_key = None
    if args.api_key is not None:
        api_key = args.api_key
    elif 'HONEYCOMB_API_KEY' in os.environ:
        api_key = os.environ['HONEYCOMB_API_KEY']
    else:
        logger.critical('You must provide an API key via the -k flag or the HONEYCOMB_API_KEY environment variable')
        sys.exit(1)

    fetcher = HoneycombFetcher(api_key)

    # fetch all SLOs
    auth_info = fetcher.fetch_auth_info()
    logger.info('Fetching all SLOs for ' + auth_info + "\n\n")

    all_slos = fetcher.fetch_all_slos()
    if all_slos is None:
        logger.critical('No SLOs found')
        sys.exit(1)

    # group all SLOs by dataset
    for dataset, slos_group in groupby(all_slos, key=lambda slo: slo['dataset']):
        logger.info(f"Running batches for Dataset: {dataset}")
        # take batches of SLOs and fetch SLI data for them
        for slo_batch in batched(slos_group, args.batch_size):
            slo_names = [slo['name'] for slo in slo_batch]
            logger.info(f"SLOs in this batch: {slo_names}")
            sli_data = fetcher.fetch_sli_service_values_counts(slo_batch, dataset)
            # output sli_data to stdout
            print(json.dumps(sli_data, indent=2))


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        logger.critical('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
