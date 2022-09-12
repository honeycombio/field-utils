#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

# Install Refinery
curl -L -o /tmp/refinery.rpm \
  https://github.com/honeycombio/refinery/releases/download/v${REFINERY_RELEASE}/refinery-${REFINERY_RELEASE}-1.aarch64.rpm
sudo rpm -ivh /tmp/refinery.rpm

# Install Honeycomb otel-collector
curl -o /tmp/otelcol \
  -L https://github.com/honeycombio/opentelemetry-collector-configs/releases/download/v${OTEL_CONFIG_RELEASE}/otelcol_hny_linux_arm64

sudo mv /tmp/honeycomb-metrics-config.yaml /etc/honeycomb-metrics-config.yaml
sudo mv /tmp/otelcol /usr/local/bin/otelcol
sudo chmod +x /usr/local/bin/otelcol

