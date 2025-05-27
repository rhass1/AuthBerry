# AuthBerry Makefile
# Provides shortcuts for building and running the application

# Default values
TAG ?= latest
REGISTRY ?=
AUTH_BERRY_UID ?= $(shell id -u)
AUTH_BERRY_GID ?= $(shell id -g)
TSS_UID ?= $(shell id -u tss 2>/dev/null || echo 113)
TSS_GID ?= $(shell getent group tss | cut -d: -f3 2>/dev/null || echo 113)
TPM_DEVICES ?= /dev/tpmrm0

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

# Docker buildx setup
.PHONY: buildx-setup
buildx-setup:
	@if ! docker buildx ls | grep -q "buildx-builder"; then \
		echo "Setting up Docker Buildx builder..."; \
		docker buildx create --name buildx-builder --use; \
		docker buildx inspect --bootstrap; \
	else \
		echo "Docker Buildx builder already exists"; \
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

# Initialize database
.PHONY: init-db
init-db:
	@echo "Initializing database..."
	docker exec -it auth_berry_flask bash -c "flask db init && flask db migrate -m 'Initial database setup.' && flask db upgrade"

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
	@echo "Commands:"
	@echo "  make build-dev         - Build development images"
	@echo "  make build-prod        - Build production images"
	@echo "  make deploy-dev        - Build and deploy development environment"
	@echo "  make deploy-prod       - Build and deploy production environment"
	@echo "  make clean             - Stop containers and remove networks"
	@echo "  make clean-all         - Clean containers, networks, and images"
	@echo "  make init-db           - Initialize database (run after first deployment)"
	@echo "  make backup-db         - Create database backup with TPM credentials"
	@echo "  make restore-db        - Restore database from backup (requires BACKUP_FILE=path)"
	@echo "  make logs              - Show container logs"
	@echo ""
	@echo "Optional parameters:"
	@echo "  TAG=<tag>              - Image tag (default: latest)"
	@echo "  REGISTRY=<registry>    - Container registry for pushing images"
	@echo "  TPM_DEVICES=<device>   - TPM device path (default: /dev/tpmrm0)"

# Default target
.DEFAULT_GOAL := help
