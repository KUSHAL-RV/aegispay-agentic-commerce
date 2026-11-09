"""LangGraph Procurement Verification Workflow - 4-node agent graph with real-time broadcasting."""

import json
from typing import TypedDict, Optional, Literal, Any, Callable, Awaitable, Dict, Tuple
from datetime import datetime, timezone

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    END = "__end__"

    class FallbackCompiledGraph:
        """Deterministic sequential executor fallback matching LangGraph's API."""
        def __init__(self, nodes: Dict[str, Callable], entry_point: str, edges: Dict[str, str], conditional_edges: Dict[str, Tuple[Callable, Dict[str, str]]]):
            self.nodes = nodes
            self.entry_point = entry_point
            self.edges = edges
            self.conditional_edges = conditional_edges

        def stream(self, initial_state: dict):
            state = dict(initial_state)
            curr = self.entry_point
            visited = 0
            while curr and curr != END and visited < 20:
                visited += 1
                node_fn = self.nodes.get(curr)
                if not node_fn:
                    break
                state = node_fn(state)
                yield {curr: state}

                if curr in self.conditional_edges:
                    routing_fn, mapping = self.conditional_edges[curr]
                    route = routing_fn(state)
                    next_node = mapping.get(route, END)
                    if next_node == END:
                        break
                    curr = next_node
                elif curr in self.edges:
                    next_node = self.edges[curr]
                    if next_node == END:
                        break
                    curr = next_node
                else:
                    break

    class FallbackStateGraph:
        """Fallback StateGraph matching LangGraph builder."""
        def __init__(self, state_schema):
            self.state_schema = state_schema
            self.nodes: Dict[str, Callable] = {}
            self.entry_point: Optional[str] = None
            self.edges: Dict[str, str] = {}
            self.conditional_edges: Dict[str, Tuple[Callable, Dict[str, str]]] = {}

        def add_node(self, name: str, fn: Callable):
            self.nodes[name] = fn

        def set_entry_point(self, name: str):
            self.entry_point = name

        def add_edge(self, from_node: str, to_node: str):
            self.edges[from_node] = to_node

        def add_conditional_edges(self, from_node: str, routing_fn: Callable, mapping: Dict[str, str]):
            self.conditional_edges[from_node] = (routing_fn, mapping)

        def compile(self):
            return FallbackCompiledGraph(self.nodes, self.entry_point or "pii_scan", self.edges, self.conditional_edges)

    StateGraph = FallbackStateGraph

from app.security.presidio_guard import get_presidio_guard
from app.security.crypto_signer import get_crypto_signer


class ProcurementState(TypedDict):
    """State flowing through the procurement verification graph."""
    transaction_id: str
    vendor_name: str
    vendor_email: str
    description: str
    amount: float
    currency: str
    # PII scan results
    pii_clean_description: Optional[str]
    pii_entities: Optional[list]
    pii_detected: Optional[bool]
    # Policy check
    policy_passed: Optional[bool]
    policy_flags: Optional[list]
    # Agent decision
    decision: Optional[str]  # "APPROVE", "REJECT", "ESCALATE"
    reasoning: Optional[str]
    # Crypto signature
    signature: Optional[str]
    public_key: Optional[str]
    payload_hash: Optional[str]
    # Metadata
    current_node: Optional[str]
    error: Optional[str]


# Maximum transaction value the agent can auto-approve
POLICY_AMOUNT_CAP = 50_000.00
BLOCKED_VENDORS = ["fraudcorp", "scam-services"]


def pii_scan_node(state: ProcurementState) -> ProcurementState:
    """Node 1: Scan and redact PII from transaction metadata."""
    guard = get_presidio_guard()
    result = guard.scan_and_redact(state["description"])

    return {
        **state,
        "pii_clean_description": result.redacted_text,
        "pii_entities": result.entities_found,
        "pii_detected": result.pii_detected,
        "current_node": "pii_scan"
    }


def policy_check_node(state: ProcurementState) -> ProcurementState:
    """Node 2: Validate against corporate procurement policies."""
    flags = []

    # Amount cap check
    if state["amount"] > POLICY_AMOUNT_CAP:
        flags.append(f"Amount ${state['amount']:,.2f} exceeds cap of ${POLICY_AMOUNT_CAP:,.2f}")

    # Vendor blocklist
    if state["vendor_name"].lower() in BLOCKED_VENDORS:
        flags.append(f"Vendor '{state['vendor_name']}' is on the blocklist")

    # Currency check
    if state["currency"] not in ("USD", "EUR", "GBP", "CAD"):
        flags.append(f"Currency '{state['currency']}' is not in approved list")

    # Minimum amount
    if state["amount"] <= 0:
        flags.append("Transaction amount must be positive")

    # PII was detected - flag for review
    if state.get("pii_detected"):
        flags.append("PII detected in description - auto-redacted before PayPal submission")

    return {
        **state,
        "policy_passed": len([f for f in flags if "blocklist" in f or "cap" in f.lower() or "positive" in f]) == 0,
        "policy_flags": flags,
        "current_node": "policy_check"
    }


def agent_decision_node(state: ProcurementState) -> ProcurementState:
    """Node 3: AI agent makes approve/reject/escalate decision."""
    if not state.get("policy_passed", False):
        hard_flags = [f for f in (state.get("policy_flags") or [])
                      if "blocklist" in f or "positive" in f]
        if hard_flags:
            decision = "REJECT"
            reasoning = f"Rejected due to policy violations: {'; '.join(hard_flags)}"
        else:
            decision = "ESCALATE"
            reasoning = f"Escalated for human review due to: {'; '.join(state.get('policy_flags', []))}"
    else:
        decision = "APPROVE"
        reasons = []
        reasons.append(f"Amount ${state['amount']:,.2f} within policy cap")
        reasons.append(f"Vendor '{state['vendor_name']}' passed blocklist check")
        if state.get("pii_detected"):
            reasons.append("PII auto-redacted for compliance")
        reasons.append("All procurement policies satisfied")
        reasoning = "; ".join(reasons)

    return {
        **state,
        "decision": decision,
        "reasoning": reasoning,
        "current_node": "agent_decision"
    }


def crypto_sign_node(state: ProcurementState) -> ProcurementState:
    """Node 4: Cryptographically sign the approval with Ed25519."""
    if state.get("decision") != "APPROVE":
        return {
            **state,
            "current_node": "crypto_sign",
            "signature": None,
            "public_key": None,
            "payload_hash": None
        }

    signer = get_crypto_signer()
    result = signer.sign_approval(
        transaction_id=state["transaction_id"],
        amount=state["amount"],
        vendor=state["vendor_name"],
        agent_decision=state["decision"],
        reasoning=state.get("reasoning", "")
    )

    return {
        **state,
        "signature": result.signature_b64,
        "public_key": result.public_key_b64,
        "payload_hash": result.payload_hash,
        "current_node": "crypto_sign"
    }


def should_sign(state: ProcurementState) -> str:
    """Conditional edge: only sign if approved."""
    if state.get("decision") == "APPROVE":
        return "crypto_sign"
    return "end"


def build_procurement_graph() -> StateGraph:
    """Build the 4-node LangGraph procurement verification workflow."""
    workflow = StateGraph(ProcurementState)

    # Add nodes
    workflow.add_node("pii_scan", pii_scan_node)
    workflow.add_node("policy_check", policy_check_node)
    workflow.add_node("agent_decision", agent_decision_node)
    workflow.add_node("crypto_sign", crypto_sign_node)

    # Define edges
    workflow.set_entry_point("pii_scan")
    workflow.add_edge("pii_scan", "policy_check")
    workflow.add_edge("policy_check", "agent_decision")
    workflow.add_conditional_edges("agent_decision", should_sign, {
        "crypto_sign": "crypto_sign",
        "end": END
    })
    workflow.add_edge("crypto_sign", END)

    return workflow.compile()


# Compiled graph singleton
_graph = None

def get_procurement_graph():
    global _graph
    if _graph is None:
        _graph = build_procurement_graph()
    return _graph


async def run_procurement_pipeline(
    transaction_id: str,
    vendor_name: str,
    vendor_email: str,
    description: str,
    amount: float,
    currency: str = "USD",
    broadcast_fn: Optional[Callable[[dict], Awaitable[None]]] = None
) -> ProcurementState:
    """Run the full procurement verification pipeline with optional broadcasting."""
    graph = get_procurement_graph()

    initial_state: ProcurementState = {
        "transaction_id": transaction_id,
        "vendor_name": vendor_name,
        "vendor_email": vendor_email,
        "description": description,
        "amount": amount,
        "currency": currency,
        "pii_clean_description": None,
        "pii_entities": None,
        "pii_detected": None,
        "policy_passed": None,
        "policy_flags": None,
        "decision": None,
        "reasoning": None,
        "signature": None,
        "public_key": None,
        "payload_hash": None,
        "current_node": None,
        "error": None,
    }

    final_state = None

    try:
        for output in graph.stream(initial_state):
            for node_name, node_state in output.items():
                final_state = node_state
                if broadcast_fn:
                    await broadcast_fn({
                        "type": "agent_trace",
                        "node": node_name,
                        "transaction_id": transaction_id,
                        "state": {
                            "current_node": node_name,
                            "decision": node_state.get("decision"),
                            "reasoning": node_state.get("reasoning"),
                            "pii_detected": node_state.get("pii_detected"),
                            "policy_passed": node_state.get("policy_passed"),
                            "policy_flags": node_state.get("policy_flags"),
                            "signature": node_state.get("signature", "")[:32] + "..." if node_state.get("signature") else None,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
    except Exception as e:
        if final_state:
            final_state["error"] = str(e)
        else:
            initial_state["error"] = str(e)
            final_state = initial_state

    return final_state
