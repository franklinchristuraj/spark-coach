"""
SPARK Coach API - Main Application
FastAPI entry point with health check and MCP test endpoints
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os as _os

from config import settings
from auth import verify_token
from routes.auth import router as auth_router
from mcp_client import mcp_client
from routes.briefing import router as briefing_router
from routes.quiz import router as quiz_router
from routes.nudges import router as nudges_router
from routes.voice import router as voice_router
from routes.stats import router as stats_router
from models.database import init_db
from scheduler import setup_scheduler, start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"MCP Server URL: {settings.MCP_SERVER_URL}")

    # Initialize database
    db_initialized = init_db()
    if db_initialized:
        logger.info("✓ Database initialized")
    else:
        logger.warning("⚠ Database initialization failed")

    # Check MCP server connectivity
    mcp_healthy = await mcp_client.health_check()
    if mcp_healthy:
        logger.info("✓ MCP server is reachable")
    else:
        logger.warning("⚠ MCP server is not reachable - some features may not work")

    # Start scheduler for automated jobs
    setup_scheduler()
    start_scheduler()
    logger.info("✓ Scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down SPARK Coach API")
    stop_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Learning & Accountability System for SPARK PKM",
    lifespan=lifespan
)

# Configure CORS
_allowed_origins = _os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(briefing_router)
app.include_router(quiz_router)
app.include_router(nudges_router)
app.include_router(voice_router)
app.include_router(stats_router)


# ─────────────────────────────────────────────────────────────────────────────
# Health & System Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """
    Health check endpoint - no authentication required
    Returns 200 if the API is running
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI Learning & Accountability System",
        "docs": "/docs",
        "health": "/health"
    }


# ─────────────────────────────────────────────────────────────────────────────
# MCP Test Endpoints (Day 1)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/test-mcp")
async def test_mcp_connection(_: str = Depends(verify_token)):
    """
    Test MCP server connectivity by reading a note from the vault
    Requires authentication

    Returns:
        Sample note from the vault or connection status
    """
    try:
        # First check if MCP server is reachable
        is_healthy = await mcp_client.health_check()

        if not is_healthy:
            raise HTTPException(
                status_code=503,
                detail="MCP server is not reachable. Check MCP_SERVER_URL configuration."
            )

        # Try to list notes to verify connectivity
        notes = await mcp_client.list_notes(folder="01_seeds", recursive=False)

        if not notes:
            # If no seeds, try another folder
            notes = await mcp_client.list_notes(recursive=False)

        if notes and len(notes) > 0:
            # Read the first note as a test
            first_note_path = notes[0].get("path")
            note_content = await mcp_client.read_note(first_note_path)

            return {
                "status": "success",
                "message": "MCP connection successful",
                "test_note": {
                    "path": first_note_path,
                    "title": notes[0].get("title", "Untitled"),
                    "content_preview": note_content.get("content", "")[:200] + "...",
                    "frontmatter": note_content.get("frontmatter", {})
                },
                "total_notes_found": len(notes)
            }
        else:
            return {
                "status": "success",
                "message": "MCP connection successful but no notes found in vault",
                "total_notes_found": 0
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"MCP test failed: {str(e)}"
        )


@app.get("/api/v1/mcp/search")
async def test_mcp_search(
    query: str,
    folder: str = None,
    _: str = Depends(verify_token)
):
    """
    Test MCP search functionality
    Requires authentication

    Args:
        query: Search query string
        folder: Optional folder to search in

    Returns:
        Search results from vault
    """
    try:
        results = await mcp_client.search_notes(query, folder)

        return {
            "status": "success",
            "query": query,
            "folder": folder,
            "results_count": len(results),
            "results": results[:10]  # Limit to first 10 for testing
        }

    except Exception as e:
        logger.error(f"MCP search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/api/v1/mcp/read/{path:path}")
async def test_mcp_read(path: str, _: str = Depends(verify_token)):
    """
    Test reading a specific note by path
    Requires authentication

    Args:
        path: Note path relative to vault root

    Returns:
        Note content and metadata
    """
    try:
        note = await mcp_client.read_note(path)

        return {
            "status": "success",
            "path": path,
            "note": note
        }

    except Exception as e:
        logger.error(f"MCP read failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Read failed: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG
    )
