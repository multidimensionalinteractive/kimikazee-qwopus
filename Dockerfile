# Kimikazee Qwopus - Dockerfile
# ==============================
# A production-ready Docker image for running Kimikazee Qwopus
# Qwen3.5-9B-Uncensored hyper agent system

# Build arguments for versioning
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# ==============================================================================
# Stage 1: Builder
# ==============================================================================
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up pip caching
RUN pip install --upgrade pip setuptools wheel
RUN pip install --upgrade pip-tools

# Copy requirements first for better caching
COPY requirements.txt .

# Build requirements
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ==============================================================================
# Stage 2: Production
# ==============================================================================
FROM python:3.11-slim-bookworm AS production

# Add build info labels
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

LABEL \
    org.label-schema.build-date="${BUILD_DATE}" \
    org.label-schema.name="Kimikazee Qwopus" \
    org.label-schema.description="Qwen3.5-9B-Uncensored hyper agent system" \
    org.label-schema.version="${VERSION}" \
    org.label-schema.vcs-ref="${VCS_REF}" \
    org.label-schema.schema-version="1.0" \
    maintainer="Kimikazee Team"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    APP_HOME=/app \
    MODEL_PATH=/models \
    LOG_LEVEL=INFO \
    LOG_FILE=/logs/agent.log

# Create directories
RUN mkdir -p \
    ${APP_HOME} \
    ${MODEL_PATH} \
    /logs \
    /tmp \
    && chmod 755 /app /logs

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /wheels /wheels

# Install Python packages
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application code
COPY kimikazee_qwopus.py ${APP_HOME}/
COPY server.py ${APP_HOME}/
COPY config.yaml ${APP_HOME}/
COPY Makefile ${APP_HOME}/

# Copy environment example
COPY .env.example ${APP_HOME}/.env.example

# Set working directory
WORKDIR ${APP_HOME}

# Create non-root user for security
RUN adduser --disabled-password --gecos '' qwopus \
    && chown -R qwopus:qwopus ${APP_HOME} /logs

# Switch to non-root user
USER qwopus

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entry point
ENTRYPOINT ["python"]

# Default command
CMD ["-m", "server"]

# ==============================================================================
# Stage 3: Debug (optional)
# ==============================================================================
FROM production AS debug

# Install debugging tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    htop \
    procps \
    gdb \
    && rm -rf /var/lib/apt/lists/*

# Switch to root for debugging
USER root

# ==============================================================================
# Stage 4: Slim (minimal)
# ==============================================================================
FROM production AS slim

# Remove unnecessary files to reduce size
RUN rm -rf \
    ${APP_HOME}/*.pyc \
    ${APP_HOME}/__pycache__ \
    ${APP_HOME}/.pytest_cache \
    ${APP_HOME}/.pytest \
    /root/.cache \
    && find ${APP_HOME} -type f -name "*.pyc" -delete
