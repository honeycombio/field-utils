variable "refinery_metrics_dataset" {
  description = "Dataset to use for refinery metrics"
  type        = string
  default     = "Refinery Metrics"
}

variable "refinery_logs_dataset" {
  description = "Dataset to use for refinery logs"
  type        = string
  default     = "Refinery Logs"
}

# variable "honeycomb_api_key" {
#   description = "Honeycomb API key"
#   type        = string
# }
