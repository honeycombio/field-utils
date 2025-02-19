# Webhook Events Receiver Configuration

This is the helm values file needed to deploy a collector with the webhook events receiver enabled.

It includes ingress assuming the webhook emitter and receiver are not in the same cluster.

The design is to work with Auth0's webhook log stream so references to Auth0 are related to that.

## Instructions

```shell
kubectl create ns auth0
kubectl config set-context --current --namespace=auth0
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
```

```shell
kubectl create secret generic honeycomb --from-literal=api-key=hcaik_xxxxxxxxxxx---whatever----
```

Edit the otel-webhook-receiver.yaml file to set the correct certificate ARN and domain names.

```shell
helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector -f otel-webhook-receiver.yaml --debug --wait
```

## Notes

The webhook receiver is not in the K8s image so we have to  go to full contrib or make your own.

As-of this commit, the ability to read multiple lines from the same webhook request is not in the contrib image.
Pull request is here: https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/38042

The values file refers to this image: https://github.com/users/mterhar/packages/container/opentelemetry-collector-releases%2Fotelcol-contrib/359060571?tag=webhook-v1