# Installation Guide

This guide covers installing and running the Salla MCP Server in various environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Docker](#docker)
- [Kubernetes](#kubernetes)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jamalla/fastmcp-openapi-spec.git
   cd fastmcp-openapi-spec
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Configure environment:**
   ```bash
   cp config/development.env .env
   # Edit .env with your SALLA_API_TOKEN
   ```

5. **Run the server:**
   ```bash
   python server.py
   ```

Expected output:
```
Initializing Salla MCP Server
Loaded OpenAPI spec from ./openapi.json
Found 47 endpoints
Server initialized successfully
Starting Salla MCP Server
```

## Development Setup

### Full Development Environment

```bash
# Clone and navigate
git clone https://github.com/jamalla/fastmcp-openapi-spec.git
cd fastmcp-openapi-spec

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development tools
pip install -e .[dev,test,docs]

# Setup pre-commit hooks
pre-commit install
```

### Using Make

```bash
# View available commands
make help

# Setup development environment
make dev

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

### VS Code Setup

1. Install Python extension
2. Select interpreter from `venv/bin/python`
3. Extensions recommended:
   - Python (microsoft.python)
   - Pylance (ms-python.vscode-pylance)
   - Black Formatter (ms-python.black-formatter)
   - Pytest (littlefoxteam.vscode-pytest)

Configure `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## Production Deployment

### System Installation (Linux/macOS)

```bash
# Create application directory
sudo mkdir -p /opt/salla-mcp
sudo chown $USER:$USER /opt/salla-mcp

# Clone repository
cd /opt/salla-mcp
git clone https://github.com/jamalla/fastmcp-openapi-spec.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Configure environment
cp config/production.env .env
# Edit .env with production credentials

# Create system user
sudo useradd -r -s /bin/bash salla-mcp

# Install systemd service
sudo cp deployment/systemd/salla-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable salla-mcp
sudo systemctl start salla-mcp

# Check status
sudo systemctl status salla-mcp
sudo journalctl -u salla-mcp -f
```

### Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install nginx

# Configure Nginx
sudo tee /etc/nginx/sites-available/salla-mcp > /dev/null <<EOF
upstream salla_mcp {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.example.com;
    client_max_body_size 10M;

    location / {
        proxy_pass http://salla_mcp;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/salla-mcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Docker

### Build Image

```bash
# Build image
docker build -f deployment/Dockerfile -t salla-mcp:latest .

# Build with specific Python version
docker build -f deployment/Dockerfile \
  --build-arg PYTHON_VERSION=3.11 \
  -t salla-mcp:3.11 .
```

### Run Container

```bash
# Run interactively
docker run -it \
  -e SALLA_API_TOKEN=your-token \
  -v $(pwd)/openapi.json:/app/openapi.json \
  salla-mcp:latest

# Run in background
docker run -d \
  --name salla-mcp \
  -e SALLA_API_TOKEN=your-token \
  -v $(pwd)/openapi.json:/app/openapi.json \
  salla-mcp:latest

# View logs
docker logs -f salla-mcp

# Stop container
docker stop salla-mcp
docker rm salla-mcp
```

### Docker Compose

```bash
# Start services
docker-compose -f deployment/docker-compose.yml up

# Run in background
docker-compose -f deployment/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker-compose.yml logs -f

# Stop services
docker-compose -f deployment/docker-compose.yml down
```

## Kubernetes

### Deploy with Kubectl

```bash
# Create namespace
kubectl create namespace salla-mcp

# Create secret
kubectl create secret generic salla-mcp-secrets \
  --from-literal=api-token=your-token \
  -n salla-mcp

# Create ConfigMap for OpenAPI spec
kubectl create configmap salla-mcp-spec \
  --from-file=openapi.json=./openapi.json \
  -n salla-mcp

# Deploy
kubectl apply -f deployment/kubernetes/deployment.yaml

# Check deployment
kubectl get deployment -n salla-mcp
kubectl get pods -n salla-mcp
kubectl logs -f deployment/salla-mcp-server -n salla-mcp

# Port forward
kubectl port-forward svc/salla-mcp-service 8000:8000 -n salla-mcp
```

### Using Helm

For production deployments, consider creating a Helm chart. See `deployment/kubernetes/` for examples.

## Configuration

### Environment Variables

See `config/development.env` or `config/production.env` for available options.

**Required:**
- `SALLA_API_TOKEN` - Bearer token for Salla API

**Optional:**
- `SALLA_BASE_URL` - API base URL (default: https://api.salla.dev/v2)
- `LOG_LEVEL` - Logging level (default: INFO)
- `LOG_FORMAT` - Log format: json or text (default: json)
- `API_TIMEOUT` - Request timeout in seconds (default: 30)

## Troubleshooting

### "SALLA_API_TOKEN not configured"

**Solution:**
```bash
# Check if .env exists and token is set
cat .env | grep SALLA_API_TOKEN

# If missing, set environment variable
export SALLA_API_TOKEN=your-token
```

### "OpenAPI spec not found"

**Solution:**
```bash
# Check openapi.json exists
ls -la openapi.json

# Set correct path if using different location
export OPENAPI_SPEC_PATH=/path/to/openapi.json
```

### Module import errors

**Solution:**
```bash
# Reinstall package in development mode
pip install -e .

# Or with all extras
pip install -e .[dev,test]
```

### Port already in use

**Solution:**
```bash
# Change port
export SERVER_PORT=8001

# Or kill process on port 8000
# Linux/macOS:
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Memory issues with Docker

**Solution:**
```bash
# Limit memory
docker run -m 512m salla-mcp:latest

# Or in docker-compose.yml:
services:
  salla-mcp:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Next Steps

- [Configuration Guide](./docs/index.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Code Mode Pattern](./CODE_MODE_GUIDE.md)
- [Contributing Guide](./CONTRIBUTING.md)

## Support

For additional help:
1. Check [Troubleshooting section](#troubleshooting)
2. Review documentation in `docs/`
3. Search existing GitHub issues
4. Open a new GitHub issue with:
   - Python version
   - OS
   - Error logs
   - Steps to reproduce
