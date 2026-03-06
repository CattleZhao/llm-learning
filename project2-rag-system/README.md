# 项目2：RAG知识库问答系统

> 基于检索增强生成（RAG）的智能问答系统

## 功能

- 📄 支持PDF、TXT、MD、DOCX文档上传
- 🔍 智能语义检索
- 💬 基于检索内容的精准问答
- 📊 Streamlit Web界面

## 技术栈

- LangChain: 应用框架
- ChromaDB: 向量数据库
- Sentence Transformers: 文本嵌入
- Streamlit: Web界面

## 安装

```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run src/app.py
```

## 使用

```bash
streamlit run src/app.py
```
