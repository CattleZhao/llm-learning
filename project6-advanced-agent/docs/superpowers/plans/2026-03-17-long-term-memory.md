# Long-Term Memory Enhancement Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 APK 分析 Agent 添加长记忆能力，支持历史分析存储、相似样本检索、自动规则学习

**Architecture:** 使用 Chroma DB 作为向量存储，sentence-transformers 生成 embedding，通过 LLM 从分析结果和 PDF 文档中提取结构化信息

**Tech Stack:** chromadb, sentence-transformers, PyPDF2, Anthropic Claude API

---

## File Structure

```
memory/                              # 新增：长记忆模块
├── __init__.py                      # 模块导出
├── vector_store.py                  # Chroma 向量存储封装
├── document_importer.py             # 历史文档导入器
├── rule_learner.py                  # AI 规则提取器
└── analytics.py                     # 数据分析

agents/
└── apk_agent_llm.py                 # 修改：集成长记忆系统

app/
└── web.py                           # 修改：添加历史查看、导入、规则审核界面

tests/                               # 新增测试
├── test_vector_store.py
├── test_document_importer.py
└── test_rule_learner.py

scripts/
└── import_history.py                # CLI 导入脚本

config.py                            # 修改：添加 MemorySettings

requirements.txt                     # 修改：添加新依赖
```

---

## Chunk 1: 基础设施设置

### Task 1: 更新依赖配置

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 添加新依赖到 requirements.txt**

```bash
cat >> requirements.txt << 'EOF'

# Long-term memory
chromadb>=0.4.0
sentence-transformers>=2.2.0
PyPDF2>=3.0.0
EOF
```

- [ ] **Step 2: 安装新依赖**

Run: `pip install chromadb sentence-transformers PyPDF2`
Expected: 安装成功，无错误

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat(memory): add chromadb, sentence-transformers, PyPDF2 dependencies"
```

---

### Task 2: 更新配置管理

**Files:**
- Modify: `config.py`

- [ ] **Step 1: 添加 MemorySettings 类**

在 `config.py` 末尾添加：

```python
from pathlib import Path
from pydantic import Field
from typing import Optional


class MemorySettings(BaseSettings):
    """长记忆系统配置"""

    # 向量存储配置
    chroma_persist_dir: Path = Field(
        default="memory/chroma",
        description="Chroma DB 持久化目录"
    )

    # Embedding 模型配置
    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="支持中英文的轻量级模型"
    )

    # 相似度检索配置
    similarity_top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="检索相似样本数量"
    )

    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )

    # 规则学习配置
    enable_auto_learning: bool = Field(
        default=True,
        description="是否启用自动规则学习"
    )

    candidate_rules_dir: Path = Field(
        default="memory/pending_rules",
        description="候选规则存储目录"
    )

    class Config:
        env_prefix = "MEMORY_"


# 更新 get_settings() 函数，添加 memory 配置
def get_settings() -> Settings:
    """获取配置单例"""
    # ... 现有代码保持不变 ...
    # 确保 Settings 类有 memory 字段
```

- [ ] **Step 2: 更新 Settings 类添加 memory 字段**

在 `Settings` 类中添加：

```python
class Settings(BaseSettings):
    # ... 现有字段 ...

    memory: MemorySettings = Field(
        default_factory=MemorySettings,
        description="长记忆系统配置"
    )
```

- [ ] **Step 3: 验证配置加载**

Run: `python -c "from config import get_settings; s = get_settings(); print(s.memory.chroma_persist_dir)"`
Expected: 输出 `memory/chroma`

- [ ] **Step 4: Commit**

```bash
git add config.py
git commit -m "feat(config): add MemorySettings for long-term memory system"
```

---

## Chunk 2: VectorStore 实现

### Task 3: 创建 memory 模块基础

**Files:**
- Create: `memory/__init__.py`

- [ ] **Step 1: 创建 memory 模块初始化文件**

```python
"""
长记忆系统模块

提供向量存储、文档导入、规则学习等功能
"""

from .vector_store import VectorStore, get_vector_store
from .document_importer import DocumentImporter
from .rule_learner import RuleLearner, get_rule_learner
from .analytics import Analytics

__all__ = [
    "VectorStore",
    "get_vector_store",
    "DocumentImporter",
    "RuleLearner",
    "get_rule_learner",
    "Analytics",
]
```

- [ ] **Step 2: 创建必要目录**

Run: `mkdir -p memory/chroma memory/pending_rules`

- [ ] **Step 3: 创建 .gitkeep 保持目录结构**

Run: `touch memory/chroma/.gitkeep memory/pending_rules/.gitkeep`

- [ ] **Step 4: Commit**

```bash
git add memory/
git commit -m "feat(memory): create memory module structure"
```

---

### Task 4: 实现 VectorStore 类

**Files:**
- Create: `memory/vector_store.py`

- [ ] **Step 1: 编写 VectorStore 测试**

```python
# tests/test_vector_store.py

import pytest
from pathlib import Path
from memory.vector_store import VectorStore
from agents.base import AgentResponse

@pytest.fixture
def vector_store(tmp_path):
    """创建临时 VectorStore 实例"""
    store = VectorStore(persist_dir=str(tmp_path / "chroma"))
    return store

@pytest.fixture
def mock_analysis_result():
    """模拟分析结果"""
    return AgentResponse(
        content="# APK安全分析报告\n\n检测到高危恶意软件",
        metadata={
            "apk_path": "/test/app.apk",
            "risk_level": "HIGH",
            "package": "com.malware.test",
            "summary": "检测到高危恶意软件，具有短信盗窃行为"
        }
    )

def test_store_and_retrieve(vector_store, mock_analysis_result):
    """测试存储和检索"""
    apk_hash = "test123"

    # 存储
    result_id = vector_store.store_analysis(
        apk_hash=apk_hash,
        analysis_result=mock_analysis_result
    )

    assert result_id == apk_hash

    # 检索
    retrieved = vector_store.get_by_hash(apk_hash)
    assert retrieved is not None
    assert retrieved["package"] == "com.malware.test"

def test_search_similar(vector_store, mock_analysis_result):
    """测试相似度检索"""
    apk_hash = "test456"

    vector_store.store_analysis(
        apk_hash=apk_hash,
        analysis_result=mock_analysis_result
    )

    # 搜索相似
    results = vector_store.search_similar(
        query="恶意软件短信",
        n_results=1
    )

    assert len(results) > 0
    assert results[0]["apk_hash"] == apk_hash

def test_get_stats(vector_store):
    """测试统计信息"""
    stats = vector_store.get_stats()

    assert "total_count" in stats
    assert "high_risk_count" in stats
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_vector_store.py -v`
Expected: FAIL - `VectorStore` not defined

- [ ] **Step 3: 实现 VectorStore 类**

```python
# memory/vector_store.py

"""
向量存储模块

使用 Chroma DB 存储 APK 分析结果的向量表示
"""
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings

from agents.base import AgentResponse
from config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储封装类"""

    def __init__(self, persist_dir: Optional[str] = None):
        """
        初始化向量存储

        Args:
            persist_dir: Chroma 持久化目录
        """
        settings = get_settings()

        if persist_dir is None:
            persist_dir = str(settings.memory.chroma_persist_dir)

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Chroma 客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="apk_analyses",
            metadata={"description": "APK analysis results"}
        )

        # 初始化 embedding 模型
        self.embedding_model = SentenceTransformer(
            settings.memory.embedding_model
        )

        logger.info(f"VectorStore initialized at {self.persist_dir}")

    def _embed_with_retry(self, text: str, max_retries: int = 3) -> List[float]:
        """
        生成 embedding，带重试机制

        Args:
            text: 输入文本
            max_retries: 最大重试次数

        Returns:
            embedding 向量
        """
        for attempt in range(max_retries):
            try:
                return self.embedding_model.encode(
                    text,
                    convert_to_numpy=True,
                    show_progress_bar=False
                ).tolist()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Embedding failed after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Embedding failed (attempt {attempt + 1}), retrying...")
                time.sleep(2 ** attempt)

    def store_analysis(
        self,
        apk_hash: str,
        analysis_result: AgentResponse,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        存储分析结果

        Args:
            apk_hash: APK SHA256 hash
            analysis_result: 分析结果
            metadata: 额外的元数据

        Returns:
            存储的文档 ID
        """
        if not apk_hash:
            raise ValueError("apk_hash is required")

        if not analysis_result.content:
            raise ValueError("analysis_result.content is required")

        # 合并元数据
        final_metadata = metadata or {}
        final_metadata.update({
            "apk_hash": apk_hash,
            "risk_level": analysis_result.metadata.get("risk_level", "UNKNOWN"),
            "package": analysis_result.metadata.get("package", ""),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })

        # 使用 summary 或 content 生成 embedding
        text_to_embed = (
            analysis_result.metadata.get("summary") or
            analysis_result.content[:1000]
        )

        embedding = self._embed_with_retry(text_to_embed)

        # 删除已存在的（如果有的话）
        try:
            self.collection.delete(ids=[apk_hash])
        except:
            pass

        # 存储到 Chroma
        self.collection.add(
            ids=[apk_hash],
            embeddings=[embedding],
            documents=[analysis_result.content],
            metadatas=[final_metadata]
        )

        logger.info(f"Stored analysis for {apk_hash}")
        return apk_hash

    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相似分析

        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            相似分析列表
        """
        settings = get_settings()
        if n_results is None:
            n_results = settings.memory.similarity_top_k

        query_embedding = self._embed_with_retry(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )

        # 格式化结果
        formatted_results = []
        for i, doc_id in enumerate(results["ids"][0]):
            formatted_results.append({
                "apk_hash": doc_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })

        return formatted_results

    def get_by_hash(self, apk_hash: str) -> Optional[Dict[str, Any]]:
        """
        根据 hash 获取分析记录

        Args:
            apk_hash: APK hash

        Returns:
            分析记录，如果不存在返回 None
        """
        results = self.collection.get(
            ids=[apk_hash],
            include=["documents", "metadatas"]
        )

        if not results["ids"]:
            return None

        return {
            "apk_hash": results["ids"][0],
            "content": results["documents"][0],
            "metadata": results["metadatas"][0]
        }

    def delete_by_hash(self, apk_hash: str) -> bool:
        """
        删除分析记录

        Args:
            apk_hash: APK hash

        Returns:
            是否删除成功
        """
        try:
            self.collection.delete(ids=[apk_hash])
            return True
        except Exception as e:
            logger.error(f"Failed to delete {apk_hash}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        count = self.collection.count()

        # 获取所有记录的元数据
        all_data = self.collection.get(include=["metadatas"])

        high_risk_count = sum(
            1 for m in all_data["metadatas"]
            if m.get("risk_level") in ["HIGH", "CRITICAL"]
        )

        return {
            "total_count": count,
            "high_risk_count": high_risk_count
        }


def get_vector_store() -> VectorStore:
    """获取 VectorStore 单例"""
    return VectorStore()
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_vector_store.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add memory/vector_store.py tests/test_vector_store.py
git commit -m "feat(memory): implement VectorStore with Chroma DB"
```

---

## Chunk 3: DocumentImporter 实现

### Task 5: 实现 DocumentImporter 类

**Files:**
- Create: `memory/document_importer.py`
- Create: `tests/test_document_importer.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_document_importer.py

import pytest
from pathlib import Path
from memory.document_importer import DocumentImporter

@pytest.fixture
def importer(tmp_path):
    """创建临时 importer 实例"""
    return DocumentImporter()

@pytest.fixture
def sample_pdf(tmp_path):
    """创建测试 PDF 文件"""
    # 这里使用简单的文本文件模拟，实际测试需要真实 PDF
    pdf_path = tmp_path / "test_report.txt"
    pdf_path.write_text("""
    APK 安全分析报告

    包名: com.malware.trojan
    恶意软件家族: TrojanAgent
    风险等级: CRITICAL

    威胁指标:
    - 192.168.1.100
    - malware.c2-server.com

    恶意行为:
    - 发送 premium 短信
    - 窃取通讯录
    - 远程控制

    权限:
    - SEND_SMS
    - READ_CONTACTS
    - ACCESS_FINE_LOCATION

    该木马具有典型的短信盗窃行为，会后台发送
    premium 短信并删除发送记录。
    """)
    return pdf_path

def test_import_document(importer, sample_pdf):
    """测试文档导入"""
    result = importer.import_text_file(str(sample_pdf))

    assert result is not None
    assert result["source_file"] == sample_pdf.name
    assert "summary" in result

def test_extract_with_llm_mock(importer, sample_pdf):
    """测试 LLM 提取（mock）"""
    text = sample_pdf.read_text()

    # Mock LLM 调用
    result = importer._extract_with_llm(text, use_mock=True)

    assert result["package"] == "com.malware.trojan"
    assert result["risk_level"] == "CRITICAL"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_document_importer.py -v`
Expected: FAIL - `DocumentImporter` not defined

- [ ] **Step 3: 实现 DocumentImporter 类**

```python
# memory/document_importer.py

"""
文档导入模块

从历史分析文档（PDF、TXT、MD）中提取结构化信息
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import PyPDF2
from anthropic import Anthropic

from config import get_settings

logger = logging.getLogger(__name__)


class DocumentImporter:
    """历史文档导入器"""

    def __init__(self, vector_store=None):
        """
        初始化导入器

        Args:
            vector_store: VectorStore 实例，可选
        """
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.vector_store = vector_store

    def import_pdf(
        self,
        pdf_path: str,
        extract_structured: bool = True
    ) -> Dict[str, Any]:
        """
        导入 PDF 文档

        Args:
            pdf_path: PDF 文件路径
            extract_structured: 是否提取结构化信息

        Returns:
            导入结果
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # 提取文本
        text = self._extract_text_from_pdf(pdf_path)

        if extract_structured:
            # 使用 LLM 提取结构化信息
            structured_data = self._extract_with_llm(text)
        else:
            structured_data = {
                "raw_text": text,
                "summary": text[:500]
            }

        structured_data["source_file"] = pdf_path.name

        # 如果有 vector_store，存储进去
        if self.vector_store:
            self._store_imported_data(structured_data)

        logger.info(f"Imported PDF: {pdf_path.name}")
        return structured_data

    def import_text_file(
        self,
        file_path: str,
        extract_structured: bool = True
    ) -> Dict[str, Any]:
        """
        导入文本文件（TXT、MD）

        Args:
            file_path: 文件路径
            extract_structured: 是否提取结构化信息

        Returns:
            导入结果
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = file_path.read_text(encoding="utf-8")

        if extract_structured:
            structured_data = self._extract_with_llm(text)
        else:
            structured_data = {
                "raw_text": text,
                "summary": text[:500]
            }

        structured_data["source_file"] = file_path.name

        if self.vector_store:
            self._store_imported_data(structured_data)

        logger.info(f"Imported text file: {file_path.name}")
        return structured_data

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """从 PDF 提取文本"""
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception as e:
            raise ImportError(f"Failed to parse PDF: {e}")

    def _extract_with_llm(
        self,
        text: str,
        use_mock: bool = False
    ) -> Dict[str, Any]:
        """
        使用 LLM 提取结构化信息

        Args:
            text: 原始文本
            use_mock: 是否使用 mock 模式（测试用）

        Returns:
            结构化数据
        """
        if use_mock:
            return self._mock_extract(text)

        prompt = f"""
请从以下恶意软件分析报告中提取结构化信息。

报告内容：
{text[:4000]}

请提取（如果有的话）：
- package: APK 包名
- malware_family: 恶意软件家族名称
- risk_level: 风险等级 (LOW/MEDIUM/HIGH/CRITICAL)
- ioc: 威胁指标列表 (IP、域名、URL等)，用列表表示
- behaviors: 恶意行为描述列表
- permissions: 相关权限列表
- summary: 简短摘要（100字以内）

以 JSON 格式返回，找不到的字段填 null。
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            result = json.loads(response.content[0].text)

            # 确保 summary 存在
            if not result.get("summary"):
                result["summary"] = text[:200]

            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # 降级：返回基本结构
            return {
                "package": None,
                "malware_family": None,
                "risk_level": "MEDIUM",
                "ioc": [],
                "behaviors": [],
                "permissions": [],
                "summary": text[:200],
                "raw_text": text
            }

    def _mock_extract(self, text: str) -> Dict[str, Any]:
        """Mock 提取（测试用）"""
        return {
            "package": "com.malware.trojan",
            "malware_family": "TrojanAgent",
            "risk_level": "CRITICAL",
            "ioc": {
                "domains": ["malware.c2-server.com"],
                "ips": ["192.168.1.100"],
                "urls": []
            },
            "behaviors": ["发送 premium 短信", "窃取通讯录", "远程控制"],
            "permissions": ["SEND_SMS", "READ_CONTACTS", "ACCESS_FINE_LOCATION"],
            "summary": "该木马具有典型的短信盗窃行为，会后台发送 premium 短信并删除发送记录。"
        }

    def _store_imported_data(self, data: Dict[str, Any]):
        """将导入的数据存储到向量库"""
        if not self.vector_store:
            return

        from agents.base import AgentResponse

        # 生成文档 ID（使用文件名）
        doc_id = f"imported_{data.get('source_file', 'unknown')}"

        response = AgentResponse(
            content=data.get("summary", ""),
            metadata=data
        )

        self.vector_store.store_analysis(
            apk_hash=doc_id,
            analysis_result=response
        )

    def import_batch(
        self,
        directory: str,
        pattern: str = "*.pdf"
    ) -> List[Dict[str, Any]]:
        """
        批量导入目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            导入结果列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = list(dir_path.glob(pattern))
        results = []

        for file_path in files:
            try:
                if file_path.suffix.lower() == ".pdf":
                    result = self.import_pdf(str(file_path))
                else:
                    result = self.import_text_file(str(file_path))
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to import {file_path.name}: {e}")
                results.append({
                    "source_file": file_path.name,
                    "error": str(e)
                })

        logger.info(f"Batch import complete: {len(results)} files processed")
        return results
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_document_importer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add memory/document_importer.py tests/test_document_importer.py
git commit -m "feat(memory): implement DocumentImporter for historical documents"
```

---

## Chunk 4: RuleLearner 实现

### Task 6: 实现 RuleLearner 类

**Files:**
- Create: `memory/rule_learner.py`
- Create: `tests/test_rule_learner.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_rule_learner.py

import pytest
from pathlib import Path
from memory.rule_learner import RuleLearner
from agents.base import AgentResponse

@pytest.fixture
def rule_learner(tmp_path):
    """创建临时 RuleLearner 实例"""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    return RuleLearner(rules_dir=str(rules_dir))

def test_extract_candidate_rules(rule_learner):
    """测试候选规则提取"""
    analysis = AgentResponse(
        content="# 分析报告\n发现恶意包路径: com/malware/payload/Attack",
        metadata={
            "matched_rules": ["rule1"],
            "behaviors": ["短信盗窃"]
        }
    )

    candidates = rule_learner.extract_candidate_rules(analysis)

    assert len(candidates) > 0
    assert "pattern" in candidates[0]

def test_save_and_load_rule(rule_learner, tmp_path):
    """测试规则保存和加载"""
    rule = {
        "name": "测试规则",
        "pattern": "com/malware/.*",
        "category": "test"
    }

    file_path = rule_learner.save_to_pending(rule)

    assert Path(file_path).exists()

    loaded = rule_learner.load_pending_rules()
    assert len(loaded) > 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_rule_learner.py -v`
Expected: FAIL - `RuleLearner` not defined

- [ ] **Step 3: 实现 RuleLearner 类**

```python
# memory/rule_learner.py

"""
规则学习模块

从分析结果中提取候选恶意模式规则
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List
from anthropic import Anthropic

from config import get_settings

logger = logging.getLogger(__name__)


class RuleLearner:
    """规则学习器"""

    def __init__(self, pending_dir: str = None):
        """
        初始化规则学习器

        Args:
            pending_dir: 候选规则存储目录
        """
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)

        if pending_dir is None:
            pending_dir = str(settings.memory.candidate_rules_dir)

        self.pending_dir = Path(pending_dir)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def extract_candidate_rules(
        self,
        analysis_result
    ) -> List[Dict[str, Any]]:
        """
        从分析结果中提取候选规则

        Args:
            analysis_result: AgentResponse 实例

        Returns:
            候选规则列表
        """
        prompt = f"""
请从以下 APK 分析结果中提取可能的新检测规则。

分析报告：
{analysis_result.content[:3000]}

元数据：
{json.dumps(analysis_result.metadata, ensure_ascii=False, indent=2)}

请提取：
1. 新的包路径模式（正则表达式）
2. 新的恶意行为模式
3. 新的威胁指标（域名、IP）

对每个发现的模式，输出一个 JSON 规则：
{{
    "name": "规则名称",
    "category": "类别（trojan/ransomware/spyware等）",
    "severity": "严重程度（low/medium/high/critical）",
    "description": "规则描述",
    "pattern": "正则表达式模式（仅包路径规则）",
    "indicators": {{"domains": [], "ips": [], "urls": []}},
    "reason": "为什么这个模式可疑"
}}

只输出明确的恶意模式，不要过度泛化。
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # 解析 JSON 规则
            rules = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        rule = json.loads(line)
                        rule["id"] = str(uuid.uuid4())
                        rules.append(rule)
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Extracted {len(rules)} candidate rules")
            return rules

        except Exception as e:
            logger.error(f"Failed to extract rules: {e}")
            return []

    def save_to_pending(
        self,
        rule: Dict[str, Any]
    ) -> str:
        """
        保存候选规则到待审核目录

        Args:
            rule: 规则字典

        Returns:
            保存的文件路径
        """
        rule_id = rule.get("id", str(uuid.uuid4()))
        file_path = self.pending_dir / f"{rule_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rule, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved candidate rule to {file_path}")
        return str(file_path)

    def load_pending_rules(self) -> List[Dict[str, Any]]:
        """
        加载所有待审核的规则

        Returns:
            待审核规则列表
        """
        rules = []

        for file_path in self.pending_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    rule = json.load(f)
                    rule["id"] = file_path.stem
                    rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        return rules

    def approve_rule(
        self,
        rule_id: str,
        category: str = "custom"
    ) -> str:
        """
        批准规则并添加到规则库

        Args:
            rule_id: 规则 ID
            category: 规则类别

        Returns:
            保存的文件路径
        """
        # 加载候选规则
        rule_file = self.pending_dir / f"{rule_id}.json"
        if not rule_file.exists():
            raise FileNotFoundError(f"Rule not found: {rule_id}")

        with open(rule_file, "r", encoding="utf-8") as f:
            rule = json.load(f)

        # 删除候选规则
        rule_file.unlink()

        # 保存到正式规则库
        from knowledge_base import get_rule_loader
        rule_loader = get_rule_loader()

        rules_dir = Path(rule_loader.rules_dir) / "custom"
        rules_dir.mkdir(parents=True, exist_ok=True)

        # 添加到 custom_rules.json
        custom_rules_file = rules_dir / "custom_rules.json"

        existing_rules = []
        if custom_rules_file.exists():
            with open(custom_rules_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_rules = data.get("rules", [])

        # 添加新规则
        rule["category"] = category
        existing_rules.append(rule)

        # 保存
        with open(custom_rules_file, "w", encoding="utf-8") as f:
            json.dump({"rules": existing_rules}, f, ensure_ascii=False, indent=2)

        logger.info(f"Approved rule {rule_id} added to custom rules")
        return str(custom_rules_file)

    def reject_rule(self, rule_id: str) -> bool:
        """
        拒绝并删除候选规则

        Args:
            rule_id: 规则 ID

        Returns:
            是否删除成功
        """
        rule_file = self.pending_dir / f"{rule_id}.json"

        if rule_file.exists():
            rule_file.unlink()
            logger.info(f"Rejected rule {rule_id}")
            return True

        return False


def get_rule_learner() -> RuleLearner:
    """获取 RuleLearner 单例"""
    return RuleLearner()
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_rule_learner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add memory/rule_learner.py tests/test_rule_learner.py
git commit -m "feat(memory): implement RuleLearner for AI-powered rule extraction"
```

---

## Chunk 5: 集成到现有 Agent

### Task 7: 修改 LLMAPKAnalysisAgent

**Files:**
- Modify: `agents/apk_agent_llm.py`

- [ ] **Step 1: 添加导入和初始化**

在 `agents/apk_agent_llm.py` 顶部添加导入：

```python
from memory import get_vector_store, get_rule_learner
```

在 `LLMAPKAnalysisAgent.__init__` 中添加：

```python
# 初始化长记忆系统
self.vector_store = get_vector_store()
self.rule_learner = get_rule_learner()
```

- [ ] **Step 2: 修改 think() 方法集成记忆检索**

在 `think()` 方法的 APK 路径提取之后，历史记录加载之前，添加：

```python
# 检索相似历史分析
if not history:
    similar = self.vector_store.search_similar(
        query=f"{Path(apk_path).name} APK analysis",
        n_results=3
    )

    if similar:
        similar_context = "\n\n".join([
            f"相似样本 {i+1}:\n包名: {s['metadata'].get('package', 'unknown')}\n"
            f"风险等级: {s['metadata'].get('risk_level', 'unknown')}\n"
            f"摘要: {s.get('content', '')[:200]}"
            for i, s in enumerate(similar)
        ])
        self.on_status_update(f"📚 找到 {len(similar)} 个相似历史样本")

        # 注入到 System Prompt
        self.system_prompt += f"""

参考历史分析：
{similar_context}

请参考这些相似样本的分析方式。
"""
```

- [ ] **Step 3: 在分析完成后存储结果和提取规则**

在 `think()` 方法返回 `AgentResponse` 之前，添加：

```python
# 存储分析结果到向量库
try:
    self.vector_store.store_analysis(
        apk_hash=apk_hash,
        analysis_result=AgentResponse(
            content=final_response,
            metadata=metadata
        ),
        metadata=metadata
    )
    self.on_status_update("💾 分析结果已保存到长记忆")
except Exception as e:
    logger.warning(f"Failed to store to vector store: {e}")

# 提取候选规则（如果启用了自动学习）
settings = get_settings()
if settings.memory.enable_auto_learning:
    try:
        candidates = self.rule_learner.extract_candidate_rules(
            AgentResponse(content=final_response, metadata=metadata)
        )

        if candidates:
            for candidate in candidates:
                self.rule_learner.save_to_pending(candidate)

            self.on_status_update(f"🎯 提取了 {len(candidates)} 条候选规则，请在 Web UI 中审核")
    except Exception as e:
        logger.warning(f"Failed to extract candidate rules: {e}")
```

- [ ] **Step 4: 运行集成测试**

Run: `python -c "
from agents.apk_agent_llm import create_llm_agent
agent = create_llm_agent(mcp_server_path='/root/Learn/jadx-mcp-server')
print('Agent created successfully')
print('Vector store:', agent.vector_store)
print('Rule learner:', agent.rule_learner)
"`
Expected: 输出成功创建信息

- [ ] **Step 5: Commit**

```bash
git add agents/apk_agent_llm.py
git commit -m "feat(agent): integrate long-term memory into LLMAPKAnalysisAgent"
```

---

## Chunk 6: Web UI 增强

### Task 8: 添加历史记录查看界面

**Files:**
- Modify: `app/web.py`

- [ ] **Step 1: 在侧边栏添加历史记录标签页**

在 `app/web.py` 的侧边栏部分添加：

```python
# 长记忆管理
st.markdown("---")
st.header("📚 长记忆管理")

memory_tab1, memory_tab2, memory_tab3 = st.tabs(["历史记录", "导入文档", "候选规则"])

with memory_tab1:
    show_history_view()

with memory_tab2:
    show_document_import()

with memory_tab3:
    show_rule_review()
```

- [ ] **Step 2: 实现历史记录查看函数**

```python
def show_history_view():
    """显示历史分析记录"""
    from memory import get_vector_store

    vector_store = get_vector_store()

    # 显示统计信息
    stats = vector_store.get_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 总分析数", stats["total_count"])
    with col2:
        st.metric("🔴 高风险样本", stats["high_risk_count"])

    st.markdown("---")

    # 搜索历史
    search_query = st.text_input("🔍 搜索相似分析")

    if search_query:
        with st.spinner("搜索中..."):
            results = vector_store.search_similar(search_query, n_results=5)

        if results:
            for i, result in enumerate(results):
                with st.expander(
                    f"{result['metadata'].get('package', 'unknown')} - "
                    f"{result['metadata'].get('risk_level', 'UNKNOWN')}"
                ):
                    st.markdown(f"**摘要:** {result.get('content', '')[:300]}")
                    st.caption(f"时间: {result['metadata'].get('timestamp', 'unknown')}")
        else:
            st.info("未找到相似记录")
```

- [ ] **Step 3: 实现文档导入函数**

```python
def show_document_import():
    """文档导入界面"""
    from memory import DocumentImporter, get_vector_store

    vector_store = get_vector_store()
    importer = DocumentImporter(vector_store=vector_store)

    uploaded_files = st.file_uploader(
        "上传历史分析文档",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        help="支持 PDF、TXT、MD 格式的历史分析文档"
    )

    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")

        if st.button("📥 开始导入", type="primary"):
            progress_bar = st.progress(0)
            success_count = 0

            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)

            for i, uploaded_file in enumerate(uploaded_files):
                # 保存临时文件
                temp_path = uploads_dir / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 导入
                try:
                    with st.spinner(f"处理 {uploaded_file.name}..."):
                        if uploaded_file.name.endswith(".pdf"):
                            importer.import_pdf(str(temp_path))
                        else:
                            importer.import_text_file(str(temp_path))

                    success_count += 1
                    st.success(f"✅ {uploaded_file.name} 导入成功")

                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} 导入失败: {e}")

                # 清理临时文件
                temp_path.unlink()

                progress_bar.progress((i + 1) / len(uploaded_files))

            st.info(f"导入完成: {success_count}/{len(uploaded_files)} 成功")
```

- [ ] **Step 4: 实现规则审核函数**

```python
def show_rule_review():
    """规则审核界面"""
    from memory import get_rule_learner

    rule_learner = get_rule_learner()
    candidates = rule_learner.load_pending_rules()

    if not candidates:
        st.info("暂无待审核规则")
        return

    st.info(f"有 {len(candidates)} 条候选规则待审核")

    for candidate in candidates:
        rule_id = candidate.get("id", "unknown")

        with st.expander(f"📋 {candidate.get('name', '未命名规则')}"):
            # 显示规则详情
            col1, col2 = st.columns(2)

            with col1:
                st.write("**类别:**", candidate.get("category", "unknown"))
                st.write("**严重程度:**", candidate.get("severity", "unknown"))

            with col2:
                st.write("**模式:**", candidate.get("pattern", "无"))

            st.markdown("**描述:**")
            st.markdown(candidate.get("description", ""))

            if candidate.get("reason"):
                st.markdown("**理由:**")
                st.caption(candidate["reason"])

            # 审核按钮
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button("✅ 批准", key=f"approve_{rule_id}"):
                    try:
                        rule_learner.approve_rule(rule_id)
                        st.success("规则已添加到规则库")
                        st.rerun()
                    except Exception as e:
                        st.error(f"批准失败: {e}")

            with btn_col2:
                if st.button("❌ 拒绝", key=f"reject_{rule_id}"):
                    if rule_learner.reject_rule(rule_id):
                        st.success("规则已删除")
                        st.rerun()
                    else:
                        st.error("删除失败")
```

- [ ] **Step 5: 测试 Web UI**

Run: `streamlit run app/web.py`
Expected: Web UI 启动成功，侧边栏显示"长记忆管理"标签

- [ ] **Step 6: Commit**

```bash
git add app/web.py
git commit -m "feat(web): add long-term memory management UI"
```

---

## Chunk 7: CLI 导入脚本

### Task 9: 创建 CLI 导入脚本

**Files:**
- Create: `scripts/import_history.py`

- [ ] **Step 1: 创建脚本**

```python
#!/usr/bin/env python3
"""
历史文档批量导入脚本

用法:
    python scripts/import_history.py --dir knowledge_base/raw/analyses/
    python scripts/import_history.py --file report.pdf
"""
import argparse
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import DocumentImporter, get_vector_store

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="导入历史分析文档")
    parser.add_argument("--dir", help="批量导入目录")
    parser.add_argument("--file", help="单个文件")
    parser.add_argument("--pattern", default="*.pdf", help="文件匹配模式")

    args = parser.parse_args()

    vector_store = get_vector_store()
    importer = DocumentImporter(vector_store=vector_store)

    if args.file:
        # 单个文件导入
        logger.info(f"导入文件: {args.file}")

        try:
            result = importer.import_pdf(args.file)
            logger.info(f"✅ 导入成功: {result.get('source_file')}")
        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")

    elif args.dir:
        # 批量导入
        dir_path = Path(args.dir)

        if not dir_path.exists():
            logger.error(f"目录不存在: {args.dir}")
            return

        logger.info(f"批量导入目录: {args.dir}")
        logger.info(f"匹配模式: {args.pattern}")

        results = importer.import_batch(str(dir_path), args.pattern)

        success = sum(1 for r in results if "error" not in r)
        failed = len(results) - success

        logger.info(f"\n导入完成:")
        logger.info(f"  ✅ 成功: {success}")
        logger.info(f"  ❌ 失败: {failed}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 添加执行权限**

Run: `chmod +x scripts/import_history.py`

- [ ] **Step 3: 测试脚本**

Run: `python scripts/import_history.py --help`
Expected: 显示帮助信息

- [ ] **Step 4: Commit**

```bash
git add scripts/import_history.py
git commit -m "feat(cli): add import_history.py for batch document import"
```

---

## Chunk 8: Analytics 模块（可选）

### Task 10: 实现 Analytics 类

**Files:**
- Create: `memory/analytics.py`

- [ ] **Step 1: 实现 Analytics 类**

```python
"""
数据分析模块

提供历史分析数据的统计和趋势分析
"""
import logging
from typing import Any, Dict, List
from collections import Counter

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class Analytics:
    """数据分析器"""

    def __init__(self, vector_store: VectorStore = None):
        """
        初始化分析器

        Args:
            vector_store: VectorStore 实例
        """
        if vector_store is None:
            from . import get_vector_store
            vector_store = get_vector_store()

        self.store = vector_store

    def get_risk_distribution(self) -> Dict[str, int]:
        """获取风险等级分布"""
        # 获取所有记录
        all_data = self.store.collection.get(include=["metadatas"])

        risk_levels = [
            m.get("risk_level", "UNKNOWN")
            for m in all_data["metadatas"]
        ]

        return dict(Counter(risk_levels))

    def get_top_malware_families(self, n: int = 10) -> List[tuple]:
        """获取最常见的恶意软件家族"""
        all_data = self.store.collection.get(include=["metadatas"])

        families = [
            m.get("malware_family", "Unknown")
            for m in all_data["metadatas"]
            if m.get("malware_family")
        ]

        return Counter(families).most_common(n)

    def get_common_behaviors(self, n: int = 10) -> List[tuple]:
        """获取最常见的恶意行为"""
        all_data = self.store.collection.get(include=["metadatas"])

        behaviors = []
        for m in all_data["metadatas"]:
            behaviors.extend(m.get("behaviors", []))

        return Counter(behaviors).most_common(n)

    def get_summary(self) -> Dict[str, Any]:
        """获取综合统计摘要"""
        risk_dist = self.get_risk_distribution()
        top_families = self.get_top_malware_families(5)
        common_behaviors = self.get_common_behaviors(5)

        return {
            "risk_distribution": risk_dist,
            "top_malware_families": top_families,
            "common_behaviors": common_behaviors,
            "total_analyses": self.store.collection.count()
        }
```

- [ ] **Step 2: 更新 memory/__init__.py**

```python
from .analytics import Analytics

__all__ = [..., "Analytics"]
```

- [ ] **Step 3: Commit**

```bash
git add memory/analytics.py memory/__init__.py
git commit -m "feat(memory): add Analytics for data insights"
```

---

## 最终验证

### Task 11: 端到端测试

- [ ] **Step 1: 运行所有测试**

Run: `pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 2: 启动 Web UI 验证**

Run: `streamlit run app/web.py`

验证步骤：
1. 侧边栏显示"长记忆管理"标签
2. 可以上传和导入文档
3. 可以搜索历史记录
4. 分析完成后显示候选规则

- [ ] **Step 3: 测试完整流程**

1. 分析一个 APK
2. 检查结果是否保存到向量库
3. 再次分析相同 APK，验证是否复用缓存
4. 检查是否提取了候选规则
5. 在 Web UI 中审核规则

- [ ] **Step 4: 最终提交**

```bash
git add .
git commit -m "feat(long-term-memory): complete implementation of long-term memory system

- VectorStore with Chroma DB
- DocumentImporter for PDF/TXT/MD files
- RuleLearner for AI-powered rule extraction
- Integration with LLMAPKAnalysisAgent
- Web UI for history viewing and rule review
- CLI import script

Tested and verified end-to-end functionality."
```

---

## 实施完成检查清单

- [ ] 所有测试通过
- [ ] Web UI 正常工作
- [ ] 可以导入历史文档
- [ ] 可以搜索相似历史
- [ ] 可以审核候选规则
- [ ] 分析结果正确保存
- [ ] 相同 APK 复用缓存
- [ ] 文档已更新

---

**计划状态:** ✅ 完成
**预计工时:** 4-6 小时
**优先级:** 高
