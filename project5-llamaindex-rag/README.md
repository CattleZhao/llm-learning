# Project 5: LlamaIndex RAG 知识库

> 使用 LlamaIndex 构建的本地 Markdown 技术文档知识库，支持重排序和流式输出

## 项目简介

基于 LlamaIndex 框架的 RAG（检索增强生成）系统，支持本地 Markdown 技术文档的智能问答。

**新增功能**: ✨ 支持检索结果重排序（Reranking）和流式输出

## 功能特性

- 📁 加载本地 Markdown 文档
- 🔍 智能语义搜索
- 💬 自然语言问答
- 📚 答案附带来源引用
- 🔄 **重排序优化 (Reranking)** - 提升检索质量
- 📊 **对比模式** - 可视化 rerank 效果对比
- ⚡ **流式输出** - 实时打字机效果，提升用户体验

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

## 重排序 (Reranking) 功能

### 什么是 Reranking？

Reranking 是在向量检索后，使用更精细的模型对结果重新排序，从而提高相关性。

```
Query → 向量检索 (Top-N) → Rerank 重排 → Top-K → 生成答案
```

### 支持的 Reranker 类型

| 类型 | 说明 | 需求 |
|------|------|------|
| **keyword** | 基于关键词匹配度重排序 | 无额外需求 |
| **cohere** | 使用 Cohere Rerank API | 需要配置 `COHERE_API_KEY` |

### 使用方法

在 Web 界面侧边栏的「重排序」区域：

1. 勾选「启用重排序」
2. 选择 Reranker 类型
3. (可选) 勾选「对比模式」查看效果对比

### 配置参数

在 `.env` 文件中添加：

```bash
# Reranking 配置
ENABLE_RERANK=true          # 是否启用 reranking
RERANKER_TYPE=keyword       # reranker 类型: keyword 或 cohere
COHERE_API_KEY=your-key     # 使用 cohere 时需要

# 流式输出配置
ENABLE_STREAMING=true       # 是否启用流式输出（默认启用）
```

## 流式输出 (Streaming)

### 什么是流式输出？

流式输出是逐个 token 生成并实时返回，而不是等待完整响应后一次性返回。这提供了更好的用户体验，类似 ChatGPT 的打字机效果。

### 使用方法

在 Web 界面侧边栏的「流式输出」区域：

1. 勾选「启用流式输出」
2. 查询时答案会实时逐字显示

### 效果对比

| 模式 | 用户体验 | 适用场景 |
|------|----------|----------|
| **流式输出** | 实时反馈，无需等待 | 交互式问答 |
| **非流式输出** | 等待完成后一次性显示 | 批量处理、导出 |

## 技术栈

- **LlamaIndex** - RAG 框架
- **Anthropic Claude** - LLM (原生 SDK)
- **Ollama** - 嵌入模型 (nomic-embed-text)
- **ChromaDB** - 向量数据库
- **Streamlit** - Web 界面

## 项目结构

```
project5-llamaindex-rag/
├── app/
│   └── web.py              # Streamlit Web 界面
├── src/
│   ├── config.py           # 配置管理
│   ├── loaders/            # 文档加载器
│   ├── indexes/            # 向量索引管理
│   ├── query/              # 查询引擎
│   └── rerank/             # 重排序模块 (新增)
│       ├── base.py         # 基类
│       ├── keyword_reranker.py  # 关键词重排序
│       ├── cohere_reranker.py   # Cohere API 重排序
│       └── postprocessor.py     # LlamaIndex 适配器
├── data/
│   └── docs/               # 示例文档
├── tests/
│   └── rerank/             # Reranker 测试
└── requirements.txt
```

## 测试

```bash
# 运行 reranker 测试
pytest tests/rerank/test_keyword_reranker.py -v
```
