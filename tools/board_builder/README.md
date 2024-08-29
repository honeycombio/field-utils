# Board Builder Tool

A quick tool to build a default honeycomb board for a new service

## Prerequisites

- Python 3.12+
- Requests module
- A Honeycomb API key with the "Run Queries and Manage SLOs" permission

## Setup

```shell
poetry install
```

or

```shell
pip3 install requests
```

or simply ensure that the `requests` module is installed

## To run

```shell
poetry run python3 board_builder.py -k HnyConfigurationAPIKey -n test-service-001 -t java
```

## Debugging/Info

Use the `-l` or `--log-level` option to set the logging level to either `info` or `debug` to get output useful for debugging.

```shell
poetry run python3 board_builder.py -k HnyConfigurationAPIKey -n test-service-001 -t java -l info
```
