"""AegisPay FastAPI application entry point with WebSocket support."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import transactions, webhooks


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages active WebSocket connections for real-time dashboard updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the active pool."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to every connected client."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send a JSON message to a single connected client."""
        await websocket.send_json(message)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize resources on startup and clean up on shutdown."""
    init_db()
    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AegisPay – Agentic Commerce Engine",
    description="AI-driven escrow payments with PII protection and dispute defense.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "healthy", "service": "aegispay-backend"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Persistent WebSocket connection for real-time event streaming."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
