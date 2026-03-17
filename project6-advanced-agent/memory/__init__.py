"""
长记忆系统模块

提供向量存储、文档导入、规则学习等功能
"""

# 核心组件
from .vector_store import VectorStore, get_vector_store

# 可选组件（可能因依赖缺失而失败）
try:
    from .document_importer import DocumentImporter
    _document_importer_available = True
except ImportError:
    DocumentImporter = None
    _document_importer_available = False

try:
    from .rule_learner import RuleLearner, get_rule_learner
    _rule_learner_available = True
except ImportError:
    RuleLearner = None
    get_rule_learner = None
    _rule_learner_available = False

try:
    from .analytics import Analytics
    _analytics_available = True
except ImportError:
    Analytics = None
    _analytics_available = False

__all__ = [
    "VectorStore",
    "get_vector_store",
]

if _document_importer_available:
    __all__.append("DocumentImporter")

if _rule_learner_available:
    __all__.extend(["RuleLearner", "get_rule_learner"])

if _analytics_available:
    __all__.append("Analytics")
