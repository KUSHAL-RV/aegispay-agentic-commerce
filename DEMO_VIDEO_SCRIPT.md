# AegisPay — 3-Minute Video Demo Script

> **Target Duration:** Exactly 2:50 – 3:00  
> **Platform:** YouTube (Public or Unlisted for Devpost submission)  
> **Setup Before Recording:**  
> - Browser Tab 1: `http://localhost:3000` (AegisPay Command Center)  
> - Browser Tab 2: [sandbox.paypal.com](https://www.sandbox.paypal.com) (Logged in to PayPal Sandbox Merchant Account)  
> - Browser Tab 3: [github.com/KUSHAL-RV/aegispay-agentic-commerce](https://github.com/KUSHAL-RV/aegispay-agentic-commerce)  

---

## ⏱️ Timeline & Script

### Part 1: The Problem & Solution Hook (0:00 – 0:35)
- **Screen:** Show AegisPay Command Center at `http://localhost:3000` with dark theme, live WebSocket pulsing badge, and AG Grid ledger.
- **Voiceover:**
  > *"Autonomous AI agents are beginning to make real-world procurement decisions. But there’s a multi-billion dollar problem: agents cannot safely exchange funds. Paying upfront risks capital loss on faulty deliverables; prompts inadvertently leak customer PII into payment logs violating GDPR; and there is zero cryptographic proof of which agent authorized a payment.*
  > 
  > *Welcome to **AegisPay** — an Autonomous B2B Proof-of-Work Escrow, PII-Sanitized Compliance, and PayPal Settlement Engine built for the PayPal AI Hackathon."*

---

### Part 2: Scenario 1 — Happy Path Escrow & PayPal Sandbox Proof (0:35 – 1:20)
- **Screen:** Click the **Scenario 1: Happy Path Escrow** button on the **Judge Simulator Bar**.
- **Action:** Point mouse to the **Live Agent Trace** panel on the right as the WebSocket events stream in:
  `pii_scan` ➔ `policy_check` ➔ `agent_decision` ➔ `crypto_sign`.
- **Voiceover:**
  > *"Let's trigger Scenario 1: A $12,500 cloud renewal deliverable. Watch the live agent trace stream via WebSockets in real time. Our 4-node LangGraph pipeline scans the deliverable metadata with Microsoft Presidio, validates against our $50,000 corporate policy cap, approves the transaction, and cryptographically signs it with Ed25519."*
- **Action:** Click the new row in the AG Grid ledger to slide open the **AuditDetailDrawer**.
- **Screen:** Click the **PayPal Sandbox** tab inside the drawer, highlighting the real **PayPal Order ID** and **Authorization ID**.
- **Action (Crucial Tie-Breaker):** Switch to Browser Tab 2 ([sandbox.paypal.com](https://www.sandbox.paypal.com)) and refresh the Activity page, showing the $12,500 pending authorization hold.
- **Voiceover:**
  > *"Notice the escrow status is now `AUTHORIZED`. AegisPay locked the funds in PayPal Developer Sandbox using Orders v2 with `intent=AUTHORIZE`. Here on sandbox.paypal.com, you can see the real $12,500 authorization hold held securely in escrow on PayPal's servers — not a penny is released until deliverables are verified."*

---

### Part 3: Scenario 2 — Presidio PII Scrubbing (1:20 – 1:55)
- **Screen:** Switch back to `http://localhost:3000`. Click **Scenario 2: PII Compliance Scrub** on the Judge Simulator Bar.
- **Action:** In the AG Grid ledger, click the newly generated row. Switch to the **Presidio PII Diff** tab in the drawer.
- **Voiceover:**
  > *"Now let's test compliance. In Scenario 2, an agent submits a contract containing sensitive PII: an employee's Social Security Number, phone number, and internal IP address.*
  > 
  > *Look at the Presidio PII Diff tab: AegisPay’s Presidio Guard automatically intercepted the payload, identified the 3 sensitive entities, and redacted them into clean tokens BEFORE dispatching to PayPal Orders v2. This guarantees zero GDPR or PCI-DSS leakage into PayPal financial logs."*

---

### Part 4: Human-in-the-Loop Settlement & Payouts (1:55 – 2:30)
- **Screen:** Inside the drawer for the authorized transaction, click the green **Capture & Settle** button.
- **Action:** Watch the status update to `PAYOUT_SENT` and show the **PayPal Capture ID** and **Payout Batch ID**.
- **Screen:** Switch to the **Ed25519 Proof** tab to display the Base64 signature and verification badge.
- **Voiceover:**
  > *"Once the software deliverable is approved, our Human-in-the-Loop governance allows instantaneous settlement. Clicking 'Capture & Settle' triggers a PayPal Capture on the authorization and initiates a PayPal Payouts v1 transaction to the contractor.*
  > 
  > *Under the Ed25519 Proof tab, every decision carries an asymmetric cryptographic signature generated from the agent keypair, ensuring complete non-repudiation and auditability."*

---

### Part 5: Sponsor Prizes, APIMatic SDK & Wrap-Up (2:30 – 3:00)
- **Screen:** Briefly show the terminal / repo files: `sdk-apimatic/`, `openapi.json`, and `render.yaml`.
- **Voiceover:**
  > *"For sponsor prize alignment:
  > - **PayPal**: Real sandbox calls for Orders v2 Authorize, Capture, Void, and Payouts v1.
  > - **APIMatic**: A fully typed adapter and pre-generated TypeScript SDK in `sdk-apimatic/` built from our OpenAPI 3.1 specification.
  > - **AG Grid**: Enterprise data grid with WebSocket row updates, custom cell renderers, and pinned summary totals.
  > 
  > AegisPay brings enterprise-grade escrow, compliance, and trust to the agentic economy. Thank you!"*

---

## 💡 Quick Tips for Recording
1. **Resolution:** 1080p (1920x1080) at 60fps.
2. **Audio:** Use a clean microphone or headset; speak at a brisk, energetic pace.
3. **Cursor:** Enable mouse click highlighter in OBS / Loom / Screen Studio.
