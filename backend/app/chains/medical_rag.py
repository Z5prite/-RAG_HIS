import json
import logging
from pathlib import Path
from typing import AsyncIterator, Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.retrievers.medical_retriever import retrieve_evidence
from app.llms.deepseek_llm import llm
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

def _load_red_flags() -> str:
    """加载急诊红旗规则"""
    # 兼容原有的相对路径计算
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
5. **精准识别提问类型**：如果用户并非在描述自己的身体症状求医，而是在进行**常识咨询、闲聊打招呼、查阅知识库文档大纲、或询问有关《诊疗处置指南》等文献政策本身**的问答，这属于【非诊疗咨询】。在此情况下，`<meta>` 元数据中的 `department` 必须写为 `"无需就医"`，`risk` 必须写为 `"低风险"`，`suggestion` 必须写为 `"知识库文献内容解答。"`。

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
- department: 推荐就诊的科室（如果不涉及，或属于非诊疗咨询，可写"无需就医"）
- risk: 只能从 "低风险", "中风险", "高危(急诊)" 中选择
- suggestion: 简短的一句话医嘱总结
"""

# 定义 LangChain Prompt 模版
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_message}")
])

# 使用 LCEL 构建 RAG 链
rag_chain = chat_prompt | llm | StrOutputParser()

async def generate_rag_response(user_message: str, history: List[Dict[str, str]]) -> AsyncIterator[str]:
    """使用 LangChain LCEL 构建的 RAG 问答响应链"""
    
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
        
    # 3. 准备 System Prompt 变量值
    red_flags = _load_red_flags()
    
    # 4. 组装 LangChain 消息历史（取最近 10 条）
    lc_history = []
    for msg in history[-10:]:
        if msg["role"] == "user":
            lc_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_history.append(AIMessage(content=msg["content"]))
            
    # 5. 返回证据列表给前端（作为第一个特殊的 SSE event 发送，完美适配原有 API）
    evidence_payload = json.dumps([
        {"source": e["metadata"].get("source", ""), 
         "section": e["metadata"].get("section", ""), 
         "snippet": e["content"][:100] + "..."} 
        for e in evidences
    ], ensure_ascii=False)
    
    yield f'__META_EVIDENCE__:{evidence_payload}'
    
    # 6. 调用 LCEL 链并生成流式响应
    async for chunk in rag_chain.astream({
        "red_flags": red_flags,
        "evidence": evidence_text,
        "history": lc_history,
        "user_message": user_message
    }):
        yield chunk
