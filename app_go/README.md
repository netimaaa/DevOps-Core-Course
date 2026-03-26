# DevOps Info Service (Go)

A high-performance compiled implementation of the DevOps Info Service using Go's standard library. This version demonstrates the benefits of compiled languages for containerization and production deployments.

## Overview

This Go implementation provides the same functionality as the Python version but with:
- **Faster startup time** - Compiled binary starts instantly
- **Lower memory footprint** - Typically 10-20MB vs 50MB+ for Python
- **Single binary deployment** - No runtime dependencies
- **Better performance** - Native code execution
- **Smaller container images** - Ideal for multi-stage Docker builds

## Prerequisites

- **Go**: 1.21 or higher
- **No external dependencies** - Uses only Go standard library

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course/app_go
   ```

2. **Initialize Go module** (already done):
   ```bash
   go mod init devops-info-service
   ```

3. **Verify installation**:
   ```bash
   go version
   ```

## Building the Application

### Development Build

Build for your current platform:

```bash
go build -o devops-info-service main.go
```

### Production Build

Build with optimizations and reduced binary size:

```bash
# Standard build
go build -ldflags="-s -w" -o devops-info-service main.go

# Cross-compilation examples
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-macos main.go
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go
```

**Build flags explained:**
- `-ldflags="-s -w"` - Strip debug information and symbol table (smaller binary)
- `GOOS` - Target operating system
- `GOARCH` - Target architecture

### Binary Size Comparison

```bash
# Check binary size
ls -lh devops-info-service

# Typical sizes:
# - Standard build: ~6-8 MB
# - Optimized build: ~4-5 MB
# - Python equivalent: 50+ MB (with dependencies)
```

## Running the Application

### Run Directly (Development)

```bash
# Run without building
go run main.go

# Run with custom configuration
PORT=8080 go run main.go
HOST=127.0.0.1 PORT=3000 go run main.go
```

### Run Compiled Binary

```bash
# Build first
go build -o devops-info-service main.go

# Run the binary
./devops-info-service

# Run with custom configuration
PORT=8080 ./devops-info-service
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

The service will be available at `http://localhost:8080` (default port for Go version)

## API Endpoints

### GET /

Returns comprehensive service and system information.

**Response Example:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "darwin",
    "platform_version": "go1.21.5",
    "architecture": "arm64",
    "cpu_count": 8,
    "go_version": "go1.21.5"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-26T18:00:00.000000000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
    "user_agent": "curl/8.1.2",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

**Testing:**
```bash
# Using curl
curl http://localhost:8080/

# Using curl with pretty print
curl http://localhost:8080/ | jq

# Using HTTPie
http http://localhost:8080/
```

### GET /health

Simple health check endpoint for monitoring.

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T18:00:00.000000000Z",
  "uptime_seconds": 3600
}
```

**Testing:**
```bash
curl http://localhost:8080/health
```

## Configuration

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `8080` | Port number to listen on |

**Example:**
```bash
export HOST=127.0.0.1
export PORT=9000
./devops-info-service
```

## Development

### Project Structure

```
app_go/
├── main.go                   # Main application
├── go.mod                    # Go module definition
├── README.md                 # This file
└── docs/                     # Lab documentation
    ├── LAB01.md             # Lab submission
    ├── GO.md                # Language justification
    └── screenshots/         # Proof of work
```

### Code Quality

The Go implementation follows best practices:
- **Standard library only** - No external dependencies
- **Structured types** - Clear data models with JSON tags
- **Error handling** - Proper error checking and logging
- **HTTP standards** - Correct status codes and headers
- **Clean code** - Well-organized functions and comments

### Testing

```bash
# Run the application
go run main.go

# In another terminal, test endpoints
curl http://localhost:8080/
curl http://localhost:8080/health

# Test error handling
curl http://localhost:8080/nonexistent

# Load testing
ab -n 1000 -c 10 http://localhost:8080/health
```

### Performance Benchmarking

```bash
# Build optimized binary
go build -ldflags="-s -w" -o devops-info-service main.go

# Measure startup time
time ./devops-info-service &
sleep 1
kill %1

# Measure memory usage
ps aux | grep devops-info-service

# Benchmark requests
ab -n 10000 -c 100 http://localhost:8080/health
```

## Advantages Over Python Version

### 1. Performance
- **Startup**: < 10ms vs ~1000ms for Python
- **Memory**: ~15MB vs ~50MB for Python
- **Response time**: Consistently faster due to native compilation

### 2. Deployment
- **Single binary**: No runtime or dependencies needed
- **Cross-compilation**: Build for any platform from any platform
- **Container size**: Much smaller Docker images (multi-stage builds)

### 3. Production Readiness
- **Stability**: Compiled code catches many errors at build time
- **Concurrency**: Native goroutines for handling multiple requests
- **Resource efficiency**: Lower CPU and memory usage

### 4. DevOps Benefits
- **Faster CI/CD**: Quick builds and tests
- **Smaller artifacts**: Faster deployments
- **Better scaling**: More instances per server

## Comparison: Go vs Python

| Aspect | Go | Python (FastAPI) |
|--------|----|--------------------|
| **Startup Time** | < 10ms | ~1000ms |
| **Memory Usage** | ~15MB | ~50MB |
| **Binary Size** | ~5MB | N/A (needs runtime) |
| **Dependencies** | None | FastAPI, Uvicorn |
| **Build Time** | ~1s | N/A (interpreted) |
| **Container Size** | ~10MB | ~100MB+ |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Development Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Troubleshooting

### Port Already in Use

```bash
# Find process using the port
lsof -i :8080

# Kill the process or use a different port
PORT=9000 ./devops-info-service
```

### Build Errors

```bash
# Clean build cache
go clean -cache

# Verify Go installation
go version

# Check module
go mod verify
```

### Cross-Compilation Issues

```bash
# List available platforms
go tool dist list

# Build for specific platform
GOOS=linux GOARCH=amd64 go build main.go
```

## Future Enhancements

This service will be enhanced in future labs:
- **Lab 2**: Multi-stage Docker builds (Go excels here)
- **Lab 3**: Unit tests with Go's testing package
- **Lab 8**: Prometheus metrics endpoint
- **Lab 9**: Kubernetes deployment
- **Lab 12**: Persistent storage

## Resources

- [Go Documentation](https://golang.org/doc/)
- [Go net/http Package](https://pkg.go.dev/net/http)
- [Effective Go](https://golang.org/doc/effective_go)
- [Go by Example](https://gobyexample.com/)

## License

This project is part of the DevOps Core Course.

## Author

Created for Lab 01 - DevOps Info Service: Web Application Development (Bonus Task)