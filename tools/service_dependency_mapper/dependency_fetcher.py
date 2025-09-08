#!/usr/bin/env python3
"""
Honeycomb Service Dependency Fetcher

This script fetches service dependency data from Honeycomb's Service Maps API.
It supports:
- Reading service lists from a file
- Time-based querying
- Handling large-scale service lists
- Pagination support
"""

import json
import time
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import urllib.request
import urllib.error
import urllib.parse


class HoneycombDependencyFetcher:
    def __init__(self, api_key: str, api_url: str = "https://api.honeycomb.io"):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "X-Honeycomb-Team": api_key,
            "Content-Type": "application/json"
        }

    def create_dependency_request(self,
                                  start_time: Optional[int] = None,
                                  end_time: Optional[int] = None,
                                  time_range: int = 7200,
                                  service_filters: Optional[List[str]] = None,
                                  limit: int = 10000) -> str:
        """
        Create a Map Dependency Request in Honeycomb.

        Returns the request ID for polling.
        """
        url = f"{self.api_url}/1/maps/dependencies/requests?limit={limit}"

        payload = {}

        # Handle time parameters
        if start_time and end_time:
            payload["start_time"] = start_time
            payload["end_time"] = end_time
        elif start_time:
            payload["start_time"] = start_time
            payload["time_range"] = time_range
        elif end_time:
            payload["end_time"] = end_time
            payload["time_range"] = time_range
        else:
            payload["time_range"] = time_range

        # Add service filters if provided
        if service_filters:
            payload["filters"] = [
                {"name": service, "type": "service"}
                for service in service_filters
            ]

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=self.headers, method='POST')

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['request_id']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Error creating dependency request: {e.code} - {error_body}")
            raise

    def get_dependencies(self, request_id: str, page_cursor: Optional[str] = None) -> Dict:
        """
        Get dependencies for a request ID. Handles pagination.
        """
        url = f"{self.api_url}/1/maps/dependencies/requests/{request_id}"
        if page_cursor:
            url += f"?page[next]={page_cursor}"

        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Error getting dependencies: {e.code} - {error_body}")
            raise

    def wait_for_results(self, request_id: str, max_wait: int = 300) -> Dict:
        """
        Poll for results until ready or timeout.
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            result = self.get_dependencies(request_id)

            if result['status'] == 'ready':
                return result
            elif result['status'] == 'error':
                raise Exception(f"Dependency request failed: {result}")

            # Wait before polling again
            time.sleep(2)

        raise TimeoutError(f"Dependency request timed out after {max_wait} seconds")

    def fetch_all_dependencies(self, request_id: str) -> List[Dict]:
        """
        Fetch all dependencies, handling pagination.
        """
        all_dependencies = []
        page_cursor = None

        # First, wait for the request to be ready
        initial_result = self.wait_for_results(request_id)

        if initial_result.get('dependencies'):
            all_dependencies.extend(initial_result['dependencies'])

        # Handle pagination
        while initial_result.get('links', {}).get('next'):
            # Extract cursor from next link
            next_url = initial_result['links']['next']
            if 'page[next]=' in next_url:
                page_cursor = next_url.split('page[next]=')[1].split('&')[0]
                initial_result = self.get_dependencies(request_id, page_cursor)
                if initial_result.get('dependencies'):
                    all_dependencies.extend(initial_result['dependencies'])
            else:
                break

        return all_dependencies


def load_services_from_file(filename: str) -> List[str]:
    """
    Load service names from a file (one per line).
    """
    services = []
    with open(filename, 'r') as f:
        for line in f:
            service = line.strip()
            if service and not service.startswith('#'):
                services.append(service)
    return services


def batch_services(services: List[str], batch_size: int = 100) -> List[List[str]]:
    """
    Split services into batches to avoid overwhelming the API.
    """
    batches = []
    for i in range(0, len(services), batch_size):
        batches.append(services[i:i + batch_size])
    return batches


def main():
    parser = argparse.ArgumentParser(description='Fetch service dependencies from Honeycomb')
    parser.add_argument('--api-key', required=True, help='Honeycomb API key')
    parser.add_argument('--api-url', default='https://api.honeycomb.io', help='Honeycomb API URL')
    parser.add_argument('--services-file', help='File containing service names (one per line)')
    parser.add_argument('--time-range', type=int, default=604800, help='Time range in seconds (default: 7 days)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='dependencies.json', help='Output file (default: dependencies.json)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for service filters (default: 100)')
    parser.add_argument('--limit', type=int, default=10000, help='Max dependencies per request (default: 10000)')

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = HoneycombDependencyFetcher(args.api_key, args.api_url)

    # Parse time parameters
    start_time = None
    end_time = None

    if args.start_date:
        start_time = int(datetime.strptime(args.start_date, '%Y-%m-%d').timestamp())
    if args.end_date:
        end_time = int(datetime.strptime(args.end_date, '%Y-%m-%d').timestamp())

    # Load services if file provided
    service_filters = None
    if args.services_file:
        services = load_services_from_file(args.services_file)
        print(f"Loaded {len(services)} services from {args.services_file}")

        if len(services) > args.batch_size:
            print(f"Processing services in batches of {args.batch_size}")
            batches = batch_services(services, args.batch_size)
        else:
            batches = [services]
    else:
        # No service filter - get all dependencies
        batches = [None]

    # Collect all dependencies
    all_dependencies = []
    all_services = set()

    for i, batch in enumerate(batches):
        if batch:
            print(f"Processing batch {i+1}/{len(batches)} ({len(batch)} services)")

        try:
            # Create dependency request
            request_id = fetcher.create_dependency_request(
                start_time=start_time,
                end_time=end_time,
                time_range=args.time_range,
                service_filters=batch,
                limit=args.limit
            )
            print(f"Created request: {request_id}")

            # Fetch dependencies
            dependencies = fetcher.fetch_all_dependencies(request_id)
            print(f"Fetched {len(dependencies)} dependencies")

            # Add to results
            all_dependencies.extend(dependencies)

            # Track all services seen
            for dep in dependencies:
                if dep.get('parent_node', {}).get('name'):
                    all_services.add(dep['parent_node']['name'])
                if dep.get('child_node', {}).get('name'):
                    all_services.add(dep['child_node']['name'])

        except Exception as e:
            print(f"Error processing batch {i+1}: {e}")
            continue

        # Small delay between batches
        if i < len(batches) - 1:
            time.sleep(1)

    # Prepare output
    output_data = {
        'fetch_time': datetime.now().isoformat(),
        'time_range': args.time_range,
        'start_time': start_time,
        'end_time': end_time,
        'total_dependencies': len(all_dependencies),
        'unique_services': len(all_services),
        'dependencies': all_dependencies
    }

    # Save to file
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to {args.output}")
    print(f"Total dependencies: {len(all_dependencies)}")
    print(f"Unique services: {len(all_services)}")


if __name__ == '__main__':
    main()
