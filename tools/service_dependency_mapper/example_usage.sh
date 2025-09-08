#!/bin/bash

# Example usage script for Honeycomb Service Dependency Mapper
# This demonstrates a typical workflow

# Check if API key is provided
if [ -z "$HONEYCOMB_API_KEY" ]; then
    echo "Please set HONEYCOMB_API_KEY environment variable"
    echo "Example: export HONEYCOMB_API_KEY=your_api_key_here"
    exit 1
fi

echo "=== Honeycomb Service Dependency Mapper Example ==="
echo

# Step 1: Fetch all dependencies for the last 7 days
echo "1. Fetching all dependencies for the last 7 days..."
python3 dependency_fetcher.py \
    --api-key "$HONEYCOMB_API_KEY" \
    --output all_dependencies.json

echo
echo "2. Loading dependencies into database..."
python3 dependency_tracker.py update all_dependencies.json

echo
echo "3. Viewing statistics..."
python3 dependency_tracker.py query --stats

echo
echo "4. Exporting active dependencies as JSON..."
python3 dependency_tracker.py export active_dependencies_export.json

echo
echo "5. Example: Fetching dependencies for specific services..."
echo "   Creating a sample services file..."
cat > sample_services.txt << EOF
user-service
auth-service
payment-service
EOF

python3 dependency_fetcher.py \
    --api-key "$HONEYCOMB_API_KEY" \
    --services-file sample_services.txt \
    --output filtered_dependencies.json

echo
echo "6. Updating database with filtered results..."
python3 dependency_tracker.py update filtered_dependencies.json

echo
echo "=== Example complete! ==="
echo
echo "Files created:"
echo "  - all_dependencies.json: Raw data from Honeycomb"
echo "  - filtered_dependencies.json: Filtered data for specific services"
echo "  - dependencies.db: SQLite database with historical data"
echo "  - active_dependencies_export.json: Export for validation"
echo
echo "Try these commands to explore further:"
echo "  python3 dependency_tracker.py query --service user-service"
echo "  python3 dependency_tracker.py query --new-since $(date -d '1 day ago' +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)"
echo "  python3 dependency_tracker.py export dependencies.csv --format csv"
