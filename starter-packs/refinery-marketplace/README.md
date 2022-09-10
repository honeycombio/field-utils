# Refinery AWS Cloudformation Deployment

This project aims to build a click-to-run deployment solution for Refinery that:
* Matches the patterns and best practices for high-performance cloud-native Refinery clusters
* Aims to be as easy to deploy as humanly possible for AWS users
* Aims to be relatively easy to run: update-able, self-healing, auto-scaling

## TODO
* Auth for Redis
* Implement Packer in order to eliminate all artifact downloading
* Better solution for Refinery rules management

## LocalDev

aws cloudformation validate-template --template-body file://refinery.yaml

aws cloudformation create-stack --template-body file://refinery.yaml \
  --stack-name irving-refinery \
  --capabilities CAPABILITY_IAM \
  --on-failure DO_NOTHING \
  --parameters file://stack_parameters.json

aws cloudformation update-stack --template-body file://refinery.yaml \
  --stack-name irving-refinery \
  --capabilities CAPABILITY_IAM \
  --parameters file://stack_parameters.json
