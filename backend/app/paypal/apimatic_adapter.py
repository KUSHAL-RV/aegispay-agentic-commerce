"""APIMatic SDK Adapter Layer - Typed schemas for PayPal API compatibility.

This module provides structured Pydantic models that serve as a typed adapter
layer, demonstrating compatibility with APIMatic-generated SDK patterns.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ── Orders V2 Schemas ─────────────────────────────────────

class Money(BaseModel):
    currency_code: str = "USD"
    value: str

class Payee(BaseModel):
    email_address: Optional[str] = None
    merchant_id: Optional[str] = None

class AmountBreakdown(BaseModel):
    item_total: Optional[Money] = None
    shipping: Optional[Money] = None
    tax_total: Optional[Money] = None

class Amount(BaseModel):
    currency_code: str = "USD"
    value: str
    breakdown: Optional[AmountBreakdown] = None

class PurchaseUnit(BaseModel):
    reference_id: Optional[str] = None
    description: Optional[str] = None
    amount: Amount
    payee: Optional[Payee] = None

class ExperienceContext(BaseModel):
    payment_method_preference: str = "IMMEDIATE_PAYMENT_REQUIRED"
    landing_page: str = "LOGIN"
    user_action: str = "PAY_NOW"
    return_url: str = ""
    cancel_url: str = ""

class PayPalPaymentSource(BaseModel):
    experience_context: Optional[ExperienceContext] = None

class PaymentSource(BaseModel):
    paypal: Optional[PayPalPaymentSource] = None

class CreateOrderRequest(BaseModel):
    intent: str = "AUTHORIZE"
    purchase_units: List[PurchaseUnit]
    payment_source: Optional[PaymentSource] = None

class LinkDescription(BaseModel):
    href: str
    rel: str
    method: Optional[str] = None

class Authorization(BaseModel):
    id: str
    status: str
    amount: Optional[Money] = None

class PaymentCollection(BaseModel):
    authorizations: Optional[List[Authorization]] = None

class PurchaseUnitResponse(BaseModel):
    reference_id: Optional[str] = None
    payments: Optional[PaymentCollection] = None

class OrderResponse(BaseModel):
    id: str
    status: str
    intent: Optional[str] = None
    purchase_units: Optional[List[PurchaseUnitResponse]] = None
    links: Optional[List[LinkDescription]] = None
    is_mock: bool = Field(default=False, alias="_mock")

    model_config = {"populate_by_name": True}

# ── Payouts V1 Schemas ────────────────────────────────────

class SenderBatchHeader(BaseModel):
    sender_batch_id: str
    email_subject: Optional[str] = None
    email_message: Optional[str] = None

class PayoutItem(BaseModel):
    recipient_type: str = "EMAIL"
    amount: Money
    receiver: str
    note: Optional[str] = None
    sender_item_id: Optional[str] = None

class CreatePayoutRequest(BaseModel):
    sender_batch_header: SenderBatchHeader
    items: List[PayoutItem]

class PayoutBatchHeader(BaseModel):
    payout_batch_id: str
    batch_status: str

class PayoutResponse(BaseModel):
    batch_header: PayoutBatchHeader
    is_mock: bool = Field(default=False, alias="_mock")

    model_config = {"populate_by_name": True}

# ── Dispute V1 Schemas ────────────────────────────────────

class TrackingInfo(BaseModel):
    carrier_name: str
    tracking_number: str

class EvidenceInfo(BaseModel):
    tracking_info: Optional[List[TrackingInfo]] = None

class Evidence(BaseModel):
    evidence_type: str
    evidence_info: Optional[EvidenceInfo] = None
    notes: Optional[str] = None

class SubmitEvidenceRequest(BaseModel):
    evidences: List[Evidence]


# ── Adapter Functions ─────────────────────────────────────

def parse_order_response(raw: dict) -> OrderResponse:
    """Parse raw PayPal order response into typed model."""
    return OrderResponse.model_validate(raw)

def parse_payout_response(raw: dict) -> PayoutResponse:
    """Parse raw PayPal payout response into typed model."""
    return PayoutResponse.model_validate(raw)

def build_create_order(amount: float, currency: str, description: str,
                       vendor_email: str, reference_id: str) -> dict:
    """Build a typed CreateOrderRequest and return as dict."""
    request = CreateOrderRequest(
        intent="AUTHORIZE",
        purchase_units=[PurchaseUnit(
            reference_id=reference_id,
            description=description,
            amount=Amount(currency_code=currency, value=f"{amount:.2f}"),
            payee=Payee(email_address=vendor_email)
        )]
    )
    return request.model_dump(exclude_none=True)
