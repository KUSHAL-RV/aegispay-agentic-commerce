"""AegisPay Test Suite - Presidio, Ed25519, Policy, PayPal Client tests."""

import sys
import os
import json
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    import pytest
except ImportError:
    class DummyPytest:
        class mark:
            @staticmethod
            def asyncio(fn):
                return fn
    pytest = DummyPytest()


class TestPresidioGuard:
    """Test PII detection and redaction."""

    def test_email_redaction(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        result = guard.scan_and_redact("Contact john@example.com for details")
        assert "john@example.com" not in result.redacted_text
        assert result.pii_detected is True
        assert len(result.entities_found) > 0

    def test_phone_redaction(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        result = guard.scan_and_redact("Call 555-123-4567 for support")
        assert "555-123-4567" not in result.redacted_text
        assert result.pii_detected is True

    def test_ssn_redaction(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        result = guard.scan_and_redact("SSN: 123-45-6789")
        assert "123-45-6789" not in result.redacted_text
        assert result.pii_detected is True

    def test_credit_card_redaction(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        result = guard.scan_and_redact("Card: 4111-1111-1111-1111")
        assert "4111-1111-1111-1111" not in result.redacted_text

    def test_no_pii(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        result = guard.scan_and_redact("Annual cloud license renewal for 2025")
        assert result.pii_detected is False
        assert result.redacted_text == result.original_text

    def test_empty_text(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        result = guard.scan_and_redact("")
        assert result.redacted_text == ""
        assert result.pii_detected is False

    def test_multiple_pii_types(self):
        from app.security.presidio_guard import get_presidio_guard
        guard = get_presidio_guard()
        text = "Contact Jane Doe at jane@corp.com, phone 415-555-0198, SSN 987-65-4321"
        result = guard.scan_and_redact(text)
        assert result.pii_detected is True
        assert "jane@corp.com" not in result.redacted_text
        assert "987-65-4321" not in result.redacted_text


class TestCryptoSigner:
    """Test Ed25519 signing and verification."""

    def test_keypair_generation(self):
        from app.security.crypto_signer import CryptoSigner
        private_b64, public_b64 = CryptoSigner.generate_keypair()
        assert len(private_b64) > 0
        assert len(public_b64) > 0

    def test_sign_and_verify(self):
        from app.security.crypto_signer import CryptoSigner
        signer = CryptoSigner()
        result = signer.sign_approval(
            transaction_id="test-123",
            amount=1000.0,
            vendor="Acme Corp",
            agent_decision="APPROVE",
            reasoning="All checks passed"
        )
        assert result.signature_b64
        assert result.public_key_b64
        assert result.payload_hash

        # Verify the signature
        is_valid = signer.verify_signature(
            signature_b64=result.signature_b64,
            canonical_payload=result.canonical_payload,
            public_key_b64=result.public_key_b64
        )
        assert is_valid is True

    def test_tampered_payload_fails(self):
        from app.security.crypto_signer import CryptoSigner
        signer = CryptoSigner()
        result = signer.sign_approval(
            transaction_id="test-456",
            amount=5000.0,
            vendor="Test Vendor",
            agent_decision="APPROVE",
            reasoning="Verified"
        )

        # Tamper with payload
        tampered = result.canonical_payload.replace("5000.0", "50000.0")
        is_valid = signer.verify_signature(
            signature_b64=result.signature_b64,
            canonical_payload=tampered,
            public_key_b64=result.public_key_b64
        )
        assert is_valid is False

    def test_wrong_key_fails(self):
        from app.security.crypto_signer import CryptoSigner
        signer1 = CryptoSigner()
        signer2 = CryptoSigner()  # Different keypair
        result = signer1.sign_approval(
            transaction_id="test-789",
            amount=2000.0,
            vendor="Corp",
            agent_decision="APPROVE",
            reasoning="OK"
        )
        is_valid = signer2.verify_signature(
            signature_b64=result.signature_b64,
            canonical_payload=result.canonical_payload,
            public_key_b64=signer2.public_key_b64
        )
        assert is_valid is False

    def test_canonicalization_deterministic(self):
        from app.security.crypto_signer import CryptoSigner
        payload1 = {"b": 2, "a": 1}
        payload2 = {"a": 1, "b": 2}
        assert CryptoSigner.canonicalize(payload1) == CryptoSigner.canonicalize(payload2)


class TestPolicyChecks:
    """Test procurement policy enforcement."""

    def test_amount_cap(self):
        from app.agents.procurement_graph import policy_check_node, ProcurementState
        state: ProcurementState = {
            "transaction_id": "test", "vendor_name": "Acme", "vendor_email": "a@b.com",
            "description": "test", "amount": 75000.00, "currency": "USD",
            "pii_clean_description": "test", "pii_entities": [], "pii_detected": False,
            "policy_passed": None, "policy_flags": None,
            "decision": None, "reasoning": None,
            "signature": None, "public_key": None, "payload_hash": None,
            "current_node": None, "error": None
        }
        result = policy_check_node(state)
        assert result["policy_passed"] is False
        assert any("cap" in f.lower() for f in result["policy_flags"])

    def test_blocked_vendor(self):
        from app.agents.procurement_graph import policy_check_node, ProcurementState
        state: ProcurementState = {
            "transaction_id": "test", "vendor_name": "FraudCorp", "vendor_email": "a@b.com",
            "description": "test", "amount": 1000.00, "currency": "USD",
            "pii_clean_description": "test", "pii_entities": [], "pii_detected": False,
            "policy_passed": None, "policy_flags": None,
            "decision": None, "reasoning": None,
            "signature": None, "public_key": None, "payload_hash": None,
            "current_node": None, "error": None
        }
        result = policy_check_node(state)
        assert result["policy_passed"] is False
        assert any("blocklist" in f for f in result["policy_flags"])

    def test_valid_transaction_passes(self):
        from app.agents.procurement_graph import policy_check_node, ProcurementState
        state: ProcurementState = {
            "transaction_id": "test", "vendor_name": "Acme Corp", "vendor_email": "a@b.com",
            "description": "test", "amount": 5000.00, "currency": "USD",
            "pii_clean_description": "test", "pii_entities": [], "pii_detected": False,
            "policy_passed": None, "policy_flags": None,
            "decision": None, "reasoning": None,
            "signature": None, "public_key": None, "payload_hash": None,
            "current_node": None, "error": None
        }
        result = policy_check_node(state)
        assert result["policy_passed"] is True


class TestPayPalClient:
    """Test PayPal client mock fallback."""

    def test_mock_mode_when_unconfigured(self):
        from app.paypal.client import PayPalClient
        client = PayPalClient()
        assert client.is_configured is False  # No credentials in test env

    @pytest.mark.asyncio
    async def test_mock_create_order(self):
        from app.paypal.client import PayPalClient
        client = PayPalClient()
        result = await client.create_order_authorize(
            amount=1000.0, currency="USD",
            description="Test order", vendor_email="test@test.com",
            reference_id="ref-123"
        )
        assert "id" in result
        assert result.get("_mock") is True
        assert result.get("intent") == "AUTHORIZE"

    @pytest.mark.asyncio
    async def test_mock_capture(self):
        from app.paypal.client import PayPalClient
        client = PayPalClient()
        result = await client.capture_authorization("AUTH-TEST123")
        assert result.get("_mock") is True
        assert result.get("status") == "COMPLETED"

    @pytest.mark.asyncio
    async def test_mock_void(self):
        from app.paypal.client import PayPalClient
        client = PayPalClient()
        result = await client.void_authorization("AUTH-TEST123")
        assert result.get("_mock") is True

    @pytest.mark.asyncio
    async def test_mock_payout(self):
        from app.paypal.client import PayPalClient
        client = PayPalClient()
        result = await client.create_payout(
            recipient_email="vendor@test.com", amount=500.0,
            currency="USD", note="Test payout", reference_id="ref-456"
        )
        assert result.get("_mock") is True
        assert "batch_header" in result

    def test_dispute_evidence_builder(self):
        from app.paypal.client import PayPalClient
        client = PayPalClient()
        evidence = client.build_dispute_evidence(
            transaction_id="txn-123",
            description="Test dispute",
            signature_b64="dGVzdA==",
            agent_reasoning="Verified delivery"
        )
        assert "evidences" in evidence
        assert len(evidence["evidences"]) == 1
        assert evidence["evidences"][0]["evidence_type"] == "PROOF_OF_FULFILLMENT"


def _run_coroutine(coro):
    """Deterministic coroutine runner for stand-alone script runs."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value


if __name__ == "__main__":
    print("Running AegisPay Test Suite...")

    # Run Presidio tests
    t_presidio = TestPresidioGuard()
    t_presidio.test_email_redaction()
    t_presidio.test_phone_redaction()
    t_presidio.test_ssn_redaction()
    t_presidio.test_credit_card_redaction()
    t_presidio.test_no_pii()
    t_presidio.test_empty_text()
    t_presidio.test_multiple_pii_types()
    print("  ✓ TestPresidioGuard passed (7/7)")

    # Run Ed25519 signer tests
    t_crypto = TestCryptoSigner()
    t_crypto.test_keypair_generation()
    t_crypto.test_sign_and_verify()
    t_crypto.test_tampered_payload_fails()
    t_crypto.test_wrong_key_fails()
    t_crypto.test_canonicalization_deterministic()
    print("  ✓ TestCryptoSigner passed (5/5)")

    # Run Policy & cap tests
    t_policy = TestPolicyChecks()
    t_policy.test_amount_cap()
    t_policy.test_blocked_vendor()
    t_policy.test_valid_transaction_passes()
    print("  ✓ TestPolicyChecks passed (3/3)")

    # Run PayPal client mock fallback tests
    t_paypal = TestPayPalClient()
    t_paypal.test_mock_mode_when_unconfigured()
    _run_coroutine(t_paypal.test_mock_create_order())
    _run_coroutine(t_paypal.test_mock_capture())
    _run_coroutine(t_paypal.test_mock_void())
    _run_coroutine(t_paypal.test_mock_payout())
    t_paypal.test_dispute_evidence_builder()
    print("  ✓ TestPayPalClient passed (6/6)")

    print("\nALL 21 TESTS PASSED SUCCESSFULLY! 100% SUCCESS.")
