import logging
import secrets
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.services.chunker import extract_text_from_file, chunk_markdown, chunk_text
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, "admin")
    is_pass_ok = secrets.compare_digest(credentials.password, "admin")
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.get("/stats")
async def get_kb_stats(_: str = Depends(verify_admin)):
    """获取知识库状态统计 (Admin Only)"""
    try:
        return vector_store.stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunks")
async def get_kb_chunks(collection: str = "medical_kb", _: str = Depends(verify_admin)):
    """获取知识库区块列表 (Admin Only)"""
    try:
        if collection not in ['medical_kb', 'triage_kb']:
            raise HTTPException(status_code=400, detail="Invalid collection name")
        chunks = vector_store.get_chunks(collection_name=collection, limit=50)
        return {"chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("medical_kb"), # "medical_kb" or "triage_kb"
    _: str = Depends(verify_admin)
):
    """上传文件并入库 (Admin Only)"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    ext = file.filename.lower().split('.')[-1]
    if ext not in ['md', 'txt', 'pdf', 'docx']:
        raise HTTPException(status_code=400, detail="Unsupported file type")
        
    if collection not in ['medical_kb', 'triage_kb']:
        raise HTTPException(status_code=400, detail="Invalid collection name")

    try:
        # 读取文件
        content_bytes = await file.read()
        
        # 保存备份 (可选)
        uploads_dir = Path(__file__).resolve().parents[3] / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        save_path = uploads_dir / file.filename
        save_path.write_bytes(content_bytes)
        
        # 提取文本
        text = extract_text_from_file(content_bytes, file.filename)
        
        # 切分
        if ext == 'md':
            chunks = chunk_markdown(text, filename=file.filename)
        else:
            raw_chunks = chunk_text(text)
            chunks = [
                {"text": c, "metadata": {"source": file.filename, "part": i+1}} 
                for i, c in enumerate(raw_chunks)
            ]
            
        # 入库
        if not chunks:
            raise ValueError("No text could be extracted or chunked")
            
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        vector_store.add_documents(
            collection_name=collection,
            documents=documents,
            metadatas=metadatas
        )
        
        return {
            "success": True, 
            "message": f"Successfully ingested {file.filename}",
            "chunks_added": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
