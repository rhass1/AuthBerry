#! /usr/bin/env python3


import os
import base64
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class CryptoService:
    """Handles cryptographic operations for End-to-End Encryption (E2EE) using Diffie-Hellman Key Exchange."""

    @staticmethod
    def generate_keypair():
        """
        Generates an Elliptic Curve Diffie-Hellman (ECDH) key pair using the P-256 curve.

        Returns:
            dict: A dictionary containing the base64-encoded private and public keys.
        """
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return {
            'private_key': base64.b64encode(private_bytes).decode('utf-8'),
            'public_key': base64.b64encode(public_bytes).decode('utf-8')
        }

    @staticmethod
    def compute_shared_secret(private_key_b64, peer_public_key_b64):
        """
        Computes the shared secret using the local private key and the peer's public key,
        then derives an encryption key using HKDF.

        Args:
            private_key_b64 (str): The base64-encoded local private key.
            peer_public_key_b64 (str): The base64-encoded public key of the peer.

        Returns:
            str: The base64-encoded derived shared encryption key.
        """
        private_key_bytes = base64.b64decode(private_key_b64)
        peer_public_key_bytes = base64.b64decode(peer_public_key_b64)

        private_key = serialization.load_der_private_key(
            private_key_bytes,
            password=None
        )

        peer_public_key = serialization.load_der_public_key(
            peer_public_key_bytes
        )

        shared_key = private_key.exchange(ec.ECDH(), peer_public_key)

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'AuthBerry E2EE Key'
        ).derive(shared_key)

        return base64.b64encode(derived_key).decode('utf-8')

    @staticmethod
    def encrypt(data, key_b64):
        """
        Encrypts data using AES-256 in GCM mode with a provided shared secret key.

        Args:
            data (dict or bytes): The data to encrypt. If a dictionary, it will be JSON-serialized.
            key_b64 (str): The base64-encoded shared secret encryption key.

        Returns:
            str: The base64-encoded encrypted data, including the nonce.
        """
        if not isinstance(data, bytes):
            data = json.dumps(data).encode('utf-8')

        key = base64.b64decode(key_b64)

        nonce = os.urandom(12)

        aesgcm = AESGCM(key)

        ciphertext = aesgcm.encrypt(nonce, data, None)

        encrypted_data = base64.b64encode(nonce + ciphertext).decode('utf-8')

        return encrypted_data

    @staticmethod
    def decrypt(encrypted_data_b64, key_b64):
        """
        Decrypts AES-256-GCM encrypted data using a provided shared secret key.

        Args:
            encrypted_data_b64 (str): The base64-encoded encrypted data (including nonce).
            key_b64 (str): The base64-encoded shared secret encryption key.

        Returns:
            dict or str: The decrypted data, parsed as JSON if possible, otherwise as a string.
        """
        encrypted_data = base64.b64decode(encrypted_data_b64)

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        key = base64.b64decode(key_b64)

        aesgcm = AESGCM(key)

        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        try:
            return json.loads(plaintext.decode('utf-8'))
        except:
            return plaintext.decode('utf-8')
