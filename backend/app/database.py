"""Database engine and session management for AegisPay with SQLModel & standalone fallback."""

import json
from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any, List, Optional, Type, TypeVar, Union

from app.config import get_settings

_settings = get_settings()

try:
    from sqlmodel import Session, SQLModel, create_engine, select
    SQLMODEL_AVAILABLE = True

    _connect_args: dict = {}
    if _settings.DATABASE_URL.startswith("sqlite"):
        _connect_args["check_same_thread"] = False

    engine = create_engine(_settings.DATABASE_URL, connect_args=_connect_args)

except ImportError:
    SQLMODEL_AVAILABLE = False
    engine = None

    class QueryResult:
        def __init__(self, items: list):
            self._items = items

        def all(self) -> list:
            return list(self._items)

        def first(self) -> Optional[Any]:
            return self._items[0] if self._items else None

    class MockQuery:
        def __init__(self, model_cls: Type):
            self.model_cls = model_cls
            self.conditions: list = []
            self.order_by_specs: list = []

        def where(self, *conditions):
            self.conditions.extend(conditions)
            return self

        def order_by(self, *ordering):
            self.order_by_specs.extend(ordering)
            return self

    def select(model_cls: Type) -> MockQuery:
        return MockQuery(model_cls)

    # In-memory document store partitioned by model class name
    _DB_STORE: dict[str, dict[str, Any]] = {}

    class FallbackSession:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def add(self, obj: Any) -> None:
            cls_name = obj.__class__.__name__
            if cls_name not in _DB_STORE:
                _DB_STORE[cls_name] = {}
            obj_id = getattr(obj, "id", None)
            if obj_id:
                _DB_STORE[cls_name][str(obj_id)] = obj

        def commit(self) -> None:
            pass

        def refresh(self, obj: Any) -> None:
            pass

        def get(self, model_cls: Type, obj_id: str) -> Optional[Any]:
            cls_name = model_cls.__name__
            return _DB_STORE.get(cls_name, {}).get(str(obj_id))

        def exec(self, query: MockQuery) -> QueryResult:
            cls_name = query.model_cls.__name__
            items = list(_DB_STORE.get(cls_name, {}).values())

            # Apply where conditions
            for cond in query.conditions:
                if isinstance(cond, tuple) and len(cond) == 3:
                    op, attr, val = cond
                    if op == "eq":
                        items = [i for i in items if str(getattr(i, attr, None)) == str(val)]
                    elif op == "ne":
                        items = [i for i in items if str(getattr(i, attr, None)) != str(val)]

            # Apply order_by specs
            for spec in query.order_by_specs:
                if isinstance(spec, tuple) and len(spec) == 2:
                    direction, attr = spec
                    reverse = (direction == "desc")
                    items.sort(key=lambda x: str(getattr(x, attr, "")), reverse=reverse)

            return QueryResult(items)

    Session = FallbackSession


def init_db() -> None:
    """Create all database tables and seed initial demo transactions if empty."""
    if SQLMODEL_AVAILABLE and engine is not None:
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
    seed_initial_data()


def seed_initial_data() -> None:
    """Seed initial realistic demo records if table is currently empty."""
    from app.models import EscrowTransaction, AuditLog, TransactionStatus
    from app.security.crypto_signer import get_crypto_signer

    with Session(engine) if SQLMODEL_AVAILABLE else Session() as session:
        existing = session.exec(select(EscrowTransaction)).first()
        if existing:
            return  # Already seeded or has data

        signer = get_crypto_signer()

        # Seed 1: Active Authorized Escrow (Cloud Infrastructure)
        t1 = EscrowTransaction(
            vendor_name="Acme Cloud Infrastructure",
            vendor_email="billing@acmecloud.example.com",
            description="Q1 2025 Multi-region Kubernetes cluster reservation and egress bandwidth allocation.",
            amount=14500.00,
            currency="USD",
            status=TransactionStatus.AUTHORIZED,
            paypal_order_id="9A8172635B1029384",
            paypal_auth_id="AUTH-78A9B0C1D2E3",
            pii_original="Q1 2025 Multi-region Kubernetes cluster reservation and egress bandwidth allocation.",
            pii_redacted="Q1 2025 Multi-region Kubernetes cluster reservation and egress bandwidth allocation.",
            pii_entities_found="[]",
            agent_reasoning="Amount $14,500.00 is below $50K policy threshold; vendor verified active on enterprise master agreement.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        sig1 = signer.sign_approval(t1.id, t1.amount, t1.vendor_name, "APPROVE", t1.agent_reasoning)
        t1.ed25519_signature = sig1.signature_b64
        t1.ed25519_public_key = sig1.public_key_b64
        session.add(t1)

        session.add(AuditLog(transaction_id=t1.id, action="CREATED", actor="system", details="Created via seed initialization"))
        session.add(AuditLog(transaction_id=t1.id, action="PIPELINE_APPROVE", actor="agent", details=t1.agent_reasoning))
        session.add(AuditLog(transaction_id=t1.id, action="AUTHORIZED", actor="paypal", details=f"PayPal Auth ID: {t1.paypal_auth_id}"))

        # Seed 2: Presidio Scrubbed Escrow (Data Processing with PII)
        t2 = EscrowTransaction(
            vendor_name="SecureData Analytics LLC",
            vendor_email="procurement@securedata.example.com",
            description="ETL migration services. Lead Contact: Sarah Connor (SSN: 987-65-4321), Emergency Phone: 415-555-0199, IP: 10.0.4.12",
            amount=28750.00,
            currency="USD",
            status=TransactionStatus.AUTHORIZED,
            paypal_order_id="8C1234567D8901234",
            paypal_auth_id="AUTH-34F5G6H7J8K9",
            pii_original="ETL migration services. Lead Contact: Sarah Connor (SSN: 987-65-4321), Emergency Phone: 415-555-0199, IP: 10.0.4.12",
            pii_redacted="ETL migration services. Lead Contact: <REDACTED_NAME> (SSN: <REDACTED_SSN>), Emergency Phone: <REDACTED_PHONE>, IP: <REDACTED_IP>",
            pii_entities_found=json.dumps([
                {"entity_type": "US_SSN", "start": 57, "end": 68, "score": 0.85, "text_snippet": "987-***"},
                {"entity_type": "PHONE_NUMBER", "start": 87, "end": 99, "score": 0.85, "text_snippet": "415-***"},
                {"entity_type": "IP_ADDRESS", "start": 105, "end": 114, "score": 0.85, "text_snippet": "10.0***"}
            ]),
            agent_reasoning="PII scrubbed successfully; 3 sensitive entities sanitized before dispatch to PayPal Orders v2.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        sig2 = signer.sign_approval(t2.id, t2.amount, t2.vendor_name, "APPROVE", t2.agent_reasoning)
        t2.ed25519_signature = sig2.signature_b64
        t2.ed25519_public_key = sig2.public_key_b64
        session.add(t2)

        session.add(AuditLog(transaction_id=t2.id, action="CREATED", actor="system", details="Created via seed initialization"))
        session.add(AuditLog(transaction_id=t2.id, action="PII_SANITIZED", actor="agent", details="Presidio redacted 3 PII entities"))
        session.add(AuditLog(transaction_id=t2.id, action="AUTHORIZED", actor="paypal", details=f"PayPal Auth ID: {t2.paypal_auth_id}"))

        # Seed 3: Completed Settlement with Payout (Milestone Delivered)
        t3 = EscrowTransaction(
            vendor_name="Vertex AI Research Labs",
            vendor_email="payouts@vertexlabs.example.com",
            description="Fine-tuned LLM checkpoint deliverable and evaluation benchmark suite v2.1.",
            amount=9800.00,
            currency="USD",
            status=TransactionStatus.PAYOUT_SENT,
            paypal_order_id="7B9876543A2109876",
            paypal_auth_id="AUTH-12M3N4P5Q6R7",
            paypal_capture_id="CAP-55T66U77V88W",
            paypal_payout_id="PAYOUT-99AA00BB11CC",
            pii_original="Fine-tuned LLM checkpoint deliverable and evaluation benchmark suite v2.1.",
            pii_redacted="Fine-tuned LLM checkpoint deliverable and evaluation benchmark suite v2.1.",
            pii_entities_found="[]",
            agent_reasoning="Milestone verified against GitHub deliverable SHA-256; human operator approved capture and immediate payout.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        sig3 = signer.sign_approval(t3.id, t3.amount, t3.vendor_name, "APPROVE", t3.agent_reasoning)
        t3.ed25519_signature = sig3.signature_b64
        t3.ed25519_public_key = sig3.public_key_b64
        session.add(t3)

        session.add(AuditLog(transaction_id=t3.id, action="CREATED", actor="system", details="Created via seed initialization"))
        session.add(AuditLog(transaction_id=t3.id, action="AUTHORIZED", actor="paypal", details="Funds pre-authorized"))
        session.add(AuditLog(transaction_id=t3.id, action="CAPTURED", actor="human", details=f"Capture ID: {t3.paypal_capture_id}"))
        session.add(AuditLog(transaction_id=t3.id, action="PAYOUT_SENT", actor="paypal", details=f"Payout Batch: {t3.paypal_payout_id}"))

        session.commit()


def get_session() -> Generator[Any, None, None]:
    """FastAPI dependency that yields a database session and closes it after use."""
    if SQLMODEL_AVAILABLE and engine is not None:
        with Session(engine) as session:
            yield session
    else:
        with Session() as session:
            yield session
