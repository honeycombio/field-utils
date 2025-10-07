resource "aws_instance" "refinery_servers" {

  depends_on                  = [aws_instance.redis_server]
  count                       = length(var.refinery_servers)
  ami                         = data.aws_ami.amazon-linux-2.id
  subnet_id                   = data.aws_subnet.refinery-subnet.id
  instance_type               = var.refinery_instance_type
  vpc_security_group_ids      = [aws_security_group.refinery_sg.id]
  associate_public_ip_address = true
  user_data                   = var.system_init_user_data
  key_name                    = var.aws_key

  root_block_device {
    volume_size = var.system_root_volume_size
  }

  tags = {
    Name       = "${var.system_name_prefix}-${var.refinery_servers[count.index]}"
    X-Contact  = var.contact_tag_value
    X-Dept     = var.department_tag_value
    Date       = formatdate("MMM DD, YYYY", timestamp())
    aws-apn-id = "pc:4cs7oby7dg5rzww2ys7u09nd7"
  }

  provisioner "file" {
    content = templatefile("${path.module}/files/refinery.toml", {
      redis_instance = aws_instance.redis_server.private_dns
      redis_port     = "6379"
      redis_username = var.redis_username
      redis_password = var.redis_password
      hny_api_key    = var.honeycomb_api_key
    })

    destination = "/tmp/refinery.toml"
    connection {
      host        = self.public_ip
      type        = "ssh"
      user        = var.provisioner_user
      private_key = file(var.aws_key_file_local)
    }
  }

  provisioner "file" {
    content      = var.refinery_rules_toml
    destination = "/tmp/rules.toml"
    connection {
      host        = self.public_ip
      type        = "ssh"
      user        = var.provisioner_user
      private_key = file(var.aws_key_file_local)
    }
  }

  provisioner "remote-exec" {
    inline = [
      "sudo yum update -y",
      "wget ${var.refinery_rpm_url}",
      "sudo yum localinstall -y ${var.refinery_rpm}",
      "sudo mv /tmp/refinery.toml /etc/refinery/refinery.toml",
      "sudo mv /tmp/rules.toml /etc/refinery/rules.toml",
      "sudo chown refinery:root /etc/redis/r*.toml",
      "sudo systemctl start refinery",
    ]
    connection {
      host        = self.public_ip
      type        = "ssh"
      user        = var.provisioner_user
      private_key = file(var.aws_key_file_local)
    }
  }
}

