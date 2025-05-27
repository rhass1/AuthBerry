# Dockerfile for auth_berry_app (Flask) - Production
FROM python:3.13.1-bookworm AS builder

WORKDIR /app

# Install system packages for building dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cargo \
    pkg-config \
    libmariadb-dev \
    libtss2-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Multi-stage build for production
FROM python:3.13.1-slim-bookworm

ARG AUTH_BERRY_UID
ARG AUTH_BERRY_GID
ARG TSS_UID
ARG TSS_GID

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    libtss2-esys-3.0.2-0 \
    tpm2-tools \
    libmagic1 \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up tss group and user
RUN if getent group tss > /dev/null; then \
        groupmod -g ${TSS_GID} tss || echo "Failed to modify tss group GID"; \
    else \
        groupadd -g ${TSS_GID} tss; \
    fi && \
    if id tss > /dev/null 2>&1; then \
        usermod -u ${TSS_UID} -g ${TSS_GID} tss || echo "Failed to modify tss user UID"; \
    else \
        useradd -u ${TSS_UID} -g ${TSS_GID} -s /bin/false tss; \
    fi

# Create a non-root user (auth-berry-user) with UID/GID from build args
RUN groupadd --gid ${AUTH_BERRY_GID} auth-berry-user && \
    useradd --uid ${AUTH_BERRY_UID} --gid ${AUTH_BERRY_GID} --create-home auth-berry-user && \
    usermod -aG tss auth-berry-user

# Create necessary directories
RUN mkdir -p /app/file_uploads /app/logs /app/secrets && \
    chmod -R 750 /app/file_uploads /app/logs /app/secrets && \
    chown -R auth-berry-user:auth-berry-user /app/file_uploads /app/logs /app/secrets

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend /app/backend
COPY migrations /app/migrations
COPY run.py /app/run.py
COPY config.py /app/config.py

# Copy entrypoint script
COPY docker/app/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set production environment variables
ENV FLASK_APP=run.py
ENV FLASK_DEBUG=0
ENV GUNICORN_WORKERS=4
ENV APP_SECRET_KEY_FILE=/secrets/app_secret
ENV JWT_SECRET_FILE=/secrets/jwt_secret
ENV ENCRYPTION_KEY_FILE=/secrets/encryption_key
ENV FILE_UPLOAD_PATH=/app/file_uploads

# Expose port 1337
EXPOSE 1337

# Switch to non-root auth-berry-user
USER auth-berry-user

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "--workers=1", "--worker-class=gevent", "--worker-connections=2500", "--bind=0.0.0.0:1337", "--access-logfile=-", "--error-logfile=-", "--log-level=info", "--timeout=120", "--keep-alive=5", "run:app"]
