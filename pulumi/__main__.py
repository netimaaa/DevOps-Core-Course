"""
Pulumi program to create a VM on Yandex Cloud
This recreates the same infrastructure as the Terraform configuration
"""

import pulumi
import pulumi_yandex as yandex

# Get configuration
config = pulumi.Config()
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
image_id = config.get("image_id") or "fd8kdq6d0p8sij7h5qe3"  # Ubuntu 22.04 LTS
ssh_user = config.get("ssh_user") or "ubuntu"
ssh_public_key = config.require("ssh_public_key")

# Create VPC Network
network = yandex.VpcNetwork(
    "devops-network",
    name="devops-network",
    description="Network for DevOps course VM",
    folder_id=folder_id
)

# Create Subnet
subnet = yandex.VpcSubnet(
    "devops-subnet",
    name="devops-subnet",
    description="Subnet for DevOps course VM",
    v4_cidr_blocks=["10.128.0.0/24"],
    zone=zone,
    network_id=network.id,
    folder_id=folder_id
)

# Create Security Group
security_group = yandex.VpcSecurityGroup(
    "devops-security-group",
    name="devops-security-group",
    description="Security group for DevOps course VM",
    network_id=network.id,
    folder_id=folder_id,
    ingress=[
        # Allow SSH
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow SSH",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=22
        ),
        # Allow HTTP
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80
        ),
        # Allow custom port 5000
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow port 5000 for app",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=5000
        ),
    ],
    egress=[
        # Allow all outbound traffic
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all outbound traffic",
            v4_cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=65535
        ),
    ]
)

# Create Compute Instance (VM)
vm = yandex.ComputeInstance(
    "devops-vm",
    name="devops-vm",
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20  # 20% CPU for free tier
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image_id,
            size=10,
            type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id]
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}"
    },
    labels={
        "environment": "lab",
        "course": "devops",
        "lab": "lab04",
        "tool": "pulumi"
    }
)

# Export outputs
pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("vm_external_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_internal_ip", vm.network_interfaces[0].ip_address)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("ssh_connection", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh {ssh_user}@{ip}"
))