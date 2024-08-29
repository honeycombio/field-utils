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

        required_columns = {
            "jvm.memory.used": "integer",
            "jvm.memory.limit": "integer",
            "jvm.memory.committed": "integer",
            "jvm.memory.used_after_last_gc": "integer",
            "jvm.memory.type": "string",
            "jvm.memory.pool.name": "string",
            "jvm.gc.duration.avg": "float",
            "jvm.gc.duration.max": "float",
            "jvm.gc.action": "string",
            "jvm.cpu.recent_utilization": "float",
            "host.name": "string",
        }

        if not check_dataset_exists(service_name, self.api_key, self.region):
            # Create the dataset
            create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        for column, column_type in required_columns.items():
            if not check_column_exists(service_name, column, self.api_key, self.region):
                create_column(service_name, column, column_type, self.api_key, self.region)

        # Query for JVM Memory (Young Generation)
        jvm_mem_yg_query_name = "JVM Memory (Young Generation)"
        jvm_mem_yg_query_description = "Eden space on the JVM heap is where newly created objects are stored. When it fills, a minor GC occurs, moving all \"live\" objects to the Survivor space. In addition to current memory usage, committed represents the guaranteed available memory, and limit represents maximum usable."
        jvm_mem_yg_qb = craft_query_body(time_range=86400,
                                         breakdowns=["jvm.memory.pool.name", "host.name"],
                                         filters=[
                                                {"column": "jvm.memory.type", "op": "=", "value": "heap"},
                                                {"column": "jvm.memory.pool.name", "op": "in", "value": ["Eden Space", "Survivor Space"]},
                                                {"column": "jvm.memory.used", "op": "exists"}
                                         ],
                                         calculations=[
                                                       {"op": "MAX", "column": "jvm.memory.used"},
                                                       {"op": "MAX", "column": "jvm.memory.committed"},
                                                       {"op": "MAX", "column": "jvm.memory.limit"},
                                                       {"op": "MAX", "column": "jvm.memory.used_after_last_gc"}
                                         ])
        queries.append(craft_board_query(service_name,
                                         jvm_mem_yg_query_name,
                                         jvm_mem_yg_query_description,
                                         jvm_mem_yg_qb,
                                         self.api_key, self.region))

        # Query for JVM Memory (Old Generation)
        jvm_mem_og_query_name = "JVM Memory (Old Generation)"
        jvm_mem_og_query_description = "Tenured Gen JVM heap space stores long-lived objects. When a Full or Major GC is performed, it is expensive and may pause app execution. Committed represents guaranteed available memory, and limit represents maximum usable memory."
        jvm_mem_og_qb = craft_query_body(time_range=86400,
                                         breakdowns=["jvm.memory.pool.name", "host.name"],
                                         filters=[
                                                {"column": "jvm.memory.type", "op": "=", "value": "heap"},
                                                {"column": "jvm.memory.pool.name", "op": "=", "value": "Tenured Gen"},
                                                {"column": "jvm.memory.used", "op": "exists"}
                                         ],
                                         calculations=[
                                                       {"op": "MAX", "column": "jvm.memory.used"},
                                                       {"op": "MAX", "column": "jvm.memory.committed"},
                                                       {"op": "MAX", "column": "jvm.memory.limit"},
                                                       {"op": "MAX", "column": "jvm.memory.used_after_last_gc"}
                                         ])
        queries.append(craft_board_query(service_name,
                                         jvm_mem_og_query_name,
                                         jvm_mem_og_query_description,
                                         jvm_mem_og_qb,
                                         self.api_key, self.region))

        # Query for JVM Memory (Non-Heap)
        jvm_mem_nh_query_name = "JVM Non-Heap Memory Usage"
        jvm_mem_nh_query_description = "JVM non-heap memory is allocated above and beyond the heap size you've configured. It is a section of memory in the JVM that stores class information (Metaspace), compiled code cache, thread stack, etc. It cannot be garbage collected."
        jvm_mem_nh_qb = craft_query_body(time_range=86400,
                                         breakdowns=["jvm.memory.pool.name", "host.name"],
                                         filters=[
                                                {"column": "jvm.memory.type", "op": "=", "value": "non_heap"},
                                                {"column": "jvm.memory.used", "op": "exists"}
                                         ],
                                         calculations=[
                                                       {"op": "MAX", "column": "jvm.memory.used"},
                                                       {"op": "MAX", "column": "jvm.memory.committed"},
                                                       {"op": "MAX", "column": "jvm.memory.limit"},
                                         ])
        queries.append(craft_board_query(service_name,
                                         jvm_mem_nh_query_name,
                                         jvm_mem_nh_query_description,
                                         jvm_mem_nh_qb,
                                         self.api_key, self.region))

        # Query for Garbage Collection
        jvm_gc_query_name = "JVM GC (Garbage Collection) Activity"
        jvm_gc_query_description = "JVM GC actions occur periodically to reclaim memory but consume CPU cycles to do so. In the worst cases, a GC can cause the entire JVM to pause, making the application appear unresponsive."
        jvm_gc_qb = craft_query_body(time_range=86400,
                                     breakdowns=["jvm.gc.action", "host.name"],
                                     filters=[{"column": "jvm.gc.action", "op": "exists"}],
                                     calculations=[
                                                 {"op": "AVG", "column": "jvm.gc.duration.avg"},
                                                 {"op": "MAX", "column": "jvm.gc.duration.max"}
                                     ])
        queries.append(craft_board_query(service_name,
                                         jvm_gc_query_name,
                                         jvm_gc_query_description,
                                         jvm_gc_qb,
                                         self.api_key, self.region))

        # Query for CPU Utilization
        jvm_cpu_query_name = "JVM CPU Utilization"
        jvm_cpu_query_description = "Shows system CPU utilization, as captured by the JVM"
        jvm_cpu_qb = craft_query_body(time_range=86400,
                                      breakdowns=["host.name"],
                                      filters=[{"column": "jvm.cpu.recent_utilization", "op": "exists"}],
                                      calculations=[{"op": "MAX", "column": "jvm.cpu.recent_utilization"}])
        queries.append(craft_board_query(service_name,
                                         jvm_cpu_query_name,
                                         jvm_cpu_query_description,
                                         jvm_cpu_qb,
                                         self.api_key, self.region))

        return queries

    def build_ruby_queries(self, service_name):
        logger.info("Building Ruby queries")
        queries = []

        # required_columns = {}

        # Create the dataset
        # if not check_dataset_exists(service_name, self.api_key, self.region):
        #     create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        # for column, column_type in required_columns.items():
        #     if not check_column_exists(service_name, column, self.api_key, self.region):
        #         create_column(service_name, column, column_type, self.api_key, self.region)

        logger.warning("No Ruby queries have been defined yet")

        return queries

    def build_python_queries(self, service_name):
        logger.info("Building Python queries")
        queries = []

        # required_columns = {}

        # Create the dataset
        # if not check_dataset_exists(service_name, self.api_key, self.region):
        #     create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        # for column, column_type in required_columns.items():
        #     if not check_column_exists(service_name, column, self.api_key, self.region):
        #         create_column(service_name, column, column_type, self.api_key, self.region)

        logger.warning("No Python queries have been defined yet")

        return queries

    def build_node_queries(self, service_name):
        logger.info("Building Node queries")
        queries = []

        # required_columns = {}

        # Create the dataset
        # if not check_dataset_exists(service_name, self.api_key, self.region):
        #     create_dataset(service_name, self.api_key, self.region)

        # Create the columns
        # for column, column_type in required_columns.items():
        #     if not check_column_exists(service_name, column, self.api_key, self.region):
        #         create_column(service_name, column, column_type, self.api_key, self.region)

        logger.warning("No Node queries have been defined yet")

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
            case "python":
                type_queries = self.build_python_queries(service_name)
            case "node":
                type_queries = self.build_node_queries(service_name)
            case "_":
                type_queries = []

        queries = service_queries + type_queries

        # Create the board
        board = craft_board(board_name, dataset, queries, self.api_key, self.region)

        # Print the board
        logger.info(f"Board URL: {board['links']['board_url']}")
        print('\n' + board['links']['board_url'])
