import json
import logging
import re
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.database import add_message, create_session, list_messages
from app.services.rag_chain import generate_rag_response

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        await create_session(session_id)
        
    # 保存用户消息
    await add_message(session_id, "user", request.message)
    
    # 读取历史消息 (不包含刚才存的那条，rag_chain 内部会拼接最新一条 user 消息)
    history_records = await list_messages(session_id, limit=20)
    history = [{"role": r["role"], "content": r["content"]} for r in history_records[:-1]]
    
    async def sse_generator():
        full_response = ""
        evidence_list = []
        
        try:
            async for chunk in generate_rag_response(request.message, history):
                if chunk.startswith("__META_EVIDENCE__:"):
                    evidence_list = json.loads(chunk[len("__META_EVIDENCE__:") :])
                    yield f'data: {json.dumps({"type": "evidence", "items": evidence_list}, ensure_ascii=False)}\n\n'
                    continue
                    
                full_response += chunk
                yield f'data: {json.dumps({"type": "chunk", "delta": chunk}, ensure_ascii=False)}\n\n'
                
            # 解析回答末尾的 <meta> 标签
            meta_data = {}
            meta_match = re.search(r'<meta>(.*?)</meta>', full_response, re.DOTALL)
            if meta_match:
                try:
                    meta_data = json.loads(meta_match.group(1).strip())
                    # 清理响应，移除 meta 标签，使其不在最终对话中显示
                    full_response = re.sub(r'<meta>.*?</meta>', '', full_response, flags=re.DOTALL).strip()
                except Exception as e:
                    logger.warning(f"Failed to parse AI meta tag: {e}")
                    
            # 存入数据库
            await add_message(
                session_id=session_id, 
                role="assistant", 
                content=full_response, 
                metadata={"evidence": evidence_list, **meta_data}
            )
            
            # 发送结束事件
            yield f'data: {json.dumps({"type": "done", "meta": meta_data, "session_id": session_id}, ensure_ascii=False)}\n\n'
            
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f'data: {json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)}\n\n'
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
