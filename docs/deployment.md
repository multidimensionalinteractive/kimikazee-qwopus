# 🚀 Kimikazee Qwopus Deployment Guide

Complete deployment instructions for Kimikazee Qwopus across different environments.

---

## Table of Contents

- [Overview](#overview)
- [Deployment Options](#deployment-options)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Checklist](#production-checklist)
- [Monitoring Setup](#monitoring-setup)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Kimikazee Qwopus is designed for flexible deployment across various environments:

- **Local Development:** Quick setup for testing and development
- **Docker:** Containerized deployment for consistency
- **Kubernetes:** Scalable production deployment
- **Cloud Providers:** AWS, GCP, Azure, etc.

---

## Deployment Options

| Method | Complexity | Scalability | Best For |
|--------|------------|-------------|----------|
| Local Dev | Low | Low | Development, testing |
| Docker | Medium | Medium | Staging, small production |
| Kubernetes | High | High | Production, scaling |
| Cloud PaaS | Low-Medium | High | Managed deployments |

---

## Local Development

### Prerequisites

- Python 3.10+
- pip or conda
- Git

### Installation

**Option 1: Using pip**

```bash
# Clone repository
git clone https://github.com/kimikazee/kimikazee-qwopus.git
cd kimikazee-qwopus

# Install dependencies
pip install -r requirements.txt

# Download model (optional - will load on first request)
# Model should be placed in project root or ~/.models/

# Run server
python -m server
```

**Option 2: Using Make**

```bash
git clone https://github.com/kimikazee/kimikazee-qwopus.git
cd kimikazee-qwopus

# Install dependencies
make install-test

# Run server
make server
```

**Option 3: Using pipx (isolated)**

```bash
pipx install kimikazee-qwopus
qwopus
```

### Environment Setup

1. **Create config.yaml:**
   ```yaml
   model: Qwen3.5-9B-Uncensored-Q8_0.gguf
   context_window: 32000
   temp: 0.7
   log_level: DEBUG
   ```

2. **Download model file** (recommended):
   ```bash
   # Place model in project root
   # Or set MODEL_PATH environment variable
   export MODEL_PATH=/path/to/model.gguf
   ```

3. **Start server:**
   ```bash
   python -m server
   # or
   uvicorn server:app --reload --host 0.0.0.0 --port 8080
   ```

### Development Mode

Enable auto-reload for development:

```bash
uvicorn server:app --reload \
  --host 0.0.0.0 \
  --port 8080 \
  --log-level debug
```

### Testing Local Deployment

```bash
# Health check
curl http://localhost:8080/health

# Test chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7
  }'

# View API docs
open http://localhost:8080/docs
```

---

## Docker Deployment

### Building the Image

**Quick build:**
```bash
docker build -t kimikazee/qwopus:latest .
```

**Build with tags:**
```bash
docker build -t kimikazee/qwopus:1.0.0 .
docker build -t kimikazee/qwopus:1.0.0-alpine .
```

**Build with arguments:**
```bash
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VERSION=1.0.0 \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t kimikazee/qwopus:latest .
```

### Running with Docker

**Basic run:**
```bash
docker run -d \
  --name qwopus \
  -p 8080:8080 \
  kimikazee/qwopus:latest
```

**With model volume:**
```bash
docker run -d \
  --name qwopus \
  -p 8080:8080 \
  -v $(pwd)/models:/models \
  -e MODEL_PATH=/models/Qwen3.5-9B-Uncensored-Q8_0.gguf \
  kimikazee/qwopus:latest
```

**With custom config:**
```bash
docker run -d \
  --name qwopus \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -e QWOPUS_CONFIG=/app/config.yaml \
  kimikazee/qwopus:latest
```

**With environment variables:**
```bash
docker run -d \
  --name qwopus \
  -p 8080:8080 \
  -e QWOPUS_HOST=0.0.0.0 \
  -e QWOPUS_PORT=8080 \
  -e LOG_LEVEL=INFO \
  -e MODEL_PATH=/models/Qwen3.5-9B-Uncensored-Q8_0.gguf \
  kimikazee/qwopus:latest
```

### Docker Compose

**Basic docker-compose.yml:**
```yaml
version: '3.8'

services:
  qwopus:
    image: kimikazee/qwopus:latest
    container_name: qwopus
    ports:
      - "8080:8080"
    environment:
      - QWOPUS_HOST=0.0.0.0
      - QWOPUS_PORT=8080
      - LOG_LEVEL=INFO
    volumes:
      - ./models:/models
      - ./config.yaml:/app/config.yaml
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

**Advanced docker-compose.yml with GPU support:**
```yaml
version: '3.8'

services:
  qwopus:
    image: kimikazee/qwopus:latest
    container_name: qwopus
    ports:
      - "8080:8080"
    environment:
      - QWOPUS_HOST=0.0.0.0
      - QWOPUS_PORT=8080
      - LOG_LEVEL=INFO
      - MODEL_PATH=/models/Qwen3.5-9B-Uncensored-Q8_0.gguf
    volumes:
      - ./models:/models
      - ./config.yaml:/app/config.yaml
      - ./logs:/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
```

**NVIDIA Container Toolkit required:**
```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit.gpg] https://nvidia.github.io/libnvidia-container/stable/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Docker Registry

**Push to Docker Hub:**
```bash
docker tag kimikazee/qwopus:latest yourusername/qwopus:latest
docker login
docker push yourusername/qwopus:latest
```

**Push to GitHub Container Registry:**
```bash
docker tag kimikazee/qwopus:latest ghcr.io/kimikazee/qwopus:latest
docker push ghcr.io/kimikazee/qwopus:latest
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- NVIDIA GPU support (optional)

### Basic Deployment

**create-k8s-resources.sh:**
```bash
#!/bin/bash

# Namespace
cat > namespace.yaml <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: qwopus
EOF

# ConfigMap
cat > configmap.yaml <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: qwopus-config
  namespace: qwopus
data:
  config.yaml: |
    model: Qwen3.5-9B-Uncensored-Q8_0.gguf
    context_window: 64000
    parallel: 4
    n_predict: -1
    temp: 0.7
    top_p: 0.9
    top_k: 40
    flash_attn: true
    n_threads: 8
    n_gpu_layers: -1
    log_level: INFO
    log_file: /logs/agent.log
EOF

# Persistent Volume Claim
cat > pvc.yaml <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qwopus-models
  namespace: qwopus
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
EOF

# Deployment
cat > deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwopus
  namespace: qwopus
  labels:
    app: qwopus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qwopus
  template:
    metadata:
      labels:
        app: qwopus
    spec:
      containers:
        - name: qwopus
          image: kimikazee/qwopus:latest
          ports:
            - containerPort: 8080
          env:
            - name: QWOPUS_HOST
              value: "0.0.0.0"
            - name: QWOPUS_PORT
              value: "8080"
            - name: MODEL_PATH
              value: "/models/Qwen3.5-9B-Uncensored-Q8_0.gguf"
          volumeMounts:
            - name: config
              mountPath: /app/config.yaml
              subPath: config.yaml
            - name: models
              mountPath: /models
            - name: logs
              mountPath: /logs
          resources:
            requests:
              memory: "16Gi"
              cpu: "4000m"
              nvidia.com/gpu: 1
            limits:
              memory: "24Gi"
              cpu: "8000m"
              nvidia.com/gpu: 1
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 120
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
      volumes:
        - name: config
          configMap:
            name: qwopus-config
        - name: models
          persistentVolumeClaim:
            claimName: qwopus-models
        - name: logs
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: qwopus-service
  namespace: qwopus
spec:
  selector:
    app: qwopus
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
EOF

echo "Kubernetes resources created in current directory"
```

### Apply Resources

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml

# Check deployment
kubectl get pods -n qwopus
kubectl get svc -n qwopus

# Scale deployment (if using multiple replicas)
kubectl scale deployment qwopus --replicas=2 -n qwopus

# View logs
kubectl logs -f deployment/qwopus -n qwopus

# Exec into container
kubectl exec -it deployment/qwopus -n qwopus -- bash
```

### GPU Node Assignment

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: qwopus-gpu
spec:
  nodeSelector:
    nvidia.com/gpu.present: "true"
  containers:
    - name: qwopus
      image: kimikazee/qwopus:latest
      resources:
        limits:
          nvidia.com/gpu: 1
```

### HPA for Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: qwopus-hpa
  namespace: qwopus
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: qwopus
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## Production Checklist

### Pre-Deployment

- [ ] Model file downloaded and verified
- [ ] Configuration tested locally
- [ ] Security hardened (firewall, authentication)
- [ ] Monitoring configured
- [ ] Backup strategy defined
- [ ] Disaster recovery plan documented
- [ ] SLA requirements defined
- [ ] Cost estimation completed

### Deployment

- [ ] Environment variables secured
- [ ] Secrets management implemented
- [ ] Health checks configured
- [ ] Resource limits set
- [ ] Logging centralized
- [ ] Metrics collection enabled
- [ ] Network policies configured
- [ ] SSL/TLS certificates installed

### Post-Deployment

- [ ] Load testing completed
- [ ] Performance benchmarks recorded
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Alerting configured
- [ ] Runbook created
- [ ] Incident response plan tested

---

## Monitoring Setup

### Health Check Endpoint

The `/health` endpoint provides real-time status:

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### Prometheus Metrics

Add metrics endpoint by extending the app:

```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import PlainTextResponse

request_counter = Counter('qwopus_requests_total', 'Total requests', ['endpoint', 'status'])
request_latency = Histogram('qwopus_request_latency_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Grafana Dashboard

Create dashboard with these panels:

1. **Request Rate:** `rate(qwopus_requests_total[5m])`
2. **Response Time:** `histogram_quantile(0.95, rate(qwopus_request_latency_seconds_bucket[5m]))`
3. **Model Status:** `qwopus_model_loaded`
4. **Error Rate:** `rate(qwopus_requests_total{status="error"}[5m])`
5. **Token Usage:** `rate(qwopus_tokens_total[5m])`

### Logging Aggregation

**ELK Stack (Elasticsearch, Logstash, Kibana):**
```yaml
# docker-compose.yml
services:
  qwopus:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    volumes:
      - ./logs:/logs:rw
  
  logstash:
    image: logstash:8.x
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
  
  elasticsearch:
    image: elasticsearch:8.x
  
  kibana:
    image: kibana:8.x
```

### Application Performance Monitoring

**Recommended APM tools:**

1. **New Relic:** Full stack monitoring
2. **Datadog:** APM + infrastructure
3. **Sentry:** Error tracking
4. **Jaeger:** Distributed tracing

### Custom Health Checks

**Enhanced health endpoint:**
```python
@app.get("/health/ready")
async def readiness_check():
    """Check if service is ready to receive traffic."""
    if not app_state.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}
```

---

## Security Best Practices

### Network Security

**Firewall rules:**
```bash
# Allow only necessary ports
ufw allow 8080/tcp
ufw deny out from any to any port 22
ufw enable
```

**Reverse proxy with TLS:**
```nginx
server {
    listen 443 ssl http2;
    server_name qwopus.example.com;
    
    ssl_certificate /etc/letsencrypt/live/qwopus.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qwopus.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Authentication

**API Key middleware:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
API_KEY = os.environ.get("API_KEY")

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials
```

### Secrets Management

**Kubernetes Secrets:**
```bash
# Create secret
kubectl create secret generic qwopus-secrets \
  --from-literal=api-key='your-secure-api-key' \
  --from-literal=db-password='your-db-password' \
  -n qwopus
```

**Environment variable injection:**
```yaml
env:
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: qwopus-secrets
        key: api-key
```

### Input Validation

**Sanitize user input:**
```python
from html import escape
import re

def sanitize_input(text: str) -> str:
    """Basic input sanitization."""
    # Remove potentially dangerous characters
    text = escape(text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Limit length
    return text[:10000]
```

---

## Troubleshooting

### Common Issues

#### Model Not Loading

**Symptoms:** `/health` returns `model_loaded: false`

**Solutions:**
1. Check file exists:
   ```bash
   ls -la /models/Qwen3.5-9B-Uncensored-Q8_0.gguf
   ```

2. Check permissions:
   ```bash
   chmod +r /models/Qwen3.5-9B-Uncensored-Q8_0.gguf
   ```

3. Increase memory:
   ```bash
   docker update --memory=16g qwopus
   ```

#### Out of Memory

**Symptoms:** Container crashes, OOMKilled

**Solutions:**
1. Reduce VRAM usage:
   ```yaml
   n_gpu_layers: 40  # Instead of -1
   context_window: 32000
   ```

2. Increase container memory:
   ```bash
   docker update --memory=24g qwopus
   ```

3. Use smaller model:
   ```bash
   model: Qwen3.5-9B-Uncensored-Q4_K_M.gguf
   ```

#### Slow Performance

**Symptoms:** High latency, low tokens/second

**Solutions:**
1. Enable GPU:
   ```yaml
   n_gpu_layers: -1
   flash_attn: true
   ```

2. Reduce context:
   ```yaml
   context_window: 32000
   ```

3. Increase resources:
   ```bash
   kubectl scale deployment qwopus --replicas=2
   ```

#### CORS Errors

**Symptoms:** Browser console shows CORS error

**Solutions:**
1. Configure CORS properly:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-domain.com"],
       allow_credentials=True,
   )
   ```

2. Use reverse proxy:
   ```nginx
   location / {
       proxy_set_header Origin $http_origin;
       proxy_pass http://localhost:8080;
   }
   ```

### Debug Mode

**Enable debug logging:**
```bash
export LOG_LEVEL=DEBUG
docker logs -f qwopus
```

**Interactive debugging:**
```bash
docker exec -it qwopus bash
python -c "from server import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8080)"
```

---

## Related Documentation

- [API Reference](/root/repos/kimikazee-qwopus/docs/api.md)
- [Configuration Guide](/root/repos/kimikazee-qwopus/docs/configuration.md)
- [Usage Examples](/root/repos/kimikazee-qwopus/examples/)

---

## Support

- **GitHub Issues:** [kimikazee/kimikazee-qwopus/issues](https://github.com/kimikazee/kimikazee-qwopus/issues)
- **Documentation:** [Kimikazee Qwopus Docs](https://kimikazee.github.io/kimikazee-qwopus)

---

*Last updated: 2026-04-30 | Version: 1.0.0*
