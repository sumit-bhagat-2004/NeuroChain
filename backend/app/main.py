"""
Main — FastAPI application entry point with debate support.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.routes.nodes import router as nodes_router
from app.routes.debate import router as debate_router  # NEW
from app.routes.websocket import router as websocket_router  # NEW
from app.services.snowflake_service import initialize_tables
from app.services.debate_snowflake_service import initialize_debate_tables  # NEW
from app.services.embedding_service import init_embedding_cache
from app.utils.logger import logger


# Create FastAPI app
app = FastAPI(
    title="Cognitive Graph Engine",
    description="Semantic knowledge graph with transcription with smart merging",
    version="2.1.0"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Cognitive Graph Engine + Debate System...")

    # Initialize embedding cache
    init_embedding_cache(settings.embedding_cache_capacity)

    # Connect to Snowflake and initialize tables
    logger.info("Connecting to Snowflake...")
    await initialize_tables()
    await initialize_debate_tables()  # NEW

    # Log configuration
    logger.info(f"Configuration loaded:")
    logger.info(f"  - Score threshold: {settings.score_threshold}")
    logger.info(f"  - Max edges per node: {settings.max_edges_per_node}")
    logger.info(f"  - Time decay half-life: {settings.time_decay_halflife}ms")
    logger.info(f"  - Candidate limit: {settings.candidate_limit}")
    logger.info(f"  - Cache capacity: {settings.embedding_cache_capacity}")
    logger.info(f"  - Debate merge threshold: 0.75")  # NEW

    logger.info("Cognitive Graph Engine + Debate System ready!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Cognitive Graph Engine",
        "version": "2.1.0",
        "status": "running",
        "features": {
            "knowledge_graph": "Standard node + edge system",
            "debate_transcription": "Smart merge system for similar content"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "engine": "Cognitive Graph Engine + Debate",
        "version": "2.1.0"
    }


# Include routers
app.include_router(nodes_router)
app.include_router(debate_router)
app.include_router(websocket_router)