"""
APK 分析报告解析器

负责从 LLM 生成的报告中提取结构化信息
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReportParser:
    """解析 LLM 生成的 APK 分析报告"""

    @staticmethod
    def parse_risk_level(report: str) -> str:
        """
        从报告中解析风险等级

        Args:
            report: LLM 生成的报告文本

        Returns:
            风险等级: low, medium, high, critical
        """
        # 查找风险等级关键词
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if level in report.upper():
                return level.lower()
        return "low"

    @staticmethod
    def parse_findings_count(report: str) -> int:
        """
        从报告中估计发现数量

        Args:
            report: LLM 生成的报告文本

        Returns:
            发现数量
        """
        # 统计发现相关的关键词出现次数
        keywords = ["发现", "检测到", "匹配", "警告", "风险"]
        count = sum(report.count(keyword) for keyword in keywords)
        return min(count, 100)  # 限制在合理范围内

    @staticmethod
    def extract_summary(report: str, max_length: int = 200) -> str:
        """
        提取报告摘要

        Args:
            report: LLM 生成的报告文本
            max_length: 最大长度

        Returns:
            报告摘要
        """
        lines = report.strip().split('\n')
        summary_lines = []
        total_length = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if total_length + len(line) > max_length:
                break
            summary_lines.append(line)
            total_length += len(line)

        return ' '.join(summary_lines) if summary_lines else report[:max_length]

    @staticmethod
    def validate_report(report: str) -> bool:
        """
        验证报告是否有效

        Args:
            report: 报告文本

        Returns:
            是否为有效报告
        """
        if not report or len(report) < 50:
            return False

        # 检查是否包含基本的报告结构
        required_keywords = ["# APK", "##", "分析", "报告"]
        return any(keyword in report for keyword in required_keywords)
