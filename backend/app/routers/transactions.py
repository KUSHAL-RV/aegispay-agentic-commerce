"""Transaction Router - REST endpoints, HITL approve/void, and Judge Simulator scenarios."""

import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session, Session, select
from app.models import EscrowTransaction, AuditLog, DisputeDefenseRecord, TransactionStatus
from app.security.presidio_guard import get_presidio_guard
from app.security.crypto_signer import get_crypto_signer
from app.paypal.client import get_paypal_client
from app.agents.procurement_graph import run_procurement_pipeline

router = APIRouter(prefix="/transactions", tags=["transactions"])


class CreateTransactionRequest(BaseModel):
    vendor_name: str
    vendor_email: str
    description: str
    amount: float
    currency: str = "USD"


class TransactionResponse(BaseModel):
    id: str
    vendor_name: str
    vendor_email: str
    description: str
    amount: float
    currency: str
    status: str
    paypal_order_id: Optional[str] = None
    paypal_auth_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    paypal_payout_id: Optional[str] = None
    pii_original: Optional[str] = None
    pii_redacted: Optional[str] = None
    pii_entities_found: Optional[str] = None
    ed25519_signature: Optional[str] = None
    ed25519_public_key: Optional[str] = None
    agent_reasoning: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Import manager here to avoid circular imports
def get_manager():
    from app.main import manager
    return manager


@router.post("/create", response_model=TransactionResponse)
async def create_transaction(req: CreateTransactionRequest, session: Session = Depends(get_session)):
    """Create a new escrow transaction and run through the AI procurement pipeline."""
    mgr = get_manager()

    # Create transaction record
    txn = EscrowTransaction(
        vendor_name=req.vendor_name,
        vendor_email=req.vendor_email,
        description=req.description,
        amount=req.amount,
        currency=req.currency,
        status=TransactionStatus.PENDING_REVIEW
    )
    session.add(txn)
    session.commit()
    session.refresh(txn)

    # Log creation
    audit = AuditLog(
        transaction_id=txn.id,
        action="CREATED",
        actor="system",
        details=f"Transaction created for {req.vendor_name}, amount: {req.amount} {req.currency}"
    )
    session.add(audit)
    session.commit()

    # Broadcast creation
    await mgr.broadcast({
        "type": "transaction_update",
        "transaction_id": txn.id,
        "status": txn.status,
        "action": "CREATED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Run procurement pipeline with broadcasting
    async def broadcast_fn(msg):
        await mgr.broadcast(msg)

    pipeline_result = await run_procurement_pipeline(
        transaction_id=txn.id,
        vendor_name=req.vendor_name,
        vendor_email=req.vendor_email,
        description=req.description,
        amount=req.amount,
        currency=req.currency,
        broadcast_fn=broadcast_fn
    )

    # Update transaction with pipeline results
    txn.pii_original = req.description
    txn.pii_redacted = pipeline_result.get("pii_clean_description")
    txn.pii_entities_found = json.dumps(pipeline_result.get("pii_entities", []))
    txn.agent_reasoning = pipeline_result.get("reasoning")
    txn.ed25519_signature = pipeline_result.get("signature")
    txn.ed25519_public_key = pipeline_result.get("public_key")

    decision = pipeline_result.get("decision", "REJECT")

    if decision == "APPROVE":
        txn.status = TransactionStatus.AGENT_APPROVED
        # Create PayPal authorization
        paypal = get_paypal_client()
        try:
            order = await paypal.create_order_authorize(
                amount=req.amount,
                currency=req.currency,
                description=pipeline_result.get("pii_clean_description", req.description),
                vendor_email=req.vendor_email,
                reference_id=txn.id
            )
            txn.paypal_order_id = order.get("id")

            # Try to authorize
            auth_result = await paypal.authorize_order(order["id"])
            auths = (auth_result.get("purchase_units", [{}])[0]
                     .get("payments", {}).get("authorizations", []))
            if auths:
                txn.paypal_auth_id = auths[0]["id"]
            txn.status = TransactionStatus.AUTHORIZED

            audit2 = AuditLog(
                transaction_id=txn.id,
                action="AUTHORIZED",
                actor="agent",
                details=f"PayPal Order: {txn.paypal_order_id}, Auth: {txn.paypal_auth_id}"
            )
            session.add(audit2)
        except Exception as e:
            txn.agent_reasoning = (txn.agent_reasoning or "") + f" | PayPal Error: {str(e)}"

    elif decision == "ESCALATE":
        txn.status = TransactionStatus.PENDING_REVIEW

    else:
        txn.status = TransactionStatus.FAILED

    txn.updated_at = datetime.now(timezone.utc)
    session.add(txn)

    audit3 = AuditLog(
        transaction_id=txn.id,
        action=f"PIPELINE_{decision}",
        actor="agent",
        details=pipeline_result.get("reasoning")
    )
    session.add(audit3)
    session.commit()
    session.refresh(txn)

    # Broadcast final state
    await mgr.broadcast({
        "type": "transaction_update",
        "transaction_id": txn.id,
        "status": txn.status,
        "action": f"PIPELINE_{decision}",
        "data": {
            "paypal_order_id": txn.paypal_order_id,
            "paypal_auth_id": txn.paypal_auth_id,
            "pii_detected": pipeline_result.get("pii_detected"),
            "signature": txn.ed25519_signature[:32] + "..." if txn.ed25519_signature else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return TransactionResponse(**txn.model_dump())


@router.post("/{transaction_id}/approve", response_model=TransactionResponse)
async def approve_transaction(transaction_id: str, session: Session = Depends(get_session)):
    """Human-in-the-loop: Approve and capture an authorized transaction."""
    mgr = get_manager()
    txn = session.get(EscrowTransaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if txn.status not in (TransactionStatus.AUTHORIZED, TransactionStatus.PENDING_REVIEW, TransactionStatus.AGENT_APPROVED):
        raise HTTPException(status_code=400, detail=f"Cannot approve transaction in {txn.status} status")

    paypal = get_paypal_client()

    # If we have an auth ID, capture it
    if txn.paypal_auth_id:
        try:
            capture = await paypal.capture_authorization(txn.paypal_auth_id)
            txn.paypal_capture_id = capture.get("id")
            txn.status = TransactionStatus.CAPTURED

            # Send payout to vendor
            payout = await paypal.create_payout(
                recipient_email=txn.vendor_email,
                amount=txn.amount,
                currency=txn.currency,
                note=f"AegisPay milestone payment for: {txn.pii_redacted or txn.description}",
                reference_id=txn.id
            )
            txn.paypal_payout_id = payout.get("batch_header", {}).get("payout_batch_id")
            txn.status = TransactionStatus.PAYOUT_SENT
        except Exception as e:
            txn.status = TransactionStatus.CAPTURED
            txn.agent_reasoning = (txn.agent_reasoning or "") + f" | Payout Error: {str(e)}"
    else:
        # No auth yet - create full flow
        try:
            order = await paypal.create_order_authorize(
                amount=txn.amount, currency=txn.currency,
                description=txn.pii_redacted or txn.description,
                vendor_email=txn.vendor_email, reference_id=txn.id
            )
            txn.paypal_order_id = order.get("id")
            auth_result = await paypal.authorize_order(order["id"])
            auths = (auth_result.get("purchase_units", [{}])[0]
                     .get("payments", {}).get("authorizations", []))
            if auths:
                txn.paypal_auth_id = auths[0]["id"]
            capture = await paypal.capture_authorization(txn.paypal_auth_id or "mock")
            txn.paypal_capture_id = capture.get("id")
            txn.status = TransactionStatus.CAPTURED
        except Exception as e:
            txn.agent_reasoning = (txn.agent_reasoning or "") + f" | Error: {str(e)}"

    txn.updated_at = datetime.now(timezone.utc)
    session.add(txn)
    audit = AuditLog(
        transaction_id=txn.id, action="HITL_APPROVED",
        actor="human", details=f"Captured: {txn.paypal_capture_id}, Payout: {txn.paypal_payout_id}"
    )
    session.add(audit)
    session.commit()
    session.refresh(txn)

    await mgr.broadcast({
        "type": "transaction_update", "transaction_id": txn.id,
        "status": txn.status, "action": "HITL_APPROVED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return TransactionResponse(**txn.model_dump())


@router.post("/{transaction_id}/void", response_model=TransactionResponse)
async def void_transaction(transaction_id: str, session: Session = Depends(get_session)):
    """Human-in-the-loop: Void an authorized transaction."""
    mgr = get_manager()
    txn = session.get(EscrowTransaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if txn.status not in (TransactionStatus.AUTHORIZED, TransactionStatus.PENDING_REVIEW, TransactionStatus.AGENT_APPROVED):
        raise HTTPException(status_code=400, detail=f"Cannot void transaction in {txn.status} status")

    paypal = get_paypal_client()
    if txn.paypal_auth_id:
        try:
            await paypal.void_authorization(txn.paypal_auth_id)
        except Exception:
            pass

    txn.status = TransactionStatus.VOIDED
    txn.updated_at = datetime.now(timezone.utc)
    session.add(txn)
    audit = AuditLog(
        transaction_id=txn.id, action="VOIDED",
        actor="human", details="Transaction voided by human operator"
    )
    session.add(audit)
    session.commit()
    session.refresh(txn)

    await mgr.broadcast({
        "type": "transaction_update", "transaction_id": txn.id,
        "status": txn.status, "action": "VOIDED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return TransactionResponse(**txn.model_dump())


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    status: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """List all transactions with optional status filter."""
    query = select(EscrowTransaction)
    if status:
        query = query.where(EscrowTransaction.status == status)
    query = query.order_by(EscrowTransaction.created_at.desc())
    results = session.exec(query).all()
    return [TransactionResponse(**t.model_dump()) for t in results]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, session: Session = Depends(get_session)):
    """Get a single transaction by ID."""
    txn = session.get(EscrowTransaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse(**txn.model_dump())


@router.get("/{transaction_id}/audit")
async def get_audit_log(transaction_id: str, session: Session = Depends(get_session)):
    """Get audit log for a transaction."""
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.transaction_id == transaction_id)
        .order_by(AuditLog.timestamp.asc())
    ).all()
    return [{"id": l.id, "action": l.action, "actor": l.actor,
             "details": l.details, "timestamp": l.timestamp.isoformat()} for l in logs]


# ── Judge Simulator Scenarios ─────────────────────────────

SCENARIOS = {
    "happy_path": {
        "vendor_name": "Acme Cloud Services",
        "vendor_email": "billing@acmecloud.example.com",
        "description": "Annual cloud infrastructure license renewal for Q1 2025. Contact: John Smith, john.smith@acme.com, phone: 555-123-4567",
        "amount": 12500.00,
        "currency": "USD"
    },
    "pii_heavy": {
        "vendor_name": "SecureData Analytics",
        "vendor_email": "payments@securedata.example.com",
        "description": "Data processing contract. PM: Jane Doe (SSN: 123-45-6789), Credit Card: 4111-1111-1111-1111, IP: 192.168.1.100, jane.doe@company.com, Phone: (415) 555-0198",
        "amount": 28750.00,
        "currency": "USD"
    },
    "policy_breach": {
        "vendor_name": "FraudCorp",
        "vendor_email": "pay@fraudcorp.example.com",
        "description": "Enterprise consulting engagement with premium support tier and dedicated account management. Contact: Bob Wilson, bob@fraudcorp.com",
        "amount": 75000.00,
        "currency": "USD"
    }
}


@router.post("/simulate/{scenario}")
async def simulate_scenario(scenario: str, session: Session = Depends(get_session)):
    """Run a pre-built Judge Simulator scenario."""
    if scenario not in SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario. Available: {list(SCENARIOS.keys())}"
        )

    data = SCENARIOS[scenario]
    req = CreateTransactionRequest(**data)
    return await create_transaction(req, session)
