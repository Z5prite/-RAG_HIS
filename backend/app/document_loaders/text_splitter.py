import re
import io
from typing import List, Dict, Any

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
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
    使用 LangChain 的 MarkdownHeaderTextSplitter 按 Markdown 标题层级切分文本。
    """
    # 1. 定义按哪些标题级别进行切割
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    
    # 2. 实例化 LangChain 的 Markdown 标题分割器
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    try:
        # 执行切分
        lc_docs = markdown_splitter.split_text(text)
    except Exception:
        # 如果切分失败，降级为普通纯文本切分
        lc_docs = []

    chunk_size = SETTINGS.get("chroma", {}).get("chunk_size", 500)
    chunk_overlap = SETTINGS.get("chroma", {}).get("chunk_overlap", 80)
    
    # 3. 对每个标题块进行进一步的长度细分（防止单个标题下的内容过长）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    
    final_chunks = []
    
    if lc_docs:
        for doc in lc_docs:
            # 提取分割后的标题信息作为 section 名字
            header_keys = ["Header 1", "Header 2", "Header 3", "Header 4"]
            section_parts = [doc.metadata[k] for k in header_keys if k in doc.metadata]
            section_name = " - ".join(section_parts) if section_parts else "General"
            
            sub_docs = text_splitter.split_text(doc.page_content)
            for i, sub_text in enumerate(sub_docs):
                final_chunks.append({
                    "text": sub_text,
                    "metadata": {
                        "source": filename,
                        "section": section_name,
                        "part": i + 1
                    }
                })
    else:
        # 降级：完全没有 Markdown 结构时，使用通用切分
        raw_chunks = chunk_text(text, chunk_size, chunk_overlap)
        for i, c in enumerate(raw_chunks):
            final_chunks.append({
                "text": c,
                "metadata": {
                    "source": filename,
                    "section": "General",
                    "part": i + 1
                }
            })
            
    return final_chunks

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """使用 LangChain 的 RecursiveCharacterTextSplitter 进行通用文本切分"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len
    )
    return text_splitter.split_text(text)
