resource "aws_instance" "redis_server" {

  ami                         = data.aws_ami.amazon-linux-2.id
  subnet_id                   = data.aws_subnet.refinery-subnet.id
  instance_type               = var.redis_instance_type
  vpc_security_group_ids      = [aws_security_group.redis_sg.id]
  associate_public_ip_address = true
  key_name                    = var.aws_key


  user_data = <<-EOF
    #!/bin/bash

    mkdir -p /etc/redis

    amazon-linux-extras install -y redis6

    echo "${templatefile("${path.module}/files/redis.conf", {
      redis_username = var.redis_username
      redis_password = var.redis_password
    })}" > /etc/redis/redis.conf

    chown redis:root /etc/redis/redis.conf

    systemctl start redis

  EOF


  root_block_device {
    volume_size = var.system_root_volume_size
  }

  tags = {
    Name      = "${var.system_name_prefix}-${var.redis_server}"
    X-Contact = var.contact_tag_value
    X-Dept    = var.department_tag_value
    Date      = formatdate("MMM DD, YYYY", timestamp())
  }

  # provisioner "file" {
  #   content = templatefile("${path.module}/files/redis.conf", {
  #     redis_username = var.redis_username
  #     redis_password = var.redis_password
  #   })

  #   destination = "/tmp/redis.conf"
  #   connection {
  #     host        = self.public_ip
  #     type        = "ssh"
  #     user        = var.provisioner_user
  #     private_key = file(var.aws_key_file_local)
  #   }
  # }

  # provisioner "remote-exec" {
  #   inline = [
  #     "sudo yum update -y",
  #     "sudo amazon-linux-extras install -y redis6",
  #     "sudo mv /tmp/redis.conf /etc/redis/redis.conf",
  #     "sudo chown redis:root /etc/redis/redis.conf",
  #     "sudo systemctl start redis",
  #   ]
  #   connection {
  #     host        = self.public_ip
  #     type        = "ssh"
  #     user        = var.provisioner_user
  #     private_key = file(var.aws_key_file_local)
  #   }
  # }
}
