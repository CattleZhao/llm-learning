# Project 5: LlamaIndex RAG 知识库 设计文档

**项目名称**：project5-llamaindex-rag
**创建日期**：2026-03-10
**目的**：使用 LlamaIndex 框架构建本地 Markdown 技术文档知识库，学习专业 RAG 系统

---

## 1. 项目概述

### 1.1 目标

构建一个基于 LlamaIndex 的 RAG 知识库系统，支持：
- 加载本地 Markdown 技术文档
- 智能切分和向量化索引
- 自然语言问答
- 返回答案 + 来源引用

### 1.2 学习目标

- 掌握 LlamaIndex 核心概念（Documents、Nodes、Indexes、Query Engines）
- 理解向量数据库（ChromaDB）的使用
- 学习 RAG 系统的完整流程
- 实践文档解析和索引优化技巧

### 1.3 与之前项目的关系

| 项目 | 内容 | 本项目延伸 |
|------|------|-----------|
| project2-rag | 基于文件的简单 RAG | 使用专业框架 + 向量数据库 |
| project4-crewai | 多 Agent 系统 | 可集成作为 Agent 的知识库 Tool |

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                        │
│  - 文档上传 / 选择目录                                      │
│  - 查询输入框                                              │
│  - 结果显示（答案 + 引用）                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│              LlamaIndex Query Engine                        │
│  - VectorStoreIndex (向量索引)                             │
│  - CitationQueryEngine (带引用的查询)                       │
│  - 查询处理（检索 + 生成）                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    数据层                                   │
├─────────────────────────────────────────────────────────────┤
│  SimpleDirectoryReader  │  Markdown 解析                   │
│  MarkdownNodeParser      │  智能切分                        │
│  ChromaDB               │  向量持久化                      │
│  Ollama Embedding       │  本地向量化                      │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                  本地 Markdown 文档                         │
│  README.md, API_DOCS.md, NOTES/*.md                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件设计

### 3.1 文件结构

```
project5-llamaindex-rag/
├── src/
│   ├── loaders/              # 文档加载器
│   │   ├── __init__.py
│   │   └── markdown_loader.py
│   ├── indexes/              # 索引管理
│   │   ├── __init__.py
│   │   └── vector_index.py
│   ├── query/                # 查询引擎
│   │   ├── __init__.py
│   │   └── query_engine.py
│   └── config.py             # 配置管理
├── app/
│   └── web.py                # Streamlit 界面
├── tests/                    # 测试
│   ├── unit/
│   └── fixtures/
├── data/
│   └── docs/                 # 示例 Markdown 文档
├── storage/                  # ChromaDB 持久化目录
├── requirements.txt
├── .env.example
└── README.md
```

### 3.2 核心类设计

| 组件 | 类名 | 主要方法 | 职责 |
|------|------|---------|------|
| 文档加载 | `MarkdownLoader` | `load_documents(dir_path)` | 递归读取目录、解析 MD |
| 索引管理 | `VectorIndexManager` | `create_index()`, `load_index()`, `update_index()` | 创建/加载/更新索引 |
| 查询引擎 | `RAGQueryEngine` | `query(question)` | 处理查询、返回答案+引用 |
| 配置 | `Settings` | `get_model_config()`, `get_embed_config()` | 模型、嵌入、存储配置 |

---

## 4. 数据流程

### 4.1 索引构建流程

```
1. 用户选择文档目录
   ↓
2. SimpleDirectoryReader 加载所有 .md 文件
   ↓
3. Markdown 解析为 Documents
   ↓
4. MarkdownNodeParser 切分为 Nodes
   - chunk_size: 512
   - chunk_overlap: 50
   ↓
5. Ollama 嵌入模型向量化 (nomic-embed-text)
   ↓
6. 存储到 ChromaDB（持久化到 storage/chroma）
   ↓
7. 显示索引统计（文档数、节点数）
```

### 4.2 查询流程

```
1. 用户输入问题
   ↓
2. QueryEngine 检索 Top-K 相关节点 (k=3)
   ↓
3. 构建提示词（问题 + 检索到的上下文）
   ↓
4. LLM 生成答案 (Ollama - qwen2.5)
   ↓
5. 格式化输出
   - 答案
   - 来源文档
   - 引用片段
```

---

## 5. 关键技术实现

### 5.1 文档加载

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import MarkdownReader

loader = SimpleDirectoryReader(
    input_dir="data/docs",
    recursive=True,
    file_extractor={".md": MarkdownReader()}
)
documents = loader.load_data()
```

### 5.2 文档切分

```python
from llama_index.core.node_parser import MarkdownNodeParser

parser = MarkdownNodeParser(
    chunk_size=512,
    chunk_overlap=50
)
nodes = parser.get_nodes_from_documents(documents)
```

### 5.3 向量存储

```python
import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

db = chromadb.PersistentClient(path="storage/chroma")
chroma_store = ChromaVectorStore(chroma_collection=db.get_or_create_collection("docs"))
index = VectorStoreIndex(nodes, vector_store=chroma_store)
```

### 5.4 查询引擎

```python
from llama_index.core.query_engine import CitationQueryEngine

query_engine = CitationQueryEngine.from_args(
    index,
    similarity_top_k=3,
    citation_chunk_size=512
)
```

---

## 6. 用户界面设计

### 6.1 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  📚 LlamaIndex 技术文档知识库                               │
├─────────────────────────────────────────────────────────────┤
│  侧边栏                        │    主区域                   │
│  ┌─────────────────────────┐   │  ┌───────────────────────┐│
│  │ 📁 文档管理             │   │  │ 📖 知识库问答         ││
│  │                        │   │  │                       ││
│  │ 选择目录: [data/docs]   │   │  │ 你的问题:             ││
│  │ [🔄 重建索引]          │   │  │ [___________________] ││
│  │                        │   │  │                       ││
│  │ 📊 索引统计:           │   │  │     [🔍 搜索]        ││
│  │   文档: 15 个          │   │  │                       ││
│  │   节点: 342 个         │   │  │  ──────────────────────││
│  │                        │   │  │                       ││
│  │ ⚙️ 设置                │   │  │  📝 答案              ││
│  │   顶部K: [3]           │   │  │  [LLM 生成的回答]     ││
│  │   温度: [0.7]          │   │  │                       ││
│  │                        │   │  │  📚 来源               ││
│  │ 📖 使用说明            │   │  │  • README.md          ││
│  │                        │   │  │  • API.md             ││
│  └─────────────────────────┘   │  │  > 引用片段...       ││
│                                 │  └───────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 6.2 交互流程

1. 用户首次打开 → 显示使用说明
2. 选择文档目录 → 自动检测 .md 文件数量
3. 点击"重建索引" → 显示进度条
4. 输入问题 → 显示加载动画 → 返回答案 + 引用

---

## 7. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 目录无 .md 文件 | 友好提示："未找到 Markdown 文档" |
| 索引构建失败 | 捕获异常，显示错误详情 + 重试按钮 |
| 查询无相关结果 | 返回"未找到相关信息，请换个问法" |
| LLM 生成失败 | 降级到仅显示检索到的文档片段 |
| 文档编码错误 | 跳过该文件，记录日志，继续处理 |

---

## 8. 测试策略

### 8.1 测试类型

| 测试 | 内容 |
|------|------|
| 单元测试 | 文档加载、切分、索引创建 |
| 集成测试 | 完整查询流程 |
| 功能测试 | 各种 Markdown 格式处理 |
| 性能测试 | 大文档集索引速度 |

### 8.2 测试文档

- 用少量已知文档验证答案准确性
- 测试中英文混合内容
- 测试代码块、表格等特殊格式

---

## 9. 依赖清单

```txt
# LlamaIndex 核心依赖
llama-index-core>=0.10.0
llama-index-readers-file>=0.1.0
llama-index-vector-stores-chroma>=0.1.0
llama-index-llms-ollama>=0.1.0
llama-index-embeddings-ollama>=0.1.0

# 向量数据库
chromadb>=0.4.0

# Web UI
streamlit>=1.28.0

# 嵌入和 LLM（通过 Ollama）
# ollama serve（单独安装）

# 测试
pytest>=7.4.0
pytest-mock>=3.12.0

# 工具
python-dotenv>=1.0.0
```

---

## 10. 配置说明

### 10.1 环境变量 (.env)

```bash
# Ollama 服务地址
OLLAMA_BASE_URL=http://localhost:11434

# LLM 模型
LLM_MODEL=qwen2.5:7b

# 嵌入模型
EMBED_MODEL=nomic-embed-text

# 文档目录
DOCS_DIR=data/docs

# 存储目录
STORAGE_DIR=storage/chroma

# 索引参数
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=3
```

### 10.2 Ollama 模型安装

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

---

## 11. 实现计划

1. **环境搭建** - 安装依赖、配置 Ollama
2. **文档加载** - 实现 MarkdownLoader
3. **索引管理** - 实现 VectorIndexManager
4. **查询引擎** - 实现 RAGQueryEngine
5. **Web 界面** - 实现 Streamlit UI
6. **测试优化** - 完善测试和错误处理

---

## 12. 后续扩展

- [ ] 支持更多文档格式（PDF, DOCX）
- [ ] 添加查询历史记录
- [ ] 支持多知识库切换
- [ ] 添加文档上传功能
- [ ] 集成到多 Agent 系统中

---

**文档状态**: ✅ 已批准
**下一步**: 调用 writing-plans 技能创建实现计划
