"""
知识库模块

提供规则加载、恶意模式管理和 PDF 解析功能
"""
from knowledge_base.malware_patterns import MalwareKnowledgeBase, get_knowledge_base
from knowledge_base.loaders.rule_loader import RuleLoader, MalwareRule, get_rule_loader

__all__ = [
    # 原有的知识库
    "MalwareKnowledgeBase",
    "get_knowledge_base",
    # 新增的规则加载器
    "RuleLoader",
    "MalwareRule",
    "get_rule_loader",
]
