"""Hybrid encryption helpers based on X25519 + XChaCha20-Poly1305."""
from __future__ import annotations

from base64 import b64encode, b64decode
from typing import Tuple

from nacl.public import PrivateKey, PublicKey
from nacl.utils import random
from nacl.bindings import (
    crypto_scalarmult,
    crypto_aead_xchacha20poly1305_ietf_encrypt,
    crypto_aead_xchacha20poly1305_ietf_decrypt,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

_HKDF_INFO = b"moodsense-xchacha20-v1"


def _derive_symmetric_key(shared_secret: bytes) -> bytes:
    """Stretch the raw X25519 shared secret into a 32-byte AEAD key."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_HKDF_INFO,
    )
    return hkdf.derive(shared_secret)


def generate_server_keypair() -> Tuple[str, str]:
    """Return `(private_key_b64, public_key_b64)` for server bootstrap."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    private_b64 = b64encode(private_key.encode()).decode("utf-8")
    public_b64 = b64encode(public_key.encode()).decode("utf-8")
    return private_b64, public_b64


def encrypt_for_server(server_public_key_b64: str, plaintext: bytes) -> Tuple[str, str, str]:
    """Envelope-encrypt `plaintext` for the server.

    Returns `(client_public_b64, nonce_b64, ciphertext_b64)`.
    """
    server_public = PublicKey(b64decode(server_public_key_b64))

    client_private = PrivateKey.generate()
    client_public = client_private.public_key

    shared_secret = crypto_scalarmult(
        client_private.encode(),
        server_public.encode(),
    )
    symmetric_key = _derive_symmetric_key(shared_secret)

    nonce = random(24)  # XChaCha20 nonce length
    ciphertext = crypto_aead_xchacha20poly1305_ietf_encrypt(
        plaintext,
        None,
        nonce,
        symmetric_key,
    )

    return (
        b64encode(client_public.encode()).decode("utf-8"),
        b64encode(nonce).decode("utf-8"),
        b64encode(ciphertext).decode("utf-8"),
    )


class NaClEnvelopeEncryption:
    """Server-side helper that keeps the long-term private key."""

    def __init__(self, private_key_b64: str) -> None:
        self._private_key = PrivateKey(b64decode(private_key_b64))

    @property
    def public_key_b64(self) -> str:
        """Return the matching public key (useful for diagnostics)."""
        return b64encode(self._private_key.public_key.encode()).decode("utf-8")

    def decrypt(self, client_public_key_b64: str, nonce_b64: str, ciphertext_b64: str) -> bytes:
        """Decrypt data produced by `encrypt_for_server`."""
        client_public = PublicKey(b64decode(client_public_key_b64))

        shared_secret = crypto_scalarmult(
            self._private_key.encode(),
            client_public.encode(),
        )
        symmetric_key = _derive_symmetric_key(shared_secret)

        nonce = b64decode(nonce_b64)
        ciphertext = b64decode(ciphertext_b64)

        plaintext = crypto_aead_xchacha20poly1305_ietf_decrypt(
            ciphertext,
            None,
            nonce,
            symmetric_key,
        )
        return plaintext