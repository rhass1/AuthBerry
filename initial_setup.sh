#!/bin/bash

# AuthBerry Initial Setup Script
# Prepares the environment for AuthBerry:
# - Installs system dependencies and Docker + Docker Compose.
# - Creates a dedicated service user (because security is cool).
# - Configures environment variables (.env file used by the application).
# - Sets up a Python virtual environment.
# - Runs a secondary Python configuration script (because Python is so much nicer to write than Bash).
# - Optionally starts AuthBerry services (prompts the user).

# --- Script Configuration & Safety ---
set -o nounset # Treat unset variables as an error
set -o pipefail # Causes a pipeline to return the exit status of the last command that exited with a non-zero status

# --- Utility Functions ---

# Helper to execute a command and exit fatally on error.
run_command() {
  local cmd_array=("$@")
  echo "[*] Executing: ${cmd_array[*]}"
  if ! "${cmd_array[@]}"; then
    echo "[-] Fatal error executing: ${cmd_array[*]}"
    exit 1
  fi
}

# Helper to execute a command as the auth-berry-user.
# Returns 0 on success, 1 on failure (does not exit script directly).
run_as_auth_berry() {
  local cmd_array=("$@")
  echo "[*] Executing as auth-berry-user: ${cmd_array[*]}"
  if ! sudo -u auth-berry-user "${cmd_array[@]}"; then
    echo "[-] Error executing as auth-berry-user: ${cmd_array[*]}"
    return 1
  fi
  return 0
}

# Finds an available TCP port within the dynamic range (49152-65535).
# Optionally takes a port number to exclude from the search. Used to ensure the Vue and Flask ports are different.
find_available_port() {
  local exclude_port=${1:-""} # Optional port to exclude
  local port
  local start_port=49152
  local end_port=65535
  # Get currently used TCP ports
  local used_ports
  used_ports=$(ss -tan | awk '{print $4}' | grep -oP ':\K[0-9]+' | sort -un)

  for port in $(seq "$start_port" "$end_port"); do
    if [[ "$port" -eq "$exclude_port" ]]; then
      continue
    fi
    if ! echo "$used_ports" | grep -q "^$port$"; then
      echo "$port"
      return 0
    fi
  done
  echo "[-] Error: No available TCP ports found in range $start_port-$end_port." >&2
  exit 1
}

# Detects available TPM device paths.
# Prioritizes /dev/tpmrm0, then /dev/tpm0, then lists other available tpm* and tpmrm* devices.
find_tpm_devices() {
  local devices_list=()

  # Check for primary candidates first
  if [ -c "/dev/tpmrm0" ]; then
    devices_list+=("/dev/tpmrm0")
  elif [ -c "/dev/tpm0" ]; then
    devices_list+=("/dev/tpm0")
  fi

  # Add other tpmrm devices, ensuring no duplicates from primary check or within this loop
  for i in $(seq 0 9); do
    local dev_path="/dev/tpmrm$i"
    if [ -c "$dev_path" ]; then
      is_duplicate=false
      for existing_dev in "${devices_list[@]}"; do
        if [[ "$existing_dev" == "$dev_path" ]]; then
          is_duplicate=true
          break
        fi
      done
      if ! $is_duplicate; then
        devices_list+=("$dev_path")
      fi
    fi
  done

  # Add other tpm devices, ensuring no duplicates from any previous additions
  for i in $(seq 0 9); do
    local dev_path="/dev/tpm$i"
    if [ -c "$dev_path" ]; then
      is_duplicate=false
      for existing_dev in "${devices_list[@]}"; do
        if [[ "$existing_dev" == "$dev_path" ]]; then
          is_duplicate=true
          break
        fi
      done
      if ! $is_duplicate; then
        devices_list+=("$dev_path")
      fi
    fi
  done

  # Join the list with commas
  local result=""
  if [ ${#devices_list[@]} -gt 0 ]; then
    result="${devices_list[0]}"
    for i in $(seq 1 $((${#devices_list[@]} - 1))); do
      result="$result,${devices_list[$i]}"
    done
  fi
  echo "$result"
}


# Gets the Group ID for the 'tss' (TPM Software Stack) group.
# TPM 2.0 support is REQUIRED for this application. May consider adding a fallback at a later date (e.g., software TPM or no TPM).
get_tss_gid() {
  local tss_gid
  if tss_gid=$(getent group tss | cut -d: -f3); then
    if [ -n "$tss_gid" ]; then
      echo "$tss_gid"
      return 0
    fi
  fi
  echo "[-] Error: TPM 2.0 support is required for this application." >&2
  echo "    Could not identify 'tss' group ID, which indicates TPM software stack is not properly installed." >&2
  echo "    Please ensure you're using a system with TPM 2.0 support and that 'tpm2-tools' is installed correctly." >&2
  exit 1
}

# Prompts the user for a yes/no answer. Defaults to 'yes'.
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

# Waits for a Docker container to be running and responsive.
# Uses the health endpoint to verify the Flask application is ready.
check_container_ready() {
  local container_name="$1"
  local max_attempts="${2:-30}" # Approx 60 seconds
  local attempt=0

  echo "[*] Waiting for container '$container_name' to be ready..."
  while [ "$attempt" -lt "$max_attempts" ]; do
    if docker container inspect "$container_name" &>/dev/null && \
       [[ "$(docker container inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null)" == "running" ]]; then
      
      # Check if Flask application is responding via health endpoint
      # Get the Flask port from the .env file
      local flask_port
      flask_port=$(grep "^FLASK_PORT=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d'=' -f2)
      if [ -z "$flask_port" ]; then
        flask_port="1337"  # Default fallback
      fi
      
      if curl -s -f "http://localhost:$flask_port/api/ping" >/dev/null 2>&1; then
        echo "[+] Container '$container_name' is ready."
        return 0
      fi
    fi
    attempt=$((attempt + 1))
    echo "  [*] Still waiting for '$container_name' (attempt $attempt/$max_attempts)..."
    sleep 2
  done

  echo "[-] Timed out waiting for container '$container_name' to become ready."
  return 1
}


# Get the primary IPv4 address of the system so we can tell the user where to access the application.
get_primary_ipv4() {
  local ip=""
  
  # Try the most reliable method first
  ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' | head -1)
  
  # Validate it's a valid IPv4 and not empty
  if [[ ! $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # Fall back to hostname method
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    
    # Validate again
    if [[ ! $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      ip=""
    fi
  fi
  
  echo "$ip"
}

# Get the hostname of the system so we can tell the user where to access the application.
get_hostname() {
  local hostname
  hostname=$(hostname)
  echo "$hostname"
}

# Command line arguments
ENVIRONMENT="dev"  # Default to dev environment
if [ $# -gt 0 ]; then
  if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
    ENVIRONMENT="prod"
    echo "[+] Setting up production environment"
  elif [ "$1" == "dev" ] || [ "$1" == "development" ]; then
    ENVIRONMENT="dev"
    echo "[+] Setting up development environment"
  else
    echo "Usage: $0 [dev|prod]"
    echo "  dev - Set up development environment (default)"
    echo "  prod - Set up production environment"
    exit 1
  fi
else
  echo "[+] No environment specified, defaulting to development"
fi

# Must be root to run this script.
if [ "$EUID" -ne 0 ]; then
  echo "[-] Error: This script requires root privileges. Please run with sudo: sudo ./initial_setup.sh"
  exit 1
fi

echo "[+] AuthBerry Initial Setup"
echo "========================="
echo ""

# Get the actual user who ran sudo, not root
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_UID=$(id -u "$ACTUAL_USER")
ACTUAL_GID=$(id -g "$ACTUAL_USER")

echo "[+] Detected user: $ACTUAL_USER (UID: $ACTUAL_UID, GID: $ACTUAL_GID)"

# Determine the script's own directory and change to it.
# This ensures relative paths (like for requirements.txt, .env, docker-compose.yml) work correctly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "[-] Failed to change to script directory: $SCRIPT_DIR"; exit 1; }

# System updates and dependency installation.
echo "[+] Updating system packages and installing dependencies..."
run_command apt update
run_command apt -y full-upgrade
run_command apt -y autoremove

# Install required packages.
run_command apt -y install build-essential pkg-config libtss2-dev tpm2-tools \
                           libmariadb-dev libmariadb3 mariadb-client \
                           python3-venv python3-pip cargo libmagic1
echo "[+] System updated and dependencies installed."

# Remove auth-berry-user creation section and replace with this comment
echo "[+] Using host user '$ACTUAL_USER' for container permissions"

# Add user to the tss group for TPM access if needed
echo "[+] Adding '$ACTUAL_USER' to the 'tss' group for TPM access..."
if getent group tss >/dev/null 2>&1; then
  if ! groups "$ACTUAL_USER" | grep -q '\btss\b'; then
    run_command usermod -aG tss "$ACTUAL_USER"
    echo "[+] Added '$ACTUAL_USER' to the 'tss' group."
  else
    echo "[*] User '$ACTUAL_USER' is already in the 'tss' group."
  fi
else
  echo "[-] Error: 'tss' group not found. TPM 2.0 support is required for this application." >&2
  echo "    Please ensure 'tpm2-tools' or related packages are installed correctly." >&2
  exit 1
fi

# Gather information for the .env file.
echo "[+] Collecting system information for .env file..."

# Get TSS GID (will exit if not found due to updated get_tss_gid function)
TSS_GID=$(get_tss_gid)

# Get TSS UID - also required
if id -u tss >/dev/null 2>&1; then
  TSS_UID=$(id -u tss)
else
  echo "[-] Error: 'tss' user not found. The application requires both tss user and group." >&2
  echo "    Please ensure 'tpm2-tools' or related packages are installed correctly." >&2
  exit 1
fi

# Check for TPM devices
TPM_DEVICES=$(find_tpm_devices)
if [ -z "$TPM_DEVICES" ]; then
  echo "[-] Error: TPM 2.0 support is required for this application." >&2
  echo "    No TPM devices were found on this system." >&2
  echo "    Please ensure you're using a system with TPM 2.0 support." >&2
  exit 1
fi

echo "[+] Finding available ports for services..."
FLASK_PORT=$(find_available_port)
VUE_PORT=$(find_available_port "$FLASK_PORT")  # Pass Flask port to exclude it so Vue container port is different

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
TPM_DEVICES=$TPM_DEVICES

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

# Set up Docker Buildx
echo "[+] Setting up Docker Buildx..."
if ! sudo -u "$ACTUAL_USER" sg docker -c "docker buildx ls | grep -q 'buildx-builder'"; then
  sudo -u "$ACTUAL_USER" sg docker -c "docker buildx create --name buildx-builder --use && docker buildx inspect --bootstrap"
  echo "[+] Docker Buildx builder created."
else
  echo "[+] Docker Buildx builder already exists."
fi

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

  # Wait for the Flask container (application backend) to be ready.
  FLASK_CONTAINER_NAME="auth_berry_flask"
  if ! check_container_ready "$FLASK_CONTAINER_NAME"; then
    echo "[-] Flask container '$FLASK_CONTAINER_NAME' did not become ready."
    if ! prompt_yes_no "Database initialization might fail. Continue with database initialization anyway?"; then
      echo "[+] Skipping database initialization. You can initialize it later using:"
      echo "    make init-db"
      exit 0
    fi
  fi

  # Initialize the database
  echo "[+] Initializing application database..."
  if sudo -u "$ACTUAL_USER" sg docker -c "cd \"$SCRIPT_DIR\" && make init-db"; then
    echo "[+] Database initialized successfully."
  else
    echo "[-] Error: Failed to initialize the database."
    echo "[!] You will need to run the initialization manually later using:"
    echo "    make init-db"
    exit 1
  fi

  # Get the primary IPv4 address and hostname of the system.
  PRIMARY_IPV4=$(get_primary_ipv4)
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
  echo "    2. Initialize database (if first time): make init-db"
  echo ""
fi

exit 0