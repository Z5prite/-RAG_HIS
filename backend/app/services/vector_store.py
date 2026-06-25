import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

import chromadb

from app.core.config import SETTINGS
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)

class ChromaService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
        
    def _init_db(self):
        persist_dir = Path(__file__).resolve().parents[4] / "data" / "chroma"
        config_dir = SETTINGS.get("chroma", {}).get("persist_dir")
        if config_dir:
            persist_dir = (Path(__file__).resolve().parents[3] / config_dir).resolve()
            
        logger.info(f"Initializing ChromaDB at {persist_dir}")
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        
        kb_name = SETTINGS.get("chroma", {}).get("kb_collection", "medical_kb")
        triage_name = SETTINGS.get("chroma", {}).get("triage_collection", "triage_kb")
        
        self.kb_collection = self.client.get_or_create_collection(
            name=kb_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.triage_collection = self.client.get_or_create_collection(
            name=triage_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, collection_name: str, documents: List[str], metadatas: List[Dict[str, Any]]):
        if not documents:
            return
            
        embeddings = embedding_service.embed_documents(documents)
        ids = [str(uuid.uuid4()) for _ in documents]
        
        col = self.kb_collection if collection_name == "medical_kb" else self.triage_collection
        
        # Batch insert to avoid exceeding SQLite limits
        batch_size = 5000
        for i in range(0, len(documents), batch_size):
            col.add(
                documents=documents[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
            
    def query(self, collection_name: str, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = embedding_service.embed_query(query_text)
        col = self.kb_collection if collection_name == "medical_kb" else self.triage_collection
        
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        output = []
        if results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]
            
            for doc, meta, dist in zip(docs, metas, dists):
                # Convert cosine distance to similarity score
                similarity = max(0.0, 1.0 - dist)
                output.append({
                    "content": doc,
                    "metadata": meta,
                    "score": similarity
                })
                
        return output
        
    def stats(self) -> Dict[str, int]:
        return {
            "medical_kb_count": self.kb_collection.count(),
            "triage_kb_count": self.triage_collection.count()
        }
        
    def get_chunks(self, collection_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        col = self.kb_collection if collection_name == "medical_kb" else self.triage_collection
        results = col.get(limit=limit, include=["documents", "metadatas"])
        
        output = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                output.append({
                    "id": results["ids"][i] if results["ids"] else str(i),
                    "content": doc,
                    "metadata": meta
                })
        return output

vector_store = ChromaService()
