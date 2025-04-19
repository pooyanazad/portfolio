variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "eu-north-1"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance (Ubuntu 22.04 LTS)"
  default     = "ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository URL"
  type        = string
}
