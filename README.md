# AegisPay — Agentic Commerce Platform

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)
![PayPal](https://img.shields.io/badge/PayPal-Sandbox-00457C?logo=paypal&logoColor=white)
![AG Grid](https://img.shields.io/badge/AG%20Grid-Enterprise-FF6600?logo=data:image/svg+xml;base64,&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**AegisPay is an AI-powered agentic commerce platform that orchestrates PayPal escrow transactions through an autonomous LangGraph agent, with real-time PII protection, cryptographic audit trails, and a live enterprise data grid — purpose-built to showcase the future of agent-driven payments.**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 15)                        │
│  ┌───────────────┐  ┌───────────────────┐  ┌────────────────────┐  │
│  │  AG Grid Pro   │  │  Transaction Feed │  │  Agent Chat Panel  │  │
│  │  Data Dashboard│  │  (Real-Time WS)   │  │  (LangGraph Viz)   │  │
│  └───────┬───────┘  └────────┬──────────┘  └─────────┬──────────┘  │
│          └──────────────┬────┘                        │             │
└─────────────────────────┼────────────────────────────┼─────────────┘
                          │ WebSocket + REST            │
                          ▼                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Uvicorn)                      │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐  │
│  │  PayPal Adapter  │  │  LangGraph Agent │  │  Presidio PII     │  │
│  │  (Sandbox API)   │  │  (State Machine) │  │  Guard (Scrubber) │  │
│  └────────┬────────┘  └────────┬────────┘  └─────────┬──────────┘  │
│           │                    │                      │             │
│  ┌────────▼────────────────────▼──────────────────────▼──────────┐  │
│  │                   Transaction Engine                          │  │
│  │         Ed25519 Crypto Signer · Audit Logger                  │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                          │                                         │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │              SQLite (dev) / PostgreSQL (prod)                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   PayPal Sandbox API  │
              │   (api-m.sandbox)     │
              └───────────────────────┘
```

---

## ✨ Features

- **🔐 PayPal Escrow Orchestration** — Full lifecycle management of PayPal sandbox transactions: create, authorize, capture, void, and refund with real API calls and webhook-ready architecture.
- **🤖 LangGraph AI Agent** — Autonomous transaction agent built on LangGraph that reasons over payment scenarios, decides approval/rejection, and explains its decisions with full state-graph traceability.
- **🛡️ Presidio PII Scrubbing** — Microsoft Presidio-powered pipeline that automatically detects and redacts PII (emails, SSNs, credit cards, phone numbers) from all agent logs and transaction metadata before storage.
- **🔏 Ed25519 Cryptographic Signing** — Every transaction decision is signed with Ed25519 keys, producing a tamper-evident audit trail that can be independently verified.
- **📊 AG Grid Enterprise Dashboard** — Real-time transaction monitoring with AG Grid's server-side row model, column filtering, infinite scroll, and live WebSocket-driven row updates.
- **⚖️ Judge Simulator** — Built-in scenario simulator that replays realistic payment disputes (chargebacks, fraud flags, partial captures) through the agent pipeline for live demo and testing.

---

## 🛠️ Tech Stack

| Layer        | Technology                        | Purpose                              |
|--------------|-----------------------------------|--------------------------------------|
| Frontend     | Next.js 15, React 19, TypeScript  | Server-rendered dashboard UI         |
| Data Grid    | AG Grid (Enterprise)              | High-performance transaction table   |
| Styling      | Tailwind CSS 4                    | Utility-first styling                |
| Backend      | FastAPI, Uvicorn                  | Async REST + WebSocket API           |
| AI Agent     | LangGraph, LangChain              | Stateful agent orchestration         |
| PII Guard    | Microsoft Presidio                | PII detection & anonymization        |
| Crypto       | Ed25519 (PyNaCl)                  | Transaction signing & verification   |
| Payments     | PayPal REST SDK (Sandbox)         | Order creation, capture, refund      |
| Database     | SQLAlchemy + SQLite / PostgreSQL  | Async ORM with migration support     |
| Deployment   | Docker Compose, Render            | Container orchestration & cloud IaC  |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+ with pnpm
- PayPal Developer Sandbox account ([developer.paypal.com](https://developer.paypal.com))

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/aegispay-agentic-commerce.git
cd aegispay-agentic-commerce
cp .env.example .env
# Fill in your PayPal sandbox credentials and LLM API key in .env
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live at **http://localhost:8000** with interactive docs at **/docs**.

### 3. Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

The dashboard will be live at **http://localhost:3000**.

### 4. Docker Compose (Alternative)

```bash
docker compose up --build
```

This starts the backend, frontend, and PostgreSQL database together. The frontend is available at **http://localhost:3000** and the backend API at **http://localhost:8000**.

---

## 🔧 Environment Variables

| Variable                 | Required | Default                              | Description                            |
|--------------------------|----------|--------------------------------------|----------------------------------------|
| `PAYPAL_CLIENT_ID`       | Yes      | —                                    | PayPal sandbox app client ID           |
| `PAYPAL_CLIENT_SECRET`   | Yes      | —                                    | PayPal sandbox app client secret       |
| `PAYPAL_MODE`            | No       | `sandbox`                            | PayPal environment mode                |
| `PAYPAL_BASE_URL`        | No       | `https://api-m.sandbox.paypal.com`   | PayPal API base URL                    |
| `LLM_API_KEY`            | Yes      | —                                    | API key for LLM provider              |
| `LLM_MODEL`              | No       | `gpt-4o-mini`                        | Model identifier for the agent         |
| `DATABASE_URL`           | No       | `sqlite:///./aegispay.db`            | Database connection string             |
| `ED25519_PRIVATE_KEY`    | No       | Auto-generated                       | Base64-encoded Ed25519 private key     |
| `ED25519_PUBLIC_KEY`     | No       | Auto-generated                       | Base64-encoded Ed25519 public key      |
| `NEXT_PUBLIC_API_URL`    | No       | `http://localhost:8000`              | Backend API URL for the frontend       |
| `NEXT_PUBLIC_WS_URL`     | No       | `ws://localhost:8000/ws`             | WebSocket URL for real-time updates    |

---

## 📡 API Endpoints

| Method | Endpoint                                  | Description                                      |
|--------|-------------------------------------------|--------------------------------------------------|
| POST   | `/api/transactions/create`                | Create a new escrow transaction via PayPal        |
| POST   | `/api/transactions/{id}/approve`          | Approve and capture a pending transaction         |
| POST   | `/api/transactions/{id}/void`             | Void/cancel a pending transaction                 |
| POST   | `/api/transactions/simulate/{scenario}`   | Run Judge Simulator scenario (`happy_path`, `pii_heavy`, `policy_breach`) |
| GET    | `/api/transactions/{id}`                  | Retrieve single escrow transaction by ID         |
| GET    | `/api/transactions/{id}/audit`            | Fetch immutable audit trail for a transaction    |
| POST   | `/api/webhooks/paypal`                    | Ingest PayPal Sandbox webhooks (Auth, Capture, Payouts) |
| GET    | `/api/transactions`                       | List all transactions with filtering & pagination |
| WS     | `/ws`                                     | Real-time WebSocket feed for transaction updates  |

---

## 🏆 Sponsor Prize Alignment

### PayPal Challenge — Real Sandbox Integration
AegisPay performs **real PayPal Sandbox API calls** for order creation, authorization, capture, void, and refund. Every transaction is executed against PayPal's sandbox environment with full request/response logging, demonstrating production-grade payment orchestration driven by an autonomous AI agent.

### APIMatic — Typed Adapter Layer
The PayPal integration is built through a **clean, typed adapter layer** that wraps PayPal's REST API with Pydantic models, structured error handling, and retry logic — showcasing how SDK-quality API consumption patterns improve reliability and developer experience.

### AG Grid — Enterprise Data Grid
The transaction dashboard leverages **AG Grid's enterprise features** including server-side row model for handling large datasets, real-time row updates via WebSocket, column-level filtering and sorting, custom cell renderers for transaction status badges, and infinite scroll pagination.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ☕ and autonomy for the future of agentic commerce.
</p>
