import logging
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

model_name = SETTINGS["embedding"]["model_name"]
device = SETTINGS["embedding"]["device"]
logger.info(f"Loading LangChain HuggingFaceBgeEmbeddings: {model_name} on {device}")

# 全局单例实例，直接继承并暴露标准 LangChain Embeddings 接口
embedding_service = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True}
)
