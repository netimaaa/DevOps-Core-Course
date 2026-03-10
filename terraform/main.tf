terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
  required_version = ">= 1.0"
}

provider "yandex" {
  zone      = var.zone
  folder_id = var.folder_id
}

# VPC Network
resource "yandex_vpc_network" "devops_network" {
  name        = "devops-network"
  description = "Network for DevOps course VM"
}

# Subnet
resource "yandex_vpc_subnet" "devops_subnet" {
  name           = "devops-subnet"
  description    = "Subnet for DevOps course VM"
  v4_cidr_blocks = ["10.128.0.0/24"]
  zone           = var.zone
  network_id     = yandex_vpc_network.devops_network.id
}

# Security Group
resource "yandex_vpc_security_group" "devops_sg" {
  name        = "devops-security-group"
  description = "Security group for DevOps course VM"
  network_id  = yandex_vpc_network.devops_network.id

  # Allow SSH from anywhere (for lab purposes)
  ingress {
    protocol       = "TCP"
    description    = "Allow SSH"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 22
  }

  # Allow HTTP
  ingress {
    protocol       = "TCP"
    description    = "Allow HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  # Allow custom port 5000 for app deployment
  ingress {
    protocol       = "TCP"
    description    = "Allow port 5000 for app"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  # Allow all outbound traffic
  egress {
    protocol       = "ANY"
    description    = "Allow all outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

# Compute Instance (VM)
resource "yandex_compute_instance" "devops_vm" {
  name        = "devops-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20  # 20% CPU for free tier
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.devops_subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.devops_sg.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    environment = "lab"
    course      = "devops"
    lab         = "lab04"
    tool        = "terraform"
  }
}