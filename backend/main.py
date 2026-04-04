# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL - FINANCIAL FRAUD INTELLIGENCE PLATFORM
# Main FastAPI Application Entry Point
# ═══════════════════════════════════════════════════════════════════════════
#
#   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
#   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
#   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
#   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
#   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
#   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
#
#   Real-Time • Adaptive • Explainable
#
# ═══════════════════════════════════════════════════════════════════════════

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from utils.config import settings
from utils.database import init_db
from api.routes import router as api_router
from api.websocket import router as ws_router


# ═══════════════════════════════════════════════════════════════════════════
# APPLICATION LIFESPAN
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # ─────────────────────────────────────────────────────────────────────────
    # STARTUP
    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 70)
    print("SENTINEL - Financial Fraud Intelligence Platform")
    print("=" * 70)
    print(f"Version: {settings.APP_VERSION}")
    print(f"Mode: {'MOCK' if settings.USE_MOCK_ML else 'PRODUCTION'}")
    print(f"Debug: {settings.DEBUG}")
    print("=" * 70)
    
    # Initialize database
    try:
        await init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization skipped (using in-memory): {e}")
    
    print(f"Server starting on http://{settings.HOST}:{settings.PORT}")
    print("API Docs: http://localhost:8000/docs")
    print("WebSocket: ws://localhost:8000/ws/transactions")
    print("=" * 70)
    
    yield
    
    # ─────────────────────────────────────────────────────────────────────────
    # SHUTDOWN
    # ─────────────────────────────────────────────────────────────────────────
    print("Shutting down SENTINEL...")
    print("Goodbye!")


# ═══════════════════════════════════════════════════════════════════════════
# APPLICATION INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    description="""
# SENTINEL - Financial Fraud Intelligence Platform

Real-time AI-powered fraud detection and prevention system.

## Features

- **Multi-Modal AI Detection**: Combines tabular, sequential, and graph neural networks
- **Real-Time Streaming**: WebSocket-based live transaction monitoring
- **Explainable AI**: SHAP-based feature attribution and natural language reports
- **Attack Simulation**: Test the system with realistic fraud scenarios

## API Endpoints

### REST API
- `GET /api/v1/transactions/recent` - Get recent transactions
- `GET /api/v1/alerts/active` - Get active fraud alerts
- `GET /api/v1/stats/overview` - Dashboard statistics
- `POST /api/v1/simulator/inject` - Inject attack scenario

### WebSocket
- `ws://host/ws/transactions` - Real-time transaction stream
- `ws://host/ws/alerts` - Fraud alert stream
- `ws://host/ws/all` - All message types

## Integration Contract

See `/api/v1/health` for system status and version information.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ═══════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════

# CORS Middleware - Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

# Include REST API routes
app.include_router(api_router)

# Include WebSocket routes
app.include_router(ws_router)


# ═══════════════════════════════════════════════════════════════════════════
# ROOT ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "status": "operational",
        "mode": "mock" if settings.USE_MOCK_ML else "production",
        "endpoints": {
            "api": "/api/v1",
            "docs": "/docs",
            "health": "/api/v1/health",
            "websocket": "/ws/transactions"
        },
        "timestamp": datetime.now().isoformat() + "Z"
    }


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info",
    )
