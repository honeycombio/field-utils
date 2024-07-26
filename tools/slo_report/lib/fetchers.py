from .hnyapi import hnyapi_request, query_factory, craft_query_body
import json, logging, sys


class HoneycombFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

    def fetch_auth_info(self):
        """
        Fetch the auth info for the current user
        """
        response = hnyapi_request('auth', self.api_key)
        return f"Current team: {response['team']['name']}, environment: {response['environment']['name']}"

    def fetch_all_datasets(self):
        """
        Fetch all datasets in a team and return them as a list of dataset IDs
        """
        response = hnyapi_request('datasets', self.api_key)

        all_datasets = [dataset['name'] for dataset in response]
        return all_datasets

    def fetch_all_slos_for_dataset(self, dataset):
        """
        Fetch all SLOs in a dataset and return them all as json
        """
        self.logger.info(f"fetching SLOs for dataset: {dataset}")
        endpoint = f'slos/{dataset}'
        response = hnyapi_request(endpoint, self.api_key)

        all_slos = []
        for slo in response:
            self.logger.info(f"  slo {slo['name']} : {slo['id']}")
            all_slos.append(slo)

        return all_slos

    def fetch_burn_alerts_for_slo(self, dataset, slo_id):
        """
        Fetch burn alerts for a specific SLO in a dataset
        """
        self.logger.info(f"fetching burn alerts for dataset: {dataset}, slo_id: {slo_id}")

        endpoint = f'burn_alerts/{dataset}?slo_id={slo_id}'
        response = hnyapi_request(endpoint, self.api_key)

        return response

    def fetch_all_slos(self):
        all_datasets = self.fetch_all_datasets()
        if all_datasets is None:
            self.logger.critical('No datasets found')
            sys.exit(1)

        all_slos = []
        for dataset in all_datasets:
            slos_for_dataset = self.fetch_all_slos_for_dataset(dataset)
            for slo in slos_for_dataset:
                slo['dataset'] = dataset
                slo['burn_alerts'] = self.fetch_burn_alerts_for_slo(dataset, slo['id'])
                all_slos.append(slo)

        return all_slos

    def fetch_sli_data(self, sli, dataset):
        """
        Fetch SLI data for a SLO and return it as json
        """
        query = craft_query_body(time_range=3600, breakdowns=[sli, "service.name"], calculations=[{"op": "COUNT"}])
        query_result = query_factory(dataset, query, self.api_key)

        return query_result

    def fetch_sli_service_values_counts(self, slos, dataset):
        """
        Fetch SLI data for a list of SLOs and return the counts of service values
        """
        sli_names = [slo['sli']['alias'] for slo in slos]

        where_array = []
        for sli in sli_names:
            where_array.append({"column": sli, "op": "exists"})

        breakdowns = sli_names + ["service.name"]

        qb = craft_query_body(time_range=86400, filters=where_array, filter_combination="OR", breakdowns=breakdowns, calculations=[{"op": "COUNT"}])
        qr = query_factory(dataset, qb, self.api_key)

        self.logger.debug(json.dumps(qr, indent=2))
        if 'data' not in qr or 'results' not in qr['data']:
            self.logger.error(f"Query failed: {qr}")
            return []
        return self.agg_results(slos, qr['data']['results'])

    def agg_results(self, slos, results):
        """
        Aggregate the results of a query:
          - group by SLI
          - SUM of COUNT of true and false values
          - array of matching service.name values for each SLI
        """

        # iterate through sli list and aggregrate results
        for slo in slos:
            # initialize agg info to each slo
            slo['sli_values'] = {"true": 0, "false": 0}
            slo['sli_service_names'] = []

            sli = slo['sli']['alias']

            for result in results:
                res = result['data']
                # sum up all true counts
                if sli in res and res[sli] is True:
                    slo['sli_values']["true"] += res['COUNT']
                    # add deduped to service list
                    if 'service.name' in res and res['service.name'] not in slo['sli_service_names']:
                        slo["sli_service_names"].append(res['service.name'])
                    self.logger.debug(f"SLI: {sli}, true COUNT: {res['COUNT']}")

                # sum up all false counts
                if sli in res and res[sli] is False:
                    slo['sli_values']["false"] += res['COUNT']
                    # add deduped to service list
                    if 'service.name' in res and res['service.name'] not in slo['sli_service_names']:
                        slo["sli_service_names"].append(res['service.name'])
                    self.logger.debug(f"SLI: {sli}, false COUNT: {res['COUNT']}")

            slo['sli_event_count'] = slo['sli_values']["true"] + slo['sli_values']["false"]
            slo['sli_service_count'] = len(slo['sli_service_names'])

        return slos


    # example result:
    # "data": {
    #   "series": [],
    #   "results": [
    #     {
    #       "data": {
    #         "COUNT": 1023687,
    #         "service.name": "frontend",
    #         "sli.frontend-latency-3500": true,
    #         "sli.frontend-root-latency-4000ms": true,
    #         "zoc-doctest-availibility": true
    #       }
    #     },
    #     {
    #       "data": {
    #         "COUNT": 6187,
    #         "service.name": "frontend",
    #         "sli.frontend-latency-3500": true,
    #         "sli.frontend-root-latency-4000ms": true,
    #         "zoc-doctest-availibility": false
    #       }
    #     },
    #     {
    #       "data": {
    #         "COUNT": 221,
    #         "service.name": "frontend",
    #         "sli.frontend-latency-3500": false,
    #         "sli.frontend-root-latency-4000ms": true,
    #         "zoc-doctest-availibility": true
    #       }
    #     },
    #     {
    #       "data": {
    #         "COUNT": 188,
    #         "service.name": "frontend",
    #         "sli.frontend-latency-3500": false,
    #         "sli.frontend-root-latency-4000ms": false,
    #         "zoc-doctest-availibility": true
    #       }
    #     }
    #   ]
    # },
