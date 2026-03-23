"""
Agent 上下文压缩器

用于减少 LLM Agent 的 token 消耗，主要策略：
1. 对话历史滑动窗口 - 只保留最近 N 轮对话
2. 智能工具结果摘要 - 用 LLM 摘要长结果而非截断
3. 按需相似样本注入 - 只在高置信度需求时注入
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class CompressionConfig:
    """压缩配置"""
    # 对话历史窗口大小（轮数）
    history_window_size: int = 5
    # 最小保留轮数（确保至少有这些对话）
    min_history_rounds: int = 2
    # 工具结果摘要阈值（字符数）
    tool_result_summary_threshold: int = 2000
    # 最大工具结果大小（字符数）
    max_tool_result_size: int = 10000
    # 是否启用相似样本注入
    enable_similar_samples: bool = True
    # 相似样本最大数量
    max_similar_samples: int = 1


class ResultSummarizer(ABC):
    """结果摘要器接口"""

    @abstractmethod
    def summarize(self, tool_name: str, result: Any) -> str:
        """生成工具结果摘要"""
        pass


class RuleBasedSummarizer(ResultSummarizer):
    """基于规则的摘要器 - 不消耗额外 token"""

    def _get_summary_rules(self) -> dict:
        """获取摘要规则（实例方法，可访问 self）"""
        return {
            "jadx_get_manifest": self._summarize_manifest,
            "jadx_get_permissions": self._summarize_permissions,
            "jadx_get_code_paths": lambda r: f"代码文件: {r.get('count', len(r) if isinstance(r, list) else '?')} 个",
            "jadx_get_strings": lambda r: f"字符串: {r.get('count', len(r) if isinstance(r, list) else '?')} 个",
            "jadx_get_network_info": self._summarize_network,
            "jadx_get_apis": lambda r: f"API 调用: {len(r) if isinstance(r, list) else '?'} 个",
            "match_malware_rules": self._summarize_rules,
        }

    @staticmethod
    def _summarize_manifest(result: Any) -> str:
        if isinstance(result, dict):
            return f"包名: {result.get('package', 'unknown')}, 版本: {result.get('version_name', 'unknown')}"
        return str(result)[:200]

    @staticmethod
    def _summarize_permissions(result: Any) -> str:
        if isinstance(result, dict):
            total = result.get('count', 0)
            dangerous = result.get('dangerous_count', len(result.get('dangerous', [])))
            return f"权限: {total} 个 (危险: {dangerous} 个)"
        return str(result)[:200]

    @staticmethod
    def _summarize_network(result: Any) -> str:
        if isinstance(result, dict):
            urls = len(result.get('urls', []))
            ips = len(result.get('ips', []))
            has_http = result.get('has_http', False)
            has_https = result.get('has_https', False)
            return f"网络: URL {urls} 个, IP {ips} 个, HTTP={has_http}, HTTPS={has_https}"
        return str(result)[:200]

    @staticmethod
    def _summarize_rules(result: Any) -> str:
        if isinstance(result, dict):
            rules = result.get('rules', [])
            count = len(rules)
            if count > 0:
                severities = {}
                for r in rules:
                    s = r.get('severity', 'unknown')
                    severities[s] = severities.get(s, 0) + 1
                severity_str = ", ".join(f"{k}:{v}" for k, v in severities.items())
                return f"匹配规则: {count} 条 ({severity_str})"
            return "匹配规则: 0 条"
        return str(result)[:200]

    def summarize(self, tool_name: str, result: Any) -> str:
        """生成工具结果摘要"""
        # 查找匹配的规则
        summary_rules = self._get_summary_rules()
        for key, rule_fn in summary_rules.items():
            if tool_name.startswith(key):
                try:
                    return rule_fn(result)
                except Exception as e:
                    logger.warning(f"摘要规则失败: {key}, {e}")
                    break

        # 默认摘要
        result_str = str(result)
        if len(result_str) > 200:
            return f"{result_str[:200]}... (共 {len(result_str)} 字符)"
        return result_str


class ContextCompressor:
    """
    上下文压缩器

    负责管理和压缩 LLM Agent 的对话上下文，减少 token 消耗。
    """

    def __init__(
        self,
        config: Optional[CompressionConfig] = None,
        summarizer: Optional[ResultSummarizer] = None
    ):
        self.config = config or CompressionConfig()
        self.summarizer = summarizer or RuleBasedSummarizer()

        # 统计信息
        self.total_original_tokens = 0
        self.total_compressed_tokens = 0
        self.compression_count = 0

    def compress_messages(
        self,
        messages: List[Dict[str, Any]],
        iteration: int
    ) -> List[Dict[str, Any]]:
        """
        压缩对话历史

        保留：
        1. 最初的用户消息
        2. 最近 N 轮对话（滑动窗口）

        Args:
            messages: 完整消息列表
            iteration: 当前迭代次数

        Returns:
            压缩后的消息列表
        """
        if len(messages) <= self.config.history_window_size * 2:
            return messages

        # 保留第一轮（用户输入）
        compressed = [messages[0]]

        # 保留最近 N 轮（每轮 = assistant + user）
        window_start = max(1, len(messages) - self.config.history_window_size * 2)
        compressed.extend(messages[window_start:])

        removed = len(messages) - len(compressed)
        if removed > 0:
            logger.info(f"[ContextCompressor] 压缩对话: 移除 {removed} 条旧消息")

        return compressed

    def compress_tool_result(
        self,
        tool_name: str,
        tool_result: Any
    ) -> Tuple[str, bool]:
        """
        压缩工具结果

        如果结果过大，生成摘要而非简单截断

        Args:
            tool_name: 工具名称
            tool_result: 工具执行结果

        Returns:
            (处理后的结果字符串, 是否进行了摘要)
        """
        result_str = str(tool_result)
        original_size = len(result_str)

        # 如果结果很小，直接返回
        if original_size <= self.config.tool_result_summary_threshold:
            return result_str, False

        # 生成摘要
        summary = self.summarizer.summarize(tool_name, tool_result)

        # 如果摘要比原始结果小很多，使用摘要
        if len(summary) < original_size * 0.5:  # 摘要至少压缩 50%
            logger.info(
                f"[ContextCompressor] 工具结果摘要: "
                f"{tool_name} {original_size} -> {len(summary)} 字符 "
                f"({100 * (1 - len(summary) / original_size):.0f}% 压缩)"
            )
            self.compression_count += 1
            return summary, True

        # 否则截断到最大大小
        if original_size > self.config.max_tool_result_size:
            truncated = result_str[:self.config.max_tool_result_size] + "\n\n... (结果已截断)"
            logger.info(
                f"[ContextCompressor] 工具结果截断: "
                f"{tool_name} {original_size} -> {len(truncated)} 字符"
            )
            return truncated, False

        return result_str, False

    def should_inject_similar_samples(
        self,
        apk_name: str,
        has_history: bool
    ) -> bool:
        """
        判断是否应该注入相似样本

        只在没有历史记录且 APK 名称可疑时注入

        Args:
            apk_name: APK 文件名
            has_history: 是否有历史记录

        Returns:
            是否注入相似样本
        """
        if not self.config.enable_similar_samples:
            return False

        # 如果有历史记录，不需要相似样本
        if has_history:
            return False

        # 可疑关键词
        suspicious_keywords = ['hack', 'crack', 'mod', 'cheat', 'premium', 'pro']
        return any(kw in apk_name.lower() for kw in suspicious_keywords)

    def format_similar_samples(
        self,
        similar: List[Dict[str, Any]]
    ) -> str:
        """
        格式化相似样本（精简版）

        只保留最关键的信息
        """
        if not similar:
            return ""

        # 只取前 N 个样本
        samples = similar[:self.config.max_similar_samples]

        lines = ["参考历史分析:"]
        for i, s in enumerate(samples, 1):
            metadata = s.get('metadata', {})
            lines.append(
                f"  样本{i}: 包名={metadata.get('package', 'unknown')}, "
                f"风险={metadata.get('risk_level', 'unknown')}"
            )

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计"""
        return {
            "compression_count": self.compression_count,
            "config": {
                "history_window_size": self.config.history_window_size,
                "tool_result_threshold": self.config.tool_result_summary_threshold,
                "max_similar_samples": self.config.max_similar_samples,
            }
        }


# ============================================================
# 便捷函数
# ============================================================

def create_context_compressor(
    history_window_size: int = 5,
    tool_result_threshold: int = 2000,
    max_tool_result_size: int = 10000,
    enable_similar_samples: bool = True,
    max_similar_samples: int = 1
) -> ContextCompressor:
    """
    创建上下文压缩器

    Args:
        history_window_size: 对话历史窗口大小（轮数）
        tool_result_threshold: 工具结果摘要阈值（字符数）
        max_tool_result_size: 最大工具结果大小（字符数）
        enable_similar_samples: 是否启用相似样本注入
        max_similar_samples: 相似样本最大数量

    Returns:
        ContextCompressor 实例
    """
    config = CompressionConfig(
        history_window_size=history_window_size,
        tool_result_summary_threshold=tool_result_threshold,
        max_tool_result_size=max_tool_result_size,
        enable_similar_samples=enable_similar_samples,
        max_similar_samples=max_similar_samples
    )
    return ContextCompressor(config=config)


# 默认压缩器实例
_default_compressor: Optional[ContextCompressor] = None


def get_default_compressor() -> ContextCompressor:
    """获取默认压缩器（单例）"""
    global _default_compressor
    if _default_compressor is None:
        _default_compressor = create_context_compressor()
    return _default_compressor
