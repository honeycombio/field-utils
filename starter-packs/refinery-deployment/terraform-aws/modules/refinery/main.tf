# ---------------------------------------------------------------------------------------------------------------------
# module: refinery
# Used to create a Honeycomb Refinery cluster on EC2 Instances

# Places a restraint on using a specific version of terraform
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  profile = var.aws_profile_name
  region  = var.aws_region
}

data "aws_ami" "amazon-linux-2" {
  most_recent = true
  name_regex = "^amzn2-ami-hvm-.*arm64-gp2$"
  owners     = ["amazon"]
}
