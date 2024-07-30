from .hnyapi import hnyapi_request, query_factory, craft_query_body
import concurrent.futures, json, logging, sys
from itertools import batched


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

            # fetch burn alerts in parallel to speed things up where there's lots of SLOs
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_slo = {executor.submit(self.fetch_burn_alerts_for_slo, dataset, slo['id']): slo for slo in slos_for_dataset}

                for future in concurrent.futures.as_completed(future_to_slo):
                    slo = future_to_slo[future]
                    try:
                        slo['burn_alerts'] = future.result()
                        # add the dataset to the slo for convenience downstream
                        slo['dataset'] = dataset
                        all_slos.append(slo)
                    except Exception as exc:
                        self.logger.error(f"SLO {slo['id']} generated an exception: {exc}")

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
        batch_size = len(slos)
        attempts = 1

        # keep trying batches of increasingly smaller sizes down to batches of 1
        while attempts <= 10:
            results = []
            errors = 0
            for batch in batched(slos, batch_size):
                try:
                    sli_names = [slo['sli']['alias'] for slo in batch]
                    where_array = [{"column": sli, "op": "exists"} for sli in sli_names]
                    self.logger.error(f"Retry attempt {attempts} with batch size {batch_size} for SLIs: {sli_names}") if attempts > 1 else None
                    r = self.run_sli_query(dataset,
                                           filters=where_array,
                                           breakdowns=sli_names + ["service.name"])
                    results.extend(r)
                except Exception as e:
                    self.logger.error(f"Query attempt {attempts} failed for this batch of {batch_size}: {[slo['sli']['alias'] for slo in batch]}" + str(e))
                    errors += 1
                    if batch_size == 1:
                        self.logger.error("Query failed for single item batch, skipping this one but continuing")
                        # move on to next item batch
                        continue
                    # give up on this batch so we can retry with a smaller batch size
                    break

            # The batch finished, now what:
            if errors == 0:
                self.logger.info(f"Success on attempt {attempts} with batch size {batch_size}")
                return self.agg_results(slos, results)
            elif batch_size == 1:
                self.logger.error(f"Final attempt with batch size 1 had {errors} errors, returning partial results")
                return self.agg_results(slos, results)
            else:
                self.logger.error(f"Attempt {attempts} failed with {errors} errors, retrying with smaller batch size")
                # restart the inner loop with a smaller batch size and break out of the inner loop
                batch_size = batch_size // 2
                attempts += 1

        self.logger.error("Somehow all all attempts failed, returning nothing")
        return []

    def run_sli_query(self, dataset, filters, breakdowns):
        """
        Inputs:
            - dataset: dataset name
            - filters: list of filters
            - breakdowns: list of breakdowns
        Outputs:
            - Honeycomb query results object that is a list of dictionaries that look like:
                  {
                    "data": {
                        "COUNT": 594946845,
                        "service.name": "my_cool_service",
                        "my_cool_sli": true
                    }
                  },
        """
        qb = craft_query_body(time_range=86400,
                              filters=filters,
                              filter_combination="OR",
                              breakdowns=breakdowns,
                              calculations=[{"op": "COUNT"}])
        qr = query_factory(dataset, qb, self.api_key)

        if 'error' in qr:
            self.logger.debug("Raising exception: " + qr['error'])
            raise Exception(qr['error'])
        if 'data' not in qr or 'results' not in qr['data']:
            self.logger.debug("Raising exception: No query results returned")
            raise Exception("No query results returned")

        self.logger.debug(json.dumps(qr['data']['results'], indent=2))
        return qr['data']['results']

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
