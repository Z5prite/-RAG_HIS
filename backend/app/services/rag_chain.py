import json
import logging
import re
from pathlib import Path
from typing import AsyncIterator, Dict, Any, List

from app.services.retriever import retrieve_evidence
from app.services.llm_client import llm_client
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

def _load_red_flags() -> str:
    """加载急诊红旗规则"""
    rules_path = Path(__file__).resolve().parents[4] / "data" / "medical-triage-kb" / "rules" / "red_flags.md"
    config_dir = SETTINGS.get("data", {}).get("triage_kb_dir")
    if config_dir:
        rules_path = Path(__file__).resolve().parents[3] / config_dir / "rules" / "red_flags.md"
        
    try:
        return rules_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not load red flags: {e}")
        return "如出现持续高热、呼吸困难、严重胸痛或大出血，请立即急诊或拨打120。"

SYSTEM_PROMPT = """你是一个专业的医疗AI助手（RAG of HIS），为患者提供健康科普和分诊建议。

【核心原则】
1. 绝对不能做出具体疾病诊断。
2. 绝对不能开具处方药。
3. 如果患者症状严重，必须强烈建议立刻就医。
4. 你的回答**只能严格基于提供的【检索证据】和【红旗规则】**。如果检索证据中找不到相关解答，请明确回答：“抱歉，目前系统知识库中暂未收录针对您症状的权威数据，无法提供专业建议，请直接前往医院就诊。” **绝对不能根据你自己预训练的知识“夹带私货”或者编造回答！**

【红旗规则（必须严格遵守）】
{red_flags}

【检索证据】
{evidence}

【输出格式要求】
作为一名有温度的医生，你必须先用 2-3 段亲切专业的自然语言，耐心分析患者的症状，并给出详细的科普或医嘱建议。**切忌只输出干巴巴的结论或直接输出标签！**

在用自然语言充分沟通完毕后，必须在回答的最后另起一行，使用 XML 标签输出结构化元数据供系统解析。
格式如下：
<meta>
{{"department": "神经内科", "risk": "低风险", "suggestion": "建议两周内门诊就诊。"}}
</meta>

说明：
- department: 推荐就诊的科室（如果不涉及，可写"无需就医"或"全科医学科"）
- risk: 只能从 "低风险", "中风险", "高危(急诊)" 中选择
- suggestion: 简短的一句话医嘱总结
"""

async def generate_rag_response(user_message: str, history: List[Dict[str, str]]) -> AsyncIterator[str]:
    """核心 RAG 生成链路"""
    
    # 1. 检索证据
    evidences = retrieve_evidence(user_message, mode="auto")
    
    # 2. 格式化证据
    evidence_text = ""
    for i, ev in enumerate(evidences):
        source = ev["metadata"].get("source", "未知来源")
        section = ev["metadata"].get("section", "")
        content = ev["content"]
        evidence_text += f"\n--- 证据 {i+1} [{ev['type']}] ({source} - {section}) ---\n{content}\n"
        
    if not evidence_text.strip():
        evidence_text = "（没有找到直接相关的知识库记录，请根据常识和红旗规则回答，但保持免责声明）"
        
    # 3. 组装 System Prompt
    red_flags = _load_red_flags()
    sys_prompt = SYSTEM_PROMPT.format(red_flags=red_flags, evidence=evidence_text)
    
    # 4. 组装 Messages
    messages = [{"role": "system", "content": sys_prompt}]
    for msg in history[-10:]: # 取最近10条历史
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    
    # 5. 调用大模型并透传流式输出，同时返回证据列表给前端
    # 将证据列表作为第一个特殊的 SSE event 发送
    evidence_payload = json.dumps([
        {"source": e["metadata"].get("source", ""), 
         "section": e["metadata"].get("section", ""), 
         "snippet": e["content"][:100] + "..."} 
        for e in evidences
    ], ensure_ascii=False)
    
    yield f'__META_EVIDENCE__:{evidence_payload}'
    
    async for chunk in llm_client.chat_stream(messages):
        yield chunk
