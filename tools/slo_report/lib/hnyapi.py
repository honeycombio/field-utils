import logging, time
from . import session, HONEYCOMB_API

logger = logging.getLogger(__name__)

def hnyapi_request(endpoint, api_key):
    url = HONEYCOMB_API + endpoint
    response = session.get(url, headers={"X-Honeycomb-Team": api_key})
    response.raise_for_status()
    return response.json()

# create a query using https://docs.honeycomb.io/api/tag/Queries#operation/createQuery
def create_query(dataset, query, api_key):
    logger.info(f"Creating query for dataset: {dataset}")
    url = HONEYCOMB_API + 'queries/' + dataset
    response = session.post(url, headers={"X-Honeycomb-Team": api_key, "Content-Type": "application/json"}, json=query)
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()

# create a query result using https://docs.honeycomb.io/api/tag/Query-Data#operation/createQueryResult
def create_query_result(dataset, query_id, api_key):
    logger.info(f"Creating query result for query_id: {query_id}")
    url = HONEYCOMB_API + 'query_results/' + dataset
    qrjson = {"query_id": query_id, "disable_series": True, "limit": 10000}
    response = session.post(url, headers={"X-Honeycomb-Team": api_key, "Content-Type": "application/json"}, json=qrjson)
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()

# poll for a query result using https://docs.honeycomb.io/api/tag/Query-Data#operation/getQueryResult
def get_query_result(dataset, query_result_id, api_key):
    logger.info(f"Getting query result for query_result_id: {query_result_id}")
    url = HONEYCOMB_API + 'query_results/' + dataset + '/' + query_result_id
    response = session.get(url, headers={"X-Honeycomb-Team": api_key})
    logger.debug(response.text)
    response.raise_for_status()
    return response.json()

def query_factory(dataset, query, api_key):
    # create a query
    query_response = create_query(dataset, query, api_key)
    query_id = query_response['id']

    # create a query result from the query_id
    query_result = create_query_result(dataset, query_id, api_key)
    query_result_id = query_result['id']

    # poll get_query_result every second up to 30 times until complete = true
    for i in range(90):
        query_result = get_query_result(dataset, query_result_id, api_key)
        if query_result['complete']:
            return query_result
        else:
            time.sleep(1)


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
