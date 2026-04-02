# HELM.md — Helm Chart Documentation

## 1. Chart Overview

### Chart Structure

```
k8s/devops-info-service/
├── Chart.yaml                        # Chart metadata (name, version, appVersion)
├── values.yaml                       # Default configuration values
├── values-dev.yaml                   # Development environment overrides
├── values-prod.yaml                  # Production environment overrides
└── templates/
    ├── _helpers.tpl                  # Reusable named template helpers
    ├── deployment.yaml               # Kubernetes Deployment resource
    ├── service.yaml                  # Kubernetes Service resource
    ├── NOTES.txt                     # Post-install usage instructions
    └── hooks/
        ├── pre-install-job.yaml      # Pre-install lifecycle hook (Job)
        └── post-install-job.yaml     # Post-install lifecycle hook (Job)
```

### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Defines reusable named templates: `fullname`, `name`, `chart`, `labels`, `selectorLabels` |
| `deployment.yaml` | Templated Deployment with configurable replicas, image, resources, probes, env vars |
| `service.yaml` | Templated Service with configurable type (NodePort/LoadBalancer/ClusterIP) and ports |
| `hooks/pre-install-job.yaml` | Job that runs before installation for pre-flight validation |
| `hooks/post-install-job.yaml` | Job that runs after installation for smoke testing |

### Values Organization

Values are organized into logical groups:
- **`image`** — repository, tag, pullPolicy
- **`service`** — type, port, targetPort, nodePort
- **`resources`** — requests and limits for CPU/memory
- **`livenessProbe` / `readinessProbe`** — health check configuration
- **`securityContext`** — non-root user settings
- **`strategy`** — rolling update parameters
- **`env`** — environment variables list

---

## 2. Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `netimaaaa/devops-info-service` | Container image repository |
| `image.tag` | `latest` | Container image tag |
| `image.pullPolicy` | `Always` | Image pull policy |
| `service.type` | `NodePort` | Kubernetes service type |
| `service.port` | `80` | Service port |
| `service.targetPort` | `8000` | Container port |
| `service.nodePort` | `30080` | NodePort (only for NodePort type) |
| `resources.limits.cpu` | `200m` | CPU limit |
| `resources.limits.memory` | `256Mi` | Memory limit |
| `livenessProbe.initialDelaySeconds` | `10` | Liveness probe initial delay |
| `readinessProbe.initialDelaySeconds` | `5` | Readiness probe initial delay |

### Environment-Specific Customization

**Development** (`values-dev.yaml`):
- 1 replica (fast startup, low resource usage)
- `latest` image tag
- Relaxed resource limits (100m CPU, 128Mi memory)
- NodePort service type
- Shorter probe delays

**Production** (`values-prod.yaml`):
- 5 replicas (high availability)
- Pinned image tag (`1.0.0`)
- Proper resource limits (500m CPU, 512Mi memory)
- LoadBalancer service type
- Longer probe delays for stability

### Example Installations

```bash
# Install with default values
helm install myapp k8s/devops-info-service

# Install for development
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Install for production
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Override a specific value
helm install myapp k8s/devops-info-service --set replicaCount=2

# Dry-run to preview
helm install --dry-run --debug myapp k8s/devops-info-service
```

---

## 3. Hook Implementation

### Hooks Implemented

| Hook | Type | Weight | Deletion Policy | Purpose |
|------|------|--------|-----------------|---------|
| `pre-install-job.yaml` | `pre-install` | `-5` | `hook-succeeded` | Pre-flight validation before deployment |
| `post-install-job.yaml` | `post-install` | `5` | `hook-succeeded` | Smoke test after deployment |

### Hook Execution Order

1. **Pre-install hook** (weight `-5`) runs first — validates environment, checks configuration
2. **Main resources** (Deployment, Service) are created
3. **Post-install hook** (weight `5`) runs last — verifies the deployment is healthy

Lower weight values run first. Negative weights run before weight 0 (default).

### Deletion Policies

Both hooks use `hook-succeeded` deletion policy:
- The Job resource is **automatically deleted** after successful completion
- This keeps the cluster clean — no leftover Jobs after install
- If a hook fails, the Job remains for debugging (`kubectl logs job/<name>`)

### Hook Annotations

```yaml
annotations:
  "helm.sh/hook": pre-install          # Hook type
  "helm.sh/hook-weight": "-5"          # Execution order (lower = earlier)
  "helm.sh/hook-delete-policy": hook-succeeded  # Auto-cleanup on success
```

---

## 4. Installation Evidence

### `helm list` Output

```
NAME     	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART                    	APP VERSION
myapp-dev	default  	2       	2026-04-02 22:16:53.060201 +0300 MSK	deployed	devops-info-service-0.1.0	1.0.0
```

### `kubectl get all` — Dev Environment (1 replica, NodePort)

```
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/myapp-dev-devops-info-service-5768f579db-7b4h9   1/1     Running   0          77s

NAME                                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes                      ClusterIP   10.96.0.1        <none>        443/TCP        6d22h
service/myapp-dev-devops-info-service   NodePort    10.106.185.216   <none>        80:30080/TCP   77s

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-dev-devops-info-service   1/1     1            1           77s

NAME                                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/myapp-dev-devops-info-service-5768f579db   1         1         1       77s
```

### `kubectl get all` — Prod Environment (5 replicas, LoadBalancer)

```
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/myapp-dev-devops-info-service-5768f579db-47cst   1/1     Running   0          8s
pod/myapp-dev-devops-info-service-5768f579db-7b4h9   1/1     Running   0          62s
pod/myapp-dev-devops-info-service-5768f579db-9l42l   1/1     Running   0          8s
pod/myapp-dev-devops-info-service-5768f579db-mf92h   1/1     Running   0          8s
pod/myapp-dev-devops-info-service-5768f579db-xchpl   1/1     Running   0          8s

NAME                                    TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/myapp-dev-devops-info-service   LoadBalancer   10.106.185.216   <pending>     80:30080/TCP   62s

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-dev-devops-info-service   5/5     5            5           62s
```

### Hook Execution

Hooks ran and were deleted per `hook-succeeded` policy:

```bash
$ kubectl get jobs
No resources found in default namespace.
```

This confirms hooks executed successfully and were auto-cleaned up.

---

## 5. Operations

### Installation

```bash
# Dev environment
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Prod environment
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Upgrade a Release

```bash
# Upgrade to prod values
helm upgrade myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Upgrade with a specific value override
helm upgrade myapp-dev k8s/devops-info-service --set replicaCount=10
```

### Rollback

```bash
# Rollback to previous revision
helm rollback myapp-dev

# Rollback to specific revision
helm rollback myapp-dev 1

# View revision history
helm history myapp-dev
```

### Uninstall

```bash
helm uninstall myapp-dev
```

---

## 6. Testing & Validation

### `helm lint` Output

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template` Verification

```
$ helm template devops-info-service k8s/devops-info-service
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-service-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-info-service-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: devops-info-service
  template:
    spec:
      containers:
        - name: devops-info-service
          image: "netimaaaa/devops-info-service:latest"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Release History (`helm history`)

```
$ helm history myapp-dev
REVISION  UPDATED                   STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 22:15:50 2026  superseded  devops-info-service-0.1.0  1.0.0       Install complete
2         Thu Apr  2 22:16:53 2026  superseded  devops-info-service-0.1.0  1.0.0       Upgrade complete
3         Thu Apr  2 22:17:10 2026  deployed    devops-info-service-0.1.0  1.0.0       Rollback to 1
```

### Dry-run Output

```bash
helm install --dry-run --debug test-release k8s/devops-info-service
```

Shows full rendered manifests with debug info before actual installation.

### Dev Values Dry-run

```bash
helm template devops-info-service k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

### Prod Values Dry-run

```bash
helm template devops-info-service k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Application Accessibility

After dev install with NodePort:

```bash
export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services myapp-dev-devops-info-service)
export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
curl http://$NODE_IP:$NODE_PORT/health
```

### Helm Version

```
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Explored Public Chart

```bash
$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.11.0
description: Prometheus is a monitoring system and time series database.
name: prometheus
version: 27.x.x
dependencies:
- name: alertmanager
- name: kube-state-metrics
- name: prometheus-node-exporter
- name: prometheus-pushgateway
```

**Helm's Value Proposition:** Helm packages Kubernetes manifests into versioned, reusable charts with Go templating for environment-specific configuration. It provides release management (install/upgrade/rollback), lifecycle hooks for pre/post deployment tasks, and dependency management — making complex multi-component deployments reproducible and maintainable.
