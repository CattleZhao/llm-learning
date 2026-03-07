# workspace/example.py
"""示例代码文件 - 用于测试代码分析功能"""

import os
import sys
from typing import List, Dict, Any


class DataProcessor:
    """数据处理类 - 示例类"""

    def __init__(self, name: str):
        """初始化处理器"""
        self.name = name
        self.data = []

    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个数据项"""
        if not item:
            return {}

        result = {
            "name": item.get("name", ""),
            "value": item.get("value", 0) * 2,
            "processed": True
        }

        if result["value"] > 100:
            result["category"] = "high"
        elif result["value"] > 50:
            result["category"] = "medium"
        else:
            result["category"] = "low"

        return result

    def batch_process(self, items: List[Dict]) -> List[Dict]:
        """批量处理数据"""
        results = []
        for item in items:
            processed = self.process_item(item)
            results.append(processed)
        return results


def calculate_average(numbers: List[float]) -> float:
    """计算平均值"""
    if not numbers:
        return 0.0

    total = sum(numbers)
    return total / len(numbers)


def filter_data(data: List[Dict], threshold: float) -> List[Dict]:
    """过滤数据"""
    filtered = []
    for item in data:
        if item.get("value", 0) >= threshold:
            filtered.append(item)
    return filtered


# 主函数
if __name__ == "__main__":
    processor = DataProcessor("test")

    sample_data = [
        {"name": "item1", "value": 10},
        {"name": "item2", "value": 60},
        {"name": "item3", "value": 120}
    ]

    results = processor.batch_process(sample_data)

    for result in results:
        print(f"{result['name']}: {result['category']}")
