# APK 分析长记忆系统设计文档

**日期:** 2026-03-17
**项目:** project6-advanced-agent
**状态:** 设计阶段

## 1. 概述

### 1.1 目标

为 APK 恶意行为分析 Agent 增强长记忆能力，实现：
- 自动学习新的恶意模式规则
- 相似样本快速检索与复用
- 历史分析数据的持久化存储与分析

### 1.2 技术选型

| 组件 | 技术选择 | 理由 |
|------|----------|------|
| 向量数据库 | Chroma DB | 轻量级，无需额外服务，Python 原生 API |
| Embedding 模型 | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) | 支持中英文，轻量级 |
| PDF 解析 | PyPDF2 | 基础 PDF 读取 |
| 规则提取 | Claude API (LLM) | 理解语义，处理各种格式的分析文档 |

### 1.3 不使用 LlamaIndex 的理由

- 数据结构简单（分析结果摘要），不需要复杂的文档分块
- 核心是信息提取，不是 RAG chunking
- 直接使用 Chroma API 更简单直观
- 减少依赖数量

## 2. 架构设计

### 2.1 模块结构

```
memory/
├── __init__.py              # 模块初始化
├── vector_store.py          # Chroma 向量存储封装
├── rule_learner.py          # AI 规则提取器
├── document_importer.py     # 历史文档导入器
└── analytics.py             # 数据分析
```

### 2.2 数据流

```
APK 分析 → 结果向量化 → Chroma 存储
                 ↓
            相似样本检索
                 ↓
            上下文注入 (RAG)
                 ↓
            规则学习 (AI 提取)
                 ↓
            人工审核 (Web UI)
                 ↓
            规则库更新
```

## 3. 数据结构

### 3.1 Chroma Document 结构

```python
{
    "id": "sha256_hash",
    "apk_path": "/path/to/app.apk",
    "source_file": "report1.pdf",
    "package": "com.malware.xxx",
    "malware_family": "TrojanAgent",
    "risk_level": "CRITICAL",
    "confidence": 0.95,
    "matched_rules": ["rule1", "rule2"],
    "ioc": {
        "domains": ["malware.com"],
        "ips": ["192.168.1.1"],
        "urls": ["http://..."]
    },
    "behaviors": ["发送premium短信", "窃取通讯录"],
    "permissions": ["SEND_SMS", "READ_CONTACTS"],
    "summary": "检测到XXX木马...",
    "full_report": "# APK安全分析报告\n...",
    "timestamp": "2024-03-17T10:30:00",
    "analysis_method": "llm_agent",
    "model": "claude-sonnet-4-20250514"
}
```

## 4. API 接口

### 4.1 VectorStore

```python
class VectorStore:
    def store_analysis(self, apk_hash: str, analysis_result: AgentResponse, metadata: Dict) -> str
    def search_similar(self, query: str, n_results: int = 5, filters: Optional[Dict] = None) -> List[Dict]
    def get_by_hash(self, apk_hash: str) -> Optional[Dict]
    def delete_by_hash(self, apk_hash: str) -> bool
    def get_stats(self) -> Dict
```

### 4.2 DocumentImporter

```python
class DocumentImporter:
    def import_pdf(self, pdf_path: str, extract_structured: bool = True) -> Dict
    def import_batch(self, directory: str, pattern: str = "*.pdf") -> List[Dict]
    def _extract_with_llm(self, text: str) -> Dict
```

### 4.3 RuleLearner

```python
class RuleLearner:
    def extract_candidate_rules(self, analysis: AgentResponse) -> List[Dict]
    def format_rule_for_review(self, candidate: Dict) -> str
    def save_approved_rule(self, rule: Dict, category: str) -> str
```

## 5. 与现有系统集成

### 5.1 LLMAPKAnalysisAgent 修改

在 `think()` 方法中：
1. 分析开始时检索相似历史
2. 复用相同 APK 的历史结果
3. 将相似样本注入 System Prompt
4. 分析完成后存储结果
5. 提取候选规则供用户审核

### 5.2 Web UI 增强

新增侧边栏标签页：
- **历史记录**: 查看和搜索历史分析
- **导入文档**: 上传并导入历史 PDF/TXT/MD 文件
- **候选规则**: 审核和批准 AI 提取的新规则

## 6. 错误处理

- Embedding 失败: 重试 3 次，指数退避
- 存储失败: 降级到文件系统保存
- PDF 解析失败: 抛出 ImportError，记录日志
- LLM 提取失败: 返回原始文本 + null 字段

## 7. 配置管理

```python
class MemorySettings(BaseSettings):
    chroma_persist_dir: Path = "memory/chroma"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    similarity_top_k: int = 5
    similarity_threshold: float = 0.7
    enable_auto_learning: bool = True
    candidate_rules_dir: Path = "memory/pending_rules"
```

## 8. 测试策略

- 单元测试: `test_vector_store.py`, `test_document_importer.py`
- 集成测试: 端到端分析流程
- 错误场景: 测试降级处理和重试机制

## 9. 实施步骤

1. 创建 memory 模块基础结构
2. 实现 VectorStore 类
3. 实现 DocumentImporter 类
4. 实现 RuleLearner 类
5. 修改 LLMAPKAnalysisAgent 集成长记忆
6. 修改 Web UI 添加管理界面
7. 添加测试
8. 更新依赖和配置

## 10. 新增依赖

```
chromadb>=0.4.0
sentence-transformers>=2.2.0
PyPDF2>=3.0.0
```
