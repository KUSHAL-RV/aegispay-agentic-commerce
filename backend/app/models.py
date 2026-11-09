"""SQLModel ORM models for AegisPay escrow transactions, audit logs, and dispute defense with standard Pydantic fallback."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any

try:
    from sqlmodel import SQLModel, Field
    SQLMODEL_AVAILABLE = True
except ImportError:
    SQLMODEL_AVAILABLE = False
    from pydantic import BaseModel, Field as PydanticField

    class ColumnDescriptor:
        """Enables SQLModel-like attribute comparisons when SQLModel is not installed."""
        def __init__(self, name: str):
            self.name = name

        def __eq__(self, other: Any):
            return ("eq", self.name, other)

        def __ne__(self, other: Any):
            return ("ne", self.name, other)

        def desc(self):
            return ("desc", self.name)

        def asc(self):
            return ("asc", self.name)

    class SQLModel(BaseModel):
        """Fallback base model when sqlmodel is not installed."""
        def __init_subclass__(cls, table: bool = False, **kwargs):
            super().__init_subclass__(**kwargs)
            # Attach column descriptors for query building
            for field_name in cls.model_fields.keys():
                setattr(cls, field_name, ColumnDescriptor(field_name))

        model_config = {"extra": "ignore", "populate_by_name": True}

    def Field(*args, default=..., default_factory=None, primary_key=False, **kwargs):
        """Fallback field constructor matching SQLModel.Field."""
        if default_factory is not None:
            return PydanticField(default_factory=default_factory, **kwargs)
        if default is not ...:
            return PydanticField(default=default, **kwargs)
        return PydanticField(**kwargs)


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

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLog(SQLModel, table=True):
    """Immutable audit trail entry for every action taken on a transaction."""

    __tablename__ = "audit_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    transaction_id: str
    action: str
    actor: str  # "system", "agent", "human", "paypal"
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DisputeDefenseRecord(SQLModel, table=True):
    """Pre-compiled evidence packet for automated dispute defense."""

    __tablename__ = "dispute_defense_records"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    transaction_id: str
    dispute_id: Optional[str] = None
    evidence_type: str = "PROOF_OF_FULFILLMENT"
    evidence_payload: str = "{}"
    status: str = "PREPARED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
