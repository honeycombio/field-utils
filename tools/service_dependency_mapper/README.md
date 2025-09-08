# Honeycomb Service Dependency Mapper

This repository contains two Python scripts to help extract, track, and validate service dependency data from Honeycomb's Service Maps API.

## Features

- **Dependency Data Extraction**: Fetch service dependency data from Honeycomb
- **Large-Scale Support**: Handle thousands of services efficiently with batching
- **Time-Based Querying**: Support for custom time ranges (e.g., last 7 days)
- **Change Tracking**: Track "first seen" and "last seen" timestamps for dependencies
- **Data Persistence**: SQLite database for lightweight storage
- **Export Capabilities**: Export data in JSON or CSV format for integration with internal systems
- **Validation Support**: Query and analyze dependency changes over time

## Requirements

- Python 3.6+
- No external dependencies (uses only Python standard library)
- Honeycomb API key with "Read Service Maps" permission

## Installation

Simply clone or download the scripts to your local machine:

```bash
git clone <repository>
cd tools/service_dependency_mapper
```

Make the scripts executable:

```bash
chmod +x dependency_fetcher.py dependency_tracker.py
```

**Note**: If `python` command is not available on your system, you may need to use `python3` instead. You can create an alias or modify the scripts' shebang line to use `python3` explicitly.

## Usage

### 1. Fetching Dependencies (`dependency_fetcher.py`)

This script fetches dependency data from Honeycomb's Service Maps API.

#### Basic Usage

Fetch all dependencies for the last 7 days:

```bash
python3 dependency_fetcher.py --api-key YOUR_API_KEY
```

#### With Service Filter

Fetch dependencies for specific services (from a file):

```bash
python3 dependency_fetcher.py --api-key YOUR_API_KEY --services-file services.txt
```

#### Custom Time Range

Fetch dependencies for a specific time period:

```bash
# Last 24 hours
python3 dependency_fetcher.py --api-key YOUR_API_KEY --time-range 86400

# Specific date range
python3 dependency_fetcher.py --api-key YOUR_API_KEY \
  --start-date 2024-01-01 --end-date 2024-01-07
```

#### All Options

```bash
python3 dependency_fetcher.py --help

Options:
  --api-key         Honeycomb API key (required)
  --api-url         Honeycomb API URL (default: https://api.honeycomb.io)
  --services-file   File containing service names (one per line)
  --time-range      Time range in seconds (default: 604800 = 7 days)
  --start-date      Start date (YYYY-MM-DD)
  --end-date        End date (YYYY-MM-DD)
  --output          Output file (default: dependencies.json)
  --batch-size      Batch size for service filters (default: 100)
  --limit           Max dependencies per request (default: 10000)
```

### 2. Tracking Dependencies (`dependency_tracker.py`)

This script manages a SQLite database to track dependencies over time.

#### Update Database

Load dependencies from the fetcher output:

```bash
python3 dependency_tracker.py update dependencies.json
```

#### Export for Validation

Export active dependencies for validation against internal systems:

```bash
# Export as JSON
python3 dependency_tracker.py export dependencies_export.json

# Export as CSV
python3 dependency_tracker.py export dependencies_export.csv --format csv
```

#### Query Dependencies

Get dependencies for a specific service:

```bash
python3 dependency_tracker.py query --service user-service
```

View new dependencies since a date:

```bash
python3 dependency_tracker.py query --new-since 2024-01-01
```

View removed dependencies:

```bash
python3 dependency_tracker.py query --removed-since 2024-01-01
```

View statistics:

```bash
python3 dependency_tracker.py query --stats
```

## Example Workflow

### 1. Create a services file (optional)

Create `services.txt`:

```
user-service
auth-service
payment-service
notification-service
# Add more services...
```

### 2. Initial dependency fetch

```bash
python3 dependency_fetcher.py --api-key YOUR_API_KEY \
  --services-file services.txt \
  --output initial_dependencies.json
```

### 3. Load into database

```bash
python3 dependency_tracker.py update initial_dependencies.json
```

### 4. Schedule regular updates

Create a cron job or scheduled task:

```bash
# Fetch new data daily
0 2 * * * cd /path/to/scripts && python3 dependency_fetcher.py --api-key YOUR_API_KEY --output daily_dependencies.json && python3 dependency_tracker.py update daily_dependencies.json
```

### 5. Export for validation

```bash
python3 dependency_tracker.py export weekly_report.json
```

### 6. Check for changes

```bash
# New dependencies in the last week
python3 dependency_tracker.py query --new-since $(date -d '7 days ago' +%Y-%m-%d)

# Services that are no longer connected
python3 dependency_tracker.py query --removed-since $(date -d '30 days ago' +%Y-%m-%d)
```

## Output Formats

### Fetcher Output (dependencies.json)

```json
{
  "fetch_time": "2024-01-15T10:30:00",
  "time_range": 604800,
  "start_time": null,
  "end_time": null,
  "total_dependencies": 150,
  "unique_services": 25,
  "dependencies": [
    {
      "parent_node": {
        "name": "user-service",
        "type": "service"
      },
      "child_node": {
        "name": "auth-service",
        "type": "service"
      },
      "call_count": 1523
    }
  ]
}
```

### Tracker Export (JSON)

```json
{
  "export_time": "2024-01-15T11:00:00",
  "total_dependencies": 150,
  "dependencies": [
    {
      "parent_service": "user-service",
      "child_service": "auth-service",
      "first_seen": "2024-01-01T00:00:00",
      "last_seen": "2024-01-15T10:30:00",
      "total_calls": 10523,
      "active": true
    }
  ]
}
```

## Database Schema

The tracker uses SQLite with the following tables:

- **dependencies**: Tracks unique service-to-service relationships
- **dependency_history**: Historical record of all observations
- **services**: List of all observed services

## Tips and Best Practices

1. **API Rate Limits**: The scripts include automatic delays between batches to avoid rate limiting

2. **Large Service Lists**: For thousands of services, use the `--batch-size` parameter to control how many services are queried at once

3. **Time Ranges**: Honeycomb's API may have limits on how far back you can query. The scripts default to 7 days

4. **Regular Updates**: Set up a scheduled job to fetch dependencies regularly for accurate tracking

5. **Database Backups**: The SQLite database (`dependencies.db`) contains all your historical data - back it up regularly

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure your API key has the "Read Service Maps" permission

2. **Empty Results**: Check that your services are actually generating traces with proper service names

3. **Timeout Errors**: Increase the timeout or reduce the batch size for large queries

4. **Database Locked**: Ensure only one process is writing to the database at a time

## Security Considerations

- Store API keys securely (use environment variables or secure key management)
- The SQLite database contains service relationship information - protect it appropriately
- Consider encrypting exports if they contain sensitive service topology information
