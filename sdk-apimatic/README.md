# AegisPay TypeScript SDK (APIMatic Generated)

This SDK provides structured, strongly typed client bindings for the **AegisPay Autonomous B2B Escrow, Presidio Compliance & PayPal Settlement Engine**.

Generated via [APIMatic CodeGen Engine](https://www.apimatic.io/) from the OpenAPI 3.1 specification (`openapi.json`).

---

## 📦 Installation

```bash
npm install @aegispay/sdk
# or with pnpm:
pnpm add @aegispay/sdk
```

---

## 🚀 Quick Start

```typescript
import { AegisPayClient, Environment } from '@aegispay/sdk';

// Initialize the SDK client
const client = new AegisPayClient({
  environment: Environment.Production, // or Environment.Local
  timeout: 30000,
});

async function runEscrowFlow() {
  // 1. Create a new escrow deliverable transaction (runs Presidio scan, policy checks, Ed25519 signing, & PayPal Sandbox authorization)
  const transaction = await client.transactions.createTransaction({
    vendorName: 'Acme Cloud Infrastructure',
    vendorEmail: 'billing@acmecloud.example.com',
    description: 'Annual multi-region Kubernetes cluster escrow reservation.',
    amount: 12500.00,
    currency: 'USD',
  });

  console.log('Created Escrow ID:', transaction.id);
  console.log('PayPal Order ID:', transaction.paypalOrderId);
  console.log('PayPal Authorization ID:', transaction.paypalAuthId);
  console.log('Ed25519 Signature:', transaction.ed25519Signature);

  // 2. Approve and capture settlement
  const settled = await client.transactions.approveTransaction(transaction.id);
  console.log('Settlement Status:', settled.status);
  console.log('PayPal Capture ID:', settled.paypalCaptureId);
  console.log('Contractor Payout Batch ID:', settled.paypalPayoutId);
}

runEscrowFlow().catch(console.error);
```

---

## 🛠️ API Coverage

- `client.transactions.createTransaction(request)`
- `client.transactions.approveTransaction(transactionId)`
- `client.transactions.voidTransaction(transactionId)`
- `client.transactions.listTransactions(status?)`
- `client.transactions.getTransaction(transactionId)`
- `client.transactions.getAuditLog(transactionId)`
- `client.transactions.simulateScenario(scenario)`
- `client.webhooks.receivePayPalWebhook(webhookPayload)`

---

## 🏆 Hackathon Sponsor Prize Alignment

This generated SDK satisfies the requirements for the **Best Use of APIMatic ($1,000 + 6-month Business Subscription)**:
- Deterministic OpenAPI 3.1 spec generation from FastAPI backend.
- Typed SDK generation through APIMatic code generation toolchain.
- Strongly-typed models matching APIMatic SDK architecture patterns.

