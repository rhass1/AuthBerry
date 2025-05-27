#! /usr/bin/env python3


import secrets
from pathlib import Path
from typing import Union, ByteString

from tpm2_pytss import ESAPI, ESYS_TR, TSS2_Exception
from tpm2_pytss.constants import TPM2_ALG_ID, TPMA_OBJECT
from tpm2_pytss.types import (
    TPM2B_SENSITIVE_CREATE,
    TPM2B_PUBLIC,
    TPM2B_PRIVATE,
    TPMT_PUBLIC,
    TPM2B_DIGEST,
    TPM2B_PUBLIC_KEY_RSA,
    TPMS_RSA_PARMS,
    TPMT_SYM_DEF_OBJECT,
    TPMU_SYM_KEY_BITS,
    TPMU_SYM_MODE,
    TPMT_RSA_SCHEME,
    TPML_PCR_SELECTION,
    TPM2B_DATA,
    TPMS_SENSITIVE_CREATE,
    TPMS_KEYEDHASH_PARMS,
    TPMT_KEYEDHASH_SCHEME,
    TPMU_PUBLIC_PARMS,
    TPMU_PUBLIC_ID,
    TPM2_HANDLE,
)


class TPMManager:
    """
    Manages the creation, sealing, and unsealing of secrets using TPM.
    """

    def __init__(self, secrets_dir: Union[str, Path], persistent_handle: int = 0x81010001):
        """
        Initializes the TPMManager.

        Args:
            secrets_dir: The directory path where sealed secrets will be stored.
            persistent_handle: The TPM persistent handle value to use for the primary key.
        """
        self.ectx = ESAPI()
        self.primary_handle = None
        self.secret = None
        self.persistent_handle = TPM2_HANDLE(persistent_handle)
        self.secrets_dir = Path(secrets_dir)

        try:
            self.secrets_dir.mkdir(exist_ok=True, parents=True)
            print(f"[TPMManager] Using secrets directory: {self.secrets_dir.absolute()}")
        except PermissionError:
            print(f"[TPMManager] Permission error creating directory {self.secrets_dir}")
            raise
        except Exception as e:
            print(f"[TPMManager] Error creating directory {self.secrets_dir}: {str(e)}")
            raise

    def generate_or_load_primary_key(self) -> None:
        """
        Generates a new primary key on the TPM or loads an existing one if available.
        This key is used as the parent for sealing other secrets.

        Raises:
            TSS2_Exception: If there's an underlying error interacting with the TPM.
        """
        try:
            self.primary_handle = self.ectx.tr_from_tpmpublic(self.persistent_handle)
            print("[TPMManager] Using existing persistent primary key.")
        except TSS2_Exception:
            print("[TPMManager] No persistent key found. Creating a new primary key...")

            in_sensitive = TPM2B_SENSITIVE_CREATE()
            in_public = TPM2B_PUBLIC(
                publicArea=TPMT_PUBLIC(
                    type=TPM2_ALG_ID.RSA,
                    nameAlg=TPM2_ALG_ID.SHA256,
                    objectAttributes=(
                            TPMA_OBJECT.RESTRICTED
                            | TPMA_OBJECT.DECRYPT
                            | TPMA_OBJECT.FIXEDTPM
                            | TPMA_OBJECT.FIXEDPARENT
                            | TPMA_OBJECT.SENSITIVEDATAORIGIN
                            | TPMA_OBJECT.USERWITHAUTH
                    ),
                    authPolicy=TPM2B_DIGEST(buffer=b""),
                    parameters=TPMU_PUBLIC_PARMS(
                        rsaDetail=TPMS_RSA_PARMS(
                            symmetric=TPMT_SYM_DEF_OBJECT(
                                algorithm=TPM2_ALG_ID.AES,
                                keyBits=TPMU_SYM_KEY_BITS(aes=128),
                                mode=TPMU_SYM_MODE(aes=TPM2_ALG_ID.CFB),
                            ),
                            scheme=TPMT_RSA_SCHEME(scheme=TPM2_ALG_ID.NULL),
                            keyBits=2048,
                            exponent=0,
                        )
                    ),
                    unique=TPMU_PUBLIC_ID(rsa=TPM2B_PUBLIC_KEY_RSA(buffer=b"")),
                )
            )

            creation_result = self.ectx.create_primary(
                in_sensitive=in_sensitive,
                in_public=in_public,
                primary_handle=ESYS_TR.OWNER,
                outside_info=TPM2B_DATA(buffer=b""),
                creation_pcr=TPML_PCR_SELECTION(),
            )

            self.primary_handle = creation_result[0]

            self.ectx.evict_control(
                ESYS_TR.OWNER, self.primary_handle, self.persistent_handle
            )
            print("[TPMManager] Created and persisted new primary key.")

    def generate_secret(self, size: int = 32) -> bytes:
        """
        Generates a cryptographically secure random secret of a specified size.

        Args:
            size: The size of the secret in bytes.

        Returns:
            bytes: The generated random secret.
        """
        self.secret = secrets.token_bytes(size)
        return self.secret

    def seal_secret(self, secret: ByteString, filename: str) -> Path:
        """
        Seals a given secret using the TPM primary key. The sealed secret can only
        be unsealed by the same TPM and conditions.

        Args:
            secret: The secret (bytes-like object) to be sealed.
            filename: The name of the file to store the sealed secret blob.

        Returns:
            Path: The file system path where the sealed secret was stored.

        Raises:
            ValueError: If the primary key has not been loaded or generated.
        """
        if self.primary_handle is None:
            raise ValueError("Primary key must be generated or loaded first.")

        in_sensitive = TPM2B_SENSITIVE_CREATE(
            sensitive=TPMS_SENSITIVE_CREATE(
                userAuth=b"",
                data=secret,
            )
        )

        in_public = TPM2B_PUBLIC(
            publicArea=TPMT_PUBLIC(
                type=TPM2_ALG_ID.KEYEDHASH,
                nameAlg=TPM2_ALG_ID.SHA256,
                objectAttributes=(
                        TPMA_OBJECT.USERWITHAUTH
                        | TPMA_OBJECT.FIXEDTPM
                        | TPMA_OBJECT.FIXEDPARENT
                        | TPMA_OBJECT.NODA
                ),
                authPolicy=TPM2B_DIGEST(buffer=b""),
                parameters=TPMU_PUBLIC_PARMS(
                    keyedHashDetail=TPMS_KEYEDHASH_PARMS(
                        scheme=TPMT_KEYEDHASH_SCHEME(scheme=TPM2_ALG_ID.NULL)
                    )
                ),
                unique=TPMU_PUBLIC_ID(keyedHash=TPM2B_DIGEST(buffer=b"")),
            )
        )

        creation_result = self.ectx.create(
            parent_handle=self.primary_handle,
            in_sensitive=in_sensitive,
            in_public=in_public,
            outside_info=TPM2B_DATA(buffer=b""),
            creation_pcr=TPML_PCR_SELECTION(),
        )

        out_private, out_public = creation_result[0], creation_result[1]

        blob_file = self.secrets_dir / filename

        with open(blob_file, "wb") as f:
            f.write(out_private.marshal())
            f.write(out_public.marshal())

        print(f"[TPMManager] Sealed secret written to {blob_file}")
        return blob_file

    def unseal_secret(self, filename: str) -> bytes:
        """
        Unseals a previously sealed secret from a file.

        Args:
            filename: The name of the file containing the sealed secret blob.

        Returns:
            bytes: The unsealed secret.

        Raises:
            ValueError: If the primary key has not been loaded or generated.
            FileNotFoundError: If the specified sealed secret file does not exist.
        """
        if self.primary_handle is None:
            raise ValueError("Primary key must be generated or loaded first.")

        blob_file = self.secrets_dir / filename

        if not blob_file.exists():
            raise FileNotFoundError(f"Secret file {blob_file} not found")

        with open(blob_file, "rb") as f:
            blob_data = f.read()

        offset = 0
        out_private, consumed = TPM2B_PRIVATE.unmarshal(blob_data[offset:])
        offset += consumed
        out_public, consumed = TPM2B_PUBLIC.unmarshal(blob_data[offset:])

        loaded_handle = self.ectx.load(self.primary_handle, out_private, out_public)
        unsealed_data = self.ectx.unseal(loaded_handle, ESYS_TR.PASSWORD)

        unsealed_bytes = bytes(unsealed_data.buffer)

        print(f"[TPMManager] Unsealed secret {filename} (size={len(unsealed_bytes)})")
        return unsealed_bytes
