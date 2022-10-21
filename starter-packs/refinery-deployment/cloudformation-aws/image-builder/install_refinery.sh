#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

# Install Refinery
curl -L -o /tmp/refinery.rpm \
  https://github.com/honeycombio/refinery/releases/download/v${REFINERY_RELEASE}/refinery-${REFINERY_RELEASE}-1.aarch64.rpm
sudo rpm -ivh /tmp/refinery.rpm

# Install the refinery config script
sudo mv /tmp/configure-refinery.sh /usr/local/bin/configure-refinery.sh
chmod +x /usr/local/bin/configure-refinery.sh

# Install Honeycomb otel-collector
curl -o /tmp/otelcol \
  -L https://github.com/honeycombio/opentelemetry-collector-configs/releases/download/v${OTEL_CONFIG_RELEASE}/otelcol_hny_linux_arm64

sudo mv /tmp/honeycomb-metrics-config.yaml /etc/honeycomb-metrics-config.yaml
sudo mv /tmp/otelcol /usr/local/bin/otelcol
sudo chmod +x /usr/local/bin/otelcol

cat <<EOF | sudo tee /etc/systemd/system/otel-collector.service
[Unit]
Description=otel-collector
After=network.target

[Service]
EnvironmentFile=/etc/otel-collector.env
ExecStart=/usr/local/bin/otelcol --config /etc/honeycomb-metrics-config.yaml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF | sudo tee /etc/otel-collector.env
HNY_API_KEY="ReplaceMe"
HNY_DATASET="hostmetrics"
OTEL_RESOURCE_ATTRIBUTES="service.name=refinery,deployment.environment=NotConfigured"
EOF

# Install crude
cd /tmp
curl -L -o - https://github.com/irvingpop/crude/releases/download/v0.1.2/crude_0.1.2_Linux_arm64.tar.gz | tar -xvzf - bin/crude
sudo mv bin/crude /usr/local/bin/crude

# Systemd unit file for crude
cat <<EOF | sudo tee /etc/systemd/system/crude.service
[Unit]
Description=Crude
After=network.target

[Service]
EnvironmentFile=/etc/crude.env
ExecStart=/usr/local/bin/crude
Restart=always

[Install]
WantedBy=multi-user.target
EOF
