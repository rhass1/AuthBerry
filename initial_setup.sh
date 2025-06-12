#!/bin/bash

# AuthBerry Initial Setup Script
# Prepares the environment for AuthBerry:
# - Installs system dependencies and Docker + Docker Compose.
# - Configures TPM 2.0 hardware support (boot config on RPi)
# - Sets up user permissions and environment variables.
# - Builds and deploys the application stack.

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to execute commands with error handling
run_command() {
    local cmd_array=("$@")
    echo "[*] Executing: ${cmd_array[*]}"
    if ! "${cmd_array[@]}"; then
        echo "[-] Fatal error executing: ${cmd_array[*]}"
        exit 1
    fi
}

# Function to execute commands as the actual user (not root)
run_as_user() {
    local cmd_array=("$@")
    echo "[*] Executing as auth-berry-user: ${cmd_array[*]}"
    if ! sudo -u "$ACTUAL_USER" "${cmd_array[@]}"; then
        echo "[-] Error executing as auth-berry-user: ${cmd_array[*]}"
        return 1
    fi
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to find an available TCP port
find_available_port() {
    local start_port=$1
    local end_port=$2
    
    # Get list of used ports
    used_ports=$(ss -tan | awk '{print $4}' | grep -oP ':\K[0-9]+' | sort -un)
    
    # Find first available port in range
    for port in $(seq $start_port $end_port); do
        if ! echo "$used_ports" | grep -q "^$port$"; then
            echo "$port"
            return 0
        fi
    done
    
    echo "[-] Error: No available TCP ports found in range $start_port-$end_port." >&2
    return 1
}

# Function to check if we're running on Raspberry Pi
is_raspberry_pi() {
    if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        return 0
    elif [[ -f /sys/firmware/devicetree/base/model ]] && grep -q "Raspberry Pi" /sys/firmware/devicetree/base/model 2>/dev/null; then
        return 0
    elif [[ -f /proc/cpuinfo ]] && grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check and update Raspberry Pi boot configuration
check_and_update_rpi_boot_config() {
    local config_file="/boot/firmware/config.txt"
    local cmdline_file="/boot/firmware/cmdline.txt"
    local changes_made=false
    local config_changes=()
    local cmdline_changes=()
    
    echo "[*] Checking Raspberry Pi boot configuration..."
    
    # Check if config.txt exists
    if [[ ! -f "$config_file" ]]; then
        echo "[-] Error: $config_file not found. This may not be a Raspberry Pi system."
        return 1
    fi
    
    # Required TPM settings for config.txt
    local required_settings=(
        "dtparam=spi=on"
        "dtoverlay=tpm-slb9670"
    )
    
    # Check each required setting
    for setting in "${required_settings[@]}"; do
        local key="${setting%%=*}"
        local value="${setting#*=}"
        
        # Check if setting exists and is enabled
        if grep -q "^${key}=${value}$" "$config_file"; then
            echo "[+] $setting is already configured"
        elif grep -q "^#.*${key}=${value}" "$config_file"; then
            # Setting exists but is commented out
            config_changes+=("Uncomment: $setting")
        elif grep -q "^${key}=" "$config_file"; then
            # Setting exists with different value
            local current_value=$(grep "^${key}=" "$config_file" | cut -d'=' -f2)
            config_changes+=("Change: ${key}=${current_value} → ${key}=${value}")
        else
            # Setting doesn't exist
            config_changes+=("Add: $setting")
        fi
    done
    
    # Check cmdline.txt for cgroup settings
    if [[ -f "$cmdline_file" ]]; then
        local cmdline_content=$(cat "$cmdline_file")
        local required_cgroup_params=(
            "cgroup_enable=cpuset"
            "cgroup_memory=1"
            "cgroup_enable=memory"
        )
        
        for param in "${required_cgroup_params[@]}"; do
            if [[ ! "$cmdline_content" =~ $param ]]; then
                cmdline_changes+=("Add: $param")
            fi
        done
    fi
    
    # Report all required changes
    if [[ ${#config_changes[@]} -gt 0 ]] || [[ ${#cmdline_changes[@]} -gt 0 ]]; then
        echo ""
        echo "="*70
        echo "🔧 BOOT CONFIGURATION CHANGES REQUIRED"
        echo "="*70
        
        if [[ ${#config_changes[@]} -gt 0 ]]; then
            echo "Changes needed in $config_file:"
            for change in "${config_changes[@]}"; do
                echo "  • $change"
            done
        fi
        
        if [[ ${#cmdline_changes[@]} -gt 0 ]]; then
            echo "Changes needed in $cmdline_file:"
            for change in "${cmdline_changes[@]}"; do
                echo "  • $change"
            done
        fi
        
        echo ""
        echo "These changes are required for TPM 2.0 hardware detection."
        echo "="*70
        
        # Ask user permission to make changes
        while true; do
            read -p "Apply these boot configuration changes? (y/n): " yn
            case $yn in
                [Yy]* ) break;;
                [Nn]* ) 
                    echo "[-] Boot configuration changes are required for TPM 2.0 functionality."
                    echo "    Setup cannot continue without these changes."
                    exit 1
                    ;;
                * ) echo "Please answer 'y' or 'n'." ;;
            esac
        done
        
        # Apply config.txt changes
        if [[ ${#config_changes[@]} -gt 0 ]]; then
            echo "[*] Applying changes to $config_file..."
            
            # Create backup
            cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
            
            for setting in "${required_settings[@]}"; do
                local key="${setting%%=*}"
                local value="${setting#*=}"
                
                if grep -q "^${key}=${value}$" "$config_file"; then
                    # Already correct
                    continue
                elif grep -q "^#.*${key}=${value}" "$config_file"; then
                    # Uncomment the line
                    sed -i "s/^#.*${key}=${value}$/${setting}/" "$config_file"
                    echo "[+] Uncommented: $setting"
                elif grep -q "^${key}=" "$config_file"; then
                    # Replace existing value
                    sed -i "s/^${key}=.*$/${setting}/" "$config_file"
                    echo "[+] Updated: $setting"
                else
                    # Add new line
                    echo "$setting" >> "$config_file"
                    echo "[+] Added: $setting"
                fi
            done
        fi
        
        # Apply cmdline.txt changes
        if [[ ${#cmdline_changes[@]} -gt 0 ]]; then
            echo "[*] Applying changes to $cmdline_file..."
            
            # Create backup
            cp "$cmdline_file" "${cmdline_file}.backup.$(date +%Y%m%d_%H%M%S)"
            
            local cmdline_content=$(cat "$cmdline_file")
            for param in "${required_cgroup_params[@]}"; do
                if [[ ! "$cmdline_content" =~ $param ]]; then
                    # Add parameter to end of line
                    cmdline_content="$cmdline_content $param"
                    echo "[+] Added: $param"
                fi
            done
            
            # Write updated content
            echo "$cmdline_content" > "$cmdline_file"
        fi
        
        changes_made=true
    else
        echo "[+] Boot configuration is already correct for TPM 2.0"
    fi
    
    # Return whether changes were made
    if [[ "$changes_made" == true ]]; then
        return 1  # Changes made, reboot needed
    else
        return 0  # No changes needed
    fi
}

# Function to check x86_64 cgroup configuration
check_x86_64_cgroups() {
    echo "[*] Checking cgroup configuration for x86_64 system..."
    
    # Check if cgroups v2 is available
    if [[ -d /sys/fs/cgroup/unified ]] || [[ -f /sys/fs/cgroup/cgroup.controllers ]]; then
        echo "[+] cgroups v2 detected and available"
    elif [[ -d /sys/fs/cgroup/memory ]] && [[ -d /sys/fs/cgroup/cpuset ]]; then
        echo "[+] cgroups v1 detected and available"
    else
        echo "[!] Warning: cgroup support may be limited on this system"
        echo "    This may affect container resource management"
    fi
}

# Function to wait for container to be ready
wait_for_container() {
    local container_name="$1"
    local max_attempts="${2:-30}" # Approx 60 seconds
    local attempt=1
    
    echo "[*] Waiting for container '$container_name' to be ready..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker container inspect "$container_name" &>/dev/null && \
           [[ "$(docker container inspect -f '{{.State.Status}}' "$container_name")" == "running" ]]; then
            # Additional check: ensure the container is actually responsive
            sleep 2
            if docker container inspect "$container_name" &>/dev/null && \
               [[ "$(docker container inspect -f '{{.State.Status}}' "$container_name")" == "running" ]]; then
                echo "[+] Container '$container_name' is ready."
                return 0
            fi
        fi
        
        if [[ $((attempt % 5)) -eq 0 ]]; then
            echo "  [*] Still waiting for '$container_name' (attempt $attempt/$max_attempts)..."
        fi
        
        sleep 2
        ((attempt++))
    done
    
    echo "[-] Timed out waiting for container '$container_name' to become ready."
    return 1
}

# Function to wait for database to be ready
wait_for_database() {
    local max_attempts="${1:-30}"
    local attempt=1
    
    echo "[*] Waiting for database to be ready for connections..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker exec auth_berry_mariadb mariadb -u root -p"$(docker exec auth_berry_mariadb cat /run/secrets/mariadb_root_password)" -e "SELECT 1;" &>/dev/null; then
            echo "[+] Database is ready and accessible."
            return 0
        fi
        
        if [[ $((attempt % 5)) -eq 0 ]]; then
            echo "  [*] Still waiting for database readiness (attempt $attempt/$max_attempts)..."
        fi
        
        sleep 2
        ((attempt++))
    done
    
    echo "[-] Timed out waiting for database to become ready."
    return 1
}

# Function to wait for all services to be ready
wait_for_services() {
    local mariadb_container="auth_berry_mariadb"
    local flask_container="auth_berry_flask"
    local max_attempts=30
    local attempt=1
    
    echo "[*] Waiting for all services to be ready..."
    
    # First, wait for MariaDB container to be healthy
    echo "[*] Checking MariaDB container health..."
    while [[ $attempt -le $max_attempts ]]; do
        if docker container inspect "$mariadb_container" &>/dev/null; then
            # Check health status if available
            health_status=$(docker container inspect -f '{{.State.Health.Status}}' "$mariadb_container" 2>/dev/null || echo "none")
            
            if [[ "$health_status" == "healthy" ]]; then
                echo "[+] MariaDB container is healthy."
                break
            elif [[ "$health_status" == "none" ]] && \
                 [[ "$(docker container inspect -f '{{.State.Status}}' "$mariadb_container")" == "running" ]]; then
                # No health check defined, but container is running
                echo "[+] MariaDB container is running (no health check defined)."
                break
            fi
        fi
        
        if [[ $((attempt % 5)) -eq 0 ]]; then
            echo "  [*] MariaDB not healthy yet (attempt $attempt/$max_attempts)..."
        fi
        
        sleep 2
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        echo "[-] MariaDB container did not become healthy in time."
        return 1
    fi
    
    # Wait for Flask container
    if ! wait_for_container "$flask_container"; then
        echo "[-] Flask container failed to become ready."
        return 1
    fi
    
    # Wait for database connectivity
    if ! wait_for_database; then
        echo "[-] Database authentication not ready."
        return 1
    fi
    
    echo "[+] All services are ready!"
    return 0
}

# Function to get local IP address
get_local_ip() {
    local ip
    # Try to get IP from default route interface
    ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K[0-9.]+' | head -1)
    if [[ ! $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # Fallback: get IP from first non-loopback interface
        ip=$(hostname -I | awk '{print $1}')
        if [[ ! $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            ip="localhost"
        fi
    fi
    echo "$ip"
}

# Function to get hostname
get_hostname() {
    local hostname
    hostname=$(hostname -f 2>/dev/null || hostname)
    echo "$hostname"
}

# Parse command line arguments
ENVIRONMENT="dev"
if [[ $# -gt 0 ]]; then
    case "$1" in
        "prod")
            echo "[+] Setting up production environment"
            ENVIRONMENT="prod"
            ;;
        "dev")
            echo "[+] Setting up development environment"
            ENVIRONMENT="dev"
            ;;
        *)
            echo "Usage: $0 [dev|prod]"
            echo "  dev - Set up development environment (default)"
            echo "  prod - Set up production environment"
            exit 1
            ;;
    esac
else
    echo "[+] No environment specified, defaulting to development"
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "[-] Error: This script requires root privileges. Please run with sudo: sudo ./initial_setup.sh"
    exit 1
fi

# Get the actual user (not root)
if [[ -n "${SUDO_USER:-}" ]]; then
    ACTUAL_USER="$SUDO_USER"
elif [[ -n "${USER:-}" ]] && [[ "$USER" != "root" ]]; then
    ACTUAL_USER="$USER"
else
    echo "[-] Error: Could not determine the actual user. Please run with sudo."
    exit 1
fi

echo "[+] Running as root, actual user: $ACTUAL_USER"

# Change to script directory
cd "$SCRIPT_DIR" || { echo "[-] Failed to change to script directory: $SCRIPT_DIR"; exit 1; }

echo ""
echo "======================================================================="
echo "🚀 AUTHBERRY INITIAL SETUP - PHASE 1: HARDWARE ENABLEMENT"
echo "======================================================================="
echo "Setting up hardware support and system dependencies..."
echo ""

# PHASE 1: HARDWARE ENABLEMENT
# Step 1: Platform-specific boot configuration (must be done first)
is_rpi=false
if is_raspberry_pi; then
    is_rpi=true
    echo "[+] Raspberry Pi detected - checking boot configuration..."
    
    if ! check_and_update_rpi_boot_config; then
        echo ""
        echo "="*70
        echo "🔄 REBOOT REQUIRED"
        echo "="*70
        echo "Boot configuration changes have been applied."
        echo "A system reboot is required to enable TPM 2.0 hardware detection."
        echo ""
        echo "After reboot, run this command to continue setup:"
        echo "  sudo bash initial_setup.sh $ENVIRONMENT"
        echo "="*70
        exit 0
    fi
else
    echo "[+] x86_64 system detected - checking cgroup configuration..."
    check_x86_64_cgroups
fi

# Step 2: Install system packages (creates TSS user/group)
echo ""
echo "[*] Installing system dependencies and TPM 2.0 support..."
run_command apt update
run_command apt -y install build-essential pkg-config libtss2-dev tpm2-tools \
    libmariadb-dev libmariadb3 mariadb-client \
    python3 python3-pip python3-venv python3-dev \
    curl wget gnupg lsb-release ca-certificates \
    software-properties-common apt-transport-https

echo "[+] System packages installed successfully."

# Step 3: Verify TSS user/group were created by package installation
echo ""
echo "[*] Verifying TPM Software Stack installation..."

if ! getent group tss >/dev/null 2>&1; then
    echo ""
    echo "======================================================================="
    echo "🚨 CRITICAL ERROR: TPM SOFTWARE STACK INSTALLATION FAILED"
    echo "======================================================================="
    echo "The 'tss' group was not created by package installation."
    echo "This indicates that TPM 2.0 tools did not install correctly."
    echo ""
    echo "Please check:"
    echo "  • Package installation completed without errors"
    echo "  • System package repositories are accessible"
    echo "  • No package conflicts exist"
    echo ""
    echo "Try running: apt install --reinstall tpm2-tools"
    echo "======================================================================="
    exit 1
fi

if ! id tss >/dev/null 2>&1; then
    echo ""
    echo "======================================================================="
    echo "🚨 CRITICAL ERROR: TSS USER NOT CREATED"
    echo "======================================================================="
    echo "The 'tss' user was not created by package installation."
    echo "This indicates that TPM 2.0 tools did not install correctly."
    echo ""
    echo "Try running: apt install --reinstall tpm2-tools"
    echo "======================================================================="
    exit 1
fi

echo "[+] TPM Software Stack (TSS) installed successfully."

# Step 4: Add user to tss group
if ! groups "$ACTUAL_USER" | grep -q '\btss\b'; then
    usermod -a -G tss "$ACTUAL_USER"
    echo "[+] Added '$ACTUAL_USER' to the 'tss' group."
else
    echo "[*] User '$ACTUAL_USER' is already in the 'tss' group."
fi

# Step 5: Basic TPM device detection (after hardware setup)
echo ""
echo "[*] Detecting TPM 2.0 devices..."

# Look for TPM devices
tpm_devices=()
for device in /dev/tpm0 /dev/tpmrm0 /dev/tpm1 /dev/tpmrm1; do
    if [[ -e "$device" ]]; then
        tpm_devices+=("$device")
        echo "[+] Found TPM device: $device"
    fi
done

if [[ ${#tpm_devices[@]} -eq 0 ]]; then
    echo ""
    echo "======================================================================="
    echo "🚨 CRITICAL ERROR: NO TPM 2.0 DEVICES DETECTED"
    echo "======================================================================="
    echo "No TPM devices were found after hardware configuration."
    echo ""
    if [[ "$is_rpi" == true ]]; then
        echo "For Raspberry Pi systems, this usually indicates:"
        echo "  • TPM 2.0 module is not properly connected"
        echo "  • SPI interface is not enabled (check boot config)"
        echo "  • Device tree overlay not loaded (reboot required)"
        echo "  • Incompatible or faulty TPM module"
        echo ""
        echo "Please verify:"
        echo "  • TPM 2.0 module is securely connected to SPI pins"
        echo "  • Boot configuration includes required settings"
        echo "  • System has been rebooted after boot config changes"
    else
        echo "For x86_64 systems, this usually indicates:"
        echo "  • TPM is disabled in BIOS/UEFI firmware"
        echo "  • TPM hardware is not present"
        echo "  • TPM driver issues"
        echo ""
        echo "Please verify:"
        echo "  • TPM 2.0 is enabled in system firmware"
        echo "  • TPM hardware is properly installed"
    fi
    echo ""
    echo "SETUP CANNOT CONTINUE without functional TPM 2.0 hardware."
    echo "======================================================================="
    exit 1
fi

echo "[+] TPM 2.0 hardware detection completed successfully."

# Continue with rest of setup...
echo ""
echo "======================================================================="
echo "🚀 AUTHBERRY INITIAL SETUP - PHASE 2: SYSTEM CONFIGURATION"
echo "======================================================================="
echo "Configuring Docker, users, and application environment..."
echo ""

# Gather information for the .env file
echo "[+] Collecting system information for .env file..."

# Get user IDs
ACTUAL_UID=$(id -u "$ACTUAL_USER")
ACTUAL_GID=$(id -g "$ACTUAL_USER")

# Get TSS information (already verified to exist)
TSS_GID=$(getent group tss | cut -d: -f3)
TSS_UID=$(id -u tss)

# Convert TPM devices array to comma-separated string
TPM_DEVICES_STRING=""
for device in "${tpm_devices[@]}"; do
    if [[ -z "$TPM_DEVICES_STRING" ]]; then
        TPM_DEVICES_STRING="$device"
    else
        TPM_DEVICES_STRING="$TPM_DEVICES_STRING,$device"
    fi
done

echo "[+] Finding available ports for services..."
FLASK_PORT=$(find_available_port 49152 65535)
VUE_PORT=$(find_available_port 49152 65535)

# Create the .env file.
echo "[+] Creating .env configuration file..."
cat << EOF > "$SCRIPT_DIR/.env"
# AuthBerry Environment Configuration
# Generated by initial_setup.sh on $(date)

# User and Group IDs for service operation
AUTH_BERRY_UID=$ACTUAL_UID
AUTH_BERRY_GID=$ACTUAL_GID

# TPM Software Stack (TSS) User/Group Information
TSS_UID=$TSS_UID
TSS_GID=$TSS_GID

# System Configuration
# Comma-separated list of detected TPM device paths
TPM_DEVICES=$TPM_DEVICES_STRING

# Service Ports (auto-detected available ports)
FLASK_PORT=$FLASK_PORT
VUE_PORT=$VUE_PORT
EOF
echo "[+] .env file created successfully. Contents:"
cat "$SCRIPT_DIR/.env"
echo ""

# Install Docker Engine.
echo "[+] Installing Docker Engine..."
if command -v docker >/dev/null 2>&1; then
  echo "[*] Docker Engine is already installed."
else
  run_command curl -fsSL https://get.docker.com -o get-docker.sh
  run_command sh ./get-docker.sh
  run_command rm get-docker.sh
  echo "[+] Docker Engine installed."
fi

# Install Docker Compose (as a CLI plugin).
echo "[+] Installing Docker Compose..."
COMPOSE_PLUGIN_DIR="/usr/local/lib/docker/cli-plugins"
COMPOSE_EXECUTABLE="$COMPOSE_PLUGIN_DIR/docker-compose"
run_command mkdir -p "$COMPOSE_PLUGIN_DIR"

if [ -x "$COMPOSE_EXECUTABLE" ] || docker compose version >/dev/null 2>&1; then
  echo "[*] Docker Compose is already installed or available."
else
  COMPOSE_VERSION_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)"
  run_command curl -SL "$COMPOSE_VERSION_URL" -o "$COMPOSE_EXECUTABLE"
  run_command chmod +x "$COMPOSE_EXECUTABLE"
  echo "[+] Docker Compose installed to $COMPOSE_EXECUTABLE."
fi

# Ensure Docker daemon is running and enabled.
echo "[+] Ensuring Docker service is active and enabled..."
run_command systemctl start docker
run_command systemctl enable docker

# Add user to the docker group for Docker command access.
echo "[+] Adding '$ACTUAL_USER' to the 'docker' group..."
run_command usermod -aG docker "$ACTUAL_USER"
echo "[*] Docker group access enabled for immediate use with sg command."

# Setup Python virtual environment for the secondary_setup.py script.
echo "[+] Setting up Python virtual environment..."
VENV_BASE_DIR="/opt/virtualenvs"
VENV_PATH="$VENV_BASE_DIR/auth_berry"
run_command mkdir -p "$VENV_BASE_DIR"

if [ ! -d "$VENV_PATH/bin" ]; then
  echo "[*] Creating Python virtual environment at $VENV_PATH..."
  run_command python3 -m venv "$VENV_PATH"
else
  echo "[*] Python virtual environment already exists at $VENV_PATH."
fi

# Install Python dependencies required for the secondary setup script.
echo "[+] Installing Python requirements..."
if [ -f "requirements.txt" ]; then
  run_command "$VENV_PATH/bin/pip" install --no-cache-dir -r requirements.txt
else
  echo "[!] Warning: 'requirements.txt' not found in $SCRIPT_DIR. Clone the repository from GitHub to get it."
  exit 1
fi

# Set correct ownership for the application and virtual environment directories.
echo "[+] Setting permissions for AuthBerry directories..."
run_command chown -R "$ACTUAL_USER:$ACTUAL_USER" "$SCRIPT_DIR"
run_command chown -R "$ACTUAL_USER:$ACTUAL_USER" "$VENV_PATH" # Ensure venv is also owned by the user

# Execute the secondary Python setup script.
echo ""
echo "[+] Running AuthBerry secondary configuration script (secondary_setup.py)..."
run_command "$VENV_PATH/bin/python3" secondary_setup.py

echo ""
echo "[+] AuthBerry core setup completed successfully!"
echo "    Application Directory: $SCRIPT_DIR"
echo "    Virtual Environment:   $VENV_PATH"
echo ""

# Set up Docker Buildx with resource limits
echo "[+] Setting up Docker Buildx with resource-limited builder..."

# Create buildkit configuration directory and copy config
run_command mkdir -p /etc/buildkit/sgl-buildkit
run_command cp "$SCRIPT_DIR/docker/buildkitd.toml" /etc/buildkit/sgl-buildkit/buildkitd.toml
run_command chown root:root /etc/buildkit/sgl-buildkit/buildkitd.toml
run_command chmod 644 /etc/buildkit/sgl-buildkit/buildkitd.toml

# Function to create resource-limited builder
setup_buildx_builder() {
  echo "[+] Creating resource-limited Docker Buildx builder..."
  
  # Remove existing builder if it exists
  if sudo -u "$ACTUAL_USER" sg docker -c "docker buildx ls | grep -q 'shared-builder'"; then
    echo "[*] Removing existing shared-builder..."
    sudo -u "$ACTUAL_USER" sg docker -c "docker buildx rm shared-builder" || true
  fi
  
  # Create new builder with configuration
  sudo -u "$ACTUAL_USER" sg docker -c "docker buildx create \
    --name shared-builder \
    --driver docker-container \
    --driver-opt network=host \
    --driver-opt image=moby/buildkit:latest \
    --config /etc/buildkit/sgl-buildkit/buildkitd.toml \
    --use"
  
  # Bootstrap the builder
  echo "[*] Bootstrapping builder (starting container)..."
  sudo -u "$ACTUAL_USER" sg docker -c "docker buildx inspect --bootstrap"
  
  # Wait for container to fully start
  echo "[*] Waiting for builder container to stabilize..."
  sleep 5
  
  # Find and apply resource limits to the builder container
  echo "[*] Applying resource limits to builder container..."
  BUILDER_CONTAINER=$(sudo -u "$ACTUAL_USER" sg docker -c 'docker ps --filter "name=buildx_buildkit_shared-builder" --format "{{.ID}}"')
  
  if [ -n "$BUILDER_CONTAINER" ]; then
    echo "[*] Found builder container ID: $BUILDER_CONTAINER"
    sudo -u "$ACTUAL_USER" sg docker -c "docker update \
      --memory=512m \
      --memory-swap=512m \
      --cpus=1.0 \
      --cpu-shares=512 \
      $BUILDER_CONTAINER"
    echo "[+] Resource limits applied to builder container."
  else
    echo "[!] Warning: Could not find builder container for resource limiting."
    echo "    The builder will still work but without container-level resource limits."
  fi
  
  echo "[+] Resource-limited Docker Buildx builder 'shared-builder' created successfully."
}

# Set up the builder
setup_buildx_builder

# Function to prompt user for yes/no answer
prompt_yes_no() {
    local message="$1"
    local user_reply
    while true; do
        read -p "$message [Y/n] " user_reply
        user_reply=${user_reply:-Y}
        case "$user_reply" in
            y|Y) return 0 ;;
            n|N) return 1 ;;
            *) echo "Please answer 'y' or 'n'." ;;
        esac
    done
}

# Prompt user to start AuthBerry services.
if prompt_yes_no "Would you like to start the AuthBerry services now?"; then
  echo "[+] Starting AuthBerry services..."
  
  # Build and run with the appropriate environment
  if [ "$ENVIRONMENT" == "dev" ]; then
    echo "[*] Building and deploying development environment..."
    if sudo -u "$ACTUAL_USER" sg docker -c "cd \"$SCRIPT_DIR\" && make deploy-dev"; then
      echo "[+] Development environment started successfully."
    else
      echo "[-] Error: Failed to start development environment."
      exit 1
    fi
  else
    echo "[*] Building and deploying production environment..."
    if sudo -u "$ACTUAL_USER" sg docker -c "cd \"$SCRIPT_DIR\" && make deploy-prod"; then
      echo "[+] Production environment started successfully."
    else
      echo "[-] Error: Failed to start production environment."
      exit 1
    fi
  fi

  # Wait for all services to be ready with enhanced checking
  if ! wait_for_services; then
    echo "[-] Services did not become ready in time."
    if ! prompt_yes_no "Database initialization might fail. Continue with database initialization anyway?"; then
      echo "[+] Skipping database initialization. You can initialize it later using:"
      echo "    make clean-db-init  # Clean any partial state"
      echo "    make init-db        # Initialize database"
      exit 0
    fi
  fi

  # Initialize the database with automatic cleanup on failure
  echo "[+] Initializing application database..."
  if sudo -u "$ACTUAL_USER" sg docker -c "cd \"$SCRIPT_DIR\" && make init-db-safe"; then
    echo "[+] Database initialized successfully."
  else
    echo "[-] Error: Failed to initialize the database."
    echo "[!] The system has automatically cleaned up partial initialization state."
    echo "[!] You can retry initialization manually using:"
    echo "    make init-db        # Try database initialization"
    echo "    make clean-db-init  # Clean partial state if needed"
    echo "    make logs           # Check container logs for issues"
    exit 1
  fi

  # Get the primary IPv4 address and hostname of the system.
  PRIMARY_IPV4=$(get_local_ip)
  HOSTNAME=$(get_hostname)

  # Use the VUE_PORT from .env for both dev and prod
  FINAL_VUE_PORT=$VUE_PORT

  echo ""
  echo "[🎉] AuthBerry has been successfully installed and started!"
  echo "[+] Access the application at: "
  echo "    http://localhost:${FINAL_VUE_PORT} (on local device)" 
  echo "    http://${PRIMARY_IPV4}:${FINAL_VUE_PORT} (on network from other devices)"
  echo "    http://${HOSTNAME}:${FINAL_VUE_PORT} (on network from other devices, using hostname if discoverable)"
  echo ""
  echo "[i] To manage services:"
  echo "    Stop:    make clean"
  echo "    Start:   make deploy-${ENVIRONMENT}"
  echo "    Logs:    make logs"
  echo "    Help:    make help"
else
  echo ""
  echo "[+] AuthBerry services not started. To run manually:"
  echo "    1. Start containers for development: make deploy-dev"
  echo "    1. Start containers for production: make deploy-prod"
  echo "    2. Initialize database (if first time): make init-db-safe"
  echo ""
  echo "[i] Database troubleshooting commands:"
  echo "    make clean-db-init  # Clean partial initialization state"
  echo "    make init-db        # Initialize database (standard)"
  echo "    make init-db-safe   # Initialize with automatic cleanup on failure"
  echo ""
fi

exit 0