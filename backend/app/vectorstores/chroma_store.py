import logging
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from langchain_chroma import Chroma

from app.core.config import SETTINGS
from app.embeddings.bge_embeddings import embedding_service

logger = logging.getLogger(__name__)

class ChromaStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_store()
        return cls._instance
        
    def _init_store(self):
        persist_dir = Path(__file__).resolve().parents[4] / "data" / "chroma"
        config_dir = SETTINGS.get("chroma", {}).get("persist_dir")
        if config_dir:
            persist_dir = (Path(__file__).resolve().parents[3] / config_dir).resolve()
            
        logger.info(f"Initializing LangChain Chroma at {persist_dir}")
        self.chroma_client = chromadb.PersistentClient(path=str(persist_dir))
        
        kb_name = SETTINGS.get("chroma", {}).get("kb_collection", "medical_kb")
        triage_name = SETTINGS.get("chroma", {}).get("triage_collection", "triage_kb")
        
        self.kb_store = Chroma(
            client=self.chroma_client,
            collection_name=kb_name,
            embedding_function=embedding_service
        )
        self.triage_store = Chroma(
            client=self.chroma_client,
            collection_name=triage_name,
            embedding_function=embedding_service
        )

    def add_documents(self, collection_name: str, documents: List[str], metadatas: List[Dict[str, Any]]):
        if not documents:
            return
        store = self.kb_store if collection_name == "medical_kb" else self.triage_store
        store.add_texts(texts=documents, metadatas=metadatas)
        
    def query(self, collection_name: str, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        store = self.kb_store if collection_name == "medical_kb" else self.triage_store
        
        # similarity_search_with_relevance_scores gives standard cosine similarity scores in LangChain
        results = store.similarity_search_with_relevance_scores(query_text, k=top_k)
        
        output = []
        for doc, score in results:
            output.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
        return output
        
    def stats(self) -> Dict[str, int]:
        return {
            "medical_kb_count": self.kb_store._collection.count(),
            "triage_kb_count": self.triage_store._collection.count()
        }
        
    def get_chunks(self, collection_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        store = self.kb_store if collection_name == "medical_kb" else self.triage_store
        results = store.get(limit=limit, include=["documents", "metadatas"])
        
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

vector_store = ChromaStore()
