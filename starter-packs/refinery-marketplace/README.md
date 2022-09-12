# Refinery AWS Cloudformation Deployment

This project aims to build a click-to-run deployment solution for Refinery that:
* Matches the patterns and best practices for high-performance cloud-native Refinery clusters
* Aims to be as easy to deploy as humanly possible for AWS users
* Aims to be relatively easy to run: update-able, self-healing, auto-scaling

Features:
* Uses AWS Graviton (ARM), Amazon Linux 2022 and Spot instance pricing for maximum performance and cost effectiveness
* Uses Autoscaling group to dynamically scale the cluster size up and down based on CPU usage
* Everything is provisioned for High Availability by default
* All Refinery Metrics and Logs, as well as host metrics are sent to Honeycomb for easy analysis


## Deployment

You can launch this stack with the push of a button:
<p><a href="https://console.aws.amazon.com/cloudformation/home#/stacks/new?templateURL=https:%2F%2Fs3.amazonaws.com%2Frefinery-marketplace-test%2Frefinery.yaml&amp;stackName=Refinery-Prod" target="_blank"><img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png" alt="Launch Stack" /></a></p>

## TODO
* Better solution for Refinery rules file management & distribution
* Automatically tune `CacheCapacity`, `MaxAlloc` and buffer sizes based on instance size

## LocalDev workflow

```bash
# Validate the template
aws cloudformation validate-template --template-body file://refinery.yaml

# Create a stack
aws cloudformation create-stack --template-body file://refinery.yaml \
  --stack-name refinery-test \
  --capabilities CAPABILITY_IAM \
  --on-failure DO_NOTHING \
  --parameters file://stack_parameters.json

# Update the stack
aws cloudformation update-stack --template-body file://refinery.yaml \
  --stack-name refinery-test \
  --capabilities CAPABILITY_IAM \
  --parameters file://stack_parameters.json

# Publish
aws s3 cp refinery.yaml s3://refinery-marketplace-test/refinery.yaml --acl public-read
```
