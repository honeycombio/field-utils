# Add Collector Names to Telemetry Data

We want to add a field to each span, metric, and log that comes through where it says which collector it's traversed.
If you include the configuration on all of your collectors, you'll be able to better troubleshot pipeline failures or delays.

Note that collector pod names can be pretty long and events have a maximum size so try to keep the names concise.
In K8s, I'd suggest using the pod name since the alternative will be that all the spans coming through any pod will have the same name which defeats the purpose.

### Environment-variable names in Helm/Pod/Docker Compose

In the Helm values file, you can add a little snippet to inject variables into the collector.

Here are some examples (in addition to the HONEYCOMB_API_KEY) that is needed. You can use POD_NAME but it can be long. 
If you want to give it a more specific value, you can do that with something like "COLLECTOR_NAME".

```yaml
extraVars:
  - name: HONEYCOMB_API_KEY
    valueFrom:
      secretKeyRef:
        name: honeycomb
        key: api-key
  - name: POD_NAME
    valueFrom:
      fieldRef:
        apiVersion: v1
        fieldPath: metadata.name
  - name: PIPELINE_COMPONENT
    value: "agent"
  - name: COLLECTOR_NAME
    value: "$(POD_NAME)-agent"
```

If you're using Docker Compose, there isn't a "valueFrom" thing so just set the value.

```yaml
  env:
    COLLECTOR_NAME: "compose-agent"
```

## Collector Configuration

Using the Transform processor, you can add statements like these to each place they're relevant.
The examples below are for only trace data so if you're sending metrics through a similar pipeline, the statements should be in all pipelines.

### Example OTTL Configuration (Agent Collector)

```yaml
  transform/pipeline_steps:
    error_mode: ignore
    trace_statements:
      - statements:
          - set(resource.attributes["otel.collector.path"], "${env:COLLECTOR_NAME}") where resource.attributes["otel.collector.path"] == nil
          - set(resource.attributes["otel.collector.path"], Concat([resource.attributes["otel.collector.path"], "${env:COLLECTOR_NAME}"], " -> ")) where resource.attributes["otel.collector.path"] != nil
          - set(resource.attributes["otel.collector.gateway.pod.name"], "${env:COLLECTOR_NAME}")
    log_statements:
      - statements:
          - set(resource.attributes["otel.collector.path"], "${env:COLLECTOR_NAME}") where resource.attributes["otel.collector.path"] == nil
          - set(resource.attributes["otel.collector.path"], Concat([resource.attributes["otel.collector.path"], "${env:COLLECTOR_NAME}"], " -> ")) where resource.attributes["otel.collector.path"] != nil
          - set(resource.attributes["otel.collector.gateway.pod.name"], "${env:COLLECTOR_NAME}")
    metric_statements:
      - statements:
          - set(resource.attributes["otel.collector.path"], "${env:COLLECTOR_NAME}") where resource.attributes["otel.collector.path"] == nil
          - set(resource.attributes["otel.collector.path"], Concat([resource.attributes["otel.collector.path"], "${env:COLLECTOR_NAME}"], " -> ")) where resource.attributes["otel.collector.path"] != nil
          - set(resource.attributes["otel.collector.gateway.pod.name"], "${env:COLLECTOR_NAME}")
```

### Add the transform to the pipeline

```yaml
serices:
  pipelines:
    trace:
      receivers: [otlp]
      processors:
        - memory_limiter
        - transform/pipeline_steps
        - batch
      exporters: [otlp]
```

## Result Example

```plaintext
secondcol-1  | Resource attributes:
secondcol-1  |      -> service.name: Str(Website)
secondcol-1  |      -> service.version: Str(0.4.3)
secondcol-1  |      -> otel.collector.path: Str(firstcol -> secondcol)
secondcol-1  |      -> otel.collector.agent.pod.name: Str(firstcol)
secondcol-1  |      -> otel.collector.gateway.pod.name: Str(secondcol)
```

Now you can see all the collectors that participate in the node.

### If you don't do the `where` part

It will add "nil" to the concatenated object like this: `Str(<nil> -> firstcol -> secondcol)`

So sadly, you do have to have 2 lines in the transform, one for set and one for unset.
