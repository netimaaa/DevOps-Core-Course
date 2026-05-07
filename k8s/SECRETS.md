# Kubernetes Secrets & HashiCorp Vault — Lab 11

---

## 1. Kubernetes Secrets

### Creating the Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
```

Output: `secret/app-credentials created`

### Viewing the Secret in YAML

```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T13:08:56Z"
  name: app-credentials
  namespace: default
  resourceVersion: "181817"
  uid: b3355879-6000-4f07-aeea-16ac355e4960
type: Opaque
```

### Decoding Base64 Values

```bash
echo "YWRtaW4=" | base64 -d
# admin

echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d
# supersecret123
```

### Base64 Encoding vs Encryption

Kubernetes Secrets are **base64-encoded**, not encrypted. Base64 is simply an encoding scheme — anyone with API access can decode values instantly. This means:

- Secrets are not secure by default in etcd
- Anyone with `kubectl get secret` access can read all values
- **etcd encryption at rest** (`EncryptionConfiguration`) must be explicitly enabled to protect secrets in storage
- RBAC should restrict which users/service accounts can read secrets

**When to enable etcd encryption:** Always in production environments where compliance (PCI-DSS, HIPAA, etc.) requires data-at-rest encryption or where etcd backups might be exposed.

---

## 2. Helm Secret Integration

### Chart Structure with secrets.yaml

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── secrets.yaml        ← added in lab11
│   ├── service.yaml
│   └── NOTES.txt
```

### secrets.yaml Template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.fullname" . }}-secret
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secret.username | quote }}
  password: {{ .Values.secret.password | quote }}
```

### values.yaml Secret Defaults (Placeholders)

```yaml
secret:
  username: "placeholder-user"
  password: "placeholder-password"
```

Real values are injected at deploy time with `--set`:
```bash
helm upgrade myapp-dev ./devops-info-service \
  --set secret.username=admin \
  --set secret.password=supersecret123
```

### Consuming Secrets in Deployment (envFrom)

```yaml
containers:
  - name: devops-info-service
    envFrom:
      - secretRef:
          name: myapp-dev-devops-info-service-secret
    env:
      - name: HOST
        value: "0.0.0.0"
```

### Verification — Environment Variables in Pod

```bash
kubectl exec myapp-dev-devops-info-service-6cc7f948cb-4lhfz -- env | grep -i user
username=admin
```

Secret values are available as env vars. In `kubectl describe pod`, only the secret name is shown — not the values:

```
Environment Variables from:
  myapp-dev-devops-info-service-secret  Secret  Optional: false
Environment:
  HOST:   0.0.0.0
  PORT:   8000
  DEBUG:  false
```

---

## 3. Resource Management

### Resource Limits Configuration (values.yaml)

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### Requests vs Limits

| Concept | Description |
|---------|-------------|
| **requests** | Guaranteed resources the scheduler uses for placement decisions. The pod will always get at least this amount. |
| **limits** | Hard upper bound. If the container exceeds CPU limit, it is throttled. If it exceeds memory limit, it is OOMKilled. |

### How to Choose Values

1. **Profile the app** — run under realistic load and measure actual usage
2. **Set requests** to typical (P50) usage — ensures stable scheduling
3. **Set limits** to ~2x requests for CPU and ~1.5x for memory — allows bursting without unbounded growth
4. **Avoid setting limits == requests for CPU** — causes unnecessary throttling under bursty workloads
5. Use `kubectl top pods` to monitor actual usage and tune values over time

---

## 4. Vault Integration

### Vault Installation Verification

```bash
kubectl get pods
```

```
NAME                                             READY   STATUS    RESTARTS   AGE
myapp-dev-devops-info-service-6cc7f948cb-4lhfz   2/2     Running   0          22s
myapp-dev-devops-info-service-6cc7f948cb-jt684   2/2     Running   0          13s
myapp-dev-devops-info-service-6cc7f948cb-pdzcl   2/2     Running   0          31s
vault-0                                          1/1     Running   0          10m
vault-agent-injector-5d48bf476c-vxbvt            1/1     Running   0          10m
```

App pods show `2/2` — the vault-agent sidecar is injected alongside the main container.

### KV Secrets Engine Configuration

```bash
# Dev mode already has secret/ path — verify with:
kubectl exec vault-0 -- vault kv put secret/myapp/config username="admin" password="secret123"

kubectl exec vault-0 -- vault kv get secret/myapp/config
# ====== Data ======
# Key         Value
# ---         -----
# password    secret123
# username    admin
```

### Policy Configuration (Sanitized)

```hcl
# devops-info-service policy
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Applied with:
```bash
kubectl cp devops-policy.hcl vault-0:/tmp/devops-policy.hcl
kubectl exec vault-0 -- vault policy write devops-info-service /tmp/devops-policy.hcl
# Success! Uploaded policy: devops-info-service
```

### Role Configuration

```bash
kubectl exec vault-0 -- vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=devops-info-service \
  ttl=24h
# Success! Data written to: auth/kubernetes/role/devops-info-service
```

### Proof of Secret Injection

```bash
kubectl exec myapp-dev-devops-info-service-6cc7f948cb-4lhfz \
  -c devops-info-service -- ls /vault/secrets/
# config

kubectl exec myapp-dev-devops-info-service-6cc7f948cb-4lhfz \
  -c devops-info-service -- cat /vault/secrets/config
# data: map[password:secret123 username:admin]
# metadata: map[created_time:2026-04-09T13:13:16.852722831Z ...]
```

The secret file is available at `/vault/secrets/config` inside the application container.

### Sidecar Injection Pattern

The Vault Agent Injector works via a Kubernetes **MutatingAdmissionWebhook**. When a pod is created with specific annotations, the webhook intercepts the request and injects two containers:

1. **`vault-agent-init`** (init container) — authenticates to Vault using the pod's service account token and fetches secrets before the app starts
2. **`vault-agent`** (sidecar container) — keeps running alongside the app to refresh secrets and handle dynamic credential rotation

Vault annotations added to the deployment template:
```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

---

## 5. Security Analysis

### K8s Secrets vs Vault

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---------|-------------------|-----------------|
| **Storage** | etcd (base64, not encrypted by default) | Vault backend (AES-256 encrypted) |
| **Access control** | Kubernetes RBAC | Vault policies + K8s auth |
| **Dynamic secrets** | No | Yes (DB creds, PKI, etc.) |
| **Secret rotation** | Manual / operator-based | Built-in lease/renewal system |
| **Audit log** | Kubernetes audit log (optional) | Built-in detailed audit log |
| **Complexity** | Low | High |
| **Ops overhead** | Minimal | Requires running and maintaining Vault |

### When to Use Each

**Use Kubernetes Secrets when:**
- Simple workloads with static credentials
- Small teams / early-stage projects
- etcd encryption at rest is enabled
- You want minimal operational overhead

**Use Vault when:**
- Enterprise environments with compliance requirements (SOC2, PCI-DSS)
- Dynamic secrets needed (short-lived DB credentials)
- Multiple teams/clusters sharing secret management
- Detailed audit trail is required
- Secret rotation without pod restarts is needed

### Production Recommendations

1. **Never commit real secrets to Git** — use placeholder values in `values.yaml`
2. **Enable etcd encryption at rest** for any K8s Secrets in production
3. **Use Vault for credentials** that need rotation (DB passwords, API keys, TLS certs)
4. **Apply strict RBAC** — pods should only access secrets they need (principle of least privilege)
5. **Use namespaces** to isolate secrets between teams/environments
6. **Consider External Secrets Operator** as an alternative to Vault Agent for cloud-native secret management (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)

---

## 6. Bonus — Vault Agent Templates

### Template Annotation — Rendering Secrets as .env Format

Instead of injecting raw Vault JSON output, the `agent-inject-template-*` annotation lets Vault Agent render a custom file using Go templating:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/myapp/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

The template name suffix (`-config`) must match the secret annotation suffix (`-secret-config`).

### Rendered Secret File Content

```bash
kubectl exec myapp-dev-devops-info-service-7f98f55dd9-cwn9p \
  -c devops-info-service -- cat /vault/secrets/config
```

```
USERNAME=admin
PASSWORD=secret123
```

The file is rendered in `.env` format — no raw JSON, ready for `source /vault/secrets/config` or parsing by the application.

### Benefits of Templating Approach

| Without Template | With Template |
|-----------------|---------------|
| Raw Vault JSON with metadata | Clean `.env` / JSON / TOML as needed |
| App must parse Vault response format | App reads a standard config file |
| Tied to Vault response structure | Decoupled — format is controlled by annotation |

### Dynamic Secret Rotation

Vault Agent continuously monitors secret leases. When a secret is updated in Vault:

1. The **vault-agent sidecar** detects the TTL expiry or lease renewal
2. It re-authenticates and fetches the updated secret
3. It rewrites `/vault/secrets/config` with new values
4. Optionally, a command is executed to notify the application:

```yaml
vault.hashicorp.com/agent-inject-command: "kill -HUP 1"
```

The `vault.hashicorp.com/agent-inject-command` annotation specifies a shell command the agent runs **after** writing the updated secret file. Common uses:
- `kill -HUP 1` — send SIGHUP to PID 1 to trigger config reload
- `curl -X POST http://localhost:8000/reload` — hit an app reload endpoint
- A script that restarts the process gracefully

The application does not need to restart or be redeployed — the sidecar handles rotation transparently.

### Named Template for Environment Variables

The `devops-info-service.envVars` named template in `_helpers.tpl` demonstrates the DRY principle:

**`_helpers.tpl`:**
```yaml
{{/*
Common environment variables (DRY principle)
*/}}
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.service.host | default "0.0.0.0" | quote }}
- name: PORT
  value: {{ .Values.service.targetPort | toString | quote }}
- name: DEBUG
  value: {{ .Values.debug | default "false" | quote }}
{{- end }}
```

**`deployment.yaml` — using `include` instead of repeating env vars inline:**
```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

**Result:**
- Environment variables are defined once in `_helpers.tpl`
- Any future template (jobs, init containers, etc.) can `include` the same block
- Changing a variable name or default only requires editing one place
- Values are still driven from `values.yaml` (`service.targetPort`, `debug`)
