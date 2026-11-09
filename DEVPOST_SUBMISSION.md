# Devpost Submission — AegisPay (`aegispay-agentic-commerce`)

> **Project Tagline:** Autonomous B2B Proof-of-Work Escrow, PII-Sanitized Compliance, and PayPal Settlement Engine for AI Agents.

---

## 💡 Inspiration

As autonomous AI agents evolve from code generation to enterprise procurement and commerce, a critical vulnerability has emerged: **how do AI agents exchange money safely without human micro-management?**

Current payment flows suffer from three critical bottlenecks:
1. **Blind Upfront Payments**: Paying vendors before deliverables are verified results in disputes and lost capital.
2. **PII Leaks into Financial Ledgers**: Agent prompts and metadata often contain sensitive personal data (names, SSNs, credit cards, emails, IP addresses), which inadvertently leak into PayPal order descriptions, violating GDPR, CCPA, and PCI-DSS.
3. **Lack of Non-Repudiation**: When an autonomous agent decides to release thousands of dollars, there is no cryptographic proof that the agent authorized the payment under specific policy constraints.

We built **AegisPay** to be the **autonomous financial escrow and compliance layer** for agentic commerce.

---

## 🛡️ What It Does

AegisPay is a production-grade autonomous escrow and settlement platform that bridges AI agents with the PayPal Developer Sandbox:

1. **Locks Escrow in PayPal Sandbox (`AUTHORIZE`)**: When an AI agent initiates a vendor contract, AegisPay calls PayPal Orders v2 with `intent="AUTHORIZE"`, placing a pre-authorization hold on funds without capturing them upfront.
2. **4-Node LangGraph Procurement Pipeline**:
   - **`pii_scan`**: Scans transaction metadata via Microsoft Presidio to detect and redact sensitive PII before transmission to PayPal.
   - **`policy_check`**: Enforces corporate financial caps ($50,000 max), screens against blocked entity lists, and verifies approved currencies.
   - **`agent_decision`**: Autonomously decides to `APPROVE`, `REJECT`, or `ESCALATE` for human-in-the-loop governance.
   - **`crypto_sign`**: Canonicalizes the approval payload and signs it using **Ed25519 (RFC 8032)** for non-repudiation.
3. **Settlement & Payouts (`CAPTURE` & `PAYOUTS`)**: Upon deliverable verification or operator release, AegisPay executes a PayPal Capture and triggers instant milestone contractor payments via PayPal Payouts v1.
4. **Dispute Defense Generator (`CUSTOMER.DISPUTE`)**: In case of vendor conflict, AegisPay automatically packages FEDEX tracking info, Ed25519 digital signatures, and agent reasoning logs for PayPal Disputes v1 evidence submission.
5. **Real-Time AG Grid Command Center**: Streams live telemetry over WebSockets into an enterprise AG Grid dashboard with status badges, Presidio diffs, and live agent reasoning traces.

---

## 🛠️ How We Built It

- **Backend**: Python 3.11+, FastAPI, SQLModel (SQLAlchemy + Pydantic), WebSockets, httpx async client.
- **Agent Intelligence**: **LangGraph** state machine orchestrating deterministic 4-node verification with live state streaming.
- **Privacy & Compliance**: **Microsoft Presidio** (`presidio-analyzer`, `presidio-anonymizer`) for automated PII entity scrubbing.
- **Cryptography**: **Ed25519** asymmetric digital signatures for tamper-proof transaction non-repudiation.
- **PayPal Integration**: Real REST calls against PayPal Sandbox (`https://api-m.sandbox.paypal.com`):
  - OAuth2 Client Credentials caching (`/v1/oauth2/token`)
  - Orders v2 (`intent="AUTHORIZE"`)
  - Authorizations Capture & Void (`/v2/payments/authorizations/{id}/*`)
  - Payouts v1 (`/v1/payments/payouts`)
  - Webhooks Receiver (`PAYMENT.AUTHORIZATION.CREATED`, `PAYMENT.CAPTURE.COMPLETED`, etc.)
- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide Icons, and **AG Grid React (`ag-grid-react`, `ag-grid-community`)** with pinned bottom totals and cell-flash animations.
- **APIMatic Integration**: Clean typed Pydantic adapter and full OpenAPI 3.1.0 specification with generated TypeScript SDK (`sdk-apimatic/`).

---

## 🏆 Sponsor Prize Track Alignment

### 1. PayPal Challenge — Real Developer Sandbox Integration
- Real asynchronous calls to PayPal Developer Sandbox APIs for Orders v2 (authorization hold), Capture, Void, Payouts v1, and Disputes v1.
- Complete lifecycle handling with webhook event ingestion.
- Built-in graceful mock fallback for zero-configuration testing.

### 2. Best Use of APIMatic ($1,000 + 6-Month Business Subscription)
- Clean typed adapter layer in `backend/app/paypal/apimatic_adapter.py`.
- Complete OpenAPI 3.1.0 specification in `openapi.json`.
- Pre-generated, typed TypeScript SDK in `sdk-apimatic/` matching APIMatic SDK architecture standards.

### 3. AG Grid — Enterprise Financial Command Center
- Live financial transaction ledger powered by AG Grid Community & React.
- Custom cell renderers for status badges, PII detection chips, and Ed25519 signatures.
- Pinned bottom aggregation row calculating live escrow totals.
- WebSocket-driven row updates with flash animations.

---

## 🧗 Challenges We Ran Into

1. **Ensuring GDPR Compliance on Payment Descriptions**: Payment metadata sent to PayPal cannot contain customer SSNs or credit card numbers. Integrating Microsoft Presidio into the LangGraph pipeline ensured that only sanitized strings ever reach PayPal servers.
2. **Deterministic Cryptographic Verification**: Canonicalizing JSON payloads across platforms required strict sorting of dictionary keys, compact separators, and UTF-8 encoding to guarantee identical SHA-256 hashes for Ed25519 verification.
3. **Resilient Local & Production Operation**: We implemented dual-mode architecture — full live PayPal Sandbox connectivity with automatic fallback for offline evaluation.

---

## 🌟 Accomplishments We're Proud Of

- **Zero-Trust Autonomous Escrow**: Agents cannot bypass the policy check or PII redaction layer.
- **Instant Non-Repudiation**: Every approval produces an immutable cryptographic signature.
- **Seamless Developer Experience**: 1-click Docker orchestration and 3 pre-built Judge Simulator scenarios.

---

## 🚀 What's Next for AegisPay

- Multi-agent negotiation: Buyer agents and seller agents agreeing on milestone deliverables dynamically.
- Integration with PayPal Vault and Recurring Subscriptions for agentic SaaS billing.
- Zero-Knowledge proofs for zero-data financial compliance audits.
