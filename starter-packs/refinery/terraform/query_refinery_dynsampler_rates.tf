resource "honeycombio_column" "dynsampler_sample_rate_max" {
  key_name    = "dynsampler_sample_rate_max"
  type        = "float"
  dataset = var.refinery_metrics_dataset
}

resource "honeycombio_column" "dynsampler_sample_rate_p95" {
  key_name    = "dynsampler_sample_rate_p95"
  type        = "float"
  dataset = var.refinery_metrics_dataset
}

resource "honeycombio_column" "dynsampler_sample_rate_avg" {
  key_name    = "dynsampler_sample_rate_avg"
  type        = "float"
  dataset = var.refinery_metrics_dataset
}

resource "honeycombio_column" "dynsampler_sample_rate_min" {
  key_name    = "dynsampler_sample_rate_min"
  type        = "float"
  dataset = var.refinery_metrics_dataset
}


data "honeycombio_query_specification" "refinery-dynsampler-rates" {
  calculation {
    op     = "HEATMAP"
    column = "dynsampler_sample_rate_max"
  }

  calculation {
    op     = "HEATMAP"
    column = "dynsampler_sample_rate_p95"
  }

  calculation {
    op     = "HEATMAP"
    column = "dynsampler_sample_rate_avg"
  }

  calculation {
    op     = "HEATMAP"
    column = "dynsampler_sample_rate_min"
  }

  depends_on = [
    honeycombio_column.dynsampler_sample_rate_max,
    honeycombio_column.dynsampler_sample_rate_p95,
    honeycombio_column.dynsampler_sample_rate_avg,
    honeycombio_column.dynsampler_sample_rate_min,
  ]
}
