"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import socketio

from core.database import init_db, close_db
from api.routes import auth, sessions, agents, knowledge, admin, health


class CORSFixMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure CORS headers are always present on all responses."""

    async def dispatch(self, request: Request, call_next):
        # Get origin from request
        origin = request.headers.get("origin", "*")

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            from starlette.responses import Response
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response

        # Process normal request
        response = await call_next(request)

        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Agent-as-a-Service Platform",
    description="Multi-tenant platform for building and deploying AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS fix middleware FIRST to ensure it wraps everything
app.add_middleware(CORSFixMiddleware)

# CORS middleware for FastAPI routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Allow all origins (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Socket.IO setup with comprehensive CORS
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Allow all (remove in production)
    ],
    cors_credentials=True,
    logger=True,
    engineio_logger=True,
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
    socketio_path="/socket.io",
)


# Wrap socket_app with ASGI middleware to ensure CORS on all responses
class ASGICORSMiddleware:
    """ASGI middleware to add CORS headers to all responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get origin from headers
        origin = "*"
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"origin":
                origin = header_value.decode("utf-8")
                break

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                # Add CORS headers
                headers.append((b"access-control-allow-origin", origin.encode()))
                headers.append((b"access-control-allow-credentials", b"true"))
                headers.append((b"access-control-allow-methods", b"GET, POST, PUT, DELETE, PATCH, OPTIONS"))
                headers.append((b"access-control-allow-headers", b"*"))
                headers.append((b"access-control-expose-headers", b"*"))

                message["headers"] = headers

            await send(message)

        # Handle OPTIONS preflight
        if scope["method"] == "OPTIONS":
            await send_with_cors({
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-length", b"0"]],
            })
            await send({"type": "http.response.body", "body": b""})
            return

        await self.app(scope, receive, send_with_cors)


# Apply ASGI CORS middleware to socket_app
socket_app = ASGICORSMiddleware(socket_app)

# Import WebSocket handlers (this registers the events)
from ws_handlers.handler import register_handlers
register_handlers(sio)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(health.router, prefix="/api", tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agent-as-a-Service Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Export the socket_app for uvicorn
# Run with: uvicorn api.main:socket_app --reload
