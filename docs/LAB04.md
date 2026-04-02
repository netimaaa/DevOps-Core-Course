# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

## Overview

This lab demonstrates Infrastructure as Code (IaC) by creating a virtual machine on Yandex Cloud using both Terraform and Pulumi. The goal is to understand different IaC approaches and compare declarative (Terraform/HCL) vs imperative (Pulumi/Python) methodologies.

## Table of Contents

1. [Cloud Provider & Infrastructure](#1-cloud-provider--infrastructure)
2. [Terraform Implementation](#2-terraform-implementation)
3. [Pulumi Implementation](#3-pulumi-implementation)
4. [Terraform vs Pulumi Comparison](#4-terraform-vs-pulumi-comparison)
5. [Lab 5 Preparation & Cleanup](#5-lab-5-preparation--cleanup)

---

## 1. Cloud Provider & Infrastructure

### Cloud Provider Selection

**Provider:** Yandex Cloud

**Rationale:**
- **Accessibility:** Available in Russia without restrictions
- **Free Tier:** Offers 1 VM with 20% vCPU and 1 GB RAM at no cost
- **No Credit Card Required:** Can start without payment information
- **Good Documentation:** Comprehensive Russian and English documentation
- **Terraform/Pulumi Support:** Official providers available for both tools

### Instance Configuration

**Instance Type:** `standard-v2` with free tier specifications

**Specifications:**
- **Platform:** standard-v2
- **CPU:** 2 cores @ 20% core fraction (free tier)
- **Memory:** 1 GB RAM
- **Storage:** 10 GB HDD (network-hdd)
- **OS:** Ubuntu 22.04 LTS
- **Image ID:** `fd8kdq6d0p8sij7h5qe3`

**Region/Zone:** `ru-central1-a` (Moscow region)

**Cost:** **$0/month** (within free tier limits)

### Resources Created

Both Terraform and Pulumi create identical infrastructure:

1. **VPC Network** (`devops-network`)
   - Virtual private cloud for isolated networking

2. **Subnet** (`devops-subnet`)
   - CIDR: 10.128.0.0/24
   - Zone: ru-central1-a

3. **Security Group** (`devops-security-group`)
   - **Ingress Rules:**
     - SSH (port 22) - from 0.0.0.0/0
     - HTTP (port 80) - from 0.0.0.0/0
     - Custom (port 5000) - from 0.0.0.0/0 (for future app deployment)
   - **Egress Rules:**
     - All traffic allowed (0.0.0.0/0)

4. **Compute Instance** (`devops-vm`)
   - Public IP address (NAT enabled)
   - SSH key authentication
   - Labels for identification (environment, course, lab, tool)

---

## 2. Terraform Implementation

### Terraform Version

```bash
Terraform v1.9.0
Provider: yandex-cloud/yandex v0.100+
```

### Project Structure

```
terraform/
├── main.tf                    # Main infrastructure resources
├── variables.tf               # Input variable declarations
├── outputs.tf                 # Output value definitions
├── github.tf                  # GitHub repository management (bonus)
├── terraform.tfvars.example   # Example variable values
└── README.md                  # Setup instructions
```

### Key Configuration Decisions

1. **Modular File Structure**
   - Separated concerns: main resources, variables, outputs
   - Makes code more maintainable and readable
   - Follows Terraform best practices

2. **Variable Usage**
   - All configurable values extracted to variables
   - Sensitive values (tokens, keys) marked as sensitive
   - Default values provided where appropriate

3. **Free Tier Optimization**
   - `core_fraction = 20` ensures free tier eligibility
   - Minimal disk size (10 GB) to stay within limits
   - HDD instead of SSD for cost savings

4. **Security Configuration**
   - SSH key-based authentication only
   - Security group rules explicitly defined
   - No hardcoded credentials in code

5. **Resource Labeling**
   - All resources tagged with environment, course, lab, tool
   - Enables easy identification and cost tracking

### Setup Process

#### 1. Authentication Setup

```bash
# Install Yandex Cloud CLI
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Initialize and authenticate
yc init

# Create service account
yc iam service-account create --name terraform-sa

# Get service account ID
SA_ID=$(yc iam service-account get terraform-sa --format json | jq -r .id)

# Assign editor role
yc resource-manager folder add-access-binding <FOLDER_ID> \
  --role editor \
  --subject serviceAccount:$SA_ID

# Create authorized key
yc iam key create \
  --service-account-name terraform-sa \
  --output key.json

# Set environment variable
export YC_SERVICE_ACCOUNT_KEY_FILE=key.json
```

#### 2. Configuration

```bash
# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
# folder_id = "your-folder-id"
# zone = "ru-central1-a"
# ssh_public_key_path = "~/.ssh/id_rsa.pub"
```

#### 3. Terraform Initialization

```bash
cd terraform/
terraform init
```

**Output:**
```
Initializing the backend...

Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.100"...
- Installing yandex-cloud/yandex v0.100.0...
- Installed yandex-cloud/yandex v0.100.0

Terraform has been successfully initialized!
```

#### 4. Validation

```bash
# Format code
terraform fmt

# Validate syntax
terraform validate
```

**Output:**
```
Success! The configuration is valid.
```

#### 5. Planning

```bash
terraform plan
```

**Output (sanitized):**
```
Terraform will perform the following actions:

  # yandex_compute_instance.devops_vm will be created
  + resource "yandex_compute_instance" "devops_vm" {
      + name        = "devops-vm"
      + platform_id = "standard-v2"
      + zone        = "ru-central1-a"
      
      + resources {
          + cores         = 2
          + memory        = 1
          + core_fraction = 20
        }
      
      + boot_disk {
          + initialize_params {
              + image_id = "fd8kdq6d0p8sij7h5qe3"
              + size     = 10
              + type     = "network-hdd"
            }
        }
      
      + network_interface {
          + nat = true
        }
    }

  # yandex_vpc_network.devops_network will be created
  + resource "yandex_vpc_network" "devops_network" {
      + name = "devops-network"
    }

  # yandex_vpc_subnet.devops_subnet will be created
  + resource "yandex_vpc_subnet" "devops_subnet" {
      + name           = "devops-subnet"
      + v4_cidr_blocks = ["10.128.0.0/24"]
      + zone           = "ru-central1-a"
    }

  # yandex_vpc_security_group.devops_sg will be created
  + resource "yandex_vpc_security_group" "devops_sg" {
      + name = "devops-security-group"
      
      + ingress {
          + port     = 22
          + protocol = "TCP"
        }
      + ingress {
          + port     = 80
          + protocol = "TCP"
        }
      + ingress {
          + port     = 5000
          + protocol = "TCP"
        }
    }

Plan: 4 to add, 0 to change, 0 to destroy.
```

#### 6. Applying Infrastructure

```bash
terraform apply
```

**Output:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.devops_network: Creating...
yandex_vpc_network.devops_network: Creation complete after 2s
yandex_vpc_subnet.devops_subnet: Creating...
yandex_vpc_security_group.devops_sg: Creating...
yandex_vpc_subnet.devops_subnet: Creation complete after 1s
yandex_vpc_security_group.devops_sg: Creation complete after 2s
yandex_compute_instance.devops_vm: Creating...
yandex_compute_instance.devops_vm: Still creating... [10s elapsed]
yandex_compute_instance.devops_vm: Still creating... [20s elapsed]
yandex_compute_instance.devops_vm: Creation complete after 25s

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

vm_external_ip = "51.250.XX.XXX"
vm_id = "fhm1234567890abcdef"
vm_name = "devops-vm"
ssh_connection = "ssh ubuntu@51.250.XX.XXX"
```

#### 7. SSH Connection Test

```bash
# Get SSH command from outputs
terraform output ssh_connection

# Connect to VM
ssh ubuntu@51.250.XX.XXX
```

**Successful Connection:**
```
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

ubuntu@devops-vm:~$ uname -a
Linux devops-vm 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux

ubuntu@devops-vm:~$ free -h
              total        used        free      shared  buff/cache   available
Mem:          972Mi       150Mi       650Mi       1.0Mi       171Mi       680Mi
Swap:            0B          0B          0B

ubuntu@devops-vm:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda2       9.8G  1.8G  7.5G  20% /

ubuntu@devops-vm:~$ exit
```

### Challenges Encountered

1. **Service Account Permissions**
   - **Issue:** Initial authentication failures
   - **Solution:** Ensured service account had `editor` role on folder
   - **Learning:** Proper IAM configuration is critical

2. **Image ID Discovery**
   - **Issue:** Finding the correct Ubuntu image ID
   - **Solution:** Used `yc compute image list --folder-id standard-images`
   - **Learning:** Cloud providers have standard image catalogs

3. **Security Group Configuration**
   - **Issue:** Complex syntax for ingress/egress rules
   - **Solution:** Referred to provider documentation and examples
   - **Learning:** Security group rules require careful attention to detail

4. **State File Management**
   - **Issue:** Understanding what should/shouldn't be committed
   - **Solution:** Created comprehensive .gitignore rules
   - **Learning:** State files contain sensitive data and must be protected

---

## 3. Pulumi Implementation

### Pulumi Version & Language

```bash
Pulumi v3.100.0
Language: Python 3.11
Provider: pulumi-yandex v0.13+
```

### How Code Differs from Terraform

#### 1. Language Syntax

**Terraform (HCL):**
```hcl
resource "yandex_vpc_network" "devops_network" {
  name        = "devops-network"
  description = "Network for DevOps course VM"
}
```

**Pulumi (Python):**
```python
network = yandex.VpcNetwork(
    "devops-network",
    name="devops-network",
    description="Network for DevOps course VM",
    folder_id=folder_id
)
```

#### 2. Variable Handling

**Terraform:**
```hcl
variable "zone" {
  description = "Availability zone"
  type        = string
  default     = "ru-central1-a"
}

# Usage
zone = var.zone
```

**Pulumi:**
```python
config = pulumi.Config()
zone = config.get("zone") or "ru-central1-a"

# Usage - just use the variable
zone=zone
```

#### 3. Outputs

**Terraform:**
```hcl
output "vm_external_ip" {
  description = "External IP address"
  value       = yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address
}
```

**Pulumi:**
```python
pulumi.export("vm_external_ip", 
    vm.network_interfaces[0].nat_ip_address)
```

#### 4. Resource Dependencies

**Terraform:** Implicit through references
```hcl
network_id = yandex_vpc_network.devops_network.id
```

**Pulumi:** Explicit through object references
```python
network_id=network.id
```

### Setup Process

#### 1. Python Environment

```bash
cd pulumi/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Pulumi Login

```bash
# Login to Pulumi Cloud (free tier)
pulumi login

# Or use local backend
pulumi login --local
```

#### 3. Stack Initialization

```bash
pulumi stack init dev
```

**Output:**
```
Created stack 'dev'
```

#### 4. Configuration

```bash
# Set required configuration
pulumi config set folder_id <YOUR_FOLDER_ID>
pulumi config set ssh_public_key "$(cat ~/.ssh/id_rsa.pub)"

# Optional configuration
pulumi config set zone ru-central1-a
pulumi config set ssh_user ubuntu
```

#### 5. Preview

```bash
pulumi preview
```

**Output:**
```
Previewing update (dev)

     Type                              Name                    Plan       
 +   pulumi:pulumi:Stack               devops-yandex-cloud-dev create     
 +   ├─ yandex:index:VpcNetwork        devops-network          create     
 +   ├─ yandex:index:VpcSubnet         devops-subnet           create     
 +   ├─ yandex:index:VpcSecurityGroup  devops-security-group   create     
 +   └─ yandex:index:ComputeInstance   devops-vm               create     

Resources:
    + 5 to create
```

#### 6. Deployment

```bash
pulumi up
```

**Output:**
```
Updating (dev)

     Type                              Name                    Status      
 +   pulumi:pulumi:Stack               devops-yandex-cloud-dev created     
 +   ├─ yandex:index:VpcNetwork        devops-network          created     
 +   ├─ yandex:index:VpcSubnet         devops-subnet           created     
 +   ├─ yandex:index:VpcSecurityGroup  devops-security-group   created     
 +   └─ yandex:index:ComputeInstance   devops-vm               created     

Outputs:
    network_id      : "enp1234567890abcdef"
    ssh_connection  : "ssh ubuntu@51.250.YY.YYY"
    subnet_id       : "e9b1234567890abcdef"
    vm_external_ip  : "51.250.YY.YYY"
    vm_id           : "fhm9876543210fedcba"
    vm_internal_ip  : "10.128.0.5"
    vm_name         : "devops-vm"

Resources:
    + 5 created

Duration: 35s
```

#### 7. SSH Connection Test

```bash
# Get outputs
pulumi stack output ssh_connection

# Connect
ssh ubuntu@51.250.YY.YYY
```

**Successful Connection:**
```
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

ubuntu@devops-vm:~$ python3 --version
Python 3.10.12

ubuntu@devops-vm:~$ exit
```

### Advantages Discovered

1. **Real Programming Language**
   - Full Python features: loops, functions, conditionals
   - Can import external libraries
   - Better code reuse through functions and classes

2. **IDE Support**
   - Autocomplete for resource properties
   - Type checking catches errors before deployment
   - Inline documentation in IDE
   - Refactoring tools work natively

3. **Secrets Management**
   - Secrets encrypted by default in state
   - `pulumi config set --secret` for sensitive values
   - No plain text secrets in state file

4. **Testing Capabilities**
   - Can write unit tests for infrastructure code
   - Mock resources for testing
   - Integration with pytest

5. **Familiar Syntax**
   - If you know Python, you know Pulumi
   - No new language to learn (HCL)
   - Standard Python debugging tools work

### Challenges Encountered

1. **Pulumi Cloud Dependency**
   - **Issue:** Requires Pulumi Cloud account or self-hosted backend
   - **Solution:** Used free tier Pulumi Cloud
   - **Learning:** State management is more opinionated than Terraform

2. **Provider Documentation**
   - **Issue:** Less comprehensive than Terraform docs
   - **Solution:** Referred to Terraform docs and translated to Python
   - **Learning:** Smaller community means fewer examples

3. **Stack Configuration**
   - **Issue:** Understanding stack-specific vs project-wide config
   - **Solution:** Read Pulumi documentation on stacks
   - **Learning:** Stacks are powerful but add complexity

4. **Async/Promise Handling**
   - **Issue:** Some outputs are promises that need special handling
   - **Solution:** Used `.apply()` method for transformations
   - **Learning:** Understanding async nature of infrastructure provisioning

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

**Terraform (8/10):**
- HCL is simple and declarative
- Syntax is straightforward for basic use cases
- Extensive documentation and examples
- Large community means easy to find solutions
- **However:** HCL is a new language to learn

**Pulumi (7/10):**
- If you know Python, learning curve is minimal
- Standard programming concepts apply
- **However:** Understanding async/promises adds complexity
- Smaller community means fewer examples
- Need to understand both Pulumi concepts AND the language

**Winner:** Terraform for absolute beginners, Pulumi for developers

### Code Readability

**Terraform (9/10):**
- Declarative syntax is very readable
- Clear resource definitions
- Easy to understand what infrastructure will be created
- Consistent structure across all resources

**Pulumi (8/10):**
- Python is readable for Python developers
- Can be more verbose than HCL
- Logic can be embedded, making it less declarative
- **Advantage:** Can add comments and documentation strings

**Winner:** Terraform - more consistent and declarative

### Debugging

**Terraform (7/10):**
- Error messages are generally clear
- `terraform plan` shows what will change
- **However:** Limited debugging tools
- Can't step through code
- Must rely on logs and error messages

**Pulumi (8/10):**
- Can use Python debugger (pdb)
- Better error messages with stack traces
- Can add print statements for debugging
- IDE debugging tools work
- **However:** Async nature can complicate debugging

**Winner:** Pulumi - standard debugging tools available

### Documentation

**Terraform (10/10):**
- Excellent official documentation
- Comprehensive provider docs
- Thousands of examples and tutorials
- Large community with Stack Overflow answers
- Well-documented best practices

**Pulumi (7/10):**
- Good official documentation
- Provider docs are adequate but less detailed
- Fewer community examples
- Smaller Stack Overflow presence
- **Advantage:** Code examples in multiple languages

**Winner:** Terraform - much more mature ecosystem

### Use Cases

**When to Use Terraform:**

1. **Team Doesn't Know Programming**
   - HCL is easier for ops teams without dev background
   - Declarative approach is more intuitive

2. **Need Maximum Provider Support**
   - Terraform has more providers
   - More mature provider implementations

3. **Want Industry Standard**
   - Terraform is the de facto standard
   - More job opportunities
   - Better enterprise support

4. **Simple Infrastructure**
   - For straightforward infrastructure, HCL is cleaner
   - Less boilerplate than programming languages

5. **Need Mature Tooling**
   - More third-party tools
   - Better IDE plugins
   - More CI/CD integrations

**When to Use Pulumi:**

1. **Team Knows Programming**
   - Leverage existing Python/TypeScript/Go skills
   - No new language to learn

2. **Need Complex Logic**
   - Loops, conditionals, functions
   - Dynamic infrastructure generation
   - Complex transformations

3. **Want Better Testing**
   - Unit tests for infrastructure
   - Integration with testing frameworks
   - Mock resources for testing

4. **Need Better IDE Support**
   - Autocomplete and type checking
   - Refactoring tools
   - Inline documentation

5. **Prefer Imperative Approach**
   - More control over execution order
   - Can use programming patterns
   - Better for complex scenarios

### Summary Table

| Aspect | Terraform | Pulumi | Winner |
|--------|-----------|--------|--------|
| **Learning Curve** | Easy (new language) | Easy (if you know Python) | Tie |
| **Readability** | Excellent | Good | Terraform |
| **Debugging** | Limited | Excellent | Pulumi |
| **Documentation** | Excellent | Good | Terraform |
| **Community** | Very Large | Growing | Terraform |
| **Provider Support** | Extensive | Good | Terraform |
| **Testing** | External tools | Native | Pulumi |
| **IDE Support** | Good | Excellent | Pulumi |
| **Secrets Management** | Manual | Built-in | Pulumi |
| **Complex Logic** | Limited | Excellent | Pulumi |
| **Industry Adoption** | Very High | Growing | Terraform |
| **State Management** | Flexible | Opinionated | Terraform |

### Personal Preference

**For this lab:** I prefer **Terraform** because:
1. Simpler for straightforward infrastructure
2. Better documentation and examples
3. More widely adopted in industry
4. Cleaner syntax for simple use cases

**For complex projects:** I would choose **Pulumi** because:
1. Can leverage Python skills
2. Better testing capabilities
3. More powerful for dynamic infrastructure
4. Superior IDE support

**Overall:** Both tools are excellent. The choice depends on:
- Team skills (ops vs dev background)
- Project complexity
- Testing requirements
- Organizational standards

---

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5

**Decision:** Keeping VM for Lab 5

**Which VM:** Pulumi-created VM

**Rationale:**
- Lab 5 (Ansible) requires a VM for configuration management
- Keeping the VM avoids recreation costs and time
- Pulumi VM is identical to Terraform VM
- Can easily recreate if needed using saved code

**VM Status:**
- **Running:** Yes
- **Accessible:** Yes
- **External IP:** 51.250.YY.YYY
- **SSH Access:** Verified and working

**Verification:**
```bash
# Check VM is running
pulumi stack output vm_external_ip

# Test SSH connection
ssh ubuntu@$(pulumi stack output vm_external_ip)

# Verify system
ubuntu@devops-vm:~$ uptime
 14:23:45 up 2:15,  1 user,  load average: 0.00, 0.00, 0.00
```

### Cleanup Status

**Terraform Resources:** Destroyed

```bash
cd terraform/
terraform destroy
```

**Output:**
```
yandex_compute_instance.devops_vm: Destroying...
yandex_compute_instance.devops_vm: Still destroying... [10s elapsed]
yandex_compute_instance.devops_vm: Destruction complete after 15s
yandex_vpc_security_group.devops_sg: Destroying...
yandex_vpc_security_group.devops_sg: Destruction complete after 2s
yandex_vpc_subnet.devops_subnet: Destroying...
yandex_vpc_subnet.devops_subnet: Destruction complete after 3s
yandex_vpc_network.devops_network: Destroying...
yandex_vpc_network.devops_network: Destruction complete after 1s

Destroy complete! Resources: 4 destroyed.
```

**Pulumi Resources:** Kept for Lab 5

```bash
# Verify resources are still running
pulumi stack output

# Output shows VM is active
vm_external_ip: "51.250.YY.YYY"
vm_name: "devops-vm"
```

**Cost Impact:**
- Keeping 1 VM: $0/month (within free tier)
- No additional costs incurred

**For Lab 5:**
- VM ready for Ansible configuration
- No need to recreate infrastructure
- Can proceed directly to configuration management

**If VM needs to be recreated later:**
```bash
# Terraform
cd terraform/
terraform apply

# Or Pulumi
cd pulumi/
pulumi up
```

---

## Conclusion

This lab successfully demonstrated Infrastructure as Code using both Terraform and Pulumi on Yandex Cloud. Key learnings include:

1. **IaC Benefits:**
   - Reproducible infrastructure
   - Version-controlled changes
   - Automated provisioning
   - Documentation as code

2. **Tool Comparison:**
   - Terraform: Better for simple, declarative infrastructure
   - Pulumi: Better for complex, programmatic infrastructure
   - Both are excellent tools with different strengths

3. **Best Practices:**
   - Never commit secrets or state files
   - Use variables for configuration
   - Implement CI/CD for validation
   - Import existing resources when possible

4. **Cloud Provider:**
   - Yandex Cloud free tier is excellent for learning
   - Good documentation and tooling support
   - Accessible in Russia

The VM created in this lab is ready for Lab 5 (Ansible), where we'll use configuration management to install software and deploy applications.

---

## Files Created

### Terraform
- `terraform/main.tf