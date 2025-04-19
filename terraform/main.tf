provider "aws" {
  region = var.aws_region
}

# Create a VPC
resource "aws_vpc" "blog_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "blog-vpc"
  }
}

# Create a public subnet
resource "aws_subnet" "blog_public_subnet" {
  vpc_id                  = aws_vpc.blog_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "blog-public-subnet"
  }
}

# Create an internet gateway
resource "aws_internet_gateway" "blog_igw" {
  vpc_id = aws_vpc.blog_vpc.id

  tags = {
    Name = "blog-igw"
  }
}

# Create a route table
resource "aws_route_table" "blog_public_rt" {
  vpc_id = aws_vpc.blog_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.blog_igw.id
  }

  tags = {
    Name = "blog-public-rt"
  }
}

# Associate the route table with the subnet
resource "aws_route_table_association" "blog_public_rt_assoc" {
  subnet_id      = aws_subnet.blog_public_subnet.id
  route_table_id = aws_route_table.blog_public_rt.id
}

# Create a security group
resource "aws_security_group" "blog_sg" {
  name        = "blog-sg"
  description = "Allow HTTP, HTTPS and SSH traffic"
  vpc_id      = aws_vpc.blog_vpc.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "blog-sg"
  }
}

# Create an EC2 instance
resource "aws_instance" "blog_instance" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.blog_sg.id]
  subnet_id              = aws_subnet.blog_public_subnet.id

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y python3-pip python3-dev nginx git
              git clone ${var.github_repo} /home/ubuntu/blog
              cd /home/ubuntu/blog
              pip3 install -r requirements.txt
              pip3 install gunicorn
              
              # Set up systemd service
              cat > /etc/systemd/system/blog.service <<EOT
              [Unit]
              Description=Portfolio Blog Flask Application
              After=network.target

              [Service]
              User=ubuntu
              WorkingDirectory=/home/ubuntu/blog
              ExecStart=/usr/local/bin/gunicorn -b 0.0.0.0:8000 app:app
              Restart=always

              [Install]
              WantedBy=multi-user.target
              EOT
              
              systemctl daemon-reload
              systemctl start blog
              systemctl enable blog
              
              # Configure Nginx
              cat > /etc/nginx/sites-available/blog <<EOT
              server {
                  listen 80;
                  server_name _;

                  location / {
                      proxy_pass http://localhost:8000;
                      proxy_set_header Host \$host;
                      proxy_set_header X-Real-IP \$remote_addr;
                  }
              }
              EOT
              
              ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled
              nginx -t
              systemctl restart nginx
              EOF

  tags = {
    Name = "blog-instance"
  }
}

# Output the public IP of the EC2 instance
output "public_ip" {
  value = aws_instance.blog_instance.public_ip
}
