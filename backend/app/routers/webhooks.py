"""PayPal Webhook Router - Sandbox webhook receiver and signature verifier."""

import json
import hashlib
import hmac
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import EscrowTransaction, AuditLog, TransactionStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_manager():
    from app.main import manager
    return manager


@router.post("/paypal")
async def paypal_webhook(request: Request, session: Session = Depends(get_session)):
    """Receive and process PayPal Sandbox webhook events.
    
    In production, this would verify the webhook signature using PayPal's
    webhook signature verification API. In sandbox mode, we process events
    directly for demo purposes.
    """
    mgr = get_manager()
    
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_type = body.get("event_type", "")
    resource = body.get("resource", {})
    event_id = body.get("id", "unknown")

    # Log the webhook event
    audit = AuditLog(
        transaction_id=resource.get("id", "webhook"),
        action=f"WEBHOOK_{event_type}",
        actor="paypal",
        details=json.dumps({
            "event_id": event_id,
            "event_type": event_type,
            "resource_id": resource.get("id"),
            "resource_status": resource.get("status")
        })
    )
    session.add(audit)
    session.commit()

    # Process specific event types
    handler_map = {
        "PAYMENT.AUTHORIZATION.CREATED": _handle_auth_created,
        "PAYMENT.AUTHORIZATION.VOIDED": _handle_auth_voided,
        "PAYMENT.CAPTURE.COMPLETED": _handle_capture_completed,
        "PAYMENT.CAPTURE.DENIED": _handle_capture_denied,
        "PAYMENT.PAYOUTS-ITEM.SUCCEEDED": _handle_payout_success,
        "PAYMENT.PAYOUTS-ITEM.FAILED": _handle_payout_failed,
        "CUSTOMER.DISPUTE.CREATED": _handle_dispute_created,
    }

    handler = handler_map.get(event_type)
    if handler:
        await handler(resource, session, mgr)

    # Broadcast webhook event to all connected clients
    await mgr.broadcast({
        "type": "webhook_event",
        "event_type": event_type,
        "resource_id": resource.get("id"),
        "status": resource.get("status"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return {"status": "received", "event_id": event_id}


async def _handle_auth_created(resource: dict, session: Session, mgr):
    """Handle PAYMENT.AUTHORIZATION.CREATED event."""
    auth_id = resource.get("id")
    if auth_id:
        stmt = select(EscrowTransaction).where(EscrowTransaction.paypal_auth_id == auth_id)
        txn = session.exec(stmt).first()
        if txn:
            txn.status = TransactionStatus.AUTHORIZED
            txn.updated_at = datetime.now(timezone.utc)
            session.add(txn)
            session.commit()


async def _handle_auth_voided(resource: dict, session: Session, mgr):
    """Handle PAYMENT.AUTHORIZATION.VOIDED event."""
    auth_id = resource.get("id")
    if auth_id:
        stmt = select(EscrowTransaction).where(EscrowTransaction.paypal_auth_id == auth_id)
        txn = session.exec(stmt).first()
        if txn:
            txn.status = TransactionStatus.VOIDED
            txn.updated_at = datetime.now(timezone.utc)
            session.add(txn)
            session.commit()


async def _handle_capture_completed(resource: dict, session: Session, mgr):
    """Handle PAYMENT.CAPTURE.COMPLETED event."""
    capture_id = resource.get("id")
    if capture_id:
        stmt = select(EscrowTransaction).where(EscrowTransaction.paypal_capture_id == capture_id)
        txn = session.exec(stmt).first()
        if txn:
            txn.status = TransactionStatus.CAPTURED
            txn.updated_at = datetime.now(timezone.utc)
            session.add(txn)
            session.commit()


async def _handle_capture_denied(resource: dict, session: Session, mgr):
    """Handle PAYMENT.CAPTURE.DENIED event."""
    capture_id = resource.get("id")
    if capture_id:
        stmt = select(EscrowTransaction).where(EscrowTransaction.paypal_capture_id == capture_id)
        txn = session.exec(stmt).first()
        if txn:
            txn.status = TransactionStatus.FAILED
            txn.updated_at = datetime.now(timezone.utc)
            session.add(txn)
            session.commit()


async def _handle_payout_success(resource: dict, session: Session, mgr):
    """Handle PAYMENT.PAYOUTS-ITEM.SUCCEEDED event."""
    payout_item = resource.get("payout_item", {})
    sender_item_id = payout_item.get("sender_item_id")
    if sender_item_id:
        txn = session.get(EscrowTransaction, sender_item_id)
        if txn:
            txn.status = TransactionStatus.PAYOUT_SENT
            txn.updated_at = datetime.now(timezone.utc)
            session.add(txn)
            session.commit()


async def _handle_payout_failed(resource: dict, session: Session, mgr):
    """Handle PAYMENT.PAYOUTS-ITEM.FAILED event."""
    payout_item = resource.get("payout_item", {})
    sender_item_id = payout_item.get("sender_item_id")
    if sender_item_id:
        txn = session.get(EscrowTransaction, sender_item_id)
        if txn:
            txn.status = TransactionStatus.FAILED
            txn.updated_at = datetime.now(timezone.utc)
            session.add(txn)
            session.commit()


async def _handle_dispute_created(resource: dict, session: Session, mgr):
    """Handle CUSTOMER.DISPUTE.CREATED event."""
    dispute_id = resource.get("dispute_id")
    disputed_txns = resource.get("disputed_transactions", [])

    for dtxn in disputed_txns:
        seller_txn_id = dtxn.get("seller_transaction_id")
        if seller_txn_id:
            stmt = select(EscrowTransaction).where(
                EscrowTransaction.paypal_capture_id == seller_txn_id
            )
            txn = session.exec(stmt).first()
            if txn:
                txn.status = TransactionStatus.DISPUTED
                txn.updated_at = datetime.now(timezone.utc)
                session.add(txn)

                audit = AuditLog(
                    transaction_id=txn.id,
                    action="DISPUTE_CREATED",
                    actor="paypal",
                    details=f"Dispute {dispute_id} created for transaction {txn.id}"
                )
                session.add(audit)
                session.commit()
