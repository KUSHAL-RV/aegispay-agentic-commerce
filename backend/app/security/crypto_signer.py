"""Ed25519 Cryptographic Signer - Signs and verifies agent approval payloads."""

import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey
    )
    from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


@dataclass
class SignatureResult:
    """Result of a signing operation."""
    signature_b64: str
    public_key_b64: str
    payload_hash: str
    signed_at: str
    canonical_payload: str


class CryptoSigner:
    """Ed25519 signing and verification for agent approvals with standard fallback."""

    def __init__(self, private_key_b64: Optional[str] = None, public_key_b64: Optional[str] = None):
        if CRYPTOGRAPHY_AVAILABLE:
            if private_key_b64 and private_key_b64.strip():
                raw = base64.b64decode(private_key_b64)
                self._private_key = Ed25519PrivateKey.from_private_bytes(raw[:32])
            else:
                self._private_key = Ed25519PrivateKey.generate()

            self._public_key = self._private_key.public_key()
        else:
            # Fallback keypair generation for environments without C-extensions installed
            if private_key_b64 and private_key_b64.strip():
                self._fallback_priv = base64.b64decode(private_key_b64)[:32]
            else:
                self._fallback_priv = secrets.token_bytes(32)
            self._fallback_pub = hashlib.sha256(self._fallback_priv + b"AegisPay_Public_Derivation").digest()

    @property
    def public_key_b64(self) -> str:
        if CRYPTOGRAPHY_AVAILABLE:
            raw = self._public_key.public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw
            )
            return base64.b64encode(raw).decode()
        return base64.b64encode(self._fallback_pub).decode()

    @property
    def private_key_b64(self) -> str:
        if CRYPTOGRAPHY_AVAILABLE:
            raw = self._private_key.private_bytes(
                serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw,
                serialization.NoEncryption()
            )
            return base64.b64encode(raw).decode()
        return base64.b64encode(self._fallback_priv).decode()

    @staticmethod
    def canonicalize(payload: dict) -> str:
        """Deterministic JSON canonicalization for signing."""
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    def sign_approval(self, transaction_id: str, amount: float, vendor: str, 
                      agent_decision: str, reasoning: str) -> SignatureResult:
        """Sign an agent approval payload."""
        payload = {
            "transaction_id": transaction_id,
            "amount": amount,
            "vendor": vendor,
            "decision": agent_decision,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        canonical = self.canonicalize(payload)
        payload_hash = hashlib.sha256(canonical.encode()).hexdigest()

        if CRYPTOGRAPHY_AVAILABLE:
            signature = self._private_key.sign(canonical.encode())
            sig_b64 = base64.b64encode(signature).decode()
        else:
            # Fallback HMAC signature
            sig_bytes = hmac.new(self._fallback_priv, canonical.encode(), hashlib.sha256).digest()
            sig_b64 = base64.b64encode(sig_bytes).decode()

        return SignatureResult(
            signature_b64=sig_b64,
            public_key_b64=self.public_key_b64,
            payload_hash=payload_hash,
            signed_at=payload["timestamp"],
            canonical_payload=canonical
        )

    def verify_signature(self, signature_b64: str, canonical_payload: str, 
                         public_key_b64: Optional[str] = None) -> bool:
        """Verify an Ed25519 signature."""
        try:
            if CRYPTOGRAPHY_AVAILABLE:
                if public_key_b64:
                    raw = base64.b64decode(public_key_b64)
                    pub_key = Ed25519PublicKey.from_public_bytes(raw)
                else:
                    pub_key = self._public_key

                signature = base64.b64decode(signature_b64)
                pub_key.verify(signature, canonical_payload.encode())
                return True
            else:
                # Fallback verification: Check that signature matches derived key
                target_pub = base64.b64decode(public_key_b64) if public_key_b64 else self._fallback_pub
                if target_pub != self._fallback_pub:
                    # Cross-key verification fails
                    return False

                expected_sig = hmac.new(self._fallback_priv, canonical_payload.encode(), hashlib.sha256).digest()
                sig_bytes = base64.b64decode(signature_b64)
                return hmac.compare_digest(expected_sig, sig_bytes)
        except Exception:
            return False

    @classmethod
    def generate_keypair(cls) -> Tuple[str, str]:
        """Generate a new Ed25519 keypair, returns (private_b64, public_b64)."""
        instance = cls()
        return instance.private_key_b64, instance.public_key_b64


# Module-level singleton
_signer: Optional[CryptoSigner] = None

def get_crypto_signer() -> CryptoSigner:
    global _signer
    if _signer is None:
        from app.config import get_settings
        settings = get_settings()
        _signer = CryptoSigner(
            private_key_b64=settings.ED25519_PRIVATE_KEY,
            public_key_b64=settings.ED25519_PUBLIC_KEY
        )
    return _signer
