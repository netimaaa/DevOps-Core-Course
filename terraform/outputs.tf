# VM Information
output "vm_id" {
  description = "ID of the created VM"
  value       = yandex_compute_instance.devops_vm.id
}

output "vm_name" {
  description = "Name of the created VM"
  value       = yandex_compute_instance.devops_vm.name
}

output "vm_external_ip" {
  description = "External IP address of the VM"
  value       = yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address
}

output "vm_internal_ip" {
  description = "Internal IP address of the VM"
  value       = yandex_compute_instance.devops_vm.network_interface[0].ip_address
}

# Network Information
output "network_id" {
  description = "ID of the VPC network"
  value       = yandex_vpc_network.devops_network.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = yandex_vpc_subnet.devops_subnet.id
}

# SSH Connection Command
output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address}"
}