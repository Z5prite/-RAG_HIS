from fastapi import APIRouter, HTTPException

from app.services.database import list_sessions, list_messages, delete_session

router = APIRouter()

@router.get("/sessions")
async def get_sessions():
    """获取所有会话列表"""
    sessions = await list_sessions()
    return {"sessions": sessions}

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取指定会话的历史消息"""
    messages = await list_messages(session_id)
    return {"messages": messages}

@router.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    """删除指定会话"""
    try:
        await delete_session(session_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
