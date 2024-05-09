# OpenTelemetry Playground

This repo has a few parts that allow you to play with opentelemetry using Docker Compose and cURL.

1. Clone the repository
1. Set up refinery in the `refinery` directory and start it with `docker compose up`
1. Edit the `otelcol-config.yaml` file so it has API keys and such
1. `docker compose up -d`
1. Edit your trace.json file
1. `curl -X POST -H "Content-Type: application/json" -d @trace.json -i http://localhost:4318/v1/traces`
1. Go into Honeycomb and take a look!

## Setting up OpenTelemetry Collector

Suggest that you create a few environments:

1. Raw spans environment for trace data
1. Metrics environment for information about the collector and refinery
1. Sampled spans environrment for refinery testing

Each exporter gets one of those API keys.

## Curling stuff

If you've started the collector 

curl -X POST -H "Content-Type: application/json" -d @trace.json -i http://localhost:4318/v1/traces
