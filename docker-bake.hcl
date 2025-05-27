// docker-bake.hcl - Buildx configuration for AuthBerry

// Variables with default values
variable "AUTH_BERRY_UID" {
  default = "1000"
}

variable "AUTH_BERRY_GID" {
  default = "1000"
}

variable "TSS_UID" {
  default = "113"
}

variable "TSS_GID" {
  default = "113"
}

variable "REGISTRY" {
  default = ""
}

variable "TAG" {
  default = "latest"
}

// Base group for common settings
group "default" {
  targets = ["app-prod", "db-prod", "vue-prod"]
}

group "dev" {
  targets = ["app-dev", "db-dev", "vue-dev"]
}

group "prod" {
  targets = ["app-prod", "db-prod", "vue-prod"]
}

// Target for development DB
target "db-dev" {
  context = "."
  dockerfile = "docker/db/Dockerfile.dev"
  tags = ["auth_berry_mariadb:dev"]
  args = {
    AUTH_BERRY_UID = "${AUTH_BERRY_UID}"
    AUTH_BERRY_GID = "${AUTH_BERRY_GID}"
    TSS_UID = "${TSS_UID}"
    TSS_GID = "${TSS_GID}"
  }
}

// Target for production DB
target "db-prod" {
  context = "."
  dockerfile = "docker/db/Dockerfile"
  tags = [
    "auth_berry_mariadb:${TAG}",
    notequal("", REGISTRY) ? "${REGISTRY}/auth_berry_mariadb:${TAG}" : ""
  ]
  args = {
    AUTH_BERRY_UID = "${AUTH_BERRY_UID}"
    AUTH_BERRY_GID = "${AUTH_BERRY_GID}"
    TSS_UID = "${TSS_UID}"
    TSS_GID = "${TSS_GID}"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

// Target for development Flask app
target "app-dev" {
  context = "."
  dockerfile = "docker/app/Dockerfile.dev"
  tags = ["auth_berry_flask:dev"]
  args = {
    AUTH_BERRY_UID = "${AUTH_BERRY_UID}"
    AUTH_BERRY_GID = "${AUTH_BERRY_GID}"
    TSS_UID = "${TSS_UID}"
    TSS_GID = "${TSS_GID}"
  }
}

// Target for production Flask app
target "app-prod" {
  context = "."
  dockerfile = "docker/app/Dockerfile"
  tags = [
    "auth_berry_flask:${TAG}",
    notequal("", REGISTRY) ? "${REGISTRY}/auth_berry_flask:${TAG}" : ""
  ]
  args = {
    AUTH_BERRY_UID = "${AUTH_BERRY_UID}"
    AUTH_BERRY_GID = "${AUTH_BERRY_GID}"
    TSS_UID = "${TSS_UID}"
    TSS_GID = "${TSS_GID}"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

// Target for development Vue frontend
target "vue-dev" {
  context = "./frontend"
  dockerfile = "Dockerfile.dev"
  tags = ["auth_berry_vue:dev"]
}

// Target for production Vue frontend
target "vue-prod" {
  context = "./frontend"
  dockerfile = "Dockerfile"
  tags = [
    "auth_berry_vue:${TAG}",
    notequal("", REGISTRY) ? "${REGISTRY}/auth_berry_vue:${TAG}" : ""
  ]
  platforms = ["linux/amd64", "linux/arm64"]
}
