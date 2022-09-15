# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# You must provide a value for each of these parameters.
# ---------------------------------------------------------------------------------------------------------------------

variable "vpc_name" {
  description = "VPC name to use"
  type        = string
}

variable "subnet_name" {
  description = "Subnet name to use"
  type        = string
}

variable "aws_profile_name" {
  description = "The name of the aws profile needed for intended use"
  type        = string
}

variable "aws_region" {
  description = "The name of the region in the instance will live"
  type        = string
}

variable "refinery_security_group_name" {
  description = "The name of the security group to create/use for the refinery server"
  type        = string
}

variable "redis_security_group_name" {
  description = "The name of the security group to create/use for the redis server"
  type        = string
}

variable "security_group_ingress_cidr" {
  description = "CIDR block list to be allowed ingress access to ec2 instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "refinery_servers" {
  description = "Names of Refinery Servers"
  type        = list(string)
}

variable "redis_server" {
  description = "Name of Redis server"
  type        = string
}

variable "refinery_instance_type" {
  description = "The instance type"
  type        = string
  default     = "t3.small"
}

variable "redis_instance_type" {
  description = "The instance type"
  type        = string
  default     = "t3.micro"
}

variable "aws_key" {
  description = "Name of AWS key pair to use"
  type        = string
  default     = ""
}

variable "aws_key_file_local" {
  description = "Path to AWS key PEM file on local filesystem"
  type        = string
  default     = ""
}

variable "system_root_volume_size" {
  type    = number
  default = 25
}

variable "system_name_prefix" {
  description = "Prefix for the system name as it will be displayed in EC2."
  type        = string
}

variable "contact_tag_value" {
  description = "Contact Information"
  type        = string
}

variable "department_tag_value" {
  description = "Department Information"
  type        = string
}

variable "system_init_user_data" {
  description = "User Data block to pass to instance"
  type        = string
  default     = ""
}

variable "provisioner_user" {
  description = "Username for SSHing to Refinery Servers"
  type        = string
  default     = "ec2-user"
}

variable "provisioner_exec_data_refinery" {
  description = "Lines to sent to remote-exec provisioner"
  type        = list(string)
  default     = ["echo 'nothing to do'"]
}

variable "redis_username" {
  description = "The username to log into the redis server"
  type = string
}

variable "redis_password" {
  description = "The password for the redis_username"
  type = string
}

variable "honeycomb_api_key" {
  description = "The Honeycomb API key to send Logs and Metrics to"
  type = string
}

variable "route53_zone" {
  description = "The Route53 Hosted Zone to be used by ACM for the ELB"
  type = string
}

variable "lb_security_group_name" {
  description = "The security group name for the front side of the ELB"
  type = string
}

variable "refinery_rules_toml" {
  description = "The rules.toml file contents for supplying sampling rules to the refinery servers"
  type = string
}

variable "refinery_rpm_url" {
  type = string
}

variable "refinery_rpm" {
  type = string
}
