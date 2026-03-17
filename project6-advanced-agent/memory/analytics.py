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
            for m in all_data.get("metadatas", [])
        ]

        return dict(Counter(risk_levels))

    def get_top_malware_families(self, n: int = 10) -> List[tuple]:
        """获取最常见的恶意软件家族"""
        all_data = self.store.collection.get(include=["metadatas"])

        families = [
            m.get("malware_family", "Unknown")
            for m in all_data.get("metadatas", [])
            if m.get("malware_family")
        ]

        return Counter(families).most_common(n)

    def get_common_behaviors(self, n: int = 10) -> List[tuple]:
        """获取最常见的恶意行为"""
        all_data = self.store.collection.get(include=["metadatas"])

        behaviors = []
        for m in all_data.get("metadatas", []):
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
