import logging
from typing import AsyncIterator, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import convert_to_messages
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

# 实例化标准 LangChain ChatOpenAI，用于支持 LCEL 链式调用
llm = ChatOpenAI(
    model=SETTINGS["llm"]["model_name"],
    openai_api_key=SETTINGS["llm"]["api_key"],
    openai_api_base=SETTINGS["llm"]["base_url"],
    temperature=SETTINGS["llm"].get("temperature", 0.3),
    max_tokens=SETTINGS["llm"].get("max_tokens", 1500),
    streaming=True
)

class DeepSeekClient:
    """
    兼容原有代码接口的 LLM 包装类
    """
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        # convert_to_messages 自动把 dict 转换为 SystemMessage/HumanMessage/AIMessage
        lc_messages = convert_to_messages(messages)
        try:
            async for chunk in llm.astream(lc_messages):
                yield chunk.content
        except Exception as e:
            logger.error(f"LangChain ChatOpenAI stream error: {e}")
            yield f"\n[AI 请求出错: {str(e)}]\n"

# 导出兼容原接口的 llm_client 单例
llm_client = DeepSeekClient()
