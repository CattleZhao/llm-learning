"""
长记忆系统模块

提供向量存储、文档导入、规则学习等功能
"""

try:
    from .vector_store import VectorStore, get_vector_store
    _vector_store_available = True
except ImportError:
    _vector_store_available = False

from .document_importer import DocumentImporter

__all__ = [
    "DocumentImporter",
]

if _vector_store_available:
    __all__.extend(["VectorStore", "get_vector_store"])

# Import additional modules when they are implemented
# from .rule_learner import RuleLearner, get_rule_learner
# from .analytics import Analytics
