"""
高级上下文压缩器

集成磁盘缓存和 LLM 摘要，使用占位符替换策略：
1. 对话历史中的旧消息替换为占位符（而非直接删除）
2. 完整工具结果保存到磁盘缓存
3. 使用 Haiku LLM 生成智能摘要
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .cache_manager import ToolResultCache
from .llm_summarizer import LLMSummarizer

logger = logging.getLogger(__name__)


@dataclass
class AdvancedCompressionConfig:
    """高级压缩配置"""
    # 对话历史窗口大小（轮数）
    history_window_size: int = 5
    # 最小保留轮数
    min_history_rounds: int = 2
    # 工具结果摘要阈值（字符数）
    tool_result_summary_threshold: int = 2000
    # 是否使用 LLM 摘要（否则使用规则摘要）
    use_llm_summarizer: bool = True
    # LLM 模型（Sonnet 质量更好）
    llm_model: str = "claude-sonnet-4-20250514"
    # 是否启用磁盘缓存
    enable_disk_cache: bool = True
    # 缓存目录
    cache_dir: Optional[str] = None
    # 是否在压缩时使用占位符（而非直接删除）
    use_placeholders: bool = True


class MessageCompressor:
    """消息压缩器 - 处理占位符替换逻辑"""

    def __init__(self, cache: ToolResultCache):
        self.cache = cache

    def compress_with_placeholders(
        self,
        messages: List[Dict[str, Any]],
        window_size: int
    ) -> List[Dict[str, Any]]:
        """
        使用占位符压缩对话历史

        策略：
        - 始终保留第一条用户消息
        - 最近的 N 轮完整保留
        - 中间的旧消息替换为占位符

        Args:
            messages: 完整消息列表
            window_size: 滑动窗口大小（轮数）

        Returns:
            压缩后的消息列表
        """
        if len(messages) <= window_size * 2 + 1:
            return messages

        # 保留第一条（用户输入）
        compressed = [messages[0]]

        # 计算需要替换的消息范围
        # 从第 2 条到倒数第 window_size*2 条
        placeholder_start = 1
        placeholder_end = len(messages) - window_size * 2

        if placeholder_end > placeholder_start:
            # 统计中间被替换的工具调用
            tool_calls_in_middle = []
            for i in range(placeholder_start, placeholder_end):
                msg = messages[i]
                if msg.get("role") == "assistant":
                    # 查找工具调用
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                tool_calls_in_middle.append({
                                    "name": block.get("name"),
                                    "id": block.get("id")
                                })

            # 如果有工具调用，添加占位符
            if tool_calls_in_middle:
                placeholder_text = self._create_summary_placeholder(
                    tool_calls_in_middle,
                    placeholder_end - placeholder_start
                )
                compressed.append({
                    "role": "system",
                    "content": placeholder_text
                })

        # 保留最近 N 轮
        compressed.extend(messages[placeholder_end:])

        removed = len(messages) - len(compressed)
        if removed > 0:
            logger.info(
                f"[MessageCompressor] 占位符压缩: "
                f"{len(messages)} -> {len(compressed)} 条消息 "
                f"(移除 {removed} 条，添加占位符)"
            )

        return compressed

    def _create_summary_placeholder(
        self,
        tool_calls: List[Dict[str, Any]],
        message_count: int
    ) -> str:
        """
        创建占位符文本

        告诉 LLM 之前执行过哪些分析，而不传递完整结果。
        """
        if not tool_calls:
            return f"[之前已执行 {message_count} 轮对话，详细信息已从上下文中移除]"

        # 统计工具调用类型
        tool_summary = {}
        for call in tool_calls:
            name = call.get("name", "unknown")
            tool_summary[name] = tool_summary.get(name, 0) + 1

        # 构建占位符文本
        lines = [
            f"[上下文压缩: 之前的 {message_count} 条消息已被占位符替换]",
            "已执行的分析工具:"
        ]

        for tool_name, count in tool_summary.items():
            lines.append(f"  - {tool_name} (x{count})")

        lines.append("完整结果已保存到磁盘缓存，如需回溯可查询。")

        return "\n".join(lines)


class AdvancedContextCompressor:
    """
    高级上下文压缩器

    集成磁盘缓存、LLM 摘要和占位符替换策略。
    """

    def __init__(self, config: Optional[AdvancedCompressionConfig] = None):
        self.config = config or AdvancedCompressionConfig()

        # 初始化组件
        if self.config.enable_disk_cache:
            from pathlib import Path
            cache_path = Path(self.config.cache_dir) if self.config.cache_dir else None
            self.cache = ToolResultCache(cache_dir=cache_path)
        else:
            self.cache = None

        if self.config.use_llm_summarizer:
            self.summarizer = LLMSummarizer(model=self.config.llm_model)
        else:
            # 回退到规则摘要器
            from .context_compressor import RuleBasedSummarizer
            self.summarizer = RuleBasedSummarizer()

        # 消息压缩器
        if self.config.use_placeholders and self.cache:
            self.message_compressor = MessageCompressor(self.cache)
        else:
            self.message_compressor = None

        # 统计信息
        self.stats = {
            "cache_stores": 0,
            "cache_hits": 0,
            "llm_summaries": 0,
            "placeholder_replacements": 0,
            "tokens_saved_estimate": 0
        }

    def compress_messages(
        self,
        messages: List[Dict[str, Any]],
        iteration: int
    ) -> List[Dict[str, Any]]:
        """
        压缩对话历史

        如果启用占位符模式，使用占位符替换旧消息
        否则使用滑动窗口模式（删除旧消息）

        Args:
            messages: 完整消息列表
            iteration: 当前迭代次数

        Returns:
            压缩后的消息列表
        """
        if self.message_compressor and iteration > 1:
            # 使用占位符模式
            compressed = self.message_compressor.compress_with_placeholders(
                messages,
                self.config.history_window_size
            )
            if len(compressed) < len(messages):
                self.stats["placeholder_replacements"] += 1
            return compressed

        # 使用滑动窗口模式（原始行为）
        if len(messages) <= self.config.history_window_size * 2:
            return messages

        compressed = [messages[0]]  # 保留第一条
        window_start = max(1, len(messages) - self.config.history_window_size * 2)
        compressed.extend(messages[window_start:])

        removed = len(messages) - len(compressed)
        if removed > 0:
            logger.info(f"[AdvancedCompressor] 滑动窗口压缩: 移除 {removed} 条旧消息")

        return compressed

    def compress_tool_result(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: Any,
        tool_use_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        压缩工具结果（高级版）

        策略：
        1. 完整结果保存到磁盘缓存
        2. 生成摘要（LLM 或规则）
        3. 返回摘要文本和缓存 ID

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            tool_result: 工具执行结果
            tool_use_id: 工具调用 ID

        Returns:
            (摘要文本, 缓存 ID) - 如果未缓存则 ID 为 None
        """
        result_str = str(tool_result)
        original_size = len(result_str)

        # 小结果直接返回
        if original_size <= self.config.tool_result_summary_threshold:
            return result_str, None

        # 保存到缓存
        cache_id = None
        if self.cache:
            cache_id = self.cache.store(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_result=tool_result,
                metadata={"original_size": original_size}
            )
            self.stats["cache_stores"] += 1

        # 生成摘要
        summary = self.summarizer.summarize(tool_name, tool_result)

        if self.config.use_llm_summarizer:
            self.stats["llm_summaries"] += 1

        # 如果启用了缓存，可以在摘要中添加缓存引用
        if cache_id and self.config.use_placeholders:
            summary += f" [缓存: {cache_id}]"

        # 计算节省的 token（粗略估计）
        tokens_saved = (original_size - len(summary)) // 4
        self.stats["tokens_saved_estimate"] += tokens_saved

        logger.info(
            f"[AdvancedCompressor] {tool_name}: "
            f"{original_size} -> {len(summary)} 字符 "
            f"(~{tokens_saved} tokens 节省)"
        )

        return summary, cache_id

    def create_tool_result_placeholder(
        self,
        tool_name: str,
        cache_id: str,
        summary: str
    ) -> str:
        """
        创建工具结果占位符

        用于在后续对话中引用之前的工具执行结果。

        Args:
            tool_name: 工具名称
            cache_id: 缓存 ID
            summary: 结果摘要

        Returns:
            占位符文本
        """
        return f"[{tool_name}] 已在之前执行，结果摘要: {summary} (缓存ID: {cache_id})"

    def load_cached_result(self, cache_id: str) -> Optional[Dict[str, Any]]:
        """从缓存加载完整结果"""
        if not self.cache:
            return None

        result = self.cache.load(cache_id)
        if result:
            self.stats["cache_hits"] += 1

        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计信息"""
        stats = self.stats.copy()

        # 添加组件统计
        if self.cache:
            stats["cache"] = self.cache.get_cache_stats()

        if self.config.use_llm_summarizer:
            stats["llm"] = self.summarizer.get_stats()

        return stats

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "cache_stores": 0,
            "cache_hits": 0,
            "llm_summaries": 0,
            "placeholder_replacements": 0,
            "tokens_saved_estimate": 0
        }

        if self.config.use_llm_summarizer:
            self.summarizer.reset_stats()


# ============================================================
# 便捷函数
# ============================================================

def create_advanced_compressor(
    history_window_size: int = 5,
    use_llm_summarizer: bool = True,
    llm_model: str = "claude-haiku-4-20250514",
    enable_disk_cache: bool = True,
    use_placeholders: bool = True,
    cache_dir: Optional[str] = None
) -> AdvancedContextCompressor:
    """
    创建高级上下文压缩器

    Args:
        history_window_size: 对话历史窗口大小
        use_llm_summarizer: 是否使用 LLM 摘要
        llm_model: LLM 模型名称
        enable_disk_cache: 是否启用磁盘缓存
        use_placeholders: 是否使用占位符替换
        cache_dir: 缓存目录路径

    Returns:
        AdvancedContextCompressor 实例
    """
    config = AdvancedCompressionConfig(
        history_window_size=history_window_size,
        use_llm_summarizer=use_llm_summarizer,
        llm_model=llm_model,
        enable_disk_cache=enable_disk_cache,
        use_placeholders=use_placeholders,
        cache_dir=cache_dir
    )
    return AdvancedContextCompressor(config)


# 默认压缩器实例
_default_advanced_compressor: Optional[AdvancedContextCompressor] = None


def get_advanced_compressor() -> AdvancedContextCompressor:
    """获取默认高级压缩器（单例）"""
    global _default_advanced_compressor
    if _default_advanced_compressor is None:
        _default_advanced_compressor = create_advanced_compressor()
    return _default_advanced_compressor
