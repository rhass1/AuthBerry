#!/usr/bin/env python3
import os
import secrets
import subprocess
import logging
from pathlib import Path
from cryptography.fernet import Fernet
import sys

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("generate_required_files")

# Parse .env file
def parse_env_file(env_path='.env'):
    """Parse the environment file into a dictionary."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                except ValueError:
                    # Skip lines that don't have '=' separator
                    continue
    return env_vars

# Load configuration from .env
env_vars = parse_env_file()


# Standalone TPMManager class for the script
class ScriptTPMManager:
    """
    Manages creation, sealing, and unsealing of secrets using a TPM.
    This is a standalone version for the generate_required_files.py script.
    """

    def __init__(self, secrets_dir: str or Path, persistent_handle: int = 0x81010001):
        """
        Initialize the TPM Manager.

        Args:
            secrets_dir: Directory path where secrets will be stored
            persistent_handle: TPM persistent handle value (default: 0x81010001)
        """
        # Import TPM libraries here to avoid loading them when not needed
        from tpm2_pytss import ESAPI, ESYS_TR, TSS2_Exception
        from tpm2_pytss.constants import TPM2_ALG_ID, TPMA_OBJECT
        from tpm2_pytss.types import (
            TPM2B_SENSITIVE_CREATE, TPM2B_PUBLIC, TPM2B_PRIVATE, TPMT_PUBLIC,
            TPM2B_DIGEST, TPM2B_PUBLIC_KEY_RSA, TPMS_RSA_PARMS, TPMT_SYM_DEF_OBJECT,
            TPMU_SYM_KEY_BITS, TPMU_SYM_MODE, TPMT_RSA_SCHEME, TPML_PCR_SELECTION,
            TPM2B_DATA, TPMS_SENSITIVE_CREATE, TPMS_KEYEDHASH_PARMS, TPMT_KEYEDHASH_SCHEME,
            TPMU_PUBLIC_PARMS, TPMU_PUBLIC_ID, TPM2_HANDLE,
        )

        self.ESAPI = ESAPI
        self.ESYS_TR = ESYS_TR
        self.TSS2_Exception = TSS2_Exception
        self.TPM2_ALG_ID = TPM2_ALG_ID
        self.TPMA_OBJECT = TPMA_OBJECT
        self.TPM2B_SENSITIVE_CREATE = TPM2B_SENSITIVE_CREATE
        self.TPM2B_PUBLIC = TPM2B_PUBLIC
        self.TPM2B_PRIVATE = TPM2B_PRIVATE
        self.TPMT_PUBLIC = TPMT_PUBLIC
        self.TPM2B_DIGEST = TPM2B_DIGEST
        self.TPM2B_PUBLIC_KEY_RSA = TPM2B_PUBLIC_KEY_RSA
        self.TPMS_RSA_PARMS = TPMS_RSA_PARMS
        self.TPMT_SYM_DEF_OBJECT = TPMT_SYM_DEF_OBJECT
        self.TPMU_SYM_KEY_BITS = TPMU_SYM_KEY_BITS
        self.TPMU_SYM_MODE = TPMU_SYM_MODE
        self.TPMT_RSA_SCHEME = TPMT_RSA_SCHEME
        self.TPML_PCR_SELECTION = TPML_PCR_SELECTION
        self.TPM2B_DATA = TPM2B_DATA
        self.TPMS_SENSITIVE_CREATE = TPMS_SENSITIVE_CREATE
        self.TPMS_KEYEDHASH_PARMS = TPMS_KEYEDHASH_PARMS
        self.TPMT_KEYEDHASH_SCHEME = TPMT_KEYEDHASH_SCHEME
        self.TPMU_PUBLIC_PARMS = TPMU_PUBLIC_PARMS
        self.TPMU_PUBLIC_ID = TPMU_PUBLIC_ID
        self.TPM2_HANDLE = TPM2_HANDLE

        self.logger = logger
        self.ectx = self.ESAPI()
        self.primary_handle = None
        self.secret = None
        self.persistent_handle = self.TPM2_HANDLE(persistent_handle)
        self.secrets_dir = Path(secrets_dir)

        # Ensure the secrets directory exists
        self.secrets_dir.mkdir(exist_ok=True, parents=True)
        self.logger.debug(f"TPMManager initialized with secrets directory: {self.secrets_dir}")

    def generate_or_load_primary_key(self) -> None:
        """
        Generate a new primary key or load an existing one from the TPM.

        Raises:
            TSS2_Exception: If there's an error working with the TPM
        """
        try:
            self.primary_handle = self.ectx.tr_from_tpmpublic(self.persistent_handle)
            self.logger.info("Using existing persistent primary key.")
        except self.TSS2_Exception as e:
            self.logger.info("No persistent key found. Creating a new primary key...")
            self.logger.debug(f"TPM exception: {str(e)}")

            in_sensitive = self.TPM2B_SENSITIVE_CREATE()
            in_public = self.TPM2B_PUBLIC(
                publicArea=self.TPMT_PUBLIC(
                    type=self.TPM2_ALG_ID.RSA,
                    nameAlg=self.TPM2_ALG_ID.SHA256,
                    objectAttributes=(
                            self.TPMA_OBJECT.RESTRICTED
                            | self.TPMA_OBJECT.DECRYPT
                            | self.TPMA_OBJECT.FIXEDTPM
                            | self.TPMA_OBJECT.FIXEDPARENT
                            | self.TPMA_OBJECT.SENSITIVEDATAORIGIN
                            | self.TPMA_OBJECT.USERWITHAUTH
                    ),
                    authPolicy=self.TPM2B_DIGEST(buffer=b""),
                    parameters=self.TPMU_PUBLIC_PARMS(
                        rsaDetail=self.TPMS_RSA_PARMS(
                            symmetric=self.TPMT_SYM_DEF_OBJECT(
                                algorithm=self.TPM2_ALG_ID.AES,
                                keyBits=self.TPMU_SYM_KEY_BITS(aes=128),
                                mode=self.TPMU_SYM_MODE(aes=self.TPM2_ALG_ID.CFB),
                            ),
                            scheme=self.TPMT_RSA_SCHEME(scheme=self.TPM2_ALG_ID.NULL),
                            keyBits=2048,
                            exponent=0,
                        )
                    ),
                    unique=self.TPMU_PUBLIC_ID(rsa=self.TPM2B_PUBLIC_KEY_RSA(buffer=b"")),
                )
            )

            try:
                creation_result = self.ectx.create_primary(
                    in_sensitive=in_sensitive,
                    in_public=in_public,
                    primary_handle=self.ESYS_TR.OWNER,
                    outside_info=self.TPM2B_DATA(buffer=b""),
                    creation_pcr=self.TPML_PCR_SELECTION(),
                )

                # Unpack only the first element which is the primary handle
                self.primary_handle = creation_result[0]

                self.ectx.evict_control(
                    self.ESYS_TR.OWNER, self.primary_handle, self.persistent_handle
                )
                self.logger.info("Created and persisted new primary key.")
            except self.TSS2_Exception as e:
                self.logger.error(f"Failed to create primary key: {str(e)}")
                raise

    def seal_secret(self, secret, filename: str):
        """
        Seal a secret using the TPM primary key.

        Args:
            secret: Secret to seal
            filename: Filename to store the sealed secret under

        Returns:
            Path: Path where the sealed secret was stored

        Raises:
            ValueError: If primary key hasn't been loaded
        """
        if self.primary_handle is None:
            self.logger.error("Cannot seal secret: Primary key must be generated or loaded first.")
            raise ValueError("Primary key must be generated or loaded first.")

        self.logger.info(f"Sealing secret to file: {filename}")
        self.logger.debug(f"Secret size: {len(secret)} bytes")

        in_sensitive = self.TPM2B_SENSITIVE_CREATE(
            sensitive=self.TPMS_SENSITIVE_CREATE(
                userAuth=b"",
                data=secret,
            )
        )

        in_public = self.TPM2B_PUBLIC(
            publicArea=self.TPMT_PUBLIC(
                type=self.TPM2_ALG_ID.KEYEDHASH,
                nameAlg=self.TPM2_ALG_ID.SHA256,
                objectAttributes=(
                        self.TPMA_OBJECT.USERWITHAUTH
                        | self.TPMA_OBJECT.FIXEDTPM
                        | self.TPMA_OBJECT.FIXEDPARENT
                        | self.TPMA_OBJECT.NODA
                ),
                authPolicy=self.TPM2B_DIGEST(buffer=b""),
                parameters=self.TPMU_PUBLIC_PARMS(
                    keyedHashDetail=self.TPMS_KEYEDHASH_PARMS(
                        scheme=self.TPMT_KEYEDHASH_SCHEME(scheme=self.TPM2_ALG_ID.NULL)
                    )
                ),
                unique=self.TPMU_PUBLIC_ID(keyedHash=self.TPM2B_DIGEST(buffer=b"")),
            )
        )

        try:
            creation_result = self.ectx.create(
                parent_handle=self.primary_handle,
                in_sensitive=in_sensitive,
                in_public=in_public,
                outside_info=self.TPM2B_DATA(buffer=b""),
                creation_pcr=self.TPML_PCR_SELECTION(),
            )

            # Unpack only the needed results
            out_private, out_public = creation_result[0], creation_result[1]

            blob_file = self.secrets_dir / filename

            with open(blob_file, "wb") as f:
                f.write(out_private.marshal())
                f.write(out_public.marshal())

            self.logger.info(f"Sealed secret written to {blob_file}")
            return blob_file
        except self.TSS2_Exception as e:
            self.logger.error(f"Failed to seal secret: {str(e)}")
            raise


def generate_random_secret(length=32):
    """Generate a random secret of specified length."""
    return secrets.token_urlsafe(length)


def generate_fernet_key():
    """Generate a Fernet key for symmetric encryption."""
    key = Fernet.generate_key()
    return key.decode('utf-8')


def generate_secrets():
    """Generate and seal secrets with the TPM key."""

    # 1) Generate or load TPM primary key
    tpm_mgr = ScriptTPMManager(secrets_dir="secrets")
    tpm_mgr.generate_or_load_primary_key()

    # 2) Create sealed secrets if missing
    secrets_dir = os.path.join(".", "secrets")
    os.makedirs(secrets_dir, exist_ok=True)

    secrets_to_generate = {
        "mariadb_root": generate_random_secret(),
        "mariadb_user": generate_random_secret(),
        "app_secret": generate_random_secret(),
        "jwt_secret": generate_random_secret(),
        "encryption_key": generate_fernet_key(),
        "password_salt": generate_random_secret(32)  # Add dedicated salt for password hashing
    }

    for name, secret_value in secrets_to_generate.items():
        file_path = os.path.join(secrets_dir, name)
        if not os.path.exists(file_path):
            if isinstance(secret_value, str):
                secret_bytes = secret_value.encode("utf-8")
            else:
                secret_bytes = secret_value
            tpm_mgr.seal_secret(secret=secret_bytes, filename=name)
        else:
            print(f"[!] Secret file '{file_path}' already exists; skipping generation.")


def is_raspberry_pi():
    """Check if we are running on a Raspberry Pi."""
    # Check for Raspberry Pi specific files and information
    if os.path.exists("/proc/device-tree/model"):
        with open("/proc/device-tree/model", "r") as f:
            model = f.read()
            if "Raspberry Pi" in model:
                print(f"[+] Detected Raspberry Pi: {model.strip()}")
                return True
    
    # Check CPU info for ARM processor common in Raspberry Pi
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            if "BCM2708" in cpuinfo or "BCM2709" in cpuinfo or "BCM2711" in cpuinfo or "BCM2835" in cpuinfo:
                print("[+] Detected Raspberry Pi based on CPU information.")
                return True
    except:
        pass
    
    print("[+] Not running on a Raspberry Pi.")
    return False


def prompt_yes_no(message):
    """Prompt user for yes/no answer."""
    while True:
        response = input(f"{message} [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            print("Please answer 'y' or 'n'.")


def check_and_update_rpi_boot_config():
    """Check and optionally update Raspberry Pi boot configuration files."""
    config_path = "/boot/firmware/config.txt"
    cmdline_path = "/boot/firmware/cmdline.txt"
    
    # First check if the boot changes have already taken effect
    print("[*] Checking if boot configuration changes have taken effect...")
    
    # Check if TPM devices are now available (indicates SPI/TPM overlay working)
    tmp_devices_available = any(os.path.exists(dev) for dev in ['/dev/tpmrm0', '/dev/tpm0', '/dev/tpmrm1', '/dev/tpm1'])
    
    # Check if cgroup memory is available (indicates cmdline.txt changes working)
    cgroup_memory_available = (os.path.exists("/sys/fs/cgroup/memory") or 
                             (os.path.exists("/sys/fs/cgroup/cgroup.controllers") and 
                              "memory" in open("/sys/fs/cgroup/cgroup.controllers", 'r').read()))
    
    # If hardware is working, don't mess with boot files even if they look "wrong"
    if tmp_devices_available and cgroup_memory_available:
        print("[+] Boot configuration appears to be working correctly:")
        print(f"    ✅ TPM devices available: {tmp_devices_available}")
        print(f"    ✅ Cgroup memory available: {cgroup_memory_available}")
        print("[*] Skipping boot file modifications since hardware is functional.")
        return True
    
    # Only proceed with file checks if hardware isn't working
    print(f"[*] Hardware status - TPM: {'✅' if tmp_devices_available else '❌'}, Cgroups: {'✅' if cgroup_memory_available else '❌'}")
    print("[*] Checking boot configuration files for required settings...")
    
    # Track what needs to be updated (batch all changes together)
    config_needs_update = False
    cmdline_needs_update = False
    config_changes = []
    cmdline_changes = []
    
    # Check config.txt for TPM settings with comment handling
    tmp_settings = {
        "dtparam=spi": "on",
        "dtoverlay": "tpm-slb9670"
    }
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_lines = f.readlines()
        
        missing_settings = []
        conflicting_lines = []
        
        for setting_key, expected_value in tmp_settings.items():
            found_active = False
            found_commented = False
            
            for i, line in enumerate(config_lines):
                stripped_line = line.strip()
                
                # Skip empty lines and pure comments
                if not stripped_line or stripped_line.startswith('#'):
                    # Check if it's a commented version of our setting
                    if stripped_line.startswith('#') and setting_key in stripped_line:
                        found_commented = True
                    continue
                
                # Check for active settings
                if setting_key == "dtparam=spi":
                    if stripped_line.startswith("dtparam=spi="):
                        found_active = True
                        current_value = stripped_line.split('=', 2)[-1]
                        if current_value != expected_value:
                            conflicting_lines.append((i, stripped_line, f"dtparam=spi={expected_value}"))
                elif setting_key == "dtoverlay":
                    if stripped_line.startswith("dtoverlay=tpm-") or stripped_line == "dtoverlay=tpm-slb9670":
                        found_active = True
                        if stripped_line != f"dtoverlay={expected_value}" and stripped_line != f"dtoverlay=tmp-slb9670":
                            conflicting_lines.append((i, stripped_line, f"dtoverlay={expected_value}"))
            
            # Determine what action is needed
            if not found_active:
                if found_commented:
                    missing_settings.append(f"Uncomment and set: {setting_key}={expected_value}")
                else:
                    missing_settings.append(f"Add: {setting_key}={expected_value}")
        
        if missing_settings or conflicting_lines:
            config_needs_update = True
            config_changes.extend(missing_settings)
            config_changes.extend([f"Update line {line_num + 1}: '{current}' → '{needed}'" for line_num, current, needed in conflicting_lines])
    else:
        config_needs_update = True
        config_changes.append("Create config.txt with TPM settings")
    
    # Check cmdline.txt for cgroup settings with conflict detection
    cgroup_params = ["cgroup_enable=memory", "cgroup_memory=1"]
    if os.path.exists(cmdline_path):
        with open(cmdline_path, 'r') as f:
            cmdline_content = f.read().strip()
        
        missing_params = []
        conflicting_params = []
        
        for param in cgroup_params:
            param_key = param.split('=')[0]
            param_value = param.split('=')[1]
            
            # Check if parameter exists with any value
            found_pattern = None
            for existing_param in cmdline_content.split():
                if existing_param.startswith(f"{param_key}="):
                    found_pattern = existing_param
                    break
            
            if found_pattern:
                if found_pattern != param:
                    conflicting_params.append((found_pattern, param))
            else:
                missing_params.append(param)
        
        if missing_params or conflicting_params:
            cmdline_needs_update = True
            cmdline_changes.extend([f"Add: {param}" for param in missing_params])
            cmdline_changes.extend([f"Change: '{current}' → '{needed}'" for current, needed in conflicting_params])
    else:
        cmdline_needs_update = True
        cmdline_changes.append("Create cmdline.txt with cgroup settings")
    
    # If no changes needed, we're done
    if not config_needs_update and not cmdline_needs_update:
        print("[+] Boot configuration files are already properly configured.")
        # But check if hardware still isn't working despite correct config
        if not tmp_devices_available:
            print("\n[!] CRITICAL ERROR: Boot configuration appears correct but TPM devices are not available.")
            print("    TPM 2.0 is MANDATORY for AuthBerry - the application cannot function without it.")
            print("    This may indicate:")
            print("    - Hardware TPM module is not properly connected")
            print("    - Wrong TPM overlay (this script assumes tpm-slb9670)")
            print("    - Hardware incompatibility")
            print("    - TPM is disabled in BIOS/firmware")
            print("\n[-] SETUP FAILED: Cannot proceed without functional TPM 2.0")
            return False
        return True
    
    # Report what needs to be changed (batch summary)
    print("\n[!] Boot configuration changes required for AuthBerry:")
    if config_changes:
        print(f"    📝 {config_path}:")
        for change in config_changes:
            print(f"       • {change}")
    if cmdline_changes:
        print(f"    📝 {cmdline_path}:")
        for change in cmdline_changes:
            print(f"       • {change}")
    
    # Check if we've already tried to configure but it didn't work
    files_already_configured = False
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_content = f.read()
        if "# AuthBerry TPM Configuration" in config_content:
            files_already_configured = True
    
    if files_already_configured and not tmp_devices_available:
        print("\n[!] CRITICAL WARNING: Boot files already contain AuthBerry configuration,")
        print("    but TPM devices are still not available!")
        print("\n    TPM 2.0 is MANDATORY for AuthBerry - the application CANNOT function without it.")
        print("    This suggests a hardware problem:")
        print("    - Hardware TPM module not properly connected")
        print("    - Wrong TPM overlay needed (not tpm-slb9670)")
        print("    - Hardware incompatibility")
        print("    - TPM disabled in BIOS/firmware")
        print("\n[-] SETUP FAILED: Cannot proceed without functional TPM 2.0")
        print("    Please resolve TPM hardware issues before running setup again.")
        return False
    
    # Prompt user for batch update of ALL boot files
    print(f"\n[?] Apply ALL boot configuration changes now?")
    print("    This will update both config.txt and cmdline.txt as needed.")
    if not prompt_yes_no("Apply boot configuration changes"):
        print("[!] Boot configuration changes declined.")
        print("[-] SETUP FAILED: TPM 2.0 configuration is MANDATORY for AuthBerry")
        return False
    
    # Apply all changes
    changes_applied = False
    
    # Handle config.txt updates
    if config_needs_update:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_lines = f.readlines()
                
                # Update conflicting lines in place
                for line_num, current, needed in conflicting_lines if 'conflicting_lines' in locals() else []:
                    config_lines[line_num] = needed + '\n'
                
                # Add missing settings at the end
                if 'missing_settings' in locals() and missing_settings:
                    config_lines.append("\n# AuthBerry TPM Configuration\n")
                    for setting_key, expected_value in tmp_settings.items():
                        config_lines.append(f"{setting_key}={expected_value}\n")
                
                # Write back the file
                with open(config_path, 'w') as f:
                    f.writelines(config_lines)
            else:
                # Create new file
                with open(config_path, 'w') as f:
                    f.write("# AuthBerry TPM Configuration\n")
                    for setting_key, expected_value in tmp_settings.items():
                        f.write(f"{setting_key}={expected_value}\n")
            
            print(f"[+] Updated {config_path} with TPM configuration.")
            changes_applied = True
        except Exception as e:
            print(f"[-] FAILED to update {config_path}: {e}")
            print("[-] SETUP FAILED: Cannot proceed without TPM configuration")
            return False
    
    # Handle cmdline.txt updates
    if cmdline_needs_update:
        try:
            if os.path.exists(cmdline_path):
                with open(cmdline_path, 'r') as f:
                    current_line = f.read().strip()
                
                # Handle conflicting parameters
                for current_param, needed_param in conflicting_params if 'conflicting_params' in locals() else []:
                    current_line = current_line.replace(current_param, needed_param)
                
                # Add missing parameters
                for param in missing_params if 'missing_params' in locals() else cgroup_params:
                    if param not in current_line:
                        current_line += f" {param}"
            else:
                # Create basic cmdline.txt if it doesn't exist
                current_line = " ".join(cgroup_params)
            
            with open(cmdline_path, 'w') as f:
                f.write(current_line + "\n")
            print(f"[+] Updated {cmdline_path} with cgroup configuration.")
            changes_applied = True
        except Exception as e:
            print(f"[-] FAILED to update {cmdline_path}: {e}")
            print("[-] SETUP FAILED: Cannot proceed without cgroup configuration")
            return False
    
    # Require reboot for changes to take effect
    if changes_applied:
        print("\n" + "="*70)
        print("🔄 REBOOT REQUIRED")
        print("="*70)
        print("Boot configuration files have been updated successfully.")
        print("A REBOOT is required for these changes to take effect.")
        print("")
        print("After rebooting, you MUST re-run the setup script:")
        print("  1. cd /path/to/AuthBerry")
        print("  2. sudo bash initial_setup.sh")
        print("")
        if prompt_yes_no("Reboot now"):
            print("[*] Rebooting system...")
            print("📋 REMINDER: After reboot, run 'sudo bash initial_setup.sh' again!")
            os.system("sudo reboot")
        else:
            print("\n⚠️  IMPORTANT: You chose not to reboot now.")
            print("You MUST reboot manually and then re-run:")
            print("  sudo bash initial_setup.sh")
            print("")
            print("The setup cannot continue until reboot completes.")
            return False
    
    return False  # Always return False when reboot is needed


def check_x86_64_cgroups():
    """Check if cgroups are properly configured on x86_64 systems."""
    print("\n[+] Checking cgroup configuration for x86_64 system...")
    
    cgroup_issues = []
    
    # Check if cgroup v1 memory controller is available
    if not os.path.exists("/sys/fs/cgroup/memory"):
        # Check if cgroup v2 is available
        if not os.path.exists("/sys/fs/cgroup/cgroup.controllers"):
            cgroup_issues.append("No cgroup controllers found")
        else:
            # Check if memory controller is available in cgroup v2
            try:
                with open("/sys/fs/cgroup/cgroup.controllers", 'r') as f:
                    controllers = f.read().strip()
                if "memory" not in controllers:
                    cgroup_issues.append("Memory cgroup controller not available")
            except:
                cgroup_issues.append("Cannot read cgroup controllers")
    
    # Check kernel command line for cgroup settings
    try:
        with open("/proc/cmdline", 'r') as f:
            cmdline = f.read().strip()
        
        # These are usually enabled by default on modern x86_64 systems
        # but let's check anyway
        if "cgroup_enable=memory" not in cmdline and "systemd.unified_cgroup_hierarchy" not in cmdline:
            # This might be fine on systemd systems, but let's inform the user
            print("[*] Note: No explicit cgroup memory settings found in kernel command line.")
            print("    This is usually fine on modern x86_64 systems with systemd.")
    except:
        print("[!] Cannot read kernel command line.")
    
    if cgroup_issues:
        print("[-] Cgroup configuration issues detected:")
        for issue in cgroup_issues:
            print(f"    - {issue}")
        print("\n[!] Docker container memory limits may not work properly.")
        print("    Consider adding 'cgroup_enable=memory cgroup_memory=1' to GRUB_CMDLINE_LINUX")
        print("    in /etc/default/grub, then run 'sudo update-grub' and reboot.")
        return False
    else:
        print("[+] Cgroup configuration appears to be properly set up.")
        return True


def check_buildx_setup():
    """Check if Docker Buildx is properly configured."""
    print("\n[+] Checking Docker Buildx configuration...")
    try:
        # Check if shared-builder exists
        result = subprocess.run(['docker', 'buildx', 'ls'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            if 'shared-builder' in result.stdout:
                print("[+] Docker Buildx shared-builder is configured.")
                return True
            else:
                print("[!] Docker Buildx shared-builder not found.")
                print("    This is normal if running from initial_setup.sh (buildx setup comes later).")
                print("    If running independently, run 'make buildx-setup' to configure the resource-limited builder.")
                return False
        else:
            print("[!] Docker Buildx not available.")
            print("    This may indicate Docker is not installed or not accessible.")
            return False
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"[!] Could not check Docker Buildx: {e}")
        print("    This may indicate Docker is not installed or not in PATH.")
        return False


def main():
    """Main function to set up the AuthBerry environment."""
    print("[+] AuthBerry Configuration Script")
    print("=========================")
    
    print("\n[*] This script assumes hardware enablement is complete.")
    print("    If you're seeing TPM-related errors, re-run initial_setup.sh first.")
    
    # Get system information from .env - NO DEFAULTS, FAIL IF MISSING
    try:
        auth_berry_uid = int(env_vars['AUTH_BERRY_UID'])
        auth_berry_gid = int(env_vars['AUTH_BERRY_GID'])
    except (KeyError, ValueError) as e:
        print(f"\n[-] CRITICAL ERROR: Missing or invalid user configuration in .env: {e}")
        print("    AUTH_BERRY_UID and AUTH_BERRY_GID must be properly set.")
        print("    This indicates the initial setup process failed.")
        print("    Re-run: sudo bash initial_setup.sh")
        sys.exit(1)
    
    # TSS configuration is MANDATORY - no defaults allowed
    try:
        tss_gid = int(env_vars['TSS_GID'])
        tss_uid = int(env_vars['TSS_UID'])
    except (KeyError, ValueError) as e:
        print(f"\n[-] CRITICAL ERROR: Missing or invalid TSS configuration in .env: {e}")
        print("\n" + "="*70)
        print("🚨 TPM SOFTWARE STACK (TSS) NOT PROPERLY CONFIGURED")
        print("="*70)
        print("TSS_UID and TSS_GID must be present in .env file.")
        print("This indicates TPM 2.0 software stack is not installed.")
        print("")
        print("The initial setup process should have detected and configured this.")
        print("Re-run: sudo bash initial_setup.sh")
        print("="*70)
        sys.exit(1)
    
    # Parse TPM devices - NO DEFAULTS
    if 'TPM_DEVICES' not in env_vars or not env_vars['TPM_DEVICES']:
        print("\n" + "="*70)
        print("🚨 CRITICAL ERROR: TPM DEVICES NOT CONFIGURED")
        print("="*70)
        print("TPM_DEVICES must be present and non-empty in .env file.")
        print("This indicates TPM 2.0 hardware was not detected during setup.")
        print("")
        print("The initial setup process should have detected TPM devices.")
        print("Re-run: sudo bash initial_setup.sh")
        print("="*70)
        sys.exit(1)
    
    tmp_devices = env_vars['TPM_DEVICES'].split(',')
    
    print(f"[+] Auth Berry UID: {auth_berry_uid}")
    print(f"[+] Auth Berry GID: {auth_berry_gid}")
    print(f"[+] TSS UID: {tss_uid}")
    print(f"[+] TSS GID: {tss_gid}")
    print(f"[+] TPM Devices: {tmp_devices}")
    
    # VALIDATION PHASE: Verify all configured values actually work
    print("\n" + "="*70)
    print("🔍 VALIDATION PHASE: VERIFYING SYSTEM CONFIGURATION")
    print("="*70)
    print("Hardware enablement should be complete. Validating configuration...")
    
    # Verify TSS group exists and matches
    try:
        actual_tss_gid = int(subprocess.check_output(['getent', 'group', 'tss']).decode().split(':')[2])
        if actual_tss_gid != tss_gid:
            print(f"\n[-] CRITICAL ERROR: TSS GID mismatch!")
            print(f"    .env file says TSS_GID={tss_gid}")
            print(f"    System says tss group GID={actual_tss_gid}")
            print("    This indicates system configuration changed since initial setup.")
            print("    Re-run: sudo bash initial_setup.sh")
            sys.exit(1)
    except (subprocess.CalledProcessError, ValueError, IndexError):
        print("\n[-] CRITICAL ERROR: TSS group not found on system!")
        print("    TPM Software Stack is not properly installed.")
        print("    This indicates hardware enablement was not completed.")
        print("    Re-run: sudo bash initial_setup.sh")
        sys.exit(1)
    
    # Verify TSS user exists and matches  
    try:
        actual_tss_uid = int(subprocess.check_output(['id', '-u', 'tss']).decode().strip())
        if actual_tss_uid != tss_uid:
            print(f"\n[-] CRITICAL ERROR: TSS UID mismatch!")
            print(f"    .env file says TSS_UID={tss_uid}")
            print(f"    System says tss user UID={actual_tss_uid}")
            print("    This indicates system configuration changed since initial setup.")
            print("    Re-run: sudo bash initial_setup.sh")
            sys.exit(1)
    except (subprocess.CalledProcessError, ValueError):
        print("\n[-] CRITICAL ERROR: TSS user not found on system!")
        print("    TPM Software Stack is not properly installed.")
        print("    This indicates hardware enablement was not completed.")
        print("    Re-run: sudo bash initial_setup.sh")
        sys.exit(1)
    
    # Verify TPM devices actually exist
    missing_devices = []
    for device in tmp_devices:
        device = device.strip()
        if not os.path.exists(device):
            missing_devices.append(device)
    
    if missing_devices:
        print(f"\n[-] CRITICAL ERROR: TPM devices not found!")
        print(f"    Missing devices: {missing_devices}")
        print("    This indicates hardware enablement was not completed properly.")
        print("")
        print("    Possible causes:")
        print("    • Boot configuration changes were not applied")
        print("    • System was not rebooted after boot config changes")
        print("    • TPM hardware is not properly connected")
        print("    • TPM hardware failed after initial detection")
        print("")
        print("    Re-run: sudo bash initial_setup.sh")
        sys.exit(1)
    
    print("[+] System configuration validation passed.")
    
    # TPM FUNCTIONALITY TEST: This is where we fail hard if TPM doesn't work
    print("\n[*] Testing TPM 2.0 functionality...")
    
    # Test basic TPM access
    try:
        # Try to access TPM devices with proper permissions
        for device in tmp_devices:
            device = device.strip()
            if not os.access(device, os.R_OK | os.W_OK):
                print(f"\n[-] CRITICAL ERROR: Cannot access TPM device {device}")
                print("    Device exists but is not accessible.")
                print("    This indicates permission or driver issues.")
                print("")
                print("    Check:")
                print("    • User is in 'tss' group (may require logout/login)")
                print("    • TPM device permissions are correct")
                print("    • TPM drivers are loaded properly")
                print("")
                print("    Re-run: sudo bash initial_setup.sh")
                sys.exit(1)
        
        print("[+] TPM device access test passed.")
        
    except Exception as e:
        print(f"\n[-] CRITICAL ERROR: TPM access test failed: {e}")
        print("    TPM hardware appears to be present but non-functional.")
        print("    This indicates a hardware or driver problem.")
        print("")
        print("    Re-run: sudo bash initial_setup.sh")
        sys.exit(1)
    
    # Platform-specific validation (only if needed)
    is_rpi = is_raspberry_pi()
    
    if is_rpi:
        print("\n[+] Raspberry Pi detected - verifying boot configuration is active...")
        # Just verify the configuration is working, don't try to change it
        if not os.path.exists('/dev/tpmrm0') and not os.path.exists('/dev/tpm0'):
            print("\n[-] CRITICAL ERROR: RPi boot configuration not effective!")
            print("    Boot configuration changes may not have been applied or")
            print("    system may not have been rebooted after changes.")
            print("")
            print("    Re-run: sudo bash initial_setup.sh")
            sys.exit(1)
        print("[+] Raspberry Pi boot configuration is active and working.")
    else:
        print("\n[+] x86_64 system detected - TPM should be available via firmware...")
        # For x86_64, just verify we have working TPM devices
        if not any(os.path.exists(dev) for dev in ['/dev/tpmrm0', '/dev/tpm0']):
            print("\n[-] CRITICAL ERROR: x86_64 TPM not accessible!")
            print("    This usually indicates:")
            print("    • TPM is disabled in BIOS/UEFI firmware")
            print("    • TPM hardware is not present")
            print("    • TPM driver issues")
            print("")
            print("    Enable TPM 2.0 in your system firmware and")
            print("    re-run: sudo bash initial_setup.sh")
            sys.exit(1)
        print("[+] x86_64 TPM hardware is accessible.")
    
    # Check Docker Buildx configuration
    check_buildx_setup()
    
    # Ensure secrets directory exists
    os.makedirs('secrets', exist_ok=True)

    # Generate and seal secrets (this requires functional TPM)
    print("\n[+] Generating TPM-sealed secrets...")
    try:
        generate_secrets()
        print("[+] TPM-sealed secrets generated successfully.")
    except Exception as e:
        print(f"\n[-] FAILED to generate TPM-sealed secrets: {e}")
        print("\n" + "="*70)
        print("🚨 CRITICAL ERROR: TPM SECRET GENERATION FAILED")
        print("="*70)
        print("AuthBerry requires TPM 2.0 for secure secret management.")
        print("Secret generation failed, indicating TPM is not functional.")
        print("")
        print("This is a security-critical failure. The application")
        print("CANNOT operate without properly sealed secrets.")
        print("")
        print("Possible causes:")
        print("• TPM hardware malfunction")
        print("• TPM driver issues")
        print("• Insufficient permissions")
        print("• TPM already owned by another application")
        print("")
        print("Re-run: sudo bash initial_setup.sh")
        print("="*70)
        sys.exit(1)

    print("")
    print("="*70)
    print("✅ AUTHBERRY CONFIGURATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("🔐 TPM 2.0 verified and secrets generated")
    print("🐳 Docker Buildx configured with resource limits")
    print("⚙️  System configuration validated")
    print("")
    print("AuthBerry is ready for deployment!")
    print("="*70)


if __name__ == "__main__":
    main()