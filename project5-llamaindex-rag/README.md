# Project 5: LlamaIndex RAG 知识库

> 使用 LlamaIndex 构建的本地 Markdown 技术文档知识库，支持重排序、流式输出和元数据过滤

## 项目简介

基于 LlamaIndex 框架的 RAG（检索增强生成）系统，支持本地 Markdown 技术文档的智能问答。

**新增功能**: ✨ 支持检索结果重排序（Reranking）、流式输出和元数据过滤

## 功能特性

- 📁 加载本地 Markdown 文档
- 🔍 智能语义搜索
- 💬 自然语言问答
- 📚 答案附带来源引用
- 🔄 **重排序优化 (Reranking)** - 提升检索质量
- 📊 **对比模式** - 可视化 rerank 效果对比
- ⚡ **流式输出** - 实时打字机效果，提升用户体验
- 🏷️ **元数据过滤** - 按分类、标签、作者等精准检索

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

## 元数据过滤 (Metadata Filtering)

### 什么是元数据过滤？

在检索时根据文档的元数据（如分类、标签、作者等）进行筛选，实现精准检索。

```
Query + 过滤条件 → 向量检索 + 元数据筛选 → 精准结果
```

### 支持的元数据字段

| 字段 | 说明 | 来源 |
|------|------|------|
| **category** | 文档分类 | YAML frontmatter 或自动提取 |
| **tags** | 标签列表 | YAML frontmatter |
| **author** | 作者 | YAML frontmatter 或自动提取 |
| **year** | 年份 | 自动从日期提取 |
| **title** | 标题 | 自动提取 |
| **file_type** | 文件类型 | 自动提取 |

### 文档元数据格式

在 Markdown 文档开头添加 YAML frontmatter：

```markdown
---
title: "文档标题"
author: "作者名"
category: "分类"
tags: ["标签1", "标签2"]
date: "2024-01-15"
---

# 文档内容
...
```

### 使用方法

在 Web 界面侧边栏的「元数据过滤」区域：

1. 勾选「启用元数据过滤」
2. 选择要过滤的字段和值
3. 点击「应用过滤」

### 代码示例

```python
from src.metadata.filters import MetadataFilterBuilder

# 构建过滤器
filter_builder = (MetadataFilterBuilder()
                 .eq("category", "人工智能")
                 .gte("year", 2024))

# 应用到查询引擎
query_engine = RAGQueryEngine(
    index=index,
    metadata_filters=filter_builder.build()
)
```

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
│   ├── loaders/            # 文档加载器（支持元数据提取）
│   ├── indexes/            # 向量索引管理
│   ├── query/              # 查询引擎（支持过滤）
│   ├── metadata/           # 元数据模块 (新增)
│   │   ├── extractor.py    # 元数据提取器
│   │   └── filters.py      # 过滤器构建器
│   └── rerank/             # 重排序模块
│       ├── base.py         # 基类
│       ├── keyword_reranker.py  # 关键词重排序
│       ├── cohere_reranker.py   # Cohere API 重排序
│       └── postprocessor.py     # LlamaIndex 适配器
├── data/
│   └── docs/               # 示例文档（含元数据）
├── examples/
│   ├── reranker_demo.py    # Reranker 演示
│   ├── streaming_demo.py   # 流式输出演示
│   └── metadata_demo.py    # 元数据过滤演示 (新增)
├── tests/
│   └── rerank/             # Reranker 测试
└── requirements.txt
```

## 测试

```bash
# 运行 reranker 测试
pytest tests/rerank/test_keyword_reranker.py -v
```
