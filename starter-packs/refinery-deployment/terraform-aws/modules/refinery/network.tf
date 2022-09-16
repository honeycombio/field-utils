data "aws_vpc" "refinery" {
  filter {
    name   = "tag:Name"
    values = [var.vpc_name]
  }
}

data "aws_subnet" "refinery-subnet" {
  filter {
    name   = "tag:Name"
    values = [var.subnet_name]
  }
}
