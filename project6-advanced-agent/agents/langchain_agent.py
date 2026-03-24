"""
LangChain Agent 集成

使用 LangChain 的 create_agent 管理 Agent 循环，
解决手动管理迭代次数的问题。

注意：使用 LangChain >= 1.0.0 的新 API
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from agents.base import BaseAgent, AgentResponse
from tools.mcp.jadx_client_stdio import StdioMCPClient
from tools.llm_tools import ToolExecutor
from knowledge_base import get_rule_loader
from config import get_settings

logger = logging.getLogger(__name__)


# ============================================================
# MCP 工具适配器
# ============================================================

class MCPToolAdapter(BaseTool):
    """MCP 工具适配器 - 将 MCP 工具适配为 LangChain 工具"""

    name: str = "mcp_tool"
    description: str = "MCP 工具"
    tool_executor: Optional[ToolExecutor] = None
    mcp_tool_name: Optional[str] = None
    args_schema: Any = None  # Pydantic 模型，可选

    def __init__(
        self,
        name: str,
        description: str,
        tool_executor: ToolExecutor,
        **kwargs
    ):
        super().__init__(name=name, description=description, **kwargs)
        self.tool_executor = tool_executor
        self.mcp_tool_name = name

    def _run(self, **kwargs) -> str:
        """执行 MCP 工具"""
        if self.tool_executor is None:
            return "错误: 工具执行器未初始化"

        try:
            result = self.tool_executor.execute(self.mcp_tool_name, kwargs)
            return str(result)
        except Exception as e:
            logger.error(f"MCP 工具执行失败: {self.name}, {e}")
            return f"工具执行失败: {str(e)}"


def create_langchain_tools(
    tool_executor: ToolExecutor,
    tool_definitions: List[Dict[str, Any]]
) -> List[BaseTool]:
    """从 MCP 工具定义创建 LangChain 工具"""
    langchain_tools = []

    for tool_def in tool_definitions:
        tool = MCPToolAdapter(
            name=tool_def["name"],
            description=tool_def.get("description", ""),
            tool_executor=tool_executor
        )
        langchain_tools.append(tool)

    logger.info(f"创建了 {len(langchain_tools)} 个 LangChain 工具")
    return langchain_tools


# ============================================================
# System Prompt
# ============================================================

ANALYST_SYSTEM_PROMPT = """你是一个专业的 APK 安全分析专家，擅长检测 Android APK 中的恶意行为。

## 分析流程

请按照以下步骤分析 APK：

1. **获取基本信息** - 调用 jadx_get_manifest 获取包名、版本等
2. **分析权限** - 调用 jadx_get_permissions 检查危险权限
3. **扫描代码** - 调用 jadx_get_code_paths 了解代码结构
4. **检查网络** - 调用 jadx_get_network_info 分析网络通信
5. **检测 API** - 调用 jadx_get_apis 检测敏感 API 调用
6. **提取字符串** - 调用 jadx_get_strings 查找可疑字符串
7. **匹配规则** - 调用 match_malware_rules 匹配恶意模式

## 输出格式

完成分析后，生成以下格式的报告：

# APK 安全分析报告

## 基本信息
- 包名: `xxx`
- 版本: `xxx`
- 风险等级: 🟢 LOW / 🟡 MEDIUM / 🟠 HIGH / 🔴 CRITICAL

## 权限分析
- 总权限数: xx
- 危险权限: xx

## 安全发现
1. [风险等级] 发现内容
2. ...

## 判定
分析结论和建议。

## 重要提示

- 完成所有分析步骤后再生成报告
- 不要重复调用相同的工具
- 如果某次工具调用失败，可以重试一次
- 报告要具体详细，不要泛泛而谈"""


# ============================================================
# LangChain Agent (新 API)
# ============================================================

class LangChainAPKAgent(BaseAgent):
    """
    使用 LangChain create_agent 的 APK 分析 Agent

    新版 LangChain (>= 1.0) 使用 create_agent 函数，
    返回 CompiledStateGraph，自动管理工具调用循环。
    """

    def __init__(
        self,
        mcp_server_path: str,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        system_prompt: Optional[str] = None,  # 支持自定义 prompt
        on_status_update: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            name="APK 安全分析专家 (LangChain 驱动)",
            description="使用 LangChain create_agent 进行 APK 恶意行为分析",
            role="security_analyst",
            enable_memory=False,
            enable_reflection=False
        )

        self.on_status_update = on_status_update or (lambda msg: None)

        # 配置
        settings = get_settings()
        self.api_key = anthropic_api_key or settings.anthropic_api_key
        self.model = model
        self.system_prompt = system_prompt or ANALYST_SYSTEM_PROMPT  # 自定义或默认

        # 初始化 LLM
        self.llm = ChatAnthropic(
            api_key=self.api_key,
            model=model,
            temperature=0
        )

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

        # 初始化工具执行器
        self.rule_loader = get_rule_loader()
        self.tool_executor = ToolExecutor(
            mcp_client=self.mcp_client,
            rule_loader=self.rule_loader,
            logger=logger
        )

        # 当前分析状态
        self.current_analysis: Dict[str, Any] = {}
        self._apk_path: Optional[str] = None

    def think(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> AgentResponse:
        """执行 APK 分析 - 使用 LangChain create_agent"""
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
        self.current_analysis = {}

        self.on_status_update(f"📁 开始分析: {Path(apk_path).name}")

        try:
            # 连接 MCP Server
            self.on_status_update("🔌 连接 MCP Server...")
            if not self.mcp_client.connect():
                self.on_status_update("⚠️ MCP Server 连接失败")

            # 创建 LangChain 工具
            from tools.llm_tools import ToolDefinitions
            tool_defs = ToolDefinitions.get_all_tools()
            langchain_tools = create_langchain_tools(self.tool_executor, tool_defs)

            # 使用新版 create_agent API
            self.on_status_update("🤖 创建 LangChain Agent...")
            agent_graph = create_agent(
                model=self.llm,
                tools=langchain_tools,
                system_prompt=self.system_prompt,  # 使用自定义或默认 prompt
                debug=False  # 设为 True 可看到详细执行过程
            )

            # 执行分析
            user_message = f"{input_text}\n\nAPK 路径: {apk_path}"
            self.on_status_update("🔄 LangChain Agent 开始工作...")

            # 使用 stream 模式执行
            inputs = {"messages": [{"role": "user", "content": user_message}]}

            tool_call_count = 0
            final_response = None

            for event in agent_graph.stream(inputs, stream_mode="updates"):
                # event 格式: {node_name: {state_updates}}
                for node_name, state_updates in event.items():
                    if node_name == "agent":
                        # LLM 调用
                        self.on_status_update(f"🤖 LLM 思考中...")
                    elif node_name == "tools":
                        # 工具调用
                        tool_call_count += 1
                        messages = state_updates.get("messages", [])
                        for msg in messages:
                            if hasattr(msg, "name"):
                                self.on_status_update(f"🔧 调用工具: {msg.name}")
                            elif hasattr(msg, "content"):
                                # 工具结果
                                content_preview = str(msg.content)[:100]
                                self.on_status_update(f"   ✓ 结果: {content_preview}...")

            # 获取最终状态
            final_state = agent_graph.invoke(inputs)
            final_messages = final_state.get("messages", [])

            # 提取最后的 AI 回复作为报告
            for msg in reversed(final_messages):
                if hasattr(msg, "type") and msg.type == "ai":
                    final_response = msg.content
                    break

            if not final_response:
                final_response = "分析完成，但未能生成报告。"

            self.on_status_update(f"✅ 分析完成！执行了 {tool_call_count} 个工具调用")

            # 解析风险等级
            risk_level = self._parse_risk_level(final_response)

            metadata = {
                "apk_path": apk_path,
                "model": self.model,
                "risk_level": risk_level,
                "tool_calls_count": tool_call_count,
                "analysis": self.current_analysis,
            }

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

        finally:
            # 关闭 MCP 连接
            try:
                self.mcp_client.close()
            except:
                pass

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

    def _parse_risk_level(self, report: str) -> str:
        """从报告中解析风险等级"""
        report_lower = report.lower()
        if "critical" in report_lower or "🔴" in report:
            return "critical"
        elif "high" in report_lower or "🟠" in report:
            return "high"
        elif "medium" in report_lower or "🟡" in report:
            return "medium"
        else:
            return "low"

    def close(self):
        """关闭连接"""
        try:
            self.mcp_client.close()
        except:
            pass


# ============================================================
# 便捷函数
# ============================================================

def create_langchain_agent(
    mcp_server_path: str,
    anthropic_api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    system_prompt: Optional[str] = None,
    on_status_update: Optional[Callable[[str], None]] = None
) -> LangChainAPKAgent:
    """创建 LangChain 驱动的 APK 分析 Agent"""
    return LangChainAPKAgent(
        mcp_server_path=mcp_server_path,
        anthropic_api_key=anthropic_api_key,
        model=model,
        system_prompt=system_prompt,  # 传递自定义 prompt
        on_status_update=on_status_update
    )
