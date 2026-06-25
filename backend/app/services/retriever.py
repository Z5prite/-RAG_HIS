import logging
from typing import List, Dict, Any

from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

def retrieve_evidence(query: str, mode: str = "auto") -> List[Dict[str, Any]]:
    """
    根据模式从不同的知识库检索证据。
    mode: 
      - "kb": 仅检索健康科普
      - "triage": 仅检索分诊规则
      - "auto": 同时检索两者
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
        
    # 按 score 降序排序
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 过滤掉分数过低的干扰项（可选）
    # results = [r for r in results if r["score"] > 0.4]
    
    return results
