output "instance_name_refinery_servers" {
  description = "List of Names assigned to the instances"
  value       = aws_instance.refinery_servers.*.tags.Name
}

output "public_ip_refinery_servers" {
  description = "List of public IP addresses assigned to the instances"
  value       = aws_instance.refinery_servers.*.public_ip
}

output "public_dns_refinery_servers" {
  description = "List of public DNS names assigned to the instances. For EC2-VPC, this is only available if you've enabled DNS hostnames for your VPC"
  value       = aws_instance.refinery_servers.*.public_dns
}

output "instance_name_redis_server" {
  description = "The AWS Instance Name of the Redis Server"
  value = aws_instance.redis_server.tags.Name
}

output "public_ip_redis_server" {
  description = "Public IP address assigned to the Redis Server"
  value = aws_instance.redis_server.public_ip
}

output "public_dns_redis_server" {
  description = "Public DNS name of the Redis Server"
  value = aws_instance.redis_server.public_dns
}

output "public_dns_elb" {
  value = module.elb.elb_dns_name
}
