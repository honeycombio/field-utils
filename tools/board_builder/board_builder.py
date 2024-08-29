#!/usr/bin/env python3

# usage: board_builder
#
# Prerequisites:
#   - Python 3.12+
#   - Requests module
#   - A Honeycomb API key with the "Manage Queries and Columns" and "Manage Public Boards" permissions

import argparse
import logging
import os
import signal
import sys

from lib.builders import HoneycombBuilder

logger = logging.getLogger(__name__)


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description='Honeycomb Standard Board Builder Tool')
    parser.add_argument('-n', '--service-name',
                        help='Service name to build board for', required=True)
    parser.add_argument('-t', '--service-type',
                        default="other", choices=['java', 'ruby', 'python', 'node', 'go', 'php', 'other'],
                        help='Service type: java, ruby, python, etc...  May add extra queries to default board', required=False)
    parser.add_argument('-k', '--api-key',
                        help='Honeycomb API key', required=False)
    parser.add_argument('-r', '--region',
                        default="us", choices=['us', 'eu'],
                        help='Honeycomb region, default of "us", but can choose "eu" for customers using the EU datacenter', required=False)
    parser.add_argument('-l', '--log-level',
                        default="info", choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='Log level. Use warning or higher to only log the JSON output of this tool', required=False)
    args = parser.parse_args()

    logging.basicConfig(
        format="{asctime} ({funcName}:{levelname}) {message}",
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

    builder = HoneycombBuilder(api_key, args.region)

    builder.build_service_board(args.service_name, args.service_type)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:  # Suppress tracebacks on SIGINT
        logger.critical('\nExiting early, not done ...\n')
        sys.exit(128 + signal.SIGINT)  # http://tldp.org/LDP/abs/html/exitcodes
