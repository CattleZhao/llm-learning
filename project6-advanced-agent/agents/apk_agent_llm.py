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

        self._apk_path = apk_path
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

            return AgentResponse(
                content=final_response,
                metadata={
                    "apk_path": apk_path,
                    "model": self.model,
                    "analysis": self.current_analysis
                }
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
        messages = [
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

            # 检查是否有工具调用
            tool_use_blocks = []
            text_blocks = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_use_blocks.append(block)
                elif block.type == "text":
                    text_blocks.append(block)

            # 如果没有工具调用，说明 Claude 已完成分析
            if not tool_use_blocks:
                logger.info("\n" + "=" * 60)
                logger.info("Claude 分析完成")
                logger.info("=" * 60)
                if text_blocks:
                    return text_blocks[0].text
                return "分析完成"

            # 执行工具调用
            messages.append({"role": "assistant", "content": response.content})

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

                # 格式化结果摘要
                result_summary = ToolFormatter.format_result_summary(tool_name, tool_result)
                logger.info(f"   执行结果: {result_summary}")

                # Web 状态更新 - 显示结果摘要
                self.on_status_update(f"   ✓ {result_summary}")

                # 添加工具结果到消息
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result)
                    }]
                })

                # 保存分析结果
                self.current_analysis[tool_name] = tool_result

        logger.warning("达到最大迭代次数")
        return "分析达到最大迭代次数"

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
