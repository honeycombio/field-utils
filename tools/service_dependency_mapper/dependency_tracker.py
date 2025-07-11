#!/usr/bin/env python3
"""
Honeycomb Service Dependency Tracker

This script tracks service dependencies over time, maintaining first seen/last seen
information and providing validation capabilities against internal systems.

Uses SQLite for lightweight persistence.
"""

import json
import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os


class DependencyTracker:
    def __init__(self, db_path: str = "dependencies.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_db()

    def _initialize_db(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()

        # Dependencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_service TEXT NOT NULL,
                child_service TEXT NOT NULL,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                total_calls INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT 1,
                UNIQUE(parent_service, child_service)
            )
        """)

        # Dependency history table (for tracking changes over time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependency_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_service TEXT NOT NULL,
                child_service TEXT NOT NULL,
                observed_at TIMESTAMP NOT NULL,
                call_count INTEGER NOT NULL,
                time_range_start TIMESTAMP,
                time_range_end TIMESTAMP
            )
        """)

        # Services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deps_parent
            ON dependencies(parent_service)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deps_child
            ON dependencies(child_service)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deps_active
            ON dependencies(active)
        """)

        self.conn.commit()

    def update_dependencies(self, dependencies_file: str):
        """Update the database with dependencies from a JSON file."""
        with open(dependencies_file, 'r') as f:
            data = json.load(f)

        fetch_time = datetime.fromisoformat(data['fetch_time'])
        time_range_start = data.get('start_time')
        time_range_end = data.get('end_time')

        if time_range_start:
            time_range_start = datetime.fromtimestamp(time_range_start)
        if time_range_end:
            time_range_end = datetime.fromtimestamp(time_range_end)

        cursor = self.conn.cursor()

        # Track which dependencies we've seen in this update
        seen_dependencies = set()

        for dep in data['dependencies']:
            parent = dep['parent_node']['name']
            child = dep['child_node']['name']
            call_count = dep.get('call_count', 0)

            seen_dependencies.add((parent, child))

            # Update or insert services
            for service in [parent, child]:
                cursor.execute("""
                    INSERT INTO services (name, first_seen, last_seen, active)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(name) DO UPDATE SET
                        last_seen = ?,
                        active = 1
                """, (service, fetch_time, fetch_time, fetch_time))

            # Update or insert dependency
            cursor.execute("""
                INSERT INTO dependencies
                (parent_service, child_service, first_seen, last_seen, total_calls, active)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(parent_service, child_service) DO UPDATE SET
                    last_seen = ?,
                    total_calls = total_calls + ?,
                    active = 1
            """, (parent, child, fetch_time, fetch_time, call_count,
                  fetch_time, call_count))

            # Add to history
            cursor.execute("""
                INSERT INTO dependency_history
                (parent_service, child_service, observed_at, call_count,
                 time_range_start, time_range_end)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (parent, child, fetch_time, call_count,
                  time_range_start, time_range_end))

        # Mark dependencies not seen as inactive
        cursor.execute("""
            UPDATE dependencies
            SET active = 0
            WHERE last_seen < ?
        """, (fetch_time,))

        # Mark services not seen as inactive
        cursor.execute("""
            UPDATE services
            SET active = 0
            WHERE last_seen < ?
        """, (fetch_time,))

        self.conn.commit()

        print(f"Updated {len(seen_dependencies)} dependencies")
        return len(seen_dependencies)

    def get_all_dependencies(self, active_only: bool = True) -> List[Dict]:
        """Get all dependencies from the database."""
        cursor = self.conn.cursor()

        query = "SELECT * FROM dependencies"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY parent_service, child_service"

        cursor.execute(query)

        dependencies = []
        for row in cursor.fetchall():
            dependencies.append({
                'parent_service': row['parent_service'],
                'child_service': row['child_service'],
                'first_seen': row['first_seen'],
                'last_seen': row['last_seen'],
                'total_calls': row['total_calls'],
                'active': bool(row['active'])
            })

        return dependencies

    def get_service_dependencies(self, service_name: str) -> Dict:
        """Get all dependencies for a specific service."""
        cursor = self.conn.cursor()

        # Get dependencies where service is parent
        cursor.execute("""
            SELECT * FROM dependencies
            WHERE parent_service = ? AND active = 1
            ORDER BY child_service
        """, (service_name,))

        outgoing = []
        for row in cursor.fetchall():
            outgoing.append({
                'service': row['child_service'],
                'first_seen': row['first_seen'],
                'last_seen': row['last_seen'],
                'total_calls': row['total_calls']
            })

        # Get dependencies where service is child
        cursor.execute("""
            SELECT * FROM dependencies
            WHERE child_service = ? AND active = 1
            ORDER BY parent_service
        """, (service_name,))

        incoming = []
        for row in cursor.fetchall():
            incoming.append({
                'service': row['parent_service'],
                'first_seen': row['first_seen'],
                'last_seen': row['last_seen'],
                'total_calls': row['total_calls']
            })

        return {
            'service': service_name,
            'outgoing_dependencies': outgoing,
            'incoming_dependencies': incoming
        }

    def get_new_dependencies(self, since_date: str) -> List[Dict]:
        """Get dependencies that were first seen after a specific date."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM dependencies
            WHERE first_seen >= ?
            ORDER BY first_seen DESC
        """, (since_date,))

        new_deps = []
        for row in cursor.fetchall():
            new_deps.append({
                'parent_service': row['parent_service'],
                'child_service': row['child_service'],
                'first_seen': row['first_seen'],
                'active': bool(row['active'])
            })

        return new_deps

    def get_removed_dependencies(self, since_date: str) -> List[Dict]:
        """Get dependencies that haven't been seen since a specific date."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM dependencies
            WHERE active = 0 AND last_seen >= ?
            ORDER BY last_seen DESC
        """, (since_date,))

        removed_deps = []
        for row in cursor.fetchall():
            removed_deps.append({
                'parent_service': row['parent_service'],
                'child_service': row['child_service'],
                'last_seen': row['last_seen']
            })

        return removed_deps

    def export_for_validation(self, output_file: str, format: str = 'json'):
        """Export dependencies in a format suitable for validation against internal systems."""
        dependencies = self.get_all_dependencies(active_only=True)

        if format == 'json':
            with open(output_file, 'w') as f:
                json.dump({
                    'export_time': datetime.now().isoformat(),
                    'total_dependencies': len(dependencies),
                    'dependencies': dependencies
                }, f, indent=2)

        elif format == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['parent_service', 'child_service', 'first_seen',
                               'last_seen', 'total_calls', 'active'])
                for dep in dependencies:
                    writer.writerow([
                        dep['parent_service'], dep['child_service'],
                        dep['first_seen'], dep['last_seen'],
                        dep['total_calls'], dep['active']
                    ])

        print(f"Exported {len(dependencies)} dependencies to {output_file}")

    def get_statistics(self) -> Dict:
        """Get statistics about the tracked dependencies."""
        cursor = self.conn.cursor()

        stats = {}

        # Total dependencies
        cursor.execute("SELECT COUNT(*) FROM dependencies WHERE active = 1")
        stats['active_dependencies'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dependencies WHERE active = 0")
        stats['inactive_dependencies'] = cursor.fetchone()[0]

        # Total services
        cursor.execute("SELECT COUNT(*) FROM services WHERE active = 1")
        stats['active_services'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM services WHERE active = 0")
        stats['inactive_services'] = cursor.fetchone()[0]

        # Most connected services
        cursor.execute("""
            SELECT s.name,
                   COUNT(DISTINCT d1.child_service) as outgoing,
                   COUNT(DISTINCT d2.parent_service) as incoming
            FROM services s
            LEFT JOIN dependencies d1 ON s.name = d1.parent_service AND d1.active = 1
            LEFT JOIN dependencies d2 ON s.name = d2.child_service AND d2.active = 1
            WHERE s.active = 1
            GROUP BY s.name
            ORDER BY (outgoing + incoming) DESC
            LIMIT 10
        """)

        stats['most_connected_services'] = []
        for row in cursor.fetchall():
            stats['most_connected_services'].append({
                'service': row[0],
                'outgoing': row[1],
                'incoming': row[2],
                'total': row[1] + row[2]
            })

        return stats

    def close(self):
        """Close the database connection."""
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Track and analyze service dependencies')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update dependencies from JSON file')
    update_parser.add_argument('dependencies_file', help='JSON file from dependency_fetcher.py')
    update_parser.add_argument('--db', default='dependencies.db', help='Database path')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export dependencies for validation')
    export_parser.add_argument('output_file', help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                              help='Export format')
    export_parser.add_argument('--db', default='dependencies.db', help='Database path')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query dependency information')
    query_parser.add_argument('--service', help='Get dependencies for a specific service')
    query_parser.add_argument('--new-since', help='Get new dependencies since date (YYYY-MM-DD)')
    query_parser.add_argument('--removed-since', help='Get removed dependencies since date')
    query_parser.add_argument('--stats', action='store_true', help='Show statistics')
    query_parser.add_argument('--db', default='dependencies.db', help='Database path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = DependencyTracker(args.db)

    try:
        if args.command == 'update':
            tracker.update_dependencies(args.dependencies_file)

        elif args.command == 'export':
            tracker.export_for_validation(args.output_file, args.format)

        elif args.command == 'query':
            if args.service:
                result = tracker.get_service_dependencies(args.service)
                print(json.dumps(result, indent=2))

            elif args.new_since:
                result = tracker.get_new_dependencies(args.new_since)
                print(f"\nNew dependencies since {args.new_since}:")
                print(json.dumps(result, indent=2))

            elif args.removed_since:
                result = tracker.get_removed_dependencies(args.removed_since)
                print(f"\nRemoved dependencies since {args.removed_since}:")
                print(json.dumps(result, indent=2))

            elif args.stats:
                stats = tracker.get_statistics()
                print("\nDependency Statistics:")
                print(f"Active dependencies: {stats['active_dependencies']}")
                print(f"Inactive dependencies: {stats['inactive_dependencies']}")
                print(f"Active services: {stats['active_services']}")
                print(f"Inactive services: {stats['inactive_services']}")

                print("\nMost connected services:")
                for svc in stats['most_connected_services']:
                    print(f"  {svc['service']}: {svc['total']} connections "
                          f"({svc['outgoing']} outgoing, {svc['incoming']} incoming)")
            else:
                print("Please specify a query option (--service, --new-since, --removed-since, or --stats)")

    finally:
        tracker.close()


if __name__ == '__main__':
    main()
