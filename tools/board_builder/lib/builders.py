from .hnyapi import craft_query_body, craft_board_query, craft_board, create_column, create_dataset, check_column_exists, check_dataset_exists
import logging

logger = logging.getLogger(__name__)


class HoneycombBuilder:
    def __init__(self, api_key, region="us"):
        self.api_key = api_key
        self.region = region
        self.logger = logging.getLogger(__name__)

    def build_service_queries(self, service_name):
        queries = []

        # Define the required columns
        required_columns = {
            "duration_ms": "float",
            "error": "boolean",
            "http.response.status_code": "integer",
            "status_code": "integer",
            "http.route": "string",
        }

        if not check_dataset_exists(service_name, self.api_key, self.region):
            # Create the dataset
            create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        for column, column_type in required_columns.items():
            if not check_column_exists(service_name, column, self.api_key, self.region):
                create_column(service_name, column, column_type, self.api_key, self.region)

        # Heatmap Query for Duration
        duration_query_name = "Latency"
        duration_query_description = "Heatmap of event duration in milliseconds"
        duration_qb = craft_query_body(time_range=86400,
                                       calculations=[
                                           {"op": "HEATMAP",
                                            "column": "duration_ms"}
                                            ])
        queries.append(craft_board_query(service_name,
                                         duration_query_name,
                                         duration_query_description,
                                         duration_qb,
                                         self.api_key, self.region))

        # Query for Error Counts
        error_query_name = "Error counts by status code"
        error_query_description = "Counts of events where error = true, grouped by status code"
        errors_qb = craft_query_body(time_range=86400,
                                     filters=[{"column": "error", "op": "exists"}],
                                     breakdowns=["http.response.status_code", "status_code"],
                                     calculations=[{"op": "COUNT"}])
        queries.append(craft_board_query(service_name,
                                         error_query_name,
                                         error_query_description,
                                         errors_qb,
                                         self.api_key, self.region))

        # Query for Route Breakdown
        routes_query_name = "Route Breakdown"
        routes_query_description = "Counts of events grouped by http.route"
        routes_qb = craft_query_body(time_range=86400,
                                     breakdowns=["http.route"],
                                     calculations=[{"op": "COUNT"}])
        queries.append(craft_board_query(service_name,
                                         routes_query_name,
                                         routes_query_description,
                                         routes_qb,
                                         self.api_key, self.region))

        return queries

    def build_java_queries(self, service_name):
        logger.info("Building Java queries")
        queries = []

        required_columns = {}

        if not check_dataset_exists(service_name, self.api_key, self.region):
            # Create the dataset
            create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        for column, column_type in required_columns.items():
            if not check_column_exists(service_name, column, self.api_key, self.region):
                create_column(service_name, column, column_type, self.api_key, self.region)

        return queries

    def build_ruby_queries(self, service_name):
        logger.info("Building Ruby queries")
        queries = []

        required_columns = {}

        if not check_dataset_exists(service_name, self.api_key, self.region):
            # Create the dataset
            create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        for column, column_type in required_columns.items():
            if not check_column_exists(service_name, column, self.api_key, self.region):
                create_column(service_name, column, column_type, self.api_key, self.region)

        return queries

    def build_service_board(self, service_name, service_type):
        """
        Inputs:
            - service_name: name of the service
            - service_type: type of the service
        Outputs:
            - None
        """
        self.logger.info(f"Building board for service: {service_name}")

        # Define the datasets to query
        dataset = service_name

        # Define the board name
        board_name = f"{service_name} Operations Overview"

        # Define the queries
        service_queries = self.build_service_queries(service_name)

        match service_type:
            case "java":
                type_queries = self.build_java_queries(service_name)
            case "ruby":
                type_queries = self.build_ruby_queries(service_name)
            case "_":
                type_queries = []

        queries = service_queries + type_queries

        # Create the board
        board = craft_board(board_name, dataset, queries, self.api_key, self.region)

        # Print the board
        logger.info(f"Board URL: {board['links']['board_url']}")
        print('\n' + board['links']['board_url'])
