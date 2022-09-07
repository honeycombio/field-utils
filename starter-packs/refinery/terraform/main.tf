# Terraform configuration

terraform {
  required_providers {
    honeycombio = {
      source  = "honeycombio/honeycombio"
      version = "~> 0.10.0"
    }
  }
}

provider "honeycombio" {
  # api_key = var.honeycomb_api_key
  # You can set the API key with the environment variable HONEYCOMB_API_KEY
}
