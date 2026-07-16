import logging
from typing import List, Dict, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic import Field

from app.vectorstores.chroma_store import vector_store

logger = logging.getLogger(__name__)

class MedicalHybridRetriever(BaseRetriever):
    kb_store: Any = Field(description="Chroma vector store for medical knowledge base")
    triage_store: Any = Field(description="Chroma vector store for triage rules")
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """
        结合两个 LangChain Chroma 集合进行召回检索，并在内存中进行按分数融合排序。
        """
        results = []
        
        # 1. 检索科普库
        kb_results = self.kb_store.similarity_search_with_relevance_scores(query, k=4)
        for doc, score in kb_results:
            # 深拷贝或直接修改 metadata
            doc.metadata["type"] = "科普知识"
            doc.metadata["score"] = score
            results.append(doc)
            
        # 2. 检索分诊库
        triage_results = self.triage_store.similarity_search_with_relevance_scores(query, k=3)
        for doc, score in triage_results:
            doc.metadata["type"] = "分诊建议"
            doc.metadata["score"] = score
            results.append(doc)
            
        # 3. 按相关度得分降序排序
        results.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
        return results

# 实例化 LangChain 检索器单例
retriever_instance = MedicalHybridRetriever(
    kb_store=vector_store.kb_store,
    triage_store=vector_store.triage_store
)

def retrieve_evidence(query: str, mode: str = "auto") -> List[Dict[str, Any]]:
    """
    为保持向后兼容提供的辅助接口，支持选择检索特定集合
    """
    results = []
    
    if mode in ["kb", "auto"]:
        kb_results = vector_store.query("medical_kb", query, top_k=4)
        for r in kb_results:
            r["type"] = "科普知识"
        results.extend(kb_results)
        
    if mode in ["triage", "auto"]:
        triage_results = vector_store.query("triage_kb", query, top_k=3)
        for r in triage_results:
            r["type"] = "分诊建议"
        results.extend(triage_results)
        
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
