#! /usr/bin/env python3


import os
import sys
import subprocess
import time
from pathlib import Path

# Add the directory containing tpm_manager.py to the Python path
sys.path.append("/usr/local/bin")
try:
    from tpm_manager import TPMManager
except ImportError:
    sys.exit("[-] Critical error: TPMManager module not found")

# Constants
TEMP_MARIADB_ROOT_PASSWORD = os.environ.get("MARIADB_ROOT_PASSWORD", "")
MARIADB_USER = os.environ.get("MARIADB_USER", "auth-berry-user")
SECRETS_DIR = Path("/secrets")


def get_sealed_creds():
    """
    Reads and unseals MariaDB root and user passwords from the TPM.

    This function initializes the TPM manager, loads or generates the primary key,
    and then unseals the 'mariadb_root' and 'mariadb_user' secrets.

    Returns:
        tuple: A tuple containing (root_password, user_password) as strings if successful,
               otherwise (None, None).
    """
    try:
        tpm_mgr = TPMManager(secrets_dir=str(SECRETS_DIR))
        tpm_mgr.generate_or_load_primary_key()

        root_bytes = tpm_mgr.unseal_secret("mariadb_root")
        user_bytes = tpm_mgr.unseal_secret("mariadb_user")

        if not root_bytes or not user_bytes:
            print("[-] Failed to unseal one or more credentials")
            return None, None

        root_pass = root_bytes.decode("utf-8").strip()
        user_pass = user_bytes.decode("utf-8").strip()

        return root_pass, user_pass

    except Exception as e:
        print(f"[-] Error reading sealed credentials: {str(e)}")
        return None, None


def update_user_password(username, host_pattern, new_password, current_password):
    """
    Updates the password for a specified MariaDB user.

    This function first checks if the user exists for the given host pattern.
    If the user exists, it proceeds to update their password.

    Args:
        username (str): The username of the MariaDB account to update.
        host_pattern (str): The host pattern associated with the user (e.g., 'localhost', '%').
        new_password (str): The new password to set for the user.
        current_password (str): The current password for the 'root' user (used for authentication).

    Returns:
        bool: True if the password update was successful or the user didn't exist, False otherwise.
    """
    check_sql = f"SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user='{username}' AND host='{host_pattern}');"

    try:
        check_result = subprocess.run(
            ["mariadb", "-u", "root", f"-p{current_password}", "-N", "-s", "-e", check_sql],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if check_result.returncode != 0:
            print(f"[-] Cannot check if '{username}'@'{host_pattern}' exists: {check_result.stderr.strip()}")
            return False

        if check_result.stdout.strip() != "1":
            print(f"[*] User '{username}'@'{host_pattern}' does not exist, skipping")
            return True

        sql_cmd = f"ALTER USER '{username}'@'{host_pattern}' IDENTIFIED BY '{new_password}';"

        update_result = subprocess.run(
            ["mariadb", "-u", "root", f"-p{current_password}", "-e", sql_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if update_result.returncode == 0:
            print(f"[+] Successfully updated password for '{username}'@'{host_pattern}'")
            return True
        else:
            print(f"[-] Failed to update password: {update_result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"[-] Error in database operation: {str(e)}")
        return False


def secure_cleanup():
    """
    Cleans up sensitive variables from memory by overwriting them with zeros
    and then setting their references to None.
    """
    frame = sys._getframe()
    for var_name, var_obj in list(frame.f_locals.items()):
        if any(sensitive in var_name.lower() for sensitive in
               ['pass', 'secret', 'cred', 'key', 'token', '_bytes']):
            if isinstance(var_obj, (str, bytes)):
                if isinstance(var_obj, str):
                    frame.f_locals[var_name] = '0' * len(var_obj)
                else:
                    frame.f_locals[var_name] = b'0' * len(var_obj)
                frame.f_locals[var_name] = None

    sensitive_vars = [
        'new_root_pass', 'new_user_pass',
        'root_bytes', 'user_bytes',
        'root_pass', 'user_pass',
        'current_password', 'TEMP_MARIADB_ROOT_PASSWORD'
    ]

    for var in sensitive_vars:
        if var in frame.f_locals and frame.f_locals[var] is not None:
            frame.f_locals[var] = None


def main():
    """
    Main function to orchestrate the MariaDB password update process using TPM-sealed credentials.

    It retrieves the sealed passwords from the TPM, updates the MariaDB root and application
    user passwords, and performs a secure cleanup of sensitive data from memory.
    """
    if not TEMP_MARIADB_ROOT_PASSWORD:
        print("[-] MARIADB_ROOT_PASSWORD environment variable not set")
        sys.exit(1)

    try:
        new_root_pass, new_user_pass = get_sealed_creds()

        if not new_root_pass or not new_user_pass:
            print("[-] Failed to retrieve credentials from TPM")
            sys.exit(1)

        update_success = update_user_password("root", "localhost", new_root_pass, TEMP_MARIADB_ROOT_PASSWORD)

        if update_success:
            time.sleep(0.5)

            update_user_password("root", "%", new_root_pass, new_root_pass)
            update_user_password(MARIADB_USER, "%", new_user_pass, new_root_pass)

        print("[+] Password update process complete")

    finally:
        secure_cleanup()


if __name__ == "__main__":
    main()
    secure_cleanup()
