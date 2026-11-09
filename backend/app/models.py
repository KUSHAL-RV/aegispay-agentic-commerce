"""SQLModel ORM models for AegisPay escrow transactions, audit logs, and dispute defense."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionStatus(str, Enum):
    """Possible states for an escrow transaction throughout its lifecycle."""

    PENDING_REVIEW = "PENDING_REVIEW"
    PII_SCRUBBED = "PII_SCRUBBED"
    AGENT_APPROVED = "AGENT_APPROVED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    VOIDED = "VOIDED"
    PAYOUT_SENT = "PAYOUT_SENT"
    DISPUTED = "DISPUTED"
    FAILED = "FAILED"


class EscrowTransaction(SQLModel, table=True):
    """Represents a single escrow payment flowing through the AegisPay pipeline."""

    __tablename__ = "escrow_transactions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vendor_name: str
    vendor_email: str
    description: str
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING_REVIEW

    paypal_order_id: Optional[str] = None
    paypal_auth_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    paypal_payout_id: Optional[str] = None

    pii_original: Optional[str] = None
    pii_redacted: Optional[str] = None
    pii_entities_found: Optional[str] = None  # JSON string

    ed25519_signature: Optional[str] = None
    ed25519_public_key: Optional[str] = None

    agent_reasoning: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    """Immutable audit trail entry for every action taken on a transaction."""

    __tablename__ = "audit_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    transaction_id: str
    action: str
    actor: str  # "system", "agent", "human", "paypal"
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DisputeDefenseRecord(SQLModel, table=True):
    """Pre-compiled evidence packet for automated dispute defense."""

    __tablename__ = "dispute_defense_records"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    transaction_id: str
    dispute_id: Optional[str] = None
    evidence_type: str
    evidence_payload: str  # JSON string of evidence
    status: str = "PREPARED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
