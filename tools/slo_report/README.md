# Honeycomb SLO Report Tool

## Prerequisites:
- Python 3.12+
- Requests module
- A Honeycomb API key with the "Run Queries and Manage SLOs" permission

## Setup
```
poetry install
```

or

```
pip3 install requests
```

or simply ensure that the `requests` module is installed

## To run
```
poetry run python3 slo_report.py -k HnyConfigurationAPIKey
```
