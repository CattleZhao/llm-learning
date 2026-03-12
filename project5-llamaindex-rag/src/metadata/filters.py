"""
元数据过滤器

构建和应用元数据过滤条件
"""
from enum import Enum
from typing import Any, List, Dict, Optional
from dataclasses import dataclass
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters


class FilterOperator(Enum):
    """过滤操作符"""
    EQ = "eq"           # 等于
    NE = "ne"           # 不等于
    GT = "gt"           # 大于
    GTE = "gte"         # 大于等于
    LT = "lt"           # 小于
    LTE = "lte"         # 小于等于
    IN = "in"           # 包含于
    NIN = "nin"         # 不包含于
    CONTAINS = "contains"  # 字符串包含
    STARTS_WITH = "starts_with"  # 字符串开头
    ENDS_WITH = "ends_with"      # 字符串结尾


class FilterCondition(Enum):
    """条件组合方式"""
    AND = "and"
    OR = "or"


@dataclass
class MetadataFilter:
    """单个元数据过滤条件"""
    key: str                      # 元数据字段名
    value: Any                     # 比较值
    operator: FilterOperator = FilterOperator.EQ


class MetadataFilterBuilder:
    """
    元数据过滤器构建器

    提供流式 API 构建复杂的过滤条件
    """

    def __init__(self):
        self._filters: List[MetadataFilter] = []
        self._condition: FilterCondition = FilterCondition.AND

    def where(self, key: str, value: Any, operator: FilterOperator = FilterOperator.EQ):
        """
        添加过滤条件

        Args:
            key: 元数据字段名
            value: 比较值
            operator: 操作符

        Returns:
            self，支持链式调用
        """
        self._filters.append(MetadataFilter(key, value, operator))
        return self

    def eq(self, key: str, value: Any):
        """等于"""
        return self.where(key, value, FilterOperator.EQ)

    def ne(self, key: str, value: Any):
        """不等于"""
        return self.where(key, value, FilterOperator.NE)

    def gt(self, key: str, value: Any):
        """大于"""
        return self.where(key, value, FilterOperator.GT)

    def gte(self, key: str, value: Any):
        """大于等于"""
        return self.where(key, value, FilterOperator.GTE)

    def lt(self, key: str, value: Any):
        """小于"""
        return self.where(key, value, FilterOperator.LT)

    def lte(self, key: str, value: Any):
        """小于等于"""
        return self.where(key, value, FilterOperator.LTE)

    def in_(self, key: str, value: List[Any]):
        """包含于（列表）"""
        return self.where(key, value, FilterOperator.IN)

    def contains(self, key: str, value: str):
        """字符串包含"""
        return self.where(key, value, FilterOperator.CONTAINS)

    def and_condition(self):
        """设置为 AND 条件"""
        self._condition = FilterCondition.AND
        return self

    def or_condition(self):
        """设置为 OR 条件"""
        self._condition = FilterCondition.OR
        return self

    def build(self) -> MetadataFilters:
        """
        构建 LlamaIndex MetadataFilters

        Returns:
            MetadataFilters 对象
        """
        if not self._filters:
            return None

        llama_filters = []
        for f in self._filters:
            # 目前只支持精确匹配
            if f.operator == FilterOperator.EQ:
                llama_filters.append(
                    ExactMatchFilter(key=f.key, value=f.value)
                )
            else:
                # 其他操作符需要自定义实现
                print(f"[Warning] 操作符 {f.operator} 暂不支持，使用 EQ")
                llama_filters.append(
                    ExactMatchFilter(key=f.key, value=str(f.value))
                )

        return MetadataFilters(
            filters=llama_filters,
            condition=self._condition.value
        )

    def clear(self):
        """清空所有条件"""
        self._filters = []
        self._condition = FilterCondition.AND
        return self

    def to_dict(self) -> Dict:
        """转换为字典（用于存储或序列化）"""
        return {
            "filters": [
                {"key": f.key, "value": f.value, "operator": f.operator.value}
                for f in self._filters
            ],
            "condition": self._condition.value
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MetadataFilterBuilder':
        """从字典构建"""
        builder = cls()
        for f in data.get("filters", []):
            builder._filters.append(
                MetadataFilter(
                    key=f["key"],
                    value=f["value"],
                    operator=FilterOperator(f.get("operator", "eq"))
                )
            )
        builder._condition = FilterCondition(data.get("condition", "and"))
        return builder


# 预定义的常用过滤器
class CommonFilters:
    """常用过滤器预设"""

    @staticmethod
    def by_file_type(file_type: str) -> MetadataFilterBuilder:
        """按文件类型过滤"""
        return MetadataFilterBuilder().eq("file_type", file_type)

    @staticmethod
    def by_category(category: str) -> MetadataFilterBuilder:
        """按分类过滤"""
        return MetadataFilterBuilder().eq("category", category)

    @staticmethod
    def by_author(author: str) -> MetadataFilterBuilder:
        """按作者过滤"""
        return MetadataFilterBuilder().eq("author", author)

    @staticmethod
    def by_year(year: int) -> MetadataFilterBuilder:
        """按年份过滤"""
        return MetadataFilterBuilder().eq("year", year)

    @staticmethod
    def by_tag(tag: str) -> MetadataFilterBuilder:
        """按标签过滤（标签在数组中）"""
        return MetadataFilterBuilder().contains("tags", tag)

    @staticmethod
    def recent_years(years: int = 2) -> MetadataFilterBuilder:
        """过滤最近几年的文档"""
        from datetime import datetime
        current_year = datetime.now().year
        return MetadataFilterBuilder().gte("year", current_year - years)
