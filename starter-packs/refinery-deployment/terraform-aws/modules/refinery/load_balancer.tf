#########################
# S3 bucket for ELB logs
#########################
data "aws_elb_service_account" "this" {}

resource "aws_s3_bucket" "logs" {
  bucket        = "elb-refinery-logs"
  acl           = "private"
  policy        = data.aws_iam_policy_document.logs.json
  force_destroy = true
}

data "aws_iam_policy_document" "logs" {
  statement {
    actions = [
      "s3:PutObject",
    ]

    principals {
      type        = "AWS"
      identifiers = [data.aws_elb_service_account.this.arn]
    }

    resources = [
      "arn:aws:s3:::elb-refinery-logs/*",
    ]
  }
}

##################
# ACM certificate
##################
data "aws_route53_zone" "selected" {
  name = var.route53_zone
}

module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "~> 3.0"

  domain_name = "refinery.lb.${var.route53_zone}"
  zone_id     = data.aws_route53_zone.selected.zone_id
  
  subject_alternative_names = [
    "refinery.lb.${var.route53_zone}",
    ]

  wait_for_validation = true
}

######
# ELB
######
module "elb" {
  source = "terraform-aws-modules/elb/aws"

  name = "refinery-elb"

  subnets         = [data.aws_subnet.refinery-subnet.id]
  security_groups = [aws_security_group.refinery_lb_sg.id]
  internal        = false

  listener = [
    {
      instance_port     = "8080"
      instance_protocol = "HTTP"
      lb_port           = "443"
      lb_protocol       = "HTTPS"
      ssl_certificate_id = module.acm.acm_certificate_arn
    },
    {
      instance_port     = "9090"
      instance_protocol = "TCP"
      lb_port           = "4317"
      lb_protocol       = "TCP"
    },
  ]

  health_check = {
    target              = "HTTP:8080/alive"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
  }

  access_logs = {
    bucket = aws_s3_bucket.logs.id
  }

  tags = {
    Owner       = "user"
    Environment = "dev"
  }

  # ELB attachments
  number_of_instances = length(var.refinery_servers)
  instances           = aws_instance.refinery_servers.*.id
}


################################
# Create Route53 Entry for ELB
################################

resource "aws_route53_record" "refinery_lb" {
  zone_id = data.aws_route53_zone.selected.zone_id
  name = "refinery.lb.${var.route53_zone}"
  type = "A"

  alias {
    name = module.elb.elb_dns_name
    zone_id = module.elb.elb_zone_id
    evaluate_target_health = true
  }
}
