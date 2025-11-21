"""Main FastAPI application."""

from dotenv import load_dotenv
import os

# Load .env file from the root directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import socketio

from core.database import init_db, close_db
from api.routes import auth, sessions, agents, knowledge, admin, health


def register_tools():
    """Register all available tools in the tool registry."""
    from tools.registry import tool_registry
    from tools.calculator import CalculatorTool
    from tools.current_time import CurrentTimeTool
    from tools.notes import CreateNoteTool, ListNotesTool

    # Register basic tools
    tools_to_register = [
        CalculatorTool(),
        CurrentTimeTool(),
        CreateNoteTool(),
        ListNotesTool(),
    ]

    # Register Azure tools (Phase 1 + 2)
    try:
        from tools.azure import (
            CreateUserTool,
            GetUserTool,
            ResetPasswordTool,
            CreateGroupTool,
            GetGroupTool,
            AddGroupMemberTool,
            CreateAppRegistrationTool,
            GetAppRegistrationTool,
            AddRedirectUriTool,
            CreateClientSecretTool,
        )

        azure_tools = [
            # User Management
            CreateUserTool(),
            GetUserTool(),
            ResetPasswordTool(),
            # Group Management
            CreateGroupTool(),
            GetGroupTool(),
            AddGroupMemberTool(),
            # App Registration Management (Phase 2)
            CreateAppRegistrationTool(),
            GetAppRegistrationTool(),
            AddRedirectUriTool(),
            CreateClientSecretTool(),
        ]

        tools_to_register.extend(azure_tools)
        print(f"✓ Azure tools loaded: {len(azure_tools)} tools")

    except ImportError as e:
        print(f"⚠ Azure tools not available (missing dependencies): {e}")
        print("  To enable Azure tools, install: pip install azure-identity msgraph-sdk")

    for tool in tools_to_register:
        try:
            tool_registry.register(tool)
            print(f"✓ Registered tool: {tool.name}")
        except ValueError as e:
            print(f"⚠ Tool registration warning: {e}")

    print(f"✓ Total tools registered: {len(tool_registry.list_tools())}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Agent Platform...")
    await init_db()
    register_tools()
    print("✓ Application startup complete")
    yield
    # Shutdown
    print("👋 Shutting down...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Agent-as-a-Service Platform",
    description="Multi-tenant platform for building and deploying AI agents",
    version="1.0.0",
    lifespan=lifespan,
)



# CORS middleware for FastAPI routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
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
