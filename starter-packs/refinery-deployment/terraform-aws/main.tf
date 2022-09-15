
module "refinery" {
  source                        = "./modules/refinery/"

  # Let us know what account and region you want to build this in
  aws_profile_name              = "profile-name"
  aws_region                    = "us-east-2"

  # VPC and Subnet to use
  vpc_name                      = "refinery-vpc"
  subnet_name                   = "refinery-vpc-public-us-east-2a"

  # Create Security Groups for each component
  refinery_security_group_name  = "refinery_sg"
  lb_security_group_name        = "refinery_lb_sg"
  redis_security_group_name     = "redis_sg"

  # What Route53 Hosted Zone do you want your ELB created in for
  #   directing traffic to your Refinery servers
  route53_zone                  = "example.com"

  # Where is traffic allowed to come from to reach these systems
  # Don't leave this as 0.0.0.0 unless you want anybody to use your refinery!
  security_group_ingress_cidr   = ["0.0.0.0/0"]

  # Define the name prefix and suffixes for your EC2 Instances
  # refinery_servers also provides the count of how many servers you will have based on array size
  system_name_prefix            = "hny-refinery"
  refinery_servers              = ["001", "002", "003"]
  redis_server                  = "redis"

  # EC2 Instance Sizes and Root Volume Size (in GB)
  refinery_instance_type        = "t4g.small"
  redis_instance_type           = "t4g.micro"
  system_root_volume_size       = 25

  # Redis access credentials
  redis_username                = "refinery"
  redis_password                = "onceuponatimeinagalaxyfarfaraway"

  # AWS SSH Key Pair to Use for the EC2 Instances
  aws_key                       = "my_aws_rsa_key"
  aws_key_file_local            = ".ssh/my_aws_rsa_key"

  # Tags to use on created objects
  contact_tag_value             = "executive@awesomesawce.io"
  department_tag_value          = "executive-awesomesawce"

  # Honeycomb API Key for sending Refinery metrics and logs
  honeycomb_api_key             = "555555555555555555555555"

  # Where to get the Refinery installer RPM
  refinery_rpm_url              = "https://github.com/honeycombio/refinery/releases/download/v1.15.0/refinery-1.15.0-1.aarch64.rpm"
  refinery_rpm                  = "refinery-1.15.0-1.aarch64.rpm"

  # The Refinery rules.toml template file and the necessary variable definitions
  refinery_rules_toml = templatefile("${path.root}/files/rules.toml", { 
    env_name = "microservices-refinery-demo"
  })
}

output "refinery_names" {
  description = "List of Names assigned to the instances"
  value       = module.refinery.instance_name_refinery_servers
}

output "refinery_dns" {
  value = module.refinery.public_dns_refinery_servers
}

output "refinery_ips" {
  description = "List of public IP addresses assigned to the refinery instances"
  value       = module.refinery.public_ip_refinery_servers
}

output "redis_names" {
  description = "List of Names assigned to the redis instance"
  value       = module.refinery.instance_name_redis_server
}

output "redis_dns" {
  value = module.refinery.public_dns_redis_server
}

output "redis_ips" {
  description = "List of public IP addresses assigned to the redis instance"
  value       = module.refinery.public_ip_redis_server
}

output "refinery_elb" {
  value = module.refinery.public_dns_elb
}