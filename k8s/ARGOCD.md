# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation

ArgoCD was installed via Helm into a dedicated `argocd` namespace:

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd --namespace argocd

# Wait for server pod to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=120s
```

### Installation Verification

```bash
kubectl get pods -n argocd
```

Expected output — all pods Running:

```
NAME                                                READY   STATUS    RESTARTS
argocd-application-controller-0                     1/1     Running   0
argocd-applicationset-controller-xxx                1/1     Running   0
argocd-dex-server-xxx                               1/1     Running   0
argocd-notifications-controller-xxx                 1/1     Running   0
argocd-redis-xxx                                    1/1     Running   0
argocd-repo-server-xxx                              1/1     Running   0
argocd-server-xxx                                   1/1     Running   0
```

**Screenshot — pods running:**

<!-- INSERT SCREENSHOT: kubectl get pods -n argocd showing all Running -->
`[screenshot: argocd-pods-running.png]`

### UI Access

Port-forward was used to expose the ArgoCD server locally:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

The UI is then accessible at **https://localhost:8080** (accept the self-signed certificate warning).

**Retrieve initial admin password:**

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

Login credentials: **Username:** `admin` | **Password:** output of the command above.

**Screenshot — ArgoCD UI login page:**

<!-- INSERT SCREENSHOT: ArgoCD UI at https://localhost:8080 -->
`[screenshot: argocd-ui-login.png]`

**Screenshot — ArgoCD UI dashboard (after login):**

<!-- INSERT SCREENSHOT: ArgoCD dashboard showing applications -->
`[screenshot: argocd-ui-dashboard.png]`

### CLI Configuration

```bash
# Install on macOS
brew install argocd

# Log in (with port-forward running)
argocd login localhost:8080 --insecure
# Enter: admin / <password from above>

# Verify connection
argocd version
argocd app list
```

---

## 2. Application Configuration

### Directory Structure

```
k8s/argocd/
├── application.yaml        # Default app (namespace: default, manual sync)
├── application-dev.yaml    # Dev environment (auto-sync + selfHeal)
├── application-prod.yaml   # Prod environment (manual sync)
└── applicationset.yaml     # Bonus: generates dev+prod from one template
```

### application.yaml — Default Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/netimaaa/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

**Key fields:**

| Field | Value | Purpose |
|-------|-------|---------|
| `repoURL` | `https://github.com/netimaaa/DevOps-Core-Course.git` | Git source of truth |
| `targetRevision` | `lab13` | Branch to track |
| `path` | `k8s/devops-info-service` | Helm chart location in repo |
| `destination.namespace` | `default` | Target namespace |
| `syncPolicy` | manual (no `automated` block) | Manual trigger required |

### Deploy and Sync

```bash
# Apply the Application resource
kubectl apply -f k8s/argocd/application.yaml

# Trigger initial sync via CLI
argocd app sync python-app

# Check status
argocd app get python-app
```

**Screenshot — Application in ArgoCD UI (Synced state):**

<!-- INSERT SCREENSHOT: python-app application card in ArgoCD UI -->
`[screenshot: argocd-app-synced.png]`

**Screenshot — Application details view (resources tree):**

<!-- INSERT SCREENSHOT: ArgoCD application detail showing Deployment, Service, etc. -->
`[screenshot: argocd-app-details.png]`

### GitOps Workflow Test

A change was made to `values.yaml` (replica count modified), committed, and pushed:

```bash
# Edit values.yaml — change replicaCount: 3 → 2
git add k8s/devops-info-service/values.yaml
git commit -m "test: reduce replicas to 2 for GitOps drift test"
git push origin lab13
```

ArgoCD detects the drift within its polling interval (~3 min) and shows **OutOfSync** status. After syncing:

```bash
argocd app sync python-app
```

The cluster state was updated to match Git.

**Screenshot — OutOfSync state after Git change:**

<!-- INSERT SCREENSHOT: ArgoCD showing python-app as OutOfSync -->
`[screenshot: argocd-app-outofsync.png]`

---

## 3. Multi-Environment Deployment

### Namespace Creation

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Environment Comparison

| Configuration | Dev | Prod |
|--------------|-----|------|
| Replicas | 1 | 5 |
| Image tag | `latest` | `1.0.0` |
| CPU limit | 100m | 500m |
| Memory limit | 128Mi | 512Mi |
| Service type | NodePort | LoadBalancer |
| Log level | debug | info |
| Sync policy | Automated | Manual |
| selfHeal | true | — |
| prune | true | — |

### application-dev.yaml — Auto-Sync

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

- `automated`: ArgoCD syncs automatically when it detects drift from Git
- `prune: true`: Resources removed from Git are deleted from the cluster
- `selfHeal: true`: Manual cluster changes are automatically reverted to match Git

### application-prod.yaml — Manual Sync

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
  # No automated block — manual sync required
```

**Why manual sync for production?**

1. **Change review**: Every deployment can be inspected before applying
2. **Controlled timing**: Releases happen at a scheduled moment, not immediately on push
3. **Compliance**: Audit trail shows who approved and triggered each deployment
4. **Rollback planning**: Time to prepare a rollback plan before promoting
5. **Risk reduction**: A bad commit won't auto-deploy to prod and impact real users

### Deploy Both Environments

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# Sync prod manually (dev auto-syncs)
argocd app sync python-app-prod

# Verify both
argocd app list
kubectl get pods -n dev
kubectl get pods -n prod
```

**Screenshot — ArgoCD UI showing both python-app-dev and python-app-prod:**

<!-- INSERT SCREENSHOT: ArgoCD dashboard with both apps visible -->
`[screenshot: argocd-both-apps.png]`

**Screenshot — `argocd app list` output:**

<!-- INSERT SCREENSHOT: terminal showing argocd app list with dev and prod -->
`[screenshot: argocd-app-list.png]`

**Screenshot — pods in dev namespace:**

<!-- INSERT SCREENSHOT: kubectl get pods -n dev -->
`[screenshot: kubectl-pods-dev.png]`

**Screenshot — pods in prod namespace:**

<!-- INSERT SCREENSHOT: kubectl get pods -n prod -->
`[screenshot: kubectl-pods-prod.png]`

---

## 4. Self-Healing Evidence

### 4.1 Manual Scale Test (Dev)

**Before** — Git defines `replicaCount: 1` for dev. Dev pod count:

```bash
kubectl get pods -n dev
# NAME                                        READY   STATUS    RESTARTS
# devops-info-service-xxx-yyy                 1/1     Running   0
```

**Action** — Manually scale to 5 replicas:

```bash
kubectl scale deployment devops-info-service -n dev --replicas=5
# deployment.apps/devops-info-service scaled
```

**ArgoCD detects drift** — `argocd app get python-app-dev` shows `OutOfSync`.

**Self-heal** — Within ~15 seconds ArgoCD reverts the cluster back to 1 replica (matching Git):

```bash
kubectl get pods -n dev -w
# Extra pods enter Terminating state and are removed
```

**After** — cluster matches Git again, back to 1 pod.

**Screenshot — ArgoCD detecting drift (OutOfSync) after manual scale:**

<!-- INSERT SCREENSHOT: ArgoCD python-app-dev showing OutOfSync during scale test -->
`[screenshot: argocd-selfheal-outofsync.png]`

**Screenshot — ArgoCD after self-heal (Synced, 1 replica):**

<!-- INSERT SCREENSHOT: ArgoCD python-app-dev back to Synced -->
`[screenshot: argocd-selfheal-synced.png]`

### 4.2 Pod Deletion Test (Dev)

```bash
# Delete a running pod
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-service

# Watch Kubernetes recreate it
kubectl get pods -n dev -w
```

A new pod appears within seconds. This is **Kubernetes self-healing** (ReplicaSet controller ensures desired count), **not ArgoCD**. ArgoCD remains `Synced` because the Deployment spec hasn't changed — only the pod instance was replaced.

**Screenshot — pod being recreated after deletion:**

<!-- INSERT SCREENSHOT: kubectl get pods -n dev -w showing pod Terminating then new pod Running -->
`[screenshot: kubectl-pod-recreation.png]`

### 4.3 Configuration Drift Test (Dev)

```bash
# Manually add a label to the deployment
kubectl patch deployment devops-info-service -n dev \
  -p '{"spec":{"template":{"metadata":{"labels":{"manual-label":"test"}}}}}'
```

ArgoCD detects the configuration drift and shows a diff:

```bash
argocd app diff python-app-dev
```

With `selfHeal: true`, ArgoCD reverts the manual patch automatically, restoring the deployment to the Git-defined state.

**Screenshot — ArgoCD diff view showing configuration drift:**

<!-- INSERT SCREENSHOT: argocd app diff or ArgoCD UI diff view -->
`[screenshot: argocd-config-drift-diff.png]`

### 4.4 Sync Behavior Explanation

| Scenario | Who Heals | Mechanism |
|---------|-----------|-----------|
| Pod crashes / deleted | Kubernetes | ReplicaSet controller reconciles desired pod count |
| Replica count changed manually | ArgoCD | `selfHeal` reverts cluster state to match Git |
| Label/annotation edited manually | ArgoCD | `selfHeal` patches resource back to Git definition |
| New resource added to cluster manually | ArgoCD | `prune: true` deletes resource not in Git |
| Git commit changes values | ArgoCD | `automated` detects drift and syncs (dev) or awaits manual trigger (prod) |

**ArgoCD Sync Triggers:**
- Polls Git every **3 minutes** by default
- Webhook from GitHub can trigger immediate sync
- Manual trigger via UI or `argocd app sync`

---

## 5. Bonus — ApplicationSet

### applicationset.yaml

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
            autoSync: "true"
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: "false"
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/netimaaa/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/devops-info-service
        helm:
          valueFiles:
            - values.yaml
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        syncOptions:
          - CreateNamespace=true
```

### Generator Configuration

The **List generator** defines an explicit list of parameter sets. Each element provides variables (`env`, `namespace`, `valuesFile`) that are interpolated into the template using `{{variable}}` syntax. This single ApplicationSet generates two Application resources: `python-app-dev` and `python-app-prod`.

### Apply

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
argocd app list
```

**Screenshot — ApplicationSet generating both applications:**

<!-- INSERT SCREENSHOT: ArgoCD UI or argocd app list showing apps generated by ApplicationSet -->
`[screenshot: argocd-applicationset-apps.png]`

### ApplicationSet vs Individual Applications

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|---------------|
| Maintenance | Edit each file separately | Single template |
| Adding an environment | New YAML file | Add one list element |
| Consistency | Manual, error-prone | Template guarantees consistency |
| Scale | Grows linearly with envs | Constant effort |
| Use case | Few, very different apps | Many similar envs or clusters |

**When to use which generator:**

- **List**: Explicit, small set of environments with known parameters
- **Git directory**: Auto-discover apps from repo structure (mono-repo)
- **Cluster**: Deploy same app to multiple clusters
- **Matrix**: Cross-product of two generators (e.g., all apps × all clusters)
