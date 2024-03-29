packer {
  required_plugins {
    amazon = {
      version = ">= 1.1.1"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

source "amazon-ebs" "al2022" {
  ami_name        = "refinery-marketplace-image-builder-${legacy_isotime("200601021504")}"
  ami_description = "Honeycomb Refinery Marketplace Image"
  instance_type   = "t4g.medium"
  region          = "us-west-2"
  ssh_username    = "ec2-user"
  ebs_optimized   = true
  ena_support     = true
  sriov_support   = true

  launch_block_device_mappings {
    volume_size           = 8
    delete_on_termination = true
    volume_type           = "gp3"
    device_name           = "/dev/xvda"
  }

  // the trick to finding these names:
  // aws ec2 describe-images --owners amazon --query 'Images[*].{ID:ImageId, Name:Name}' --output text --filters "Name=name,Values=al2023-ami-2023*-arm64"
  source_ami_filter {
    filters = {
      name                = "al2023-ami-2023*-arm64"
    }
    most_recent = true
    owners      = ["amazon"]
  }

  tags = {
    os_version        = "Amazon Linux 2022"
    source_image_name = "{{ .SourceAMIName }}"
    ami_type          = "al2023arm"
    ami_version       = "0.2"
    Name              = "Honeycomb Refinery Marketplace Image"
  }

  ami_groups = ["all"]

  ami_regions = [
    // "ap-northeast-1",
    // "ap-northeast-2",
    // "ap-south-1",
    // "ap-southeast-1",
    // "ap-southeast-2",
    "ca-central-1",
    "eu-central-1",
    "eu-north-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    // "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
  ]
}

build {
  name = "honeycomb-refinery-marketplace"
  sources = [
    "source.amazon-ebs.al2022"
  ]

  provisioner "file" {
    source = "honeycomb-metrics-config.yaml"
    destination = "/tmp/honeycomb-metrics-config.yaml"
  }

  provisioner "file" {
    source = "configure-refinery.sh"
    destination = "/tmp/configure-refinery.sh"
  }

  provisioner "shell" {
    environment_vars = [
      "REFINERY_RELEASE=1.21.0",
      "OTEL_CONFIG_RELEASE=1.7.0",
      "CRUDE_RELEASE=0.1.5",
    ]
    scripts = [
      "install_refinery.sh",
    ]
  }

}
