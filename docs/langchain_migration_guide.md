# HIS RAG 项目——LangChain 架构迁移可行性分析与重构指南

您说得非常对。**当前的项目完全不是基于 LangChain 开发的**。

目前项目采用的是**原生自研（Raw Python）架构**：通过原生 `httpx` 自行实现大模型的流式对接与解析，使用原生的 `chromadb` SDK 与 `sentence-transformers` 进行向量存储与计算，并用自定义的正则与滑窗对文本进行切片。这种方式虽然轻量、无框架开销，但在面对需要增加高级检索（如 Rerank 重排、混合检索）、多模态、Agent 工具调用等复杂需求时，维护成本会迅速上升。

为了方便您评估和实施迁移，我为您整理了这篇**《LangChain 架构迁移指南》**，保存在本项目目录中供参考。

---

## 📂 1. 当前架构与 LangChain 架构对比

| 功能模块 | 当前原生实现 | 对应文件 | LangChain 替代方案 | 迁移难度 |
| :--- | :--- | :--- | :--- | :--- |
| **LLM 客户端** | 基于 `httpx` 手写 SSE 流式请求与 XML 解析 | [llm_client.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/llm_client.py) | `langchain_openai.ChatOpenAI` (适配 DeepSeek API) | ⭐ (极易) |
| **文本向量化** | 基于 `sentence-transformers` 原生封装 | [embedding.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/embedding.py) | `HuggingFaceBgeEmbeddings` | ⭐ (极易) |
| **向量数据库** | 直接操作 `chromadb.PersistentClient` | [vector_store.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/vector_store.py) | `langchain_chroma.Chroma` 包装器 | ⭐⭐ (中等) |
| **文档切片** | 自定义正则提取 Markdown 标题 + 滑动窗口 | [chunker.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/chunker.py) | `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` | ⭐⭐ (中等) |
| **多路召回检索** | 手动执行多次向量检索，在内存中合并与评分排序 | [retriever.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/retriever.py) | 继承 `BaseRetriever` 自定义检索器，或使用 `EnsembleRetriever` | ⭐⭐ (中等) |
| **RAG 链路编排** | 过程式代码，手动将上下文拼接进 Prompt | [rag_chain.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/rag_chain.py) | **LCEL (LangChain 表达语言)** 声明式工作流 | ⭐⭐⭐ (需要适配流式) |

---

## 🛠️ 2. 核心模块重构方案设计

### 模块 A. 大模型调用 (LLM)
* **现状**：手写 `httpx.stream("POST", ...)`，逐行解析 `data: ` 前缀并捕获异常。
* **LangChain 方案**：由于 DeepSeek 接口与 OpenAI 兼容，可直接使用 `ChatOpenAI`，其内部已自动处理了异步、流式中断、错误重试等机制。

```python
# 迁移后：app/services/llm_client.py
from langchain_openai import ChatOpenAI
from app.core.config import SETTINGS

llm = ChatOpenAI(
    model=SETTINGS["llm"]["model_name"],
    openai_api_key=SETTINGS["llm"]["api_key"],
    openai_api_base=SETTINGS["llm"]["base_url"],
    temperature=SETTINGS["llm"].get("temperature", 0.3),
    max_tokens=SETTINGS["llm"].get("max_tokens", 1500),
    streaming=True
)
```

---

### 模块 B. 向量数据库与 Embedding
* **现状**：使用自定义单例加载加载模型，并调用原生的 `col.add()` 和 `col.query()`。
* **LangChain 方案**：使用 `langchain_chroma` 的包装器，可以自动处理向量化过程，无需在业务层手动调用 `embedding_service.embed_documents`。

```python
# 迁移后：app/services/vector_store.py
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# 实例化 Embedding 模型
embeddings = HuggingFaceBgeEmbeddings(
    model_name=SETTINGS["embedding"]["model_name"],
    model_kwargs={"device": SETTINGS["embedding"]["device"]}
)

# 初始化 Chroma 数据库实例
kb_store = Chroma(
    collection_name="medical_kb",
    embedding_function=embeddings,
    persist_directory=persist_path
)

# 添加文档只需传入纯文本与元数据即可，LangChain 内部会自动完成向量计算与存入
kb_store.add_texts(texts=documents, metadatas=metadatas)
```

---

### 模块 C. 混合检索器 (Retriever)
* **现状**：此项目需要同时检索**“科普知识库(medical_kb)”**与**“分诊规则库(triage_kb)”**，并在内存中进行按相关度得分排序。
* **LangChain 方案**：通过继承 LangChain 的 `BaseRetriever` 实现自定义检索器，不仅格式标准，而且能获得标准的可调用接口（`invoke` 和异步 `ainvoke`）。

```python
# 迁移后：app/services/retriever.py
from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

class MedicalHybridRetriever(BaseRetriever):
    kb_store: Chroma
    triage_store: Chroma
    
    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        results = []
        
        # 1. 检索科普知识
        kb_results = self.kb_store.similarity_search_with_relevance_scores(query, k=4)
        for doc, score in kb_results:
            doc.metadata["type"] = "科普知识"
            doc.metadata["score"] = score
            results.append(doc)
            
        # 2. 检索分诊规则
        triage_results = self.triage_store.similarity_search_with_relevance_scores(query, k=3)
        for doc, score in triage_results:
            doc.metadata["type"] = "分诊建议"
            doc.metadata["score"] = score
            results.append(doc)
            
        # 3. 合并并按相似度得分从高到低排序
        results.sort(key=lambda x: x.metadata.get("score", 0.0), reverse=True)
        return results
```

---

### 模块 D. RAG 链与前端 SSE 适配 (RAG Chain)
* **现状**：
  1. 接口需要**首先**向前端发送文献来源 `__META_EVIDENCE__:<json>`，以便前端渲染引用卡片。
  2. 随后以 SSE 流式返回大模型的回答。
  3. 回答结束时需要解析 `<meta>` 标签存储科室与风险参数。
* **LangChain 方案**：使用 **LCEL (LangChain Expression Language)**。我们把 Prompt 和 LLM 编排成一条 LCEL 链，利用它的 `astream` 方法流式吐出回答，从而完美满足原有的 API 数据格式要求：

```python
# 迁移后：app/services/rag_chain.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 定义提示词模版
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),  # 接收 {red_flags} 和 {evidence}
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_message}")
])

# 拼装 LCEL 链
rag_chain = chat_prompt | llm | StrOutputParser()

async def generate_rag_response(user_message: str, history: list) -> AsyncIterator[str]:
    # 1. 召回相关文献
    retriever = MedicalHybridRetriever(kb_store=vector_store.kb_store, triage_store=vector_store.triage_store)
    docs = await retriever.ainvoke(user_message)
    
    # 2. 构建输入参数 (解析文献并格式化为提示词所需的变量)
    evidence_text = format_docs_to_string(docs)
    red_flags = _load_red_flags()
    
    # 3. 转换历史消息格式
    lc_history = convert_to_langchain_messages(history)
    
    # 4. 先行吐出检索的文献卡片数据 (兼容前端 SSE)
    yield f'__META_EVIDENCE__:{format_evidence_to_json(docs)}'
    
    # 5. 执行 LCEL 链，流式输出回答
    async for chunk in rag_chain.astream({
        "red_flags": red_flags,
        "evidence": evidence_text,
        "history": lc_history,
        "user_message": user_message
    }):
        yield chunk
```

---

## 🏃 3. 迁移步骤与路线图

1. **环境准备**：
   在 `backend/requirements.txt` 中添加依赖：
   ```text
   langchain>=0.2.0
   langchain-community>=0.2.0
   langchain-openai>=0.1.0
   langchain-chroma>=0.1.0
   ```
2. **底层迁移 (第 1-2 天)**：
   * 用 `ChatOpenAI` 替换 [llm_client.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/llm_client.py)。
   * 用 `HuggingFaceBgeEmbeddings` 和 `Chroma` 重新编写 [embedding.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/embedding.py) 和 [vector_store.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/vector_store.py)。
3. **数据重灌 (第 3 天)**：
   * 迁移文档切分模块 [chunker.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/chunker.py)，引入 LangChain 的 `MarkdownHeaderTextSplitter`。
   * 运行 [scripts/ingest.py](file:///D:/AAAA/Demo/HIS_RAG/scripts/ingest.py)，将源数据以 LangChain 识别的格式重新导入数据库。
4. **业务链路联调 (第 4-5 天)**：
   * 编写 LCEL RAG 链，完成 [rag_chain.py](file:///D:/AAAA/Demo/HIS_RAG/backend/app/services/rag_chain.py) 的替换。
   * 启动前后端进行联合调试，确保流式卡片渲染和后台分类入库功能正常运行。
