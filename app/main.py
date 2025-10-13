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
from app.api.auth import router as auth_router
from app.api.instantly import router as instantly_router
from app.api.admin import router as admin_router
from app.api.user_assignments import router as user_assignments_router
from app.api.onboarding_links import router as onboarding_links_router
from app.integrations.instantly.webhooks import router as instantly_webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db_pools()
    yield
    # Shutdown
    await close_db_pools()


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
    allow_headers=["*"]
)

# Include routers
app.include_router(health_router, tags=["Health"])
# app.include_router(auth_router)  # Temporarily disabled for testing

# Admin Dashboard routers
app.include_router(admin_router)  # Admin Dashboard API
app.include_router(user_assignments_router)  # User Assignment API
app.include_router(onboarding_links_router)  # Onboarding Links API

# Instantly Integration routers
app.include_router(instantly_router)  # API endpoints
app.include_router(instantly_webhooks_router)  # Webhook endpoints


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Salesbrain Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
