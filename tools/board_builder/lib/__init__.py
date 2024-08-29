import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

HONEYCOMB_API_US = 'https://api.honeycomb.io/1/'  # /columns/dataset_slug
HONEYCOMB_API_EU = 'https://api.eu1.honeycomb.io/1/'  # /columns/dataset_slug

# Define the retry strategy
retry_strategy = Retry(
    total=4,  # Maximum number of retries
    status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
)
# Create an HTTP adapter with the retry strategy and mount it to session
adapter = HTTPAdapter(max_retries=retry_strategy)

# Create a new session object
session = requests.Session()
session.mount('http://', adapter)
session.mount('https://', adapter)
