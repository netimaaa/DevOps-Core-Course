# Kubernetes Deployment — DevOps Info Service

## 1. Architecture Overview

```
                        ┌──────────────────────────────────────┐
                        │          minikube cluster             │
                        │                                       │
  External Traffic      │  ┌─────────────────────────────────┐ │
  :30080  ──────────────┼─▶│  Service: devops-info-service   │ │
                        │  │  Type: NodePort                  │ │
                        │  │  port 80 → targetPort 8000       │ │
                        │  └───────────┬─────────────────────┘ │
                        │              │ selector: app=devops-info-service
                        │    ┌─────────┼─────────────────┐     │
                        │    ▼         ▼                  ▼     │
                        │  ┌────┐   ┌────┐            ┌────┐   │
                        │  │Pod │   │Pod │            │Pod │   │
                        │  │:8000   │:8000            │:8000   │
                        │  └────┘   └────┘            └────┘   │
                        │       Deployment (3 replicas)         │
                        └──────────────────────────────────────┘
```

**Resource allocation:**
- CPU request: 100m per pod × 3 = 300m total
- CPU limit: 200m per pod
- Memory request: 128Mi per pod × 3 = 384Mi total
- Memory limit: 256Mi per pod

---

## 2. Manifest Files

### `deployment.yml`
Deploys the `netimaaaa/devops-info-service:latest` image with:
- **3 replicas** — minimum for HA; survives single pod failure without downtime
- **RollingUpdate** with `maxUnavailable: 0` — zero downtime updates; new pods come up before old ones go down
- **Non-root user (UID 1000)** — matches the Dockerfile `appuser`; required by `runAsNonRoot: true`
- **Liveness probe** on `/health` — Kubernetes restarts the container if it becomes unresponsive
- **Readiness probe** on `/health` — pod is removed from service endpoints until it passes; prevents traffic to a not-yet-ready container
- **Resource requests/limits** — guarantees scheduling and prevents a single pod from starving others

### `service.yml`
NodePort service exposing the deployment:
- **NodePort 30080** — fixed port in the 30000–32767 range for predictable external access
- **selector `app: devops-info-service`** — matches deployment pod labels; traffic goes only to healthy, ready pods

---

## 3. Deployment Evidence

### Cluster setup

```
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:32771
CoreDNS is running at https://127.0.0.1:32771/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   84s   v1.35.1
```

### All resources

```
$ kubectl get all
NAME                                      READY   STATUS    RESTARTS   AGE
pod/devops-info-service-b46bc7c5b-msh6g   1/1     Running   0          22s
pod/devops-info-service-b46bc7c5b-x2s5c   1/1     Running   0          22s
pod/devops-info-service-b46bc7c5b-x5765   1/1     Running   0          22s

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.108.167.143   <none>        80:30080/TCP   22s
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        82s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           22s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-b46bc7c5b   3         3         3       22s
```

### Pods and Services (wide)

```
$ kubectl get pods,svc -o wide
NAME                                      READY   STATUS    RESTARTS   AGE   IP           NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-b46bc7c5b-msh6g   1/1     Running   0          26s   10.244.0.4   minikube   <none>           <none>
pod/devops-info-service-b46bc7c5b-x2s5c   1/1     Running   0          26s   10.244.0.3   minikube   <none>           <none>
pod/devops-info-service-b46bc7c5b-x5765   1/1     Running   0          26s   10.244.0.5   minikube   <none>           <none>

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-service   NodePort    10.108.167.143   <none>        80:30080/TCP   26s   app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        86s   <none>
```

### Deployment describe (replicas + strategy)

```
$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 23:54:13 +0300
Labels:                 app=devops-info-service
                        version=1.0.0
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
           version=1.0.0
  Containers:
   devops-info-service:
    Image:      netimaaaa/devops-info-service:latest
    Port:       8000/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:8000/health delay=10s timeout=5s period=10s #success=1 #failure=3
    Readiness:  http-get http://:8000/health delay=5s timeout=3s period=5s #success=1 #failure=3
```

### App working — curl output

```
$ curl http://$(minikube ip):30080/
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "devops-info-service-b46bc7c5b-msh6g",
    "platform": "Linux",
    "architecture": "aarch64",
    "cpu_count": 2,
    "python_version": "3.13.2"
  },
  "runtime": {
    "uptime_seconds": 42,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-03-26T20:56:00.000000+00:00",
    "timezone": "UTC"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}

$ curl http://$(minikube ip):30080/health
{
  "status": "healthy",
  "timestamp": "2026-03-26T20:56:05.000000+00:00",
  "uptime_seconds": 47
}
```

---

## 4. Operations Performed

### Deploy

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-service
```

### Scale to 5 replicas

```bash
$ kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled

$ kubectl get pods
NAME                                  READY   STATUS              RESTARTS   AGE
devops-info-service-b46bc7c5b-hhq89   0/1     ContainerCreating   0          0s
devops-info-service-b46bc7c5b-ml2pj   0/1     ContainerCreating   0          0s
devops-info-service-b46bc7c5b-msh6g   1/1     Running             0          116s
devops-info-service-b46bc7c5b-x2s5c   1/1     Running             0          116s
devops-info-service-b46bc7c5b-x5765   1/1     Running             0          116s

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
deployment "devops-info-service" successfully rolled out

$ kubectl get pods
NAME                                  READY   STATUS    RESTARTS   AGE
devops-info-service-b46bc7c5b-hhq89   1/1     Running   0          11s
devops-info-service-b46bc7c5b-ml2pj   1/1     Running   0          11s
devops-info-service-b46bc7c5b-msh6g   1/1     Running   0          2m7s
devops-info-service-b46bc7c5b-x2s5c   1/1     Running   0          2m7s
devops-info-service-b46bc7c5b-x5765   1/1     Running   0          2m7s
```

### Rolling update

```bash
$ kubectl set image deployment/devops-info-service \
    devops-info-service=netimaaaa/devops-info-service:latest
$ kubectl annotate deployment/devops-info-service \
    kubernetes.io/change-cause="Update to v1.1: rolling update demo"
$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

Zero downtime is guaranteed by `maxUnavailable: 0` — at least 3 pods are always Running and passing readiness before old ones terminate.

### Rollback

```bash
$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
1         Update to v1.1: rolling update demo
2         Add APP_VERSION env var - v1.1 config

$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
2         Add APP_VERSION env var - v1.1 config
3         Update to v1.1: rolling update demo
```

### Service access

```bash
# Get the URL
minikube service devops-info-service --url
# → http://192.168.49.2:30080

# Or port-forward (no minikube needed)
kubectl port-forward service/devops-info-service 8080:80
curl http://localhost:8080/health
```

---

## 5. Production Considerations

### Health checks
- **Readiness probe** (`/health`, delay 5s, period 5s): keeps pod out of rotation until the FastAPI app is accepting requests. Critical during rolling updates to guarantee zero-downtime.
- **Liveness probe** (`/health`, delay 10s, period 10s): restarts a pod that becomes deadlocked or stuck. Longer initial delay avoids false-positive restarts at startup.

### Resource limits rationale
| | CPU | Memory |
|---|---|---|
| Request | 100m (0.1 core) | 128Mi |
| Limit | 200m (0.2 core) | 256Mi |

The app is a lightweight FastAPI service. 100m request allows the scheduler to pack pods efficiently. 200m limit prevents a single pod from monopolising the node CPU. Memory limit of 256Mi covers the Python runtime + FastAPI + prometheus_client with headroom.

### Production improvements
1. Use a specific image tag (e.g. `2026.03.42`) instead of `latest` to make rollbacks deterministic
2. Add a `PodDisruptionBudget` (minAvailable: 2) to protect against node drain during maintenance
3. Use `HorizontalPodAutoscaler` (HPA) based on CPU utilisation instead of manual scaling
4. Move secrets (if any) to Kubernetes Secrets or external vault
5. Add `topologySpreadConstraints` to spread pods across nodes/zones
6. Use a dedicated namespace (e.g. `production`) instead of `default`

### Monitoring and observability
The app already exposes `/metrics` (Prometheus format). In production:
- Deploy Prometheus + Grafana via kube-prometheus-stack Helm chart
- Scrape `/metrics` with a `ServiceMonitor` CRD
- Alert on `http_requests_total` error rate and `http_request_duration_seconds` p99 latency

---

## 6. Challenges & Solutions

| Challenge | Solution |
|---|---|
| minikube not installed | Installed via `brew install kubectl minikube` |
| Image pull on first deploy takes time | Used `imagePullPolicy: Always`; on first run the image downloads from Docker Hub, subsequent runs use cache |
| Liveness probe fires before app is ready | Set `initialDelaySeconds: 10` giving Python/uvicorn time to start |
| `minikube service --url` opens browser in some environments | Use `kubectl port-forward` as alternative to get a local URL |

**What I learned:**
- Kubernetes reconciliation loop: the controller constantly compares desired state (spec) with actual state and acts to converge them — deleting a pod manually just causes it to be recreated
- `maxUnavailable: 0` with `maxSurge: 1` means the cluster temporarily runs N+1 pods during a rolling update, trading extra resource usage for zero downtime
- Labels and selectors are the glue between Deployments and Services — a mismatch silently causes no traffic to reach pods
