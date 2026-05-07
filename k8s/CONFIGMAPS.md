# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits counter implementation
The application was extended to persist a visits counter in a file.

Implemented changes:
- Root endpoint increments the counter on every request.
- Counter is stored in a file defined by `VISITS_FILE`.
- Default local path is `./data/visits`.
- Kubernetes path is `/data/visits`.
- Counter file is initialized on startup.
- File writes use atomic replace.
- Access is protected with a process-level lock.

### New endpoint
- `GET /visits` returns the current persisted counter without incrementing it.

Example response:
```json
{
  "visits": 3,
  "file": "/data/visits"
}
```

### Local Docker testing
Local persistence is configured with [`app_python/docker-compose.yml`](app_python/docker-compose.yml).

Compose volume mapping:
```yaml
volumes:
  - ./data:/data
```

Suggested verification flow:
```bash
cd app_python
docker compose up --build -d
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/visits
cat ./data/visits
docker compose restart
curl http://localhost:8000/visits
docker compose down
```

Expected result:
- `./data/visits` exists on the host.
- Counter value survives container restart.

### Automated test evidence
Application tests passed locally:
```bash
python3 -m pytest tests/test_app.py --cov=app --cov-fail-under=0
```

Result summary:
```text
25 passed
coverage: 96%
```

---

## 2. ConfigMap Implementation

### Config file
Helm chart file created:
- [`k8s/devops-info-service/files/config.json`](k8s/devops-info-service/files/config.json)

Content:
```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visitsCounter": true,
    "prometheusMetrics": true,
    "structuredLogging": true
  }
}
```

### ConfigMap templates
Template created:
- [`k8s/devops-info-service/templates/configmap.yaml`](k8s/devops-info-service/templates/configmap.yaml)

It creates two ConfigMaps:
1. File-based ConfigMap with `config.json`
2. Environment ConfigMap with key-value pairs:
   - `APP_ENV`
   - `APP_NAME`
   - `LOG_LEVEL`
   - `FEATURE_VISITS_COUNTER`
   - `FEATURE_PROMETHEUS_METRICS`
   - `FEATURE_STRUCTURED_LOGGING`

### File mount
Deployment mounts the file ConfigMap as a volume:
- volume name: `config-volume`
- mount path: `/config`

As a result, the pod receives:
- `/config/config.json`

### Environment variables from ConfigMap
Deployment uses:
```yaml
envFrom:
  - configMapRef:
      name: <release>-devops-info-service-env
```

This injects all keys from the env ConfigMap into the container.

### Verification commands
Use these commands after deployment:
```bash
kubectl get configmap
kubectl exec <pod-name> -- cat /config/config.json
kubectl exec <pod-name> -- printenv | grep -E 'APP_|FEATURE_|LOG_LEVEL'
```

### Verification outputs
Add your real outputs here after running commands.

#### `kubectl get configmap,pvc`
```text
<insert real kubectl get configmap,pvc output here>
```

#### File content inside pod
```bash
kubectl exec <pod-name> -- cat /config/config.json
```

```text
<insert real /config/config.json output here>
```

#### Environment variables inside pod
```bash
kubectl exec <pod-name> -- printenv | grep -E 'APP_|FEATURE_|LOG_LEVEL'
```

```text
<insert real environment variable output here>
```

---

## 3. Persistent Volume

### PVC configuration
Template created:
- [`k8s/devops-info-service/templates/pvc.yaml`](k8s/devops-info-service/templates/pvc.yaml)

Configured values in [`k8s/devops-info-service/values.yaml`](k8s/devops-info-service/values.yaml):
```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  mountPath: /data
  visitsFile: /data/visits
```

### Access mode and storage class
- Access mode: `ReadWriteOnce`
- Requested size: `100Mi`
- `storageClass` is configurable from values.
- Empty `storageClass` means the cluster default storage class is used.

### Volume mount configuration
Deployment mounts the PVC as:
- volume name: `data-volume`
- mount path: `/data`

The application writes the counter to:
- `/data/visits`

### Persistence verification procedure
Suggested commands:
```bash
kubectl get pvc
kubectl exec <pod-name> -- cat /data/visits
kubectl delete pod <pod-name>
kubectl get pods -w
kubectl exec <new-pod-name> -- cat /data/visits
curl http://<service-endpoint>/visits
```

### Persistence test evidence
Fill in with real values from your cluster.

#### Counter before pod deletion
```text
<insert visits count before pod deletion>
```

#### Pod deletion command
```bash
kubectl delete pod <pod-name>
```

#### Counter after new pod starts
```text
<insert visits count after new pod starts>
```

Expected result:
- New pod starts.
- `/data/visits` still contains the previous value.
- `/visits` returns the same persisted count.

---

## 4. ConfigMap vs Secret

### When to use ConfigMap
Use ConfigMap for non-sensitive configuration such as:
- application name
- environment name
- feature flags
- log levels
- JSON/YAML/text configuration files

### When to use Secret
Use Secret for sensitive data such as:
- passwords
- API tokens
- private keys
- database credentials
- certificates

### Key differences
| Aspect | ConfigMap | Secret |
|---|---|---|
| Intended data | Non-sensitive config | Sensitive config |
| Encoding | Plain text in manifests | Base64-encoded in manifests |
| Typical examples | app settings, flags, config files | passwords, tokens, keys |
| Security expectation | Convenience/config separation | Restricted access required |

---

## 5. Helm Changes Summary

Updated chart files:
- [`k8s/devops-info-service/files/config.json`](k8s/devops-info-service/files/config.json)
- [`k8s/devops-info-service/templates/configmap.yaml`](k8s/devops-info-service/templates/configmap.yaml)
- [`k8s/devops-info-service/templates/pvc.yaml`](k8s/devops-info-service/templates/pvc.yaml)
- [`k8s/devops-info-service/templates/deployment.yaml`](k8s/devops-info-service/templates/deployment.yaml)
- [`k8s/devops-info-service/values.yaml`](k8s/devops-info-service/values.yaml)
- [`k8s/devops-info-service/values-dev.yaml`](k8s/devops-info-service/values-dev.yaml)
- [`k8s/devops-info-service/values-prod.yaml`](k8s/devops-info-service/values-prod.yaml)

Additional deployment behavior:
- ConfigMap mounted at `/config`
- Env vars injected via `envFrom`
- PVC mounted at `/data`
- `VISITS_FILE=/data/visits`
- checksum annotation added to restart pods on ConfigMap changes

---

## 6. Render Validation

Helm render command used:
```bash
helm template lab12 ./k8s/devops-info-service
```

Use this command locally to validate manifests before applying them.
