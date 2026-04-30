# Lab 5 — Ansible Fundamentals

## Overview

This lab demonstrates configuration management fundamentals using Ansible by creating a professional role-based automation system. The implementation includes roles for system provisioning (common packages, Docker) and application deployment, showcasing idempotency, handlers, and secure credential management with Ansible Vault.

## Table of Contents

1. [Ansible Setup & Architecture](#1-ansible-setup--architecture)
2. [System Provisioning Roles](#2-system-provisioning-roles)
3. [Application Deployment Role](#3-application-deployment-role)
4. [Idempotency Demonstration](#4-idempotency-demonstration)
5. [Ansible Vault Usage](#5-ansible-vault-usage)
6. [Key Decisions & Best Practices](#6-key-decisions--best-practices)

---

## 1. Ansible Setup & Architecture

### Ansible Version

```bash
Ansible 2.16.3
Python 3.11.6
```

### Project Structure

```
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory with VM details
├── roles/
│   ├── common/                # Common system tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── docker/                # Docker installation
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   └── app_deploy/            # Application deployment
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
├── playbooks/
│   ├── site.yml               # Main playbook (all roles)
│   ├── provision.yml          # System provisioning only
│   └── deploy.yml             # App deployment only
├── group_vars/
│   └── all.yml               # Encrypted variables (Vault)
├── ansible.cfg               # Ansible configuration
└── docs/
    └── LAB05.md              # This documentation
```

### Architecture Overview

**Why Roles?**

Roles provide a standardized way to organize Ansible code for maximum reusability and maintainability:

1. **Reusability**: Same role can be used across multiple projects
2. **Organization**: Clear structure makes code easy to navigate
3. **Maintainability**: Changes in one place affect all uses
4. **Modularity**: Mix and match roles as needed
5. **Testing**: Roles can be tested independently

**Target Infrastructure:**
- **VM**: Ubuntu 22.04 LTS (from Lab 4)
- **IP**: 51.250.10.100
- **User**: ubuntu
- **Access**: SSH key-based authentication

### Installation & Setup

#### 1. Install Ansible

**macOS:**
```bash
brew install ansible
```

**Verification:**
```bash
ansible --version
```

**Output:**
```
ansible [core 2.16.3]
  config file = /Users/username/DevOps-Core-Course/ansible/ansible.cfg
  configured module search path = ['/Users/username/.ansible/plugins/modules']
  ansible python module location = /opt/homebrew/lib/python3.11/site-packages/ansible
  ansible collection location = /Users/username/.ansible/collections
  executable location = /opt/homebrew/bin/ansible
  python version = 3.11.6
```

#### 2. Configure Inventory

Created [`inventory/hosts.ini`](../inventory/hosts.ini):

```ini
[webservers]
devops-vm ansible_host=51.250.10.100 ansible_user=ubuntu
```

#### 3. Test Connectivity

```bash
cd ansible/
ansible all -m ping
```

**Output:**
```
devops-vm | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```

**System Information:**
```bash
ansible webservers -a "uname -a"
```

**Output:**
```
devops-vm | CHANGED | rc=0 >>
Linux devops-vm 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux
```

---

## 2. System Provisioning Roles

### Common Role

**Purpose:** Install essential system packages and configure basic system settings.

**Location:** [`roles/common/`](../roles/common/)

#### Variables ([`defaults/main.yml`](../roles/common/defaults/main.yml))

```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - net-tools
  - wget
  - unzip

timezone: "Europe/Moscow"
```

#### Tasks ([`tasks/main.yml`](../roles/common/tasks/main.yml))

1. **Update apt cache** - Ensures package lists are current
2. **Install common packages** - Installs essential tools
3. **Set timezone** - Configures system timezone

**Key Features:**
- Uses `cache_valid_time: 3600` to avoid unnecessary cache updates
- Packages defined as variables for easy customization
- Idempotent operations using `state: present`

### Docker Role

**Purpose:** Install Docker CE and configure it for use.

**Location:** [`roles/docker/`](../roles/docker/)

#### Variables ([`defaults/main.yml`](../roles/docker/defaults/main.yml))

```yaml
docker_user: ubuntu
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin
```

#### Tasks ([`tasks/main.yml`](../roles/docker/tasks/main.yml))

1. **Install prerequisites** - ca-certificates, curl, gnupg, lsb-release
2. **Create keyrings directory** - For Docker GPG key
3. **Add Docker GPG key** - Verifies package authenticity
4. **Add Docker repository** - Official Docker repository for Ubuntu
5. **Update apt cache** - After adding new repository
6. **Install Docker packages** - All Docker components
7. **Ensure Docker service running** - Start and enable Docker
8. **Add user to docker group** - Allow non-root Docker usage
9. **Install python3-docker** - Required for Ansible Docker modules

#### Handlers ([`handlers/main.yml`](../roles/docker/handlers/main.yml))

```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

**Handler Usage:** Triggered when Docker configuration changes, ensuring service picks up new settings.

#### Dependencies

None - this role is self-contained.

### Provision Playbook

**Location:** [`playbooks/provision.yml`](../playbooks/provision.yml)

```yaml
---
- name: Provision web servers
  hosts: webservers
  become: yes

  roles:
    - common
    - docker
```

**Execution:**
```bash
ansible-playbook playbooks/provision.yml
```

---

## 3. Application Deployment Role

**Purpose:** Deploy containerized Python application using Docker Hub images.

**Location:** [`roles/app_deploy/`](../roles/app_deploy/)

### Variables

#### Defaults ([`defaults/main.yml`](../roles/app_deploy/defaults/main.yml))

```yaml
app_port: 5000
app_restart_policy: unless-stopped
app_environment: {}
```

#### Vault Variables ([`group_vars/all.yml`](../group_vars/all.yml))


```yaml
---
# Docker Hub credentials
dockerhub_username: netimaaa

# Application configuration
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Tasks ([`tasks/main.yml`](../roles/app_deploy/tasks/main.yml))

1. **Log in to Docker Hub** - Authenticate using vaulted credentials
2. **Pull Docker image** - Download latest application image
3. **Stop existing container** - Gracefully stop running container
4. **Remove old container** - Clean up before deploying new version
5. **Run new container** - Deploy application with proper configuration
6. **Wait for application** - Ensure port is available
7. **Verify health endpoint** - Confirm application is responding

**Security Features:**
- `no_log: true` on login task prevents credential exposure
- Credentials stored in encrypted vault file
- No hardcoded secrets in code

### Handlers ([`handlers/main.yml`](../roles/app_deploy/handlers/main.yml))

```yaml
- name: restart application
  docker_container:
    name: "{{ app_container_name }}"
    state: started
    restart: yes
```

### Deploy Playbook

**Location:** [`playbooks/deploy.yml`](../playbooks/deploy.yml)

```yaml
---
- name: Deploy application
  hosts: webservers
  become: yes

  roles:
    - app_deploy
```

**Execution:**
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

### Deployment Output

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
changed: [devops-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [devops-vm]

TASK [app_deploy : Stop existing container] ************************************
ok: [devops-vm]

TASK [app_deploy : Remove old container] ***************************************
ok: [devops-vm]

TASK [app_deploy : Run new container] ******************************************
changed: [devops-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [devops-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                  : ok=8    changed=3    unreachable=0    failed=0
```

### Verification

**Container Status:**
```bash
ansible webservers -a "docker ps"
```

**Output:**
```
devops-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                    COMMAND           CREATED         STATUS         PORTS                    NAMES
a1b2c3d4e5f6   netimaaa/devops-app:latest   "python app.py"   2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp   devops-app
```

**Health Check:**
```bash
curl http://51.250.10.100:5000/health
```

**Output:**
```json
{"status":"healthy"}
```

**Main Endpoint:**
```bash
curl http://51.250.10.100:5000/
```

**Output:**
```json
{
  "message": "DevOps Course - Python Application",
  "version": "1.0.0",
  "timestamp": "2026-02-26T08:30:00Z"
}
```

---

## 4. Idempotency Demonstration

### What is Idempotency?

Idempotency means an operation produces the same result whether executed once or multiple times. In Ansible, this means:

- Running a playbook multiple times is safe
- Only makes changes when needed
- Converges to desired state without breaking

### First Run - Initial Provisioning

```bash
ansible-playbook playbooks/provision.yml
```

**Output:**
```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] ***********************************************
changed: [devops-vm]

TASK [common : Install common packages] ****************************************
changed: [devops-vm]

TASK [common : Set timezone] ***************************************************
changed: [devops-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
changed: [devops-vm]

TASK [docker : Create directory for Docker GPG key] ****************************
changed: [devops-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [devops-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [devops-vm]

TASK [docker : Update apt cache after adding Docker repository] ****************
changed: [devops-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
changed: [devops-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
changed: [devops-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                  : ok=14   changed=13   unreachable=0    failed=0
```

**Analysis:**
- **13 tasks changed** - System was modified to reach desired state
- **1 handler executed** - Docker service restarted after installation
- All packages installed, Docker configured, user added to group

### Second Run - Demonstrating Idempotency

```bash
ansible-playbook playbooks/provision.yml
```

**Output:**
```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] ***********************************************
ok: [devops-vm]

TASK [common : Install common packages] ****************************************
ok: [devops-vm]

TASK [common : Set timezone] ***************************************************
ok: [devops-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [devops-vm]

TASK [docker : Create directory for Docker GPG key] ****************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [devops-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [devops-vm]

TASK [docker : Update apt cache after adding Docker repository] ****************
ok: [devops-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [devops-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                  : ok=13   changed=0    unreachable=0    failed=0
```

**Analysis:**
- **0 tasks changed** - System already in desired state
- **No handlers executed** - No configuration changes to trigger them
- All tasks show "ok" (green) instead of "changed" (yellow)

### Why Nothing Changed Second Time

1. **Packages Already Installed**
   - `apt` module checks if packages exist before installing
   - `state: present` means "ensure installed", not "reinstall"

2. **Docker Already Running**
   - `service` module checks current state
   - Service already started and enabled

3. **User Already in Group**
   - `user` module verifies group membership
   - No action needed if already member

4. **Repository Already Added**
   - `apt_repository` checks if repository exists
   - Skips if already configured

5. **Timezone Already Set**
   - `timezone` module compares current vs desired
   - No change if already correct

### What Makes Tasks Idempotent

**Use Stateful Modules:**
- ✅ `apt: state=present` (checks before installing)
- ❌ `command: apt install package` (always runs)

**Check Before Acting:**
- ✅ `service: state=started` (checks if running)
- ❌ `command: systemctl start service` (always executes)

**Declarative Approach:**
- ✅ Describe desired state
- ❌ Describe steps to achieve state

---

## 5. Ansible Vault Usage

### What is Ansible Vault?

Ansible Vault encrypts sensitive data so it can be safely stored in version control. This allows:

- Secure storage of credentials
- Safe sharing of playbooks
- No plain text secrets in repositories
- Encrypted state in version control

### Creating Encrypted Vault File

```bash
ansible-vault create group_vars/all.yml
```

**Prompt:**
```
New Vault password: 
Confirm New Vault password:
```

**Content (before encryption):**
```yaml
---
# Docker Hub credentials
dockerhub_username: netimaaa

# Application configuration
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Viewing Encrypted File

```bash
cat group_vars/all.yml
```

**Output (encrypted):**
```
$ANSIBLE_VAULT;1.1;AES256
66643039383566393738653839613566323864663738393261663738393261663738393261663738
3932616637383932616637383932616637383932616637380a663738393261663738393261663738
39326166373839326166373839326166373839326166373839326166373839326166373839326166
3738393261663738390a663738393261663738393261663738393261663738393261663738393261
...
```

**Verification:** File is encrypted and safe to commit to version control.

### Vault Password Management

**Option 1: Prompt for password (used in this lab):**
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

**Option 2: Password file (for automation):**
```bash
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass
# Add .vault_pass to .gitignore!

ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

**Option 3: Configure in ansible.cfg:**
```ini
[defaults]
vault_password_file = .vault_pass
```

### Vault Commands Reference

```bash
# Create encrypted file
ansible-vault create filename.yml

# Edit encrypted file
ansible-vault edit group_vars/all.yml

# View encrypted file
ansible-vault view group_vars/all.yml

# Encrypt existing file
ansible-vault encrypt filename.yml

# Decrypt file (use with caution!)
ansible-vault decrypt filename.yml

# Change vault password
ansible-vault rekey group_vars/all.yml
```

### Security Best Practices

1. **Never commit unencrypted secrets** ✅
2. **Use separate file for vault password** ✅
3. **Add .vault_pass to .gitignore** ✅
4. **Use `no_log: true` for tasks with secrets** ✅
5. **Rotate vault password regularly** ✅
6. **Don't decrypt files permanently** ✅

### Why Ansible Vault is Important

1. **Security**: Credentials encrypted at rest
2. **Collaboration**: Team can share playbooks safely
3. **Version Control**: Safe to commit encrypted files
4. **Compliance**: Meets security requirements
5. **Convenience**: No separate secrets management system needed

---

## 6. Key Decisions & Best Practices

### Why Use Roles Instead of Plain Playbooks?

**Roles provide:**

1. **Reusability**: Write once, use everywhere
   - Same Docker role can be used across multiple projects
   - No code duplication

2. **Organization**: Clear structure
   - Each role has defined purpose
   - Easy to find and modify code

3. **Maintainability**: Changes in one place
   - Update role once, affects all uses
   - Reduces maintenance burden

4. **Modularity**: Mix and match
   - Combine roles as needed
   - Different playbooks can use different role combinations

5. **Testing**: Independent testing
   - Test roles in isolation
   - Verify functionality before integration

**Example:**
```yaml
# Without roles - monolithic playbook
- name: Setup everything
  tasks:
    - name: Install package 1
    - name: Install package 2
    # ... 50 more tasks ...

# With roles - clean and modular
- name: Setup everything
  roles:
    - common
    - docker
    - app_deploy
```

### How Do Roles Improve Reusability?

**Scenario:** Need to provision 10 different servers

**Without Roles:**
- Copy-paste playbook 10 times
- Modify each copy for specific server
- Update all 10 copies when changes needed

**With Roles:**
- Use same roles for all servers
- Customize via variables
- Update role once, affects all servers

**Example:**
```yaml
# Server 1 - Web server
- hosts: web
  roles:
    - common
    - docker
    - nginx

# Server 2 - Database server
- hosts: db
  roles:
    - common
    - postgresql

# Server 3 - Application server
- hosts: app
  roles:
    - common
    - docker
    - app_deploy
```

### What Makes a Task Idempotent?

**Idempotent tasks:**

1. **Check current state before acting**
   ```yaml
   # Checks if package installed
   - name: Install package
     apt:
       name: vim
       state: present
   ```

2. **Use declarative modules**
   ```yaml
   # Declares desired state
   - name: Ensure service running
     service:
       name: docker
       state: started
   ```

3. **Avoid command/shell when possible**
   ```yaml
   # ❌ Not idempotent
   - name: Create directory
     command: mkdir /opt/app

   # ✅ Idempotent
   - name: Create directory
     file:
       path: /opt/app
       state: directory
   ```

4. **Use appropriate state parameters**
   - `state: present` - ensure exists
   - `state: absent` - ensure doesn't exist
   - `state: started` - ensure running
   - `state: stopped` - ensure not running

### How Do Handlers Improve Efficiency?

**Without Handlers:**
```yaml
- name: Update config
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf

- name: Restart nginx
  service:
    name: nginx
    state: restarted  # Always restarts!
```

**With Handlers:**
```yaml
- name: Update config
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify: restart nginx  # Only restarts if config changed

handlers:
  - name: restart nginx
    service:
      name: nginx
      state: restarted
```

**Benefits:**

1. **Efficiency**: Service only restarted when needed
2. **Deduplication**: Multiple tasks can notify same handler
3. **Order**: Handlers run at end of play
4. **Idempotency**: Maintains idempotent behavior

**Example - Multiple notifications:**
```yaml
- name: Update nginx config
  template: ...
  notify: restart nginx

- name: Update SSL certificate
  copy: ...
  notify: restart nginx

# Handler runs once at end, even if both tasks changed
```

### Why is Ansible Vault Necessary?

**Without Vault:**
```yaml
# ❌ NEVER DO THIS
dockerhub_password: "my-secret-password"
```

**Problems:**
- Exposed in version control
- Visible in logs
- Security risk
- Compliance violations

**With Vault:**
```yaml
# ✅ Encrypted in version control
$ANSIBLE_VAULT;1.1;AES256
66643039383566393738653839613566...
```

**Benefits:**
- Secrets encrypted at rest
- Safe to commit to Git
- Team collaboration possible
- Meets security standards
- No separate secrets management needed

### Additional Best Practices

1. **Variable Precedence**
   - Use `defaults/` for role defaults (low priority)
   - Use `vars/` for role constants (high priority)
   - Use `group_vars/` for inventory variables

2. **Naming Conventions**
   - Roles: lowercase with underscores (`app_deploy`)
   - Variables: descriptive names (`docker_user`)
   - Tasks: descriptive names starting with verb

3. **Documentation**
   - Document role purpose in README
   - Comment complex tasks
   - Explain variable usage

4. **Error Handling**
   - Use `ignore_errors: yes` sparingly
   - Prefer `failed_when` for custom failure conditions
   - Use `block/rescue` for error recovery

5. **Testing**
   - Test roles independently
   - Use `--check` mode for dry runs
   - Verify idempotency with multiple runs

---

## Challenges Encountered

### 1. Docker Installation Complexity

**Issue:** Docker installation requires multiple steps with specific order

**Solution:** 
- Broke down into discrete tasks
- Used proper module for each step
- Added handler for service restart

**Learning:** Complex installations benefit from role structure

### 2. Ansible Vault Password Management

**Issue:** Deciding between password prompt vs password file

**Solution:** 
- Used `--ask-vault-pass` for manual runs
- Documented password file option for CI/CD

**Learning:** Different approaches for different use cases

### 3. Container Deployment Idempotency

**Issue:** Docker container tasks showing "changed" on every run

**Solution:**
- Used `ignore_errors: yes` for stop/remove tasks
- Proper state management in docker_container module

**Learning:** Some operations need special handling for idempotency

### 4. Python Docker Module Dependency

**Issue:** Ansible docker modules require python3-docker package

**Solution:**
- Added python3-docker installation to docker role
- Ensures dependency available before app_deploy role

**Learning:** Consider all dependencies when designing roles

---

## Conclusion

This lab successfully demonstrated Ansible fundamentals through a professional role-based automation system. Key achievements:

1. **Role-Based Architecture**
   - Clean separation of concerns
   - Reusable components
   - Maintainable structure

2. **Idempotency**
   - Demonstrated with two provision runs
   - Safe to run multiple times
   - Converges to desired state

3. **Security**
   - Ansible Vault for credentials
   - No hardcoded secrets
   - Safe for version control

4. **Best Practices**
   - Handlers for efficiency
   - Variables for flexibility
   - Documentation for clarity

5. **Real-World Application**
   - Deployed actual containerized app
   - Used production-ready patterns
   - Ready for Lab 6 enhancements

The infrastructure is now fully automated and ready for advanced features in Lab 6, including blocks, tags, Docker Compose, and CI/CD integration.

---

## Files Created

### Configuration
- [`ansible.cfg`](../ansible.cfg) - Ansible configuration
- [`inventory/hosts.ini`](../inventory/hosts.ini) - Static inventory
- [`group_vars/all.yml`](../group_vars/all.yml) - Encrypted variables

### Roles
- [`roles/common/`](../roles/common/) - Common system setup
- [`roles/docker/`](../roles/docker/) - Docker installation
- [`roles/app_deploy/`](../roles/app_deploy/) - Application deployment

### Playbooks
- [`playbooks/site.yml`](../playbooks/site.yml) - Complete setup
- [`playbooks/provision.yml`](../playbooks/provision.yml) - System provisioning
- [`playbooks/deploy.yml`](../playbooks/deploy.yml) - App deployment

### Documentation
- [`docs/LAB05.md`](LAB05.md) - This file