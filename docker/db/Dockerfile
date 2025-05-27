# Dockerfile for auth_berry_mariadb (MariaDB with TPM)
FROM mariadb:latest

ARG TSS_GID
ARG TSS_UID
ARG AUTH_BERRY_UID
ARG AUTH_BERRY_GID

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-setuptools \
    pkg-config \
    build-essential \
    cargo \
    libtss2-dev \
    tpm2-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install tpm2-pytss
RUN pip3 install --no-cache-dir tpm2-pytss==2.3.0

# Now that tpm2-pytss is installed (which will have created the tss user),
# ensure the TSS user/group matches the host system
RUN if getent group tss > /dev/null; then \
        # If tss group exists, modify its GID to match host
        groupmod -g ${TSS_GID} tss || echo "Failed to modify tss group GID, likely already correct"; \
    else \
        # If tss group doesn't exist, create it with host's GID
        groupadd -g ${TSS_GID} tss; \
    fi && \
    if id tss > /dev/null 2>&1; then \
        # If tss user exists, modify its UID to match host
        usermod -u ${TSS_UID} -g ${TSS_GID} tss || echo "Failed to modify tss user UID, likely already correct"; \
    else \
        # If tss user doesn't exist, create it with host's UID
        useradd -u ${TSS_UID} -g ${TSS_GID} -s /bin/false tss; \
    fi

RUN usermod -aG tss mysql

# Copy TPM manager library
COPY backend/utils/tpm_manager.py /usr/local/bin/tpm_manager.py

# Copy custom initialization scripts
COPY docker/db/secure_init.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/secure_init.sh
COPY docker/db/secure_init.py /usr/local/bin/

# Production-specific optimizations
RUN echo "[mysqld]" >> /etc/mysql/conf.d/prod.cnf && \
    echo "innodb_buffer_pool_size=256M" >> /etc/mysql/conf.d/prod.cnf && \
    echo "innodb_flush_log_at_trx_commit=2" >> /etc/mysql/conf.d/prod.cnf && \
    echo "max_connections=200" >> /etc/mysql/conf.d/prod.cnf

HEALTHCHECK --interval=5s --timeout=3s --retries=15 \
    CMD healthcheck.sh --connect --innodb_initialized

CMD ["mariadbd"]
