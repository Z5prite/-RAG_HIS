import json
import logging
from typing import AsyncIterator, Dict, Any, List

import httpx

from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

class DeepSeekClient:
    def __init__(self):
        self.api_key = SETTINGS["llm"]["api_key"]
        self.base_url = SETTINGS["llm"]["base_url"]
        self.model_name = SETTINGS["llm"]["model_name"]
        self.temperature = SETTINGS["llm"].get("temperature", 0.3)
        self.max_tokens = SETTINGS["llm"].get("max_tokens", 1500)
        
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """流式调用 DeepSeek API"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE data: {data}")
            except Exception as e:
                logger.error(f"DeepSeek API stream error: {e}")
                yield f"\n[AI 请求出错: {str(e)}]\n"

llm_client = DeepSeekClient()
