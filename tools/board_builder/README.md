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

To create a new board in honeycomb for a new service, use the following command. This will provide some standard queries without additions for specific languages

```shell
poetry run python3 board_builder.py -k HnyConfigurationAPIKey -n test-service-001
```

If you want to add queries to the board for specific language information, use the `-t` or `--service-type` command flags

```shell
poetry run python3 board_builder.py -k HnyConfigurationAPIKey -n test-service-001 -t java
```

Use the `-l` or `--log-level` option to set the logging level to either `info` or `debug` to get output useful for debugging.

```shell
poetry run python3 board_builder.py -k HnyConfigurationAPIKey -n test-service-001 -t java -l info
```

## Output

The successful running of this tool should output a URL to your new board via STDOUT
