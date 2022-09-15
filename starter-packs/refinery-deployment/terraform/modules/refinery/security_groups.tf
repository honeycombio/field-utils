
#############################
# Refinery ELB Security Group
#############################

resource "aws_security_group" "refinery_lb_sg" {
  name        = var.lb_security_group_name
  description = "expose ingress rules for refinery elb"
  vpc_id      = data.aws_vpc.refinery.id
  tags = {
    Name      = var.lb_security_group_name
    X-Contact = var.contact_tag_value
    X-Dept    = var.department_tag_value
    Date      = formatdate("MMM DD, YYYY", timestamp())
  }
}

resource "aws_security_group_rule" "ingress_rule_refinery_lb_https" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = var.security_group_ingress_cidr
  security_group_id = aws_security_group.refinery_lb_sg.id
}

resource "aws_security_group_rule" "ingress_rule_refinery_lb_grpc" {
  type              = "ingress"
  from_port         = 4317
  to_port           = 4317
  protocol          = "tcp"
  cidr_blocks       = var.security_group_ingress_cidr
  security_group_id = aws_security_group.refinery_lb_sg.id
}

resource "aws_security_group_rule" "refinery_lb_egress_rule" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.refinery_lb_sg.id
}

#############################
# Refinery Security Group
#############################

resource "aws_security_group" "refinery_sg" {
  name        = var.refinery_security_group_name
  description = "expose SSH and Refinery Ports"
  vpc_id      = data.aws_vpc.refinery.id
  tags = {
    Name      = var.refinery_security_group_name
    X-Contact = var.contact_tag_value
    X-Dept    = var.department_tag_value
    Date      = formatdate("MMM DD, YYYY", timestamp())
  }
}

resource "aws_security_group_rule" "ingress_rule_refinery_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = var.security_group_ingress_cidr
  security_group_id = aws_security_group.refinery_sg.id
}

resource "aws_security_group_rule" "ingress_rule_refinery_http" {
  type              = "ingress"
  from_port         = 8080
  to_port           = 8080
  protocol          = "tcp"
  security_group_id        = aws_security_group.refinery_sg.id
  source_security_group_id = aws_security_group.refinery_lb_sg.id
}

resource "aws_security_group_rule" "ingress_rule_refinery_grpc" {
  type              = "ingress"
  from_port         = 9090
  to_port           = 9090
  protocol          = "tcp"
  security_group_id        = aws_security_group.refinery_sg.id
  source_security_group_id = aws_security_group.refinery_lb_sg.id
}

resource "aws_security_group_rule" "ingress_rule_refinery_peer" {
  type              = "ingress"
  from_port         = 8081
  to_port           = 8081
  protocol          = "tcp"
  security_group_id        = aws_security_group.refinery_sg.id
  source_security_group_id = aws_security_group.refinery_sg.id
}

resource "aws_security_group_rule" "refinery_egress_rule" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.refinery_sg.id
}

#############################
# Redis Security Group
#############################

resource "aws_security_group" "redis_sg" {
  name        = var.redis_security_group_name
  description = "expose SSH and Refinery Ports"
  vpc_id      = data.aws_vpc.refinery.id
  tags = {
    Name      = var.redis_security_group_name
    X-Contact = var.contact_tag_value
    X-Dept    = var.department_tag_value
    Date      = formatdate("MMM DD, YYYY", timestamp())
  }
}

resource "aws_security_group_rule" "ingress_rule_redis_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = var.security_group_ingress_cidr
  security_group_id = aws_security_group.redis_sg.id
}

resource "aws_security_group_rule" "ingress_rule_redis_http" {
  type              = "ingress"
  from_port         = 6379
  to_port           = 6379
  protocol          = "tcp"
  security_group_id        = aws_security_group.redis_sg.id
  source_security_group_id = aws_security_group.refinery_sg.id
}

resource "aws_security_group_rule" "redis_egress_rule" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.redis_sg.id
}
