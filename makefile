# AuthBerry Makefile
# Provides shortcuts for building and running the application

# Default values - NO FALLBACKS FOR CRITICAL SECURITY COMPONENTS
TAG ?= latest
REGISTRY ?=
AUTH_BERRY_UID ?= $(shell id -u)
AUTH_BERRY_GID ?= $(shell id -g)

# TSS UID/GID must be properly configured - NO DEFAULTS
TSS_UID_CMD = $(shell id -u tss 2>/dev/null)
TSS_GID_CMD = $(shell getent group tss | cut -d: -f3 2>/dev/null)

# Validate TSS configuration exists
ifeq ($(TSS_UID_CMD),)
$(error CRITICAL ERROR: TSS user 'tss' not found. TPM Software Stack is not properly installed. Run initial setup first.)
endif

ifeq ($(TSS_GID_CMD),)
$(error CRITICAL ERROR: TSS group 'tss' not found. TPM Software Stack is not properly installed. Run initial setup first.)
endif

# Only set TSS values if validation passed
TSS_UID = $(TSS_UID_CMD)
TSS_GID = $(TSS_GID_CMD)

# TPM devices must be configured - NO DEFAULTS
TPM_DEVICES_FROM_ENV = $(shell grep -oP '^TPM_DEVICES=\K.*' .env 2>/dev/null)
ifeq ($(TPM_DEVICES_FROM_ENV),)
$(error CRITICAL ERROR: TPM_DEVICES not found in .env file. Run initial setup first to configure TPM devices.)
endif
TPM_DEVICES = $(TPM_DEVICES_FROM_ENV)

# Get values from .env file if they exist
FLASK_PORT ?= $(shell grep -oP '^FLASK_PORT=\K.*' .env 2>/dev/null || echo 1337)
VUE_PORT ?= $(shell grep -oP '^VUE_PORT=\K.*' .env 2>/dev/null || echo 3000)

# Vue container always runs on port 3000 internally
VUE_CONTAINER_PORT = 3000

# Development environment variables
FLASK_DEBUG_DEV = 1
FLASK_VOLUMES_DEV = .:/app
NODE_ENV_DEV = development

# Production environment variables
FLASK_DEBUG_PROD = 0
FLASK_VOLUMES_PROD = ./file_uploads:/app/file_uploads
NODE_ENV_PROD = production

# Docker buildx setup with resource limits
.PHONY: buildx-setup
buildx-setup:
	@if ! docker buildx ls | grep -q "shared-builder"; then \
		echo "Setting up resource-limited Docker Buildx builder..."; \
		sudo mkdir -p /etc/buildkit/sgl-buildkit; \
		sudo cp ./docker/buildkitd.toml /etc/buildkit/sgl-buildkit/buildkitd.toml; \
		sudo chown root:root /etc/buildkit/sgl-buildkit/buildkitd.toml; \
		sudo chmod 644 /etc/buildkit/sgl-buildkit/buildkitd.toml; \
		docker buildx create \
			--name shared-builder \
			--driver docker-container \
			--driver-opt network=host \
			--driver-opt image=moby/buildkit:latest \
			--config /etc/buildkit/sgl-buildkit/buildkitd.toml \
			--use; \
		docker buildx inspect --bootstrap; \
		echo "Waiting for builder container to stabilize..."; \
		sleep 5; \
		BUILDER_CONTAINER=$$(docker ps --filter "name=buildx_buildkit_shared-builder" --format "{{.ID}}"); \
		if [ -n "$$BUILDER_CONTAINER" ]; then \
			echo "Applying resource limits to builder container: $$BUILDER_CONTAINER"; \
			docker update \
				--memory=512m \
				--memory-swap=512m \
				--cpus=1.0 \
				--cpu-shares=512 \
				$$BUILDER_CONTAINER; \
			echo "✅ Resource limits applied to builder container"; \
		else \
			echo "⚠️  Could not find builder container for resource limiting"; \
		fi; \
	else \
		echo "Docker Buildx builder 'shared-builder' already exists"; \
		docker buildx use shared-builder; \
	fi

# Build development images
.PHONY: build-dev
build-dev: buildx-setup
	@echo "Building development images..."
	docker buildx bake --file docker-bake.hcl dev \
		--set *.args.AUTH_BERRY_UID=$(AUTH_BERRY_UID) \
		--set *.args.AUTH_BERRY_GID=$(AUTH_BERRY_GID) \
		--set *.args.TSS_UID=$(TSS_UID) \
		--set *.args.TSS_GID=$(TSS_GID) \
		--load

# Build production images
.PHONY: build-prod
build-prod: buildx-setup
	@echo "Building production images..."
	docker buildx bake --file docker-bake.hcl prod \
		--set *.args.AUTH_BERRY_UID=$(AUTH_BERRY_UID) \
		--set *.args.AUTH_BERRY_GID=$(AUTH_BERRY_GID) \
		--set *.args.TSS_UID=$(TSS_UID) \
		--set *.args.TSS_GID=$(TSS_GID) \
		--set *.tags=$(if $(REGISTRY),$(REGISTRY)/auth_berry_*:$(TAG),auth_berry_*:$(TAG)) \
		--load

# Deploy development environment
.PHONY: deploy-dev
deploy-dev: build-dev
	@echo "Deploying development environment..."
	TAG=dev \
	FLASK_DEBUG=$(FLASK_DEBUG_DEV) \
	FLASK_VOLUMES=$(FLASK_VOLUMES_DEV) \
	VUE_PORT=$(VUE_PORT) \
	VUE_CONTAINER_PORT=$(VUE_CONTAINER_PORT) \
	NODE_ENV=$(NODE_ENV_DEV) \
	TPM_DEVICES=$(TPM_DEVICES) \
	docker compose -f docker-compose.dev.yml up -d

# Deploy production environment
.PHONY: deploy-prod
deploy-prod: build-prod
	@echo "Deploying production environment..."
	TAG=$(TAG) \
	FLASK_DEBUG=$(FLASK_DEBUG_PROD) \
	FLASK_VOLUMES=$(FLASK_VOLUMES_PROD) \
	VUE_PORT=$(VUE_PORT) \
	VUE_CONTAINER_PORT=$(VUE_CONTAINER_PORT) \
	NODE_ENV=$(NODE_ENV_PROD) \
	TPM_DEVICES=$(TPM_DEVICES) \
	docker compose up -d

# Clean up containers and networks
.PHONY: clean
clean:
	@echo "Cleaning up containers and networks..."
	docker compose down --remove-orphans --volumes --timeout 10 || true
	docker compose -f docker-compose.dev.yml down --remove-orphans --volumes --timeout 10 || true
	@echo "Forcefully removing any remaining AuthBerry containers..."
	docker container rm -f auth_berry_mariadb auth_berry_flask auth_berry_vue 2>/dev/null || true
	@echo "Removing AuthBerry networks..."
	docker network rm auth_berry_network authberry_auth_berry_network 2>/dev/null || true
	@echo "Pruning unused Docker resources..."
	docker system prune -f

# Clean up containers, networks, and images
.PHONY: clean-all
clean-all: clean
	@echo "Cleaning up images..."
	docker rmi auth_berry_mariadb:$(TAG) auth_berry_flask:$(TAG) auth_berry_vue:$(TAG) 2>/dev/null || true
	docker rmi auth_berry_mariadb:dev auth_berry_flask:dev auth_berry_vue:dev 2>/dev/null || true
	docker rmi auth_berry_mariadb:latest auth_berry_flask:latest auth_berry_vue:latest 2>/dev/null || true
	@echo "Removing AuthBerry volumes..."
	docker volume rm auth_berry_mariadb auth_berry_files mariadb_data file_uploads 2>/dev/null || true
	@echo "Final cleanup - removing all unused Docker resources..."
	docker system prune -af --volumes

# Clean up buildx builder
.PHONY: clean-buildx
clean-buildx:
	@echo "Cleaning up Docker Buildx builder..."
	@if docker buildx ls | grep -q "shared-builder"; then \
		echo "Removing shared-builder..."; \
		docker buildx rm shared-builder || true; \
	fi
	@echo "Removing buildkit configuration..."
	@sudo rm -rf /etc/buildkit/sgl-buildkit 2>/dev/null || true

# Clean up partial database initialization
.PHONY: clean-db-init
clean-db-init:
	@echo "Cleaning up partial database initialization..."
	@docker exec auth_berry_flask bash -c "rm -rf /app/migrations" 2>/dev/null || true
	@echo "Database initialization cleanup completed"

# Initialize database with retry logic
.PHONY: init-db
init-db:
	@echo "Initializing database..."
	docker exec -it auth_berry_flask bash -c "flask db init && flask db migrate -m 'Initial database setup.' && flask db upgrade"

# Initialize database with cleanup on failure
.PHONY: init-db-safe
init-db-safe:
	@echo "Safely initializing database..."
	@if ! $(MAKE) init-db; then \
		echo "Database initialization failed, cleaning up..."; \
		$(MAKE) clean-db-init; \
		echo "Retry with: make init-db"; \
		exit 1; \
	fi

# Show logs
.PHONY: logs
logs:
	docker compose logs -f

# Backup database with TPM-encrypted credentials
.PHONY: backup-db
backup-db:
	@echo "Creating database backup..."
	@mkdir -p ./backups
	@chmod +x scripts/backup_database.sh
	@BACKUP_DIR="$(PWD)/backups" ./scripts/backup_database.sh

# Restore database from backup
.PHONY: restore-db
restore-db:
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "Error: Please specify BACKUP_FILE=path/to/backup.sql.gz"; \
		echo "Example: make restore-db BACKUP_FILE=./backups/authberry_backup_20240101_120000.sql.gz"; \
		exit 1; \
	fi
	@echo "Restoring database from $(BACKUP_FILE)..."
	@gunzip -c "$(BACKUP_FILE)" | docker exec -i auth_berry_mariadb sh -c 'exec mariadb -uroot -p"$$(python3 -c "import sys; sys.path.append(\"/usr/local/bin\"); from tpm_manager import TPMManager; tpm = TPMManager(secrets_dir=\"/secrets\"); tpm.generate_or_load_primary_key(); print(tpm.unseal_secret(\"mariadb_root\").decode(\"utf-8\").strip())")' auth_berry

# Show help
.PHONY: help
help:
	@echo "AuthBerry Makefile Help"
	@echo "========================="
	@echo "Build & Deploy Commands:"
	@echo "  make build-dev         - Build development images"
	@echo "  make build-prod        - Build production images"
	@echo "  make deploy-dev        - Build and deploy development environment"
	@echo "  make deploy-prod       - Build and deploy production environment"
	@echo ""
	@echo "Database Commands:"
	@echo "  make init-db           - Initialize database (run after first deployment)"
	@echo "  make init-db-safe      - Initialize database with automatic cleanup on failure"
	@echo "  make clean-db-init     - Clean up partial database initialization"
	@echo "  make backup-db         - Create database backup with TPM credentials"
	@echo "  make restore-db        - Restore database from backup (requires BACKUP_FILE=path)"
	@echo ""
	@echo "Docker & Buildx Commands:"
	@echo "  make buildx-setup      - Set up resource-limited Docker Buildx builder"
	@echo "  make clean-buildx      - Remove Docker Buildx builder and configuration"
	@echo "  make clean             - Stop containers and remove networks"
	@echo "  make clean-all         - Clean containers, networks, and images"
	@echo ""
	@echo "Monitoring Commands:"
	@echo "  make logs              - Show container logs"
	@echo ""
	@echo "Optional parameters:"
	@echo "  TAG=<tag>              - Image tag (default: latest)"
	@echo "  REGISTRY=<registry>    - Container registry for pushing images"
	@echo "  TPM_DEVICES=<device>   - TPM device path (default: /dev/tpmrm0)"

# Default target
.DEFAULT_GOAL := help
