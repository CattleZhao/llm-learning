"""
APK 恶意行为分析 Agent - LLM 驱动版本

使用 Anthropic Claude API + Function Calling 的工具调用式 Agent
LLM 自主决定调用哪些分析工具

重构版本：工具相关代码已抽离到 tools/llm_tools.py
"""
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# 导入拆分后的模块
from .history_manager import HistoryManager
from .report_parser import ReportParser

sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from anthropic import Anthropic
from agents.base import BaseAgent, AgentResponse
from tools.mcp.jadx_client_stdio import StdioMCPClient
from tools.llm_tools import ToolDefinitions, ToolExecutor, ToolFormatter
from knowledge_base import get_rule_loader
from config import get_settings


# ============================================================
# 用户自定义 System Prompt - 请在此处替换您的 prompt
# ============================================================
USER_SYSTEM_PROMPT = """
# 你可以在这里放置你的 System Prompt

例如：你是一个专业的 APK 安全分析专家，擅长检测 Android APK 中的恶意行为。
你可以使用以下工具来分析 APK：
- jadx_open_apk: 打开 APK 文件
- jadx_get_manifest: 获取应用清单信息
- jadx_get_permissions: 分析权限声明
- jadx_get_code_paths: 获取代码结构
- jadx_get_strings: 提取字符串资源
- jadx_get_network_info: 分析网络通信
- jadx_get_apis: 检测敏感 API 调用
- match_malware_rules: 匹配恶意软件规则
...（共 19 个工具）

请根据 APK 的具体情况，自主决定调用哪些工具进行深入分析。
""".strip()


# ============================================================
# LLM 驱动的 APK 分析 Agent
# ============================================================

class LLMAPKAnalysisAgent(BaseAgent):
    """
    LLM 驱动的 APK 分析 Agent

    使用 Claude API 的 Function Calling 功能，
    让 LLM 自主决定调用哪些分析工具。
    """

    def __init__(
        self,
        mcp_server_path: str,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        system_prompt: Optional[str] = None,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        super().__init__(
            name="APK 安全分析专家 (LLM 驱动)",
            description="使用 Claude API 和工具调用进行 APK 恶意行为分析",
            role="security_analyst",
            enable_memory=False,
            enable_reflection=False
        )

        # 状态回调
        self.on_status_update = on_status_update or (lambda msg: None)

        # 配置
        settings = get_settings()
        self.api_key = anthropic_api_key or settings.anthropic_api_key
        self.model = model
        self.system_prompt = system_prompt or USER_SYSTEM_PROMPT

        # 初始化 Anthropic 客户端
        self.client = Anthropic(api_key=self.api_key)

        # 初始化 MCP 客户端
        import platform
        if platform.system() == "Windows":
            command = ["python", str(Path(mcp_server_path) / "jadx_mcp_server.py")]
        else:
            command = ["python3", str(Path(mcp_server_path) / "jadx_mcp_server.py")]

        self.mcp_client = StdioMCPClient(
            server_command=command,
            on_status_update=self.on_status_update
        )

        # 获取规则加载器
        self.rule_loader = get_rule_loader()

        # 初始化工具执行器和格式化器
        self.tool_executor = ToolExecutor(
            mcp_client=self.mcp_client,
            rule_loader=self.rule_loader,
            logger=logger
        )

        # 获取工具定义
        self.tools = ToolDefinitions.get_all_tools()

        # 当前分析状态
        self.current_analysis: Dict[str, Any] = {}
        self._apk_path: Optional[str] = None

        # 工具结果大小限制（字符数）
        self.max_tool_result_size = 50000  # 50KB

        # Token 使用统计
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # 历史记录管理器
        self.history_manager = HistoryManager()

        # 报告解析器
        self.report_parser = ReportParser()

    def think(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> AgentResponse:
        """
        执行 APK 分析 - LLM 自主调用工具

        Args:
            input_text: 用户输入，如 "分析 app.apk"
            context: 上下文信息，可包含 apk_path

        Returns:
            AgentResponse: 分析结果
        """
        # 提取 APK 路径
        apk_path = self._extract_apk_path(input_text, context)

        if not apk_path:
            return AgentResponse(
                content="请提供要分析的 APK 文件路径",
                metadata={"error": "no_apk_path"}
            )

        if not Path(apk_path).exists():
            return AgentResponse(
                content=f"APK 文件不存在: {apk_path}",
                metadata={"error": "file_not_found"}
            )

        # 计算 APK hash 并检查历史记录
        apk_hash = self.history_manager.calculate_apk_hash(apk_path)
        self._apk_path = apk_path

        # 重置分析状态（防止多次调用时数据累积）
        self.current_analysis = {}
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # 尝试加载历史分析数据
        history = self.history_manager.load(apk_hash)
        if history:
            self.current_analysis = history.get("analysis", {})
            self.total_input_tokens = history.get("input_tokens", 0)
            self.total_output_tokens = history.get("output_tokens", 0)
            last_analysis_time = history.get("timestamp", "")
            self.on_status_update(f"📋 加载历史分析记录 (上次分析: {last_analysis_time})")

        self.on_status_update(f"📁 开始分析: {Path(apk_path).name}")

        # 连接 MCP Server
        self.on_status_update("🔌 连接 MCP Server...")
        if not self.mcp_client.connect():
            self.on_status_update("⚠️ MCP Server 连接失败")

        # 构建 Claude API 请求
        user_message = f"{input_text}\n\nAPK 路径: {apk_path}"

        try:
            # 执行 LLM 工具调用循环
            final_response = self._run_tool_loop(user_message)

            # Fallback: 如果 LLM 没有生成报告，用 current_analysis 生成
            if not final_response or len(final_response) < 50:
                logger.warning(f"LLM 报告为空或过短 (长度: {len(final_response) if final_response else 0})，使用 fallback")
                final_response = self._generate_fallback_report()
                self.on_status_update("⚠️ LLM 未生成报告，使用工具结果生成默认报告")

            # 从 LLM 报告中解析风险等级和发现数量
            risk_level = self.report_parser.parse_risk_level(final_response)
            findings_count = self.report_parser.parse_findings_count(final_response)

            # 构建元数据
            metadata = {
                "apk_path": apk_path,
                "model": self.model,
                "risk_level": risk_level,
                "findings_count": findings_count,
                "analysis": self.current_analysis,
                "report_source": "llm" if len(final_response) > 100 else "fallback",
                "token_usage": {
                    "input_tokens": self.total_input_tokens,
                    "output_tokens": self.total_output_tokens,
                    "total_tokens": self.total_input_tokens + self.total_output_tokens
                }
            }

            # 保存历史记录
            self.history_manager.save(
                apk_hash=apk_hash,
                apk_path=apk_path,
                analysis=self.current_analysis,
                report=final_response,
                input_tokens=self.total_input_tokens,
                output_tokens=self.total_output_tokens,
                metadata=metadata
            )

            return AgentResponse(
                content=final_response,
                metadata=metadata
            )

        except Exception as e:
            import traceback
            return AgentResponse(
                content=f"分析过程中出错: {str(e)}",
                metadata={"error": str(e), "traceback": traceback.format_exc()}
            )

    def _extract_apk_path(self, input_text: str, context: Optional[Dict]) -> Optional[str]:
        """从输入中提取 APK 路径"""
        if context and "apk_path" in context:
            return context["apk_path"]
        if input_text.endswith(".apk"):
            return input_text.strip()
        if "分析" in input_text:
            parts = input_text.split()
            for part in parts:
                if part.endswith(".apk"):
                    return part
        return None

    def _run_tool_loop(self, user_message: str) -> str:
        """
        运行 LLM 工具调用循环

        持续与 Claude 交互，直到它不再请求工具调用
        """
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": user_message}
        ]

        max_iterations = 20
        iteration = 0

        logger.info("=" * 60)
        logger.info(f"开始 LLM 驱动分析: {Path(self._apk_path).name}")
        logger.info("=" * 60)

        while iteration < max_iterations:
            iteration += 1

            logger.info(f"\n[迭代 {iteration}] 请求 Claude 决策...")

            # 调用 Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
                tools=self.tools
            )

            # 记录 token 使用量
            if hasattr(response, 'usage') and response.usage:
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens
                logger.info(f"  Token 使用: 输入={response.usage.input_tokens}, 输出={response.usage.output_tokens}")

            # 检查是否有工具调用
            tool_use_blocks = []
            text_blocks = []

            for block in response.content:
                logger.info(f"  Block type: {block.type}")
                if block.type == "tool_use":
                    tool_use_blocks.append(block)
                elif block.type == "text":
                    text_blocks.append(block)
                    if block.text:
                        logger.info(f"  Text content: {block.text[:100]}...")

            # 如果没有工具调用，说明 Claude 已完成分析
            if not tool_use_blocks:
                logger.info("\n" + "=" * 60)
                logger.info("Claude 分析完成（无新工具调用）")
                logger.info(f"Text blocks 数量: {len(text_blocks)}")
                logger.info("=" * 60)

                # 如果有文本内容，直接返回
                if text_blocks and text_blocks[0].text:
                    result = text_blocks[0].text
                    logger.info(f"返回报告长度: {len(result)}")
                    return result

                # 如果没有文本内容，请求 LLM 生成最终报告
                logger.info("LLM 未生成文本报告，请求生成最终报告...")

                # 转换 response.content 为可序列化格式
                assistant_content = []
                for block in response.content:
                    if hasattr(block, 'model_dump'):
                        assistant_content.append(block.model_dump())
                    elif hasattr(block, 'dict'):
                        assistant_content.append(block.dict())
                    else:
                        assistant_content.append({
                            "type": block.type,
                            **(block.__dict__ if hasattr(block, '__dict__') else {})
                        })
                messages.append({"role": "assistant", "content": assistant_content})

                # 添加用户请求生成报告的消息
                messages.append({
                    "role": "user",
                    "content": "请基于已收集的分析数据，按照你 System Prompt 中定义的输出格式，生成完整的 APK 安全分析报告。"
                })

                # 再次请求生成报告（使用流式模式避免超时）
                logger.info("使用流式模式请求最终报告...")

                # 先尝试非流式 API 看是否能获取响应
                logger.info("先测试非流式 API...")
                try:
                    test_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=messages
                    )
                    logger.info(f"非流式 API 响应成功，content blocks: {len(test_response.content)}")
                    for block in test_response.content:
                        logger.info(f"  Block type: {block.type}")
                        if block.type == "text" and block.text:
                            logger.info(f"  找到文本内容，长度: {len(block.text)}")
                            return block.text
                except Exception as e:
                    logger.warning(f"非流式 API 失败: {e}")

                # 如果非流式失败，尝试流式
                logger.info("非流式无内容，尝试流式 API...")
                final_text = ""
                event_count = 0

                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=messages
                ) as stream:
                    for event in stream:
                        event_count += 1
                        logger.info(f"  Event #{event_count}: type={event.type}")

                        if event.type == "content_block_delta":
                            if hasattr(event.delta, 'text'):
                                text_chunk = event.delta.text
                                final_text += text_chunk
                                logger.info(f"    Text chunk: {len(text_chunk)} chars, total: {len(final_text)}")
                        elif event.type == "message_stop":
                            break

                logger.info(f"流式响应完成，{event_count} 个事件，文本长度: {len(final_text)}")

                if final_text:
                    logger.info(f"获取到最终报告，长度: {len(final_text)}")
                    return final_text

                logger.warning("流式响应为空，使用 fallback 报告")
                return self._generate_fallback_report()

            # 执行工具调用 - 转换 response.content 为可序列化格式
            assistant_content = []
            for block in response.content:
                if hasattr(block, 'model_dump'):
                    assistant_content.append(block.model_dump())
                elif hasattr(block, 'dict'):
                    assistant_content.append(block.dict())
                else:
                    # 降级处理：转换为基本类型
                    assistant_content.append({
                        "type": block.type,
                        **(block.__dict__ if hasattr(block, '__dict__') else {})
                    })
            messages.append({"role": "assistant", "content": assistant_content})

            logger.info(f"Claude 请求调用 {len(tool_use_blocks)} 个工具")

            for tool_use in tool_use_blocks:
                tool_name = tool_use.name
                tool_input = tool_use.input

                # 获取工具显示名称
                display_name = ToolFormatter.get_display_name(tool_name)

                # 控制台打印
                logger.info(f"\n🔧 工具调用 #{iteration}")
                logger.info(f"   工具名称: {tool_name}")
                logger.info(f"   输入参数: {tool_input}")

                # Web 状态更新
                self.on_status_update(f"🔧 [{iteration}] 调用工具: {display_name}")

                # 执行工具
                tool_result = self.tool_executor.execute(tool_name, tool_input)

                # 截断过大的结果以避免超出 token 限制
                result_str = str(tool_result)
                if len(result_str) > self.max_tool_result_size:
                    logger.warning(f"工具 {tool_name} 结果过大 ({len(result_str)} 字符)，截断到 {self.max_tool_result_size}")
                    result_str = result_str[:self.max_tool_result_size] + "\n\n... (结果已截断)"
                    # 保存完整结果到 current_analysis，但只传递摘要给 LLM
                    self.current_analysis[tool_name] = tool_result
                else:
                    self.current_analysis[tool_name] = tool_result

                # 格式化结果摘要
                result_summary = ToolFormatter.format_result_summary(tool_name, tool_result)
                logger.info(f"   执行结果: {result_summary}")

                # Web 状态更新 - 显示结果摘要
                self.on_status_update(f"   ✓ {result_summary}")

                # 添加工具结果到消息（使用处理后的字符串）
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result_str
                    }]
                })

        logger.warning("达到最大迭代次数")
        return "分析达到最大迭代次数"

    def _generate_fallback_report(self) -> str:
        """当 LLM 未生成报告时，用工具结果生成默认报告"""
        lines = ["# APK 安全分析报告\n"]
        lines.append("## 基本信息\n")

        # 从 manifest 获取基本信息
        if "jadx_get_manifest" in self.current_analysis:
            manifest = self.current_analysis["jadx_get_manifest"]
            if isinstance(manifest, dict):
                lines.append(f"- 包名: `{manifest.get('package', 'unknown')}`")
                lines.append(f"- 版本: `{manifest.get('version_name', 'unknown')}`\n")

        lines.append("## 工具调用结果\n")

        # 列出所有调用的工具
        for tool_name, result in self.current_analysis.items():
            if isinstance(result, dict):
                lines.append(f"### {tool_name}")
                # 只显示摘要信息
                if "count" in result:
                    lines.append(f"- 数量: {result['count']}")
                if "rules" in result:
                    lines.append(f"- 匹配规则数: {len(result.get('rules', []))}")
                if "urls" in result:
                    lines.append(f"- URL 数: {len(result.get('urls', []))}")
                lines.append("")

        lines.append("\n---\n")
        lines.append("*注: LLM 未生成详细报告，以上为工具调用原始结果的摘要。*")

        return "\n".join(lines)

    def close(self):
        """关闭连接"""
        try:
            self.mcp_client.close()
        except:
            pass


# ============================================================
# 便捷函数
# ============================================================

def create_llm_agent(
    mcp_server_path: str,
    anthropic_api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    system_prompt: Optional[str] = None,
    on_status_update: Optional[Callable[[str], None]] = None
) -> LLMAPKAnalysisAgent:
    """
    创建 LLM 驱动的 APK 分析 Agent

    Args:
        mcp_server_path: jadx-mcp-server 目录路径
        anthropic_api_key: Anthropic API Key (可选，默认从环境变量读取)
        model: Claude 模型名称
        system_prompt: 自定义 System Prompt (可选)
        on_status_update: 状态更新回调

    Returns:
        LLMAPKAnalysisAgent 实例
    """
    return LLMAPKAnalysisAgent(
        mcp_server_path=mcp_server_path,
        anthropic_api_key=anthropic_api_key,
        model=model,
        system_prompt=system_prompt,
        on_status_update=on_status_update
    )
