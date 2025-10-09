"""
Salesbrain Backend API - Main Application
Multi-Tenant B2B Sales Orchestrator
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db_pools, close_db_pools
from app.api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting Salesbrain Backend API...")
    await init_db_pools()
    print("✅ Application ready!")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_db_pools()
    print("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Salesbrain Backend API",
    description="Multi-Tenant B2B Sales Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Salesbrain Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
