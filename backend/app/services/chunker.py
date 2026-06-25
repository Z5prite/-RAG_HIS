import re
import io
from typing import List, Dict, Any

from app.core.config import SETTINGS

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """提取文件文本 (支持 .md, .txt, .pdf, .docx)"""
    ext = filename.lower().split('.')[-1]
    
    if ext in ['md', 'txt']:
        return file_bytes.decode('utf-8', errors='ignore')
        
    elif ext == 'pdf':
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {e}")
            
    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {e}")
            
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def chunk_markdown(text: str, filename: str = "") -> List[Dict[str, Any]]:
    """
    按 Markdown 标题层级切分文本。如果不是标准的 Markdown，会平滑降级为通用切分。
    """
    lines = text.split('\n')
    chunks = []
    
    current_section = "General"
    current_content = []
    
    def _save_chunk():
        if current_content:
            content_str = '\n'.join(current_content).strip()
            if content_str:
                chunks.append({
                    "text": content_str,
                    "metadata": {
                        "source": filename,
                        "section": current_section
                    }
                })
    
    for line in lines:
        header_match = re.match(r'^(#{1,4})\s+(.+)', line)
        if header_match:
            _save_chunk()
            current_section = header_match.group(2).strip()
            current_content = [line]
        else:
            current_content.append(line)
            
    _save_chunk()
    
    # 通用长度截断处理
    final_chunks = []
    chunk_size = SETTINGS.get("chroma", {}).get("chunk_size", 500)
    chunk_overlap = SETTINGS.get("chroma", {}).get("chunk_overlap", 80)
    
    # 如果整个文件都没有 Markdown 标题，或者单块还是太大，走通用滑动窗口切分
    for chunk in chunks:
        if len(chunk["text"]) <= chunk_size:
            final_chunks.append(chunk)
        else:
            sub_chunks = chunk_text(
                chunk["text"], 
                chunk_size=chunk_size, 
                overlap=chunk_overlap
            )
            for i, sub in enumerate(sub_chunks):
                final_chunks.append({
                    "text": sub,
                    "metadata": {
                        **chunk["metadata"],
                        "part": i + 1
                    }
                })
                
    return final_chunks


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """通用滑窗切分"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        
    return chunks
