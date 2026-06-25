import logging
from typing import List

from sentence_transformers import SentenceTransformer

from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        model_name = SETTINGS["embedding"]["model_name"]
        device = SETTINGS["embedding"]["device"]
        logger.info(f"Loading embedding model: {model_name} on {device}")
        # 首次运行会自动下载到 ~/.cache/huggingface/hub/
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

# 全局单例实例
embedding_service = EmbeddingService()
