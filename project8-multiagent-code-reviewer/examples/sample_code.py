"""
Sample code for testing the multi-agent code reviewer.

This file contains various code patterns and potential issues
for the agents to detect and analyze.
"""

import os
from typing import List, Dict


def calculate_sum(numbers: List[int]) -> int:
    """Calculate the sum of a list of numbers."""
    total = 0
    for num in numbers:
        total = total + num
    return total


def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number (naive implementation)."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


class DataProcessor:
    """Process and transform data."""

    def __init__(self, data: Dict):
        self.data = data
        self.cache = {}

    def process_item(self, item_id: str) -> Dict:
        """Process a single item."""
        if item_id in self.cache:
            return self.cache[item_id]

        result = {}
        for key, value in self.data.items():
            result[key.upper()] = str(value).upper()

        self.cache[item_id] = result
        return result

    def process_all(self) -> List[Dict]:
        """Process all items in the dataset."""
        results = []
        for i in range(100):
            item_result = self.process_item(f"item_{i}")
            results.append(item_result)
        return results


# TODO: Refactor this function
def OLD_FUNCTION(x, y):
    a = x
    b = y
    c = a + b
    return c


def insecure_password_check(password: str) -> bool:
    """Check if password meets requirements (insecure implementation)."""
    # This is intentionally insecure for testing
    secrets = ["password123", "admin123", "letmein"]
    return password in secrets


# Hardcoded sensitive data (for security testing)
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
DATABASE_URL = "postgres://user:password@localhost:5432/mydb"


if __name__ == "__main__":
    # Simple test
    print(calculate_sum([1, 2, 3, 4, 5]))
    print(fibonacci(10))

    processor = DataProcessor({"name": "test", "value": "42"})
    print(processor.process_item("test_1"))
