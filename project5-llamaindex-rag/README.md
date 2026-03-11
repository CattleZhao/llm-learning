# Project 5: LlamaIndex RAG 知识库

> 使用 LlamaIndex 构建的本地 Markdown 技术文档知识库

## 项目简介

基于 LlamaIndex 框架的 RAG（检索增强生成）系统，支持本地 Markdown 技术文档的智能问答。

## 功能特性

- 📁 加载本地 Markdown 文档
- 🔍 智能语义搜索
- 💬 自然语言问答
- 📚 答案附带来源引用

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 Ollama (用于嵌入)
ollama pull nomic-embed-text
ollama serve

# 配置环境变量
cp .env.example .env
# 编辑 .env，添加 ANTHROPIC_API_KEY

# 运行应用
streamlit run app/web.py
```

## 技术栈

- **LlamaIndex** - RAG 框架
- **Anthropic Claude** - LLM (原生 SDK)
- **Ollama** - 嵌入模型 (nomic-embed-text)
- **ChromaDB** - 向量数据库
- **Streamlit** - Web 界面
