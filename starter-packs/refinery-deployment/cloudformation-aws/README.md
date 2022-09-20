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


## Architecture Diagram

![Architecture Diagram](diagram.svg)


## Deployment

### Prerequisites

This template requires a VPC, SSL Certificate in ACM, SSH KeyPair and a preconfigured Security Group for admin access.
See [Prerequisites in Detail](#prerequisites-in-detail)

### Creating a cluster
You can launch this stack with the push of a button:
<p><a href="https://console.aws.amazon.com/cloudformation/home#/stacks/new?templateURL=https:%2F%2Fs3.amazonaws.com%2Frefinery-marketplace-test%2Frefinery.yaml&amp;stackName=Refinery-Prod" target="_blank"><img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png" alt="Launch Stack" /></a></p>

or via the aws CLI:
```bash
# clone and edit the stack parameters
cp stack_parameters.json.example stack_parameters.json
code stack_parameters.json

aws cloudformation create-stack \
  --template-url https://s3.amazonaws.com/refinery-marketplace-test/refinery.yaml \
  --stack-name Refinery-Prod \
  --capabilities CAPABILITY_IAM \
  --on-failure DO_NOTHING \
  --parameters file://stack_parameters.json

# To update a parameter or pick up a new stack version
aws cloudformation update-stack \
  --template-url https://s3.amazonaws.com/refinery-marketplace-test/refinery.yaml \
  --stack-name refinery-test \
  --capabilities CAPABILITY_IAM \
  --parameters file://stack_parameters.json
```

## Prerequisites in Detail

### Recommended: An external Route53 zone that is resolvable
For best results you should have a domain or subdomain that is hosted on Route53. With that, this template will create the Refinery DNS record for you (if you fill in `Route53HostedZone` and `Route53RecordName`), and will also greatly easy the creation of SSL certificates via ACM.


### SSL Certificate in ACM
You must create or upload at least one SSL certficate to AWS Certificate Manager (ACM).  If you wish, ACM can provide free SSL certificates for you and automatically manages renewals of those certificates.  For maximum convenience you can create a single wildcard certificate (ex: `*.mycompany.com`).  Since your Route53 zone is now working, use the `DNS Validation` option as it is far faster and more convenient.


### VPC
You must already have a VPC and subnets created. If you're feeling impatient you can use the default VPC and subnets. Provide the VPC ID and associated subnets to the `VPC` and `RefineryServerSubnets` parameters

1. Be split up into at least 2 subnets, each in different Availability Zones (AZ's)
2. Have enough IP's available to assign to nodes
3. Have an IGW or some way for the nodes to access the Internet (for sending metrics/logs back to Honeycomb)


### Security
1. You must have created/uploaded an SSH key to AWS. Provide the keypair name to the `SSHKeyName` parameter
2. You must also create a security group in the referenced VPC to define your administrative (SSH) access. If you're feeling impatient, you can use the default SG.  Provide sg ID to the `AdminSecurityGroupId` parameter.

### Contact Email Adress and Department Name
Supply a valid email address or team/DL alias in the `ContactEmail` field. Cloudwatch alerts will be sent to this address.

* At stack launch time you will receive an email titled `AWS Notification - Subscription Confirmation`
  * It's important you click the `Confirm subscription` button in this email or else you will not receive alerts



## TODO
* Better solution for Refinery rules file management & distribution
* Automatically tune `CacheCapacity`, `MaxAlloc` and buffer sizes based on instance size
* Ability to optionally disable Spot instance use

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
