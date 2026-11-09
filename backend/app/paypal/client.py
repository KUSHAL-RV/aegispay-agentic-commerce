"""Async PayPal Sandbox Client - OAuth2, Orders v2, Payouts v1, Disputes v1."""

import time
import json
import uuid
import httpx
from typing import Optional, Any
from dataclasses import dataclass
from app.config import get_settings


@dataclass
class PayPalToken:
    access_token: str
    expires_at: float


class PayPalClient:
    """Async client for PayPal Sandbox APIs with graceful fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.PAYPAL_BASE_URL
        self._token: Optional[PayPalToken] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.PAYPAL_CLIENT_ID and self.settings.PAYPAL_CLIENT_SECRET)

    async def _get_token(self) -> str:
        """Get OAuth2 token with caching."""
        if self._token and time.time() < self._token.expires_at - 60:
            return self._token.access_token

        if not self.is_configured:
            return "MOCK_ACCESS_TOKEN"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.settings.PAYPAL_CLIENT_ID, self.settings.PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"}
            )
            response.raise_for_status()
            data = response.json()
            self._token = PayPalToken(
                access_token=data["access_token"],
                expires_at=time.time() + data.get("expires_in", 32400)
            )
            return self._token.access_token

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make authenticated request to PayPal API."""
        if not self.is_configured:
            return self._mock_response(method, path, kwargs)

        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": str(uuid.uuid4())
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, f"{self.base_url}{path}",
                headers=headers, **kwargs
            )
            response.raise_for_status()
            if response.status_code == 204:
                return {"status": "success"}
            return response.json()

    def _mock_response(self, method: str, path: str, kwargs: dict) -> dict:
        """Generate mock responses when PayPal credentials not configured."""
        mock_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"

        if "/v2/checkout/orders" in path and method == "POST":
            return {
                "id": mock_id,
                "status": "CREATED",
                "intent": "AUTHORIZE",
                "purchase_units": kwargs.get("json", {}).get("purchase_units", []),
                "links": [
                    {"href": f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{mock_id}", "rel": "self"},
                    {"href": f"https://www.sandbox.paypal.com/checkoutnow?token={mock_id}", "rel": "approve"},
                    {"href": f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{mock_id}/authorize", "rel": "authorize"}
                ],
                "_mock": True
            }
        elif "authorize" in path and method == "POST":
            auth_id = f"AUTH-{uuid.uuid4().hex[:12].upper()}"
            return {
                "id": mock_id,
                "status": "COMPLETED",
                "purchase_units": [{
                    "payments": {
                        "authorizations": [{
                            "id": auth_id,
                            "status": "CREATED",
                            "amount": {"currency_code": "USD", "value": "1000.00"}
                        }]
                    }
                }],
                "_mock": True
            }
        elif "capture" in path and method == "POST":
            return {
                "id": f"CAP-{uuid.uuid4().hex[:12].upper()}",
                "status": "COMPLETED",
                "amount": {"currency_code": "USD", "value": "1000.00"},
                "_mock": True
            }
        elif "void" in path and method == "POST":
            return {"status": "VOIDED", "_mock": True}
        elif "/v1/payments/payouts" in path:
            return {
                "batch_header": {
                    "payout_batch_id": f"PAYOUT-{uuid.uuid4().hex[:12].upper()}",
                    "batch_status": "PENDING",
                    "sender_batch_header": kwargs.get("json", {}).get("sender_batch_header", {})
                },
                "_mock": True
            }
        elif "disputes" in path:
            return {"status": "EVIDENCE_SUBMITTED", "_mock": True}

        return {"status": "OK", "id": mock_id, "_mock": True}

    # ── Orders V2 ─────────────────────────────────────────────

    async def create_order_authorize(self, amount: float, currency: str, description: str,
                                      vendor_email: str, reference_id: str) -> dict:
        """Create an order with AUTHORIZE intent."""
        payload = {
            "intent": "AUTHORIZE",
            "purchase_units": [{
                "reference_id": reference_id,
                "description": description,
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}"
                },
                "payee": {"email_address": vendor_email}
            }],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                        "landing_page": "LOGIN",
                        "user_action": "PAY_NOW",
                        "return_url": "https://aegispay.example.com/return",
                        "cancel_url": "https://aegispay.example.com/cancel"
                    }
                }
            }
        }
        return await self._request("POST", "/v2/checkout/orders", json=payload)

    async def authorize_order(self, order_id: str) -> dict:
        """Authorize a created order."""
        return await self._request("POST", f"/v2/checkout/orders/{order_id}/authorize")

    async def capture_authorization(self, authorization_id: str) -> dict:
        """Capture an authorized payment."""
        return await self._request("POST", f"/v2/payments/authorizations/{authorization_id}/capture")

    async def void_authorization(self, authorization_id: str) -> dict:
        """Void an authorized payment."""
        return await self._request("POST", f"/v2/payments/authorizations/{authorization_id}/void")

    # ── Payouts V1 ────────────────────────────────────────────

    async def create_payout(self, recipient_email: str, amount: float, currency: str,
                            note: str, reference_id: str) -> dict:
        """Create an instant payout to a vendor/contractor."""
        payload = {
            "sender_batch_header": {
                "sender_batch_id": f"AegisPay-{uuid.uuid4().hex[:8]}",
                "email_subject": "AegisPay Milestone Payment",
                "email_message": note
            },
            "items": [{
                "recipient_type": "EMAIL",
                "amount": {"value": f"{amount:.2f}", "currency": currency},
                "receiver": recipient_email,
                "note": note,
                "sender_item_id": reference_id
            }]
        }
        return await self._request("POST", "/v1/payments/payouts", json=payload)

    # ── Disputes V1 ───────────────────────────────────────────

    async def submit_dispute_evidence(self, dispute_id: str, evidence_payload: dict) -> dict:
        """Submit evidence for a dispute."""
        return await self._request(
            "POST",
            f"/v1/customer/disputes/{dispute_id}/provide-evidence",
            json=evidence_payload
        )

    def build_dispute_evidence(self, transaction_id: str, description: str,
                                signature_b64: str, agent_reasoning: str) -> dict:
        """Build a dispute evidence payload."""
        return {
            "evidences": [{
                "evidence_type": "PROOF_OF_FULFILLMENT",
                "evidence_info": {
                    "tracking_info": [{
                        "carrier_name": "FEDEX",
                        "tracking_number": f"AEGIS-{transaction_id[:8]}"
                    }]
                },
                "notes": (
                    f"Automated verification by AegisPay AI Agent. "
                    f"Transaction: {transaction_id}. "
                    f"Agent Reasoning: {agent_reasoning}. "
                    f"Ed25519 Signature: {signature_b64[:32]}..."
                )
            }]
        }


# Module-level singleton
_client: Optional[PayPalClient] = None

def get_paypal_client() -> PayPalClient:
    global _client
    if _client is None:
        _client = PayPalClient()
    return _client
