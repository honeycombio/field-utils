data "honeycombio_query_specification" "refinery-health" {
  calculation {
    op     = "HEATMAP"
    column = "process_uptime_seconds"
  }

  calculation {
    op     = "HEATMAP"
    column = "num_goroutines"
  }

  calculation {
    op     = "HEATMAP"
    column = "memory_inuse"
  }

  breakdowns = ["hostname"]
}
