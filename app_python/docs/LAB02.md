# Lab 02 - Docker Containerization

## Docker Best Practices Applied

### 1. Non-Root User
**Why it matters:** Running containers as root is a security risk. If an attacker compromises the container, they have root privileges.

**Implementation:**
```dockerfile
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser appuser
USER appuser
```

### 2. Specific Base Image Version
**Why it matters:** Using `latest` tag can break builds when base image updates. Specific versions ensure reproducibility.

**Implementation:**
```dockerfile
FROM python:3.13-slim
```
Chose `3.13-slim` for smaller size (267MB vs 1GB+ for full image) while keeping necessary system libraries.

### 3. Layer Caching Optimization
**Why it matters:** Dependencies change less frequently than code. Copying requirements first allows Docker to cache the pip install layer.

**Implementation:**
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

### 4. .dockerignore File
**Why it matters:** Reduces build context size and speeds up builds by excluding unnecessary files.

**What's excluded:**
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environments (`venv/`)
- Documentation and tests
- IDE files (`.vscode/`, `.idea/`)

### 5. Minimal Dependencies
**Why it matters:** Smaller images = faster deployments, less attack surface, lower storage costs.

**Implementation:**
- Used `--no-cache-dir` flag to avoid storing pip cache
- Only copied necessary files (app.py, requirements.txt)

## Image Information

**Base Image:** `python:3.13-slim`
- **Justification:** Balance between size and functionality. Alpine is smaller but can have compatibility issues with Python packages.

**Final Image Size:** 267MB (58MB compressed)
- Base python:3.13-slim: ~150MB
- Dependencies (FastAPI + Uvicorn): ~10MB
- Application code: <1MB

**Layer Structure:**
1. Base OS and Python runtime
2. Non-root user creation
3. Dependencies installation (cached layer)
4. Application code (changes frequently)

## Build & Run Process

### Build Output
```bash
$ docker build -t devops-info-service:latest .
[+] Building 15.2s (10/10) FINISHED
 => [1/5] FROM python:3.13-slim
 => [2/5] WORKDIR /app
 => [3/5] RUN groupadd -r appuser -g 1000 && useradd -r -u 1000 -g appuser appuser
 => [4/5] COPY requirements.txt .
 => [5/5] RUN pip install --no-cache-dir -r requirements.txt
 => [6/5] COPY app.py .
 => [7/5] RUN chown -R appuser:appuser /app
 => exporting to image
```

### Running Container
```bash
$ docker run -d -p 8000:8000 --name devops-service devops-info-service:latest
71a8a738632d

$ docker ps
CONTAINER ID   IMAGE                          STATUS         PORTS
71a8a738632d   devops-info-service:latest    9 minutes   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

### Testing Endpoints
```bash
$ curl http://localhost:8000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"71a8a738632d","platform":"Linux","platform_version":"#1 SMP Sun Jan 25 02:26:28 UTC 2026","architecture":"aarch64","cpu_count":14,"python_version":"3.13.12"},"runtime":{"uptime_seconds":32,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T22:30:14.079372+00:00","timezone":"UTC"},"request":{"client_ip":"192.168.65.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

$ curl http://localhost:8000/health
{"status":"healthy","timestamp":"2026-02-04T22:30:23.508051+00:00","uptime_seconds":41}
```

### Verifying Non-Root User
```bash
$ docker exec devops-service whoami
appuser
```

### Docker Hub
**Repository URL:** https://hub.docker.com/r/netimaaaa/devops-info-service

**Push Output:**
```bash
$ docker tag devops-info-service:latest netimaaaa/devops-info-service:latest
$ docker push netimaaaa/devops-info-service:latest
The push refers to repository [docker.io/netimaaaa/devops-info-service]
latest: digest: sha256:ab1272860ae1cebdc3e444b95b5502be9d443a3b51d9fb409750dcd21afcae98 size: 856
```

## Technical Analysis

### Why This Dockerfile Works

1. **Layer Order:** Dependencies are installed before copying application code. Since dependencies rarely change, Docker can reuse the cached layer on subsequent builds, making rebuilds much faster.

2. **Security:** Running as non-root user limits potential damage if container is compromised. Even if attacker gains access, they can't modify system files or escalate privileges.

3. **Reproducibility:** Pinned base image version ensures builds are consistent across different environments and time periods.

### What Would Happen If Layer Order Changed?

If we copied all files first, then installed dependencies:
```dockerfile
COPY . .  # Bad: copies everything including code
RUN pip install -r requirements.txt
```

**Problem:** Every code change invalidates the pip install cache, forcing full dependency reinstall on every build. This wastes time and bandwidth.

### Security Considerations

1. **Non-root user:** Mandatory security practice. Prevents privilege escalation attacks.
2. **Slim base image:** Fewer packages = smaller attack surface
3. **No secrets in image:** Environment variables used for configuration, not hardcoded
4. **Specific versions:** Prevents supply chain attacks through unexpected updates

### How .dockerignore Improves Build

- **Faster builds:** Smaller context means less data to send to Docker daemon
- **Smaller images:** Prevents accidentally copying unnecessary files
- **Security:** Excludes sensitive files like `.env` or credentials
- **Cleaner:** Only production-relevant files in final image

## Challenges & Solutions

### Challenge 1: Understanding Layer Caching
**Issue:** Initially didn't understand why order mattered.

**Solution:** Researched Docker layer caching. Learned that each instruction creates a layer, and Docker reuses unchanged layers. Placing frequently-changing files (code) after rarely-changing files (dependencies) maximizes cache hits.

### Challenge 2: Image Size
**Issue:** First attempt used `python:3.13` (full image) resulting in 1GB+ image.

**Solution:** Switched to `python:3.13-slim` which reduced size to 267MB while keeping all necessary functionality. Considered Alpine but decided against it due to potential compatibility issues with Python packages.

### Challenge 3: File Permissions
**Issue:** Initially forgot to change ownership of files to appuser, causing permission errors.

**Solution:** Added `RUN chown -R appuser:appuser /app` before switching to non-root user.

## Key Learnings

1. **Layer caching is powerful:** Proper layer ordering can reduce build times from minutes to seconds
2. **Security by default:** Non-root user should be standard practice, not optional
3. **Size matters:** Slim images deploy faster and cost less in storage/bandwidth
4. **Reproducibility:** Pinned versions prevent "works on my machine" problems
5. **.dockerignore is essential:** Like .gitignore but for Docker builds