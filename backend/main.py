import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import SETTINGS
from app.storage.sqlite_history import init_db
from app.embeddings.bge_embeddings import embedding_service
from app.api.chat import router as chat_router
from app.api.session import router as session_router
from app.api.knowledge import router as knowledge_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up RAG of HIS backend...")
    
    # 1. Init Database
    await init_db()
    
    # 2. Preload embedding model
    # (Trigger singleton instantiation)
    _ = embedding_service
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(title="RAG of HIS API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(session_router, prefix="/api", tags=["sessions"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])

if __name__ == "__main__":
    import uvicorn
    host = SETTINGS.get("server", {}).get("host", "127.0.0.1")
    port = SETTINGS.get("server", {}).get("port", 8012)
    
    logger.info(f"Starting server at http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)

