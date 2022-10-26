#!/bin/bash -x

# Validate required variables
test -n "$REDIS_HOST" || exit 1
test -n "$REDIS_PORT" || exit 1
test -n "$REDIS_PASSWORD" || exit 1
test -n "$HONEYCOMB_API_KEY" || exit 1

# Calculate MaxAlloc and CacheCapacity based on 80% of available memory,
#  and CacheCapacity is MaxAlloc / 10,000
MEMTOTAL_KB=$(cat /proc/meminfo |grep ^MemTotal | awk '{print $2}')
MEMTOTAL_B=$(expr $MEMTOTAL_KB \* 1024)
MEMTOTAL_80PCT=$(echo "$MEMTOTAL_B * 0.8" | bc | awk '{printf "%d", $0}')
CACHE_CAPACITY=$(expr $MEMTOTAL_80PCT / 10000)

test -n "$MEMTOTAL_80PCT" || exit 1
test -n "$CACHE_CAPACITY" || exit 1

cat > /etc/refinery/refinery.toml <<EOF
ListenAddr = "0.0.0.0:8080"
GRPCListenAddr = "0.0.0.0:9090"
PeerListenAddr = "0.0.0.0:8081"
CompressPeerCommunication = true
APIKeys = [
  "*",                   # wildcard accept all keys
  ]
HoneycombAPI = "https://api.honeycomb.io"
SendDelay = "2s"
TraceTimeout = "60s"
MaxBatchSize = 500
SendTicker = "100ms"
LoggingLevel = "info"
UpstreamBufferSize = 10000
PeerBufferSize = 10000
AddHostMetadataToTrace = true
QueryAuthToken = "JolkienRolkienRolkienTolkien"
AddRuleReasonToTrace = true
AddSpanCountToRoot = true
Collector = "InMemCollector"
Logger = "honeycomb"
Metrics = "honeycomb"

[PeerManagement]
Type = "redis"
RedisHost = "${REDIS_HOST}:${REDIS_PORT}"
RedisPassword = "${REDIS_PASSWORD}"
UseTLS = true

[InMemCollector]
CacheCapacity = ${CACHE_CAPACITY}
MaxAlloc = ${MEMTOTAL_80PCT}

[HoneycombLogger]
LoggerHoneycombAPI = "https://api.honeycomb.io"
LoggerAPIKey = "${HONEYCOMB_API_KEY}"
LoggerDataset = "Refinery Logs"
LoggerSamplerEnabled = true
LoggerSamplerThroughput = 10

[HoneycombMetrics]
MetricsHoneycombAPI = "https://api.honeycomb.io"
MetricsAPIKey = "${HONEYCOMB_API_KEY}"
MetricsDataset = "Refinery Metrics"
MetricsReportingInterval = 60
EOF

cat > /etc/refinery/rules.toml <<EOF
Sampler = "DeterministicSampler"
SampleRate = 1
EOF

# Enable Refinery
/usr/bin/systemctl enable refinery || exit 1
/usr/bin/systemctl start refinery || exit 1
