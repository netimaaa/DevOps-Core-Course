# Yandex Cloud Configuration
variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "service_account_key_file" {
  description = "Path to service account key file"
  type        = string
  default     = "authorized_key.json"
}

variable "image_id" {
  description = "ID of the Ubuntu image to use"
  type        = string
  default     = "fd8kdq6d0p8sij7h5qe3" # Ubuntu 22.04 LTS
}

# SSH Configuration
variable "ssh_user" {
  description = "SSH username for VM access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}