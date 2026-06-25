# ⚕️ HIS RAG - 社区医院智能知识库与辅助诊疗系统

![Vue3](https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![DeepSeek](https://img.shields.io/badge/DeepSeek_V4-4D4D4D?style=for-the-badge&logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge)

本项目是一款面向社区基层医疗机构的**辅助问答与智能知识管理平台**。结合大模型问答能力与高级 RAG（检索增强生成）架构，为医护人员提供精准的诊疗参考依据和知识溯源，旨在降低通用大模型在医疗垂直场景下的幻觉问题，提升院内业务流转与信息获取效率。

> **声明**：本项目为 MVP (Minimum Viable Product) 演示版本，基于轻量级 FastAPI + Vue3 架构，剥离了企业级微服务（Spring Boot, MySQL, Redis），以实现**开箱即用 (Clone and Run)**。

## 📸 系统截图 (Screenshots)

<div align="center">
  <!-- 请在此处替换为你自己的截图路径或 URL -->
  <img src="https://via.placeholder.com/800x450.png?text=Login+Screen+Preview" alt="极简高定登录页" width="48%">
  <img src="https://via.placeholder.com/800x450.png?text=Chunk+Viewer+Preview" alt="知识库区块监视器" width="48%">
</div>

## 🌟 核心功能

- **🚀 智能问答与分诊建议**：基于 DeepSeek 大模型推理，严谨解答疾病科普，并在触发“红旗规则”时强制建议就医。
- **📚 知识库无缝接入**：管理员可直接在网页端上传 PDF / Word / MD 医疗指南，系统自动进行层级解析与向量化（Chunking + Embedding）。
- **🔍 精准文献溯源**：每一条 AI 生成的医疗建议，均会标注引用来源（段落级溯源），保障医疗严肃性与可信度。
- **🔬 知识区块监视器 (Chunk Viewer)**：后台数据透明化，管理员可实时可视化检视 Chroma 数据库内的切割区块。
- **✨ 极简医疗科技感 UI**：纯手工编写的“Bio-Tech Precision”视觉系统，包含毛玻璃质感、弥散渐变、微动效交互。

## 🛠️ 技术栈 (Demo Edition)

- **前端**：Vue 3 + Vite + 原生手写 CSS (零 UI 框架依赖)
- **后端**：Python 3.10 + FastAPI + Uvicorn
- **大模型 (LLM)**：DeepSeek API
- **嵌入模型 (Embedding)**：`BAAI/bge-small-zh-v1.5`
- **向量数据库**：ChromaDB
- **部署**：Docker + Docker Compose + Nginx (反向代理)

---

## 🚀 快速启动 (Local Development)

### 1. 克隆项目
```bash
git clone https://github.com/your-username/HIS_RAG.git
cd HIS_RAG
```

### 2. 配置 API Key
编辑 `backend/config.yaml` 文件，填入你的 DeepSeek API Key：
```yaml
llm:
  api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxx"  # 在这里填入你的 Key
```

### 3. 一键容器化部署 (推荐)
只需确保本地安装了 Docker 与 Docker Compose：
```bash
docker compose up -d --build
```
> 服务启动后，直接访问 `http://localhost` 即可体验！

---

## 🧑‍💻 本地源码运行 (Manual Run)

如果你希望修改代码进行二次开发，可以按照以下步骤分别运行前后端：

### 后端 (Backend) & 数据初始化
```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 初始化知识库向量数据 (重要！否则知识库为空)
python ../scripts/ingest.py

# 3. 启动服务
python main.py
# 后端服务将运行在 http://localhost:8012
```

### 前端 (Frontend)
```bash
cd frontend
npm install
npm run dev
# 前端服务通常运行在 http://localhost:5173
```

---

## 🔐 演示账号

在浏览器打开前端页面后，可使用以下测试账号登录：
- **管理员** (拥有上传文献、查看 Chunk 权限)：`admin` / `admin`
- **医生端** (仅可进行多轮问诊交互)：`user` / `user`

## 📄 开源协议
本项目采用 [MIT License](LICENSE) 开源协议。基于本系统提供的任何医疗建议均仅供**技术参考**，不得作为最终临床诊断依据。
