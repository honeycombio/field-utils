import logging
from . import session, HONEYCOMB_API_US, HONEYCOMB_API_EU
import json

logger = logging.getLogger(__name__)


def hnyapi_url(region="us"):
    if region == "eu":
        return HONEYCOMB_API_EU
    else:
        return HONEYCOMB_API_US


def hnyapi_request(endpoint, api_key, region="us"):
    url = hnyapi_url(region) + endpoint
    response = session.get(url, headers={"X-Honeycomb-Team": api_key})
    response.raise_for_status()
    return response.json()


def check_dataset_exists(dataset, api_key, region="us"):
    logger.info(f"Checking if dataset: {dataset} exists")
    url = hnyapi_url(region) + 'datasets/' + dataset
    response = session.get(url, headers={"X-Honeycomb-Team": api_key})
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


def check_column_exists(dataset, column, api_key, region="us"):
    logger.info(f"Checking if column: {column} exists for dataset: {dataset}")
    url = hnyapi_url(region) + 'columns/' + dataset + '/' + column
    response = session.get(url, headers={"X-Honeycomb-Team": api_key})
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


def create_dataset(dataset, api_key, region="us"):
    logger.info(f"Creating dataset: {dataset}")
    url = hnyapi_url(region) + 'datasets'
    dataset_body = {
        "name": dataset
    }
    response = session.post(url, headers={"X-Honeycomb-Team": api_key}, json=json.dumps(dataset_body))
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()


def create_column(dataset, column, type, api_key, region="us"):
    logger.info(f"Creating column: {column} for dataset: {dataset}")
    url = hnyapi_url(region) + 'columns/' + dataset
    column_body = {
        "key_name": column,
        "type": type
    }
    response = session.post(url, headers={"X-Honeycomb-Team": api_key, "Content-Type": "application/json"}, json=json.dumps(column_body))
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()


# create a query using https://docs.honeycomb.io/api/tag/Queries#operation/createQuery
def create_query(dataset, query, api_key, region="us"):
    logger.info(f"Creating query for dataset: {dataset}")
    url = hnyapi_url(region) + 'queries/' + dataset
    response = session.post(url, headers={"X-Honeycomb-Team": api_key, "Content-Type": "application/json"}, json=json.dumps(query))
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()


def create_annotation(dataset, query_id, name, description, api_key, region="us"):
    logger.info(f"Creating annotation for query: {query_id}")
    url = hnyapi_url(region) + 'annotations/' + dataset
    annotation_body = {
        "query_id": query_id,
        "name": name,
        "description": description,
    }
    response = session.post(url, headers={"X-Honeycomb-Team": api_key, "Content-Type": "application/json"}, json=json.dumps(annotation_body))
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()


def craft_board_query(dataset, name, description, query_body, api_key, region="us"):
    logger.info(f"Crafting board query: {name}")
    logger.debug("Creating Query:" + f"{query_body}")
    query = create_query(dataset, query_body, api_key, region)
    logger.debug("Creating Annotation" + f"{name}")
    annotation = create_annotation(dataset, query["id"], name, description, api_key, region)
    board_query_reference = {
        "query_id": query['data']['id'],
        "annotation_id": annotation['data']['id']
    }
    return board_query_reference


# quick and dirty query body for QDAPI based on https://docs.honeycomb.io/api/tag/Queries#operation/createQuery
def craft_query_body(time_range=7200, breakdowns=None, calculations=None, filters=None, filter_combination="AND", limit=1000, havings=None):
    """
    Constructs a query body for API requests.

    Parameters:
    - time_range (str): The time range for the query. Default is "1h".
    - breakdowns (list): The breakdowns for the query. Default is None.
    - calculations (list): The calculations for the query. Default is None.
    - filters (list): The filters for the query. Default is None.
    - filter_combination (str): The filter combination logic, "AND" or "OR". Default is "AND".
    - limit (int): The limit on the number of results. Default is 10000.
    - havings (list): The having conditions for the query. Default is None.

    Returns:
    dict: The constructed query body.
    """
    # Initialize the query body with default values
    query_body = {
        "time_range": time_range,
        "filter_combination": filter_combination,
        "limit": limit,
        "calculations": [{"op": "COUNT"}] if calculations is None else calculations,
        "breakdowns": [] if breakdowns is None else breakdowns,
        "filters": [] if filters is None else filters,
        "havings": [] if havings is None else havings
    }

    return query_body


def craft_queries_json_for_boards(dataset, queries):
    data = []
    for query in queries:
        item = {
            "dataset": dataset,
            "query_id": query["query_id"],
            "query_annotation_id": query["annotation_id"],
            "graph_settings": {
                "hide_markers": False,
                "log_scale": False,
                "omit_missing_values": False,
                "stacked_graphs": False,
                "utc_xaxis": False,
                "overlaid_charts": False,
            }
        }
        data.append(item)
        return data


def craft_board(name, dataset, queries, api_key, region="us"):
    """
    Creates a board with the given name, dataset, and queries.

    Parameters:
    - name (str): The name of the board.
    - dataset (str): The dataset for the board.
    - queries (list): The list of queries for the board.
    - api_key (str): The Honeycomb API key.
    - region (str): The region for the board. Default is "us".

    Returns:
    dict: The response JSON from the API.
    """
    logger.info(f"Creating board: {name}")
    url = hnyapi_url(region) + 'boards'
    board = {
        "name": name,
        "dataset": dataset,
        "queries": craft_queries_json_for_boards(dataset, queries),
        "column_layout": "multi"
    }
    response = session.post(url, headers={"X-Honeycomb-Team": api_key, "Content-Type": "application/json"}, json=json.dumps(board))
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()
