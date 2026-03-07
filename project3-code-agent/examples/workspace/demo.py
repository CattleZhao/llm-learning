
"""演示模块"""

import os
from typing import List, Dict


def calculate_sum(numbers: List[int]) -> int:
    """计算列表中数字的总和"""
    total = 0
    for num in numbers:
        total += num
    return total


class DataProcessor:
    """数据处理器类"""

    def __init__(self, name: str):
        self.name = name
        self.data = []

    def add_data(self, item: Dict) -> None:
        self.data.append(item)

    def get_summary(self) -> Dict:
        return {
            "name": self.name,
            "count": len(self.data)
        }
