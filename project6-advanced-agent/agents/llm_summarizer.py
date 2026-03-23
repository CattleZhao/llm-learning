"""
LLM 摘要器

使用 Claude Haiku 模型生成智能摘要，替代简单的规则匹配。
Haiku 便宜快速，适合用于预处理任务。
"""
import logging
from typing import Any, Dict, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMSummarizer:
    """
    LLM 驱动的摘要器

    使用 Claude Haiku 生成工具结果的智能摘要。
    """

    # 不同工具类型的摘要提示模板
    SUMMARY_TEMPLATES = {
        "manifest": """请简要总结这个 Android Manifest 的关键信息：
- 包名和版本
- 最值得注意的权限或配置

只返回 1-2 句话的摘要。""",

        "permissions": """请总结这些权限的总体情况：
- 总权限数
- 是否有危险权限，如果有列出最重要的 2-3 个

只返回 1-2 句话。""",

        "code_paths": """请总结代码结构情况：
- 代码文件数量
- 主要的包/目录结构

只返回 1 句话。""",

        "strings": """请总结字符串提取结果：
- 总数量
- 是否发现可疑的字符串（如密钥、URL、敏感词）

只返回 1-2 句话。""",

        "network": """请总结网络通信情况：
- URL 数量和类型
- 是否使用 HTTPS
- 是否有硬编码 IP

只返回 1-2 句话。""",

        "apis": """请总结 API 调用情况：
- 总数量
- 是否有隐私敏感的 API 调用

只返回 1-2 句话。""",

        "rules": """请总结规则匹配结果：
- 匹配到的规则数量
- 最严重的风险等级

只返回 1 句话。""",

        "default": """请简要总结这个工具的执行结果，突出最关键的发现。
只返回 1-2 句话的摘要。"""
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",  # 改用 Sonnet
        max_tokens: int = 150
    ):
        """
        初始化 LLM 摘要器

        Args:
            api_key: Anthropic API Key
            model: 模型名称，默认 Haiku（便宜）
            max_tokens: 最大输出 token 数
        """
        self.model = model
        self.max_tokens = max_tokens

        # 初始化客户端
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            # 从环境变量或配置读取
            from config import get_settings
            settings = get_settings()
            self.client = Anthropic(api_key=settings.anthropic_api_key)

        # 统计信息
        self.total_requests = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def summarize(self, tool_name: str, tool_result: Any) -> str:
        """
        生成工具结果的摘要

        Args:
            tool_name: 工具名称
            tool_result: 工具执行结果

        Returns:
            摘要文本
        """
        # 如果结果很小，直接返回
        result_str = self._to_string(tool_result)
        if len(result_str) < 500:
            return result_str[:200]

        # 获取对应的提示模板
        prompt_template = self._get_prompt_template(tool_name)

        # 构建完整提示
        prompt = f"{prompt_template}\n\n工具结果:\n{result_str[:3000]}"

        try:
            # 调用 Haiku API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # 提取摘要文本
            summary = response.content[0].text.strip()

            # 更新统计
            self.total_requests += 1
            if hasattr(response, 'usage') and response.usage:
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

            logger.debug(
                f"[LLMSummarizer] {tool_name}: "
                f"{len(result_str)} -> {len(summary)} 字符, "
                f"tokens: in={response.usage.input_tokens}, out={response.usage.output_tokens}"
            )

            return summary

        except Exception as e:
            logger.warning(f"[LLMSummarizer] LLM 摘要失败: {e}, 使用回退方案")
            # 回退到简单截断
            return result_str[:200] + "..."

    def _get_prompt_template(self, tool_name: str) -> str:
        """根据工具名称获取对应的提示模板"""
        tool_lower = tool_name.lower()

        if "manifest" in tool_lower:
            return self.SUMMARY_TEMPLATES["manifest"]
        elif "permission" in tool_lower:
            return self.SUMMARY_TEMPLATES["permissions"]
        elif "code_path" in tool_lower:
            return self.SUMMARY_TEMPLATES["code_paths"]
        elif "string" in tool_lower:
            return self.SUMMARY_TEMPLATES["strings"]
        elif "network" in tool_lower:
            return self.SUMMARY_TEMPLATES["network"]
        elif "api" in tool_lower:
            return self.SUMMARY_TEMPLATES["apis"]
        elif "rule" in tool_lower:
            return self.SUMMARY_TEMPLATES["rules"]
        else:
            return self.SUMMARY_TEMPLATES["default"]

    def _to_string(self, data: Any) -> str:
        """将数据转换为字符串"""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            # 只保留关键信息
            if "count" in data:
                return f"数量: {data['count']}"
            elif "package" in data:
                return f"包名: {data.get('package')}, 版本: {data.get('version_name', '?')}"
            else:
                import json
                return json.dumps(data, ensure_ascii=False, indent=2)
        elif isinstance(data, (list, tuple)):
            return f"列表，共 {len(data)} 项"
        else:
            return str(data)

    def get_stats(self) -> Dict[str, Any]:
        """获取摘要统计信息"""
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "avg_input_tokens": self.total_input_tokens / self.total_requests if self.total_requests > 0 else 0,
            "avg_output_tokens": self.total_output_tokens / self.total_requests if self.total_requests > 0 else 0,
        }

    def reset_stats(self):
        """重置统计信息"""
        self.total_requests = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0


# ============================================================
# 便捷函数
# ============================================================

_default_summarizer: Optional[LLMSummarizer] = None


def get_llm_summarizer() -> LLMSummarizer:
    """获取默认摘要器实例（单例）"""
    global _default_summarizer
    if _default_summarizer is None:
        _default_summarizer = LLMSummarizer()
    return _default_summarizer


def create_llm_summarizer(
    api_key: Optional[str] = None,
    model: str = "claude-haiku-4-20250514",
    max_tokens: int = 150
) -> LLMSummarizer:
    """
    创建 LLM 摘要器实例

    Args:
        api_key: Anthropic API Key
        model: 模型名称
        max_tokens: 最大输出 token 数

    Returns:
        LLMSummarizer 实例
    """
    return LLMSummarizer(api_key=api_key, model=model, max_tokens=max_tokens)
