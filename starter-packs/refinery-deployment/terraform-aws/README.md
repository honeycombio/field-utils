# Terraform Module For Honeycomb Refinery

A simple module for building a multi-node Refinery cluster using AWS EC2.

You will need to define the VPC and Subnet that you wish to use for building your cluster

## !!!!THIS IS A DEMO/EXAMPLE PRODUCT

Please understand that this is just an example of how one can use Terraform to stand up a Refinery cluster. It's not intended to be thrown directly into production, but to help guide users in standing up something similar for themselves.  It can also be used for quick demos or testing if desired.  Just please, use with care.

## What it does

1. Creates new security groups for the refinery instances, the redis instance, and the load balancer for the refinery instances
2. Creates a Redis server using Amazon Linux 2 EC2 Instances, with the default Redis 6 install provided by the `amazon-linux-extras` command
3. Creates a number of refinery servers - the number determined by the number of names provided to the `refinery_servers` variable. These are also Amazon Linux 2 EC2 Instances
4. Creates an ELB to direct traffic to your Refinery instances
    - This will create an ACM cert using a Route53 hosted zone in your environment. This cert will be for `refinery.lb.${route53_zone}`
    - It will also create a Route53 entry for `refinery.lb.${route53_zone}
    - The ELB will listen for HTTPS traffic at port `443` and GRPC traffic at port `4317`. These are both TLS encrypted endpoints, using the cert created.

The Redis configuration is managed via a template file in the module under `modules/refinery/files/redis.conf`. Right now this is a standard Redis config with the addition of turning off the default user, and setting up an authenticated user that Refinery will use to access Redis.  There's no TLS for this Redis, though that'd probably be a good thing to implement.

The Refinery `rules` configuration is actually a variable that's passed in the `main.tf` file.  This is stored as `files/rules.toml` in the repo, and referenced in the defining of the `refinery_rules_toml` variable. Right now, it's a very basic example that you can get from the [Refinery docs at Honeycomb](https://docs.honeycomb.io).  You should adjust these to suit your needs.

## More warnings

Please be advised, that as it currently exists, this creates a new VPC for all the networking bits and pieces that happen in the module.  It will also destroy that VPC when you do a `terraform destroy` so when adjusting this to suit your environment, please keep that in mind and maybe adjust it so that it doesn't manage a VPC but just utilizes one. :)

The Refinery installer used is the RPM installer from the GitHub releases page. This is given to the variables `refinery_rpm_url` and `refinery_rpm`.  There's no auto-discovery of the latest release, so these need to be updated when Honeycomb releases new Refinery versions.  These are also x86_64 versions as I've hardcoded the module to use x86_64 AMI's.  You can update the variables and the module reference if you want to use ARM64 instances though.
