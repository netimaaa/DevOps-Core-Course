# Lab 03 — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework

**Framework chosen: pytest**

pytest was selected because:
- Simple, readable test syntax with no boilerplate classes required
- Excellent FastAPI/httpx integration via `TestClient`
- Rich plugin ecosystem (`pytest-cov` for coverage)
- Industry standard for modern Python projects

### What is tested

| Endpoint | Tests |
|----------|-------|
| `GET /` | HTTP 200, JSON content-type, presence and types of all top-level fields (`service`, `system`, `runtime`, `request`, `endpoints`), specific field values (`name`, `framework`) |
| `GET /health` | HTTP 200, JSON content-type, `status == "healthy"`, `timestamp` is a string, `uptime_seconds` is a non-negative integer |
| Error handling | `GET /nonexistent` returns 404 JSON with `error` and `message` fields |

**Total: 25 tests**

### CI Workflow Triggers

The workflow runs on:
- `push` to `master` or `lab03` branches (when `app_python/` or the workflow file changes)
- `pull_request` targeting `master`

This avoids running Python CI for unrelated changes (e.g., Terraform, docs).

### Versioning Strategy

**CalVer (Calendar Versioning)** was chosen.

Format: `YYYY.MM.DD.<build_number>` (e.g., `2026.04.09.42`)

Rationale: This is a continuously deployed web service, not a library. CalVer makes the release date immediately visible in the tag, which suits the DevOps course workflow where releases happen frequently and breaking-change semantics (SemVer) are less meaningful.

Docker tags produced per release:
- `latest`
- `2026.04.09` (date)
- `2026.04.09.42` (date + build number)

---

## 2. Workflow Evidence

- **Successful workflow run:** _(link available after first push)_
- **Tests passing locally:**

```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
collected 25 items

tests/test_app.py::TestIndexEndpoint::test_returns_200 PASSED            [  4%]
tests/test_app.py::TestIndexEndpoint::test_response_is_json PASSED       [  8%]
tests/test_app.py::TestIndexEndpoint::test_has_service_field PASSED      [ 12%]
tests/test_app.py::TestIndexEndpoint::test_service_has_required_fields PASSED [ 16%]
tests/test_app.py::TestIndexEndpoint::test_service_name_value PASSED     [ 20%]
tests/test_app.py::TestIndexEndpoint::test_service_framework_value PASSED [ 24%]
tests/test_app.py::TestIndexEndpoint::test_has_system_field PASSED       [ 28%]
tests/test_app.py::TestIndexEndpoint::test_system_has_hostname PASSED    [ 32%]
tests/test_app.py::TestIndexEndpoint::test_system_has_platform PASSED    [ 36%]
tests/test_app.py::TestIndexEndpoint::test_system_has_python_version PASSED [ 40%]
tests/test_app.py::TestIndexEndpoint::test_has_runtime_field PASSED      [ 44%]
tests/test_app.py::TestIndexEndpoint::test_runtime_has_uptime_seconds PASSED [ 48%]
tests/test_app.py::TestIndexEndpoint::test_runtime_has_current_time PASSED [ 52%]
tests/test_app.py::TestIndexEndpoint::test_has_request_field PASSED      [ 56%]
tests/test_app.py::TestIndexEndpoint::test_request_has_method PASSED     [ 60%]
tests/test_app.py::TestIndexEndpoint::test_request_has_path PASSED       [ 64%]
tests/test_app.py::TestIndexEndpoint::test_has_endpoints_field PASSED    [ 68%]
tests/test_app.py::TestHealthEndpoint::test_returns_200 PASSED           [ 72%]
tests/test_app.py::TestHealthEndpoint::test_response_is_json PASSED      [ 76%]
tests/test_app.py::TestHealthEndpoint::test_has_status_field PASSED      [ 80%]
tests/test_app.py::TestHealthEndpoint::test_status_is_healthy PASSED     [ 84%]
tests/test_app.py::TestHealthEndpoint::test_has_timestamp_field PASSED   [ 88%]
tests/test_app.py::TestHealthEndpoint::test_has_uptime_seconds PASSED    [ 92%]
tests/test_app.py::TestErrorHandlers::test_404_returns_json PASSED       [ 96%]
tests/test_app.py::TestErrorHandlers::test_404_has_message PASSED        [100%]

============================== 25 passed in 0.35s ==============================
```

- **Docker Hub image:** `netimaaa/devops-info-service` _(tagged after first CI run)_
- **Status badge:** visible in `app_python/README.md`

---

## 3. Best Practices Implemented

- **Dependency caching:** `actions/setup-python` with `cache: pip` — avoids re-downloading packages on every run. Typical improvement: ~30–40 seconds saved per run.
- **Snyk security scanning:** runs after tests with `continue-on-error: true` and `--severity-threshold=high` — reports high/critical CVEs without blocking the pipeline for informational findings.
- **Workflow concurrency control:** `cancel-in-progress: true` — cancels an outdated run if a newer push arrives on the same branch, saving CI minutes.
- **Path-based triggers:** workflow only runs when `app_python/` or the workflow file itself changes — prevents unnecessary runs.
- **Job dependency (test → docker):** Docker build/push only runs after the test job passes, preventing broken images from being published.
- **Docker layer caching:** `cache-from/cache-to: type=gha` in `build-push-action` — reuses unchanged image layers across runs.

---

## 4. Key Decisions

**Versioning Strategy:** CalVer (`YYYY.MM.DD.<build>`). The service is deployed continuously and has no library consumers who need breaking-change signals. A date-based version makes it immediately obvious when the image was built.

**Docker Tags:** Each release produces three tags — `latest`, the date (`2026.04.09`), and date+build (`2026.04.09.42`). `latest` is for quick pulls; the versioned tags allow rollback to a specific build.

**Workflow Triggers:** Push to `master`/`lab03` for active development, PR to `master` to validate before merge. Path filters ensure only relevant changes trigger the workflow.

**Test Coverage:** All public endpoints and error handlers are tested. Internal helper functions (`get_system_info`, `get_uptime`, etc.) are covered indirectly through endpoint tests. The `__main__` block (server startup) is intentionally excluded — testing uvicorn startup is integration-level, not unit-level.

---

## 5. Challenges

- FastAPI's `TestClient` requires `httpx` as a dependency — added to `requirements.txt` alongside `pytest` and `pytest-cov`.
- On macOS with system Python, a virtual environment is required to install packages; documented in README testing section.
