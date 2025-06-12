#!/usr/bin/env python3
import os
import sys
import socket
import secrets
import subprocess
import logging
import time
import platform
import shutil
from pathlib import Path
from cryptography.fernet import Fernet

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


def main():
    """Main function to set up the AuthBerry environment."""
    print("[+] AuthBerry Configuration Script")
    print("=========================")
    
    # Get system information from .env
    # Fall back to system values if not in .env
    auth_berry_uid = int(env_vars.get('AUTH_BERRY_UID', 0))
    auth_berry_gid = int(env_vars.get('AUTH_BERRY_GID', 0))
    tss_gid = int(env_vars.get('TSS_GID', 113))
    
    # Parse TPM devices
    tpm_devices = []
    if 'TPM_DEVICES' in env_vars and env_vars['TPM_DEVICES']:
        tpm_devices = env_vars['TPM_DEVICES'].split(',')
    
    print(f"[+] Auth Berry UID: {auth_berry_uid}")
    print(f"[+] Auth Berry GID: {auth_berry_gid}")
    print(f"[+] TSS GID: {tss_gid}")
    print(f"[+] TPM Devices: {tpm_devices}")
    
    if not tpm_devices:
        print("[-] Error: No TPM devices found. Make sure your TPM is enabled and accessible.")
        print("[!] Continuing without TPM support. Some functionality may be limited.")
    
    # Check for Raspberry Pi and configure if needed
    if is_raspberry_pi() and not tpm_devices:
        print("[!] Running on Raspberry Pi without TPM devices.")
        print("[!] You may need to enable SPI and add the TPM overlay in /boot/config.txt.")
    
    # Ensure secrets directory exists
    os.makedirs('secrets', exist_ok=True)

    # Generate and seal secrets
    generate_secrets()

    print("")
    print("[+] AuthBerry configuration completed successfully!")


if __name__ == "__main__":
    main()