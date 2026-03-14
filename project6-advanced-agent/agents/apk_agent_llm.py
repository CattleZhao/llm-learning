"""
APK 恶意行为分析 Agent - LLM 驱动版本

使用 Anthropic Claude API + Function Calling 的工具调用式 Agent
LLM 自主决定调用哪些分析工具
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
from knowledge_base import get_rule_loader
from config import get_settings


# ============================================================
# 用户自定义 System Prompt - 请在此处替换您的 prompt
# ============================================================
USER_SYSTEM_PROMPT = """
# 你可以在这里放置你的 System Prompt

例如：你是一个专业的 APK 安全分析专家...
""".strip()


# ============================================================
# 工具定义 - 将 MCP 客户端方法包装为 LLM 可调用工具
# ============================================================

class ToolDefinitions:
    """工具定义类 - 定义所有 LLM 可调用的工具"""

    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """获取所有可用工具的定义"""
        return [
            ToolDefinitions.jadx_open_apk(),
            ToolDefinitions.jadx_get_manifest(),
            ToolDefinitions.jadx_get_permissions(),
            ToolDefinitions.jadx_get_code_paths(),
            ToolDefinitions.jadx_get_strings(),
            ToolDefinitions.jadx_get_network_info(),
            ToolDefinitions.jadx_get_apis(),
            ToolDefinitions.jadx_search_classes(),
            ToolDefinitions.jadx_get_class_source(),
            ToolDefinitions.match_malware_rules(),
            # 新增工具
            ToolDefinitions.jadx_get_main_activity(),
            ToolDefinitions.jadx_get_application_classes(),
            ToolDefinitions.jadx_get_resource_files(),
            ToolDefinitions.jadx_get_resource_file(),
            ToolDefinitions.jadx_get_methods_of_class(),
            ToolDefinitions.jadx_get_fields_of_class(),
            ToolDefinitions.jadx_get_smali_of_class(),
            ToolDefinitions.jadx_get_xrefs_to_class(),
            ToolDefinitions.jadx_get_xrefs_to_method(),
        ]

    @staticmethod
    def jadx_open_apk() -> Dict[str, Any]:
        """在 JADX-GUI 中打开 APK"""
        return {
            "name": "jadx_open_apk",
            "description": "在 JADX-GUI 中打开指定的 APK 文件。这是分析 APK 的第一步。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "apk_path": {
                        "type": "string",
                        "description": "APK 文件的完整路径"
                    }
                },
                "required": ["apk_path"]
            }
        }

    @staticmethod
    def jadx_get_manifest() -> Dict[str, Any]:
        """获取 AndroidManifest.xml"""
        return {
            "name": "jadx_get_manifest",
            "description": "获取 APK 的 AndroidManifest.xml 内容，包括包名、版本、权限等关键信息。",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    @staticmethod
    def jadx_get_permissions() -> Dict[str, Any]:
        """获取权限列表"""
        return {
            "name": "jadx_get_permissions",
            "description": "获取 APK 声明的所有权限，包括普通权限和危险权限。",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    @staticmethod
    def jadx_get_code_paths() -> Dict[str, Any]:
        """获取代码路径"""
        return {
            "name": "jadx_get_code_paths",
            "description": "获取 APK 中所有的类路径（代码文件列表）。",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    @staticmethod
    def jadx_get_strings() -> Dict[str, Any]:
        """提取字符串"""
        return {
            "name": "jadx_get_strings",
            "description": "提取 APK 中的所有字符串资源，可用于检测 URL、IP、敏感关键词等。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "offset": {
                        "type": "integer",
                        "description": "分页偏移量，从第几个开始获取",
                        "default": 0
                    },
                    "count": {
                        "type": "integer",
                        "description": "获取数量，0 表示获取全部",
                        "default": 0
                    }
                },
                "required": []
            }
        }

    @staticmethod
    def jadx_get_network_info() -> Dict[str, Any]:
        """获取网络信息"""
        return {
            "name": "jadx_get_network_info",
            "description": "分析 APK 的网络通信信息，包括 URL、IP 地址、域名等，并检测是否使用加密。",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    @staticmethod
    def jadx_get_apis() -> Dict[str, Any]:
        """获取 API 调用"""
        return {
            "name": "jadx_get_apis",
            "description": "分析 APK 中的 API 调用，特别是隐私敏感的 API（如短信、电话、位置等）。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "max_classes": {
                        "type": "integer",
                        "description": "最多分析的类数量",
                        "default": 50
                    }
                },
                "required": []
            }
        }

    @staticmethod
    def jadx_search_classes() -> Dict[str, Any]:
        """搜索类"""
        return {
            "name": "jadx_search_classes",
            "description": "根据关键字搜索类，可用于查找特定功能的代码。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "搜索关键字"
                    },
                    "package": {
                        "type": "string",
                        "description": "限定搜索的包名（可选）"
                    }
                },
                "required": ["search_term"]
            }
        }

    @staticmethod
    def jadx_get_class_source() -> Dict[str, Any]:
        """获取类源码"""
        return {
            "name": "jadx_get_class_source",
            "description": "获取指定类的完整源代码，用于深入分析可疑代码。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "类的完整名称（如 com.example.MainActivity）"
                    }
                },
                "required": ["class_name"]
            }
        }

    @staticmethod
    def match_malware_rules() -> Dict[str, Any]:
        """匹配恶意规则"""
        return {
            "name": "match_malware_rules",
            "description": "使用自定义的恶意软件检测规则库，对代码路径进行模式匹配，检测已知的恶意特征。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "code_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要检测的代码路径列表"
                    }
                },
                "required": ["code_paths"]
            }
        }

    @staticmethod
    def jadx_get_main_activity() -> Dict[str, Any]:
        """获取主 Activity"""
        return {
            "name": "jadx_get_main_activity",
            "description": "获取 APK 的主 Activity 类，这是应用的入口点，分析启动行为很有用。",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    @staticmethod
    def jadx_get_application_classes() -> Dict[str, Any]:
        """获取应用类列表"""
        return {
            "name": "jadx_get_application_classes",
            "description": "获取应用的 Application 类列表，用于分析应用初始化逻辑。",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    @staticmethod
    def jadx_get_resource_files() -> Dict[str, Any]:
        """获取资源文件列表"""
        return {
            "name": "jadx_get_resource_files",
            "description": "获取 APK 中所有资源文件的名称列表，可用于分析可疑资源文件。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "offset": {
                        "type": "integer",
                        "description": "分页偏移量",
                        "default": 0
                    },
                    "count": {
                        "type": "integer",
                        "description": "返回数量，0 表示全部",
                        "default": 0
                    }
                },
                "required": []
            }
        }

    @staticmethod
    def jadx_get_resource_file() -> Dict[str, Any]:
        """获取资源文件内容"""
        return {
            "name": "jadx_get_resource_file",
            "description": "获取指定资源文件的内容，用于检查可疑的配置或数据文件。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "资源文件名称"
                    }
                },
                "required": ["resource_name"]
            }
        }

    @staticmethod
    def jadx_get_methods_of_class() -> Dict[str, Any]:
        """获取类的方法列表"""
        return {
            "name": "jadx_get_methods_of_class",
            "description": "获取指定类中所有方法的列表，用于分析类的功能和行为。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "类的完整名称"
                    }
                },
                "required": ["class_name"]
            }
        }

    @staticmethod
    def jadx_get_fields_of_class() -> Dict[str, Any]:
        """获取类的字段列表"""
        return {
            "name": "jadx_get_fields_of_class",
            "description": "获取指定类中所有字段的列表，用于分析类的数据结构。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "类的完整名称"
                    }
                },
                "required": ["class_name"]
            }
        }

    @staticmethod
    def jadx_get_smali_of_class() -> Dict[str, Any]:
        """获取类的 Smali 代码"""
        return {
            "name": "jadx_get_smali_of_class",
            "description": "获取指定类的 Smali 代码，比源代码更底层，可检测混淆和隐藏行为。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "类的完整名称"
                    }
                },
                "required": ["class_name"]
            }
        }

    @staticmethod
    def jadx_get_xrefs_to_class() -> Dict[str, Any]:
        """获取类的引用"""
        return {
            "name": "jadx_get_xrefs_to_class",
            "description": "查找指定类被哪些其他类引用，用于追踪代码调用关系和数据流。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "类的完整名称"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "分页偏移量",
                        "default": 0
                    },
                    "count": {
                        "type": "integer",
                        "description": "返回数量",
                        "default": 0
                    }
                },
                "required": ["class_name"]
            }
        }

    @staticmethod
    def jadx_get_xrefs_to_method() -> Dict[str, Any]:
        """获取方法的引用"""
        return {
            "name": "jadx_get_xrefs_to_method",
            "description": "查找指定方法被哪些地方调用，用于追踪敏感方法的调用路径。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "方法所在类的完整名称"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "方法名称"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "分页偏移量",
                        "default": 0
                    },
                    "count": {
                        "type": "integer",
                        "description": "返回数量",
                        "default": 0
                    }
                },
                "required": ["class_name", "method_name"]
            }
        }


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
            enable_memory=False,  # LLM 驱动模式不需要内部记忆
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

        # 工具定义
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
            # 继续尝试，因为可能只是 JADX 未打开

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

        max_iterations = 20  # 防止无限循环
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
                # 返回最后的文本响应
                if text_blocks:
                    return text_blocks[0].text
                return "分析完成"

            # 执行工具调用
            messages.append({"role": "assistant", "content": response.content})

            logger.info(f"Claude 请求调用 {len(tool_use_blocks)} 个工具")

            for tool_use in tool_use_blocks:
                tool_name = tool_use.name
                tool_input = tool_use.input

                # 控制台打印
                logger.info(f"\n🔧 工具调用 #{iteration}.{len([t for t in tool_use_blocks if t == tool_use])}")
                logger.info(f"   工具名称: {tool_name}")
                logger.info(f"   输入参数: {tool_input}")

                # Web 状态更新
                self.on_status_update(f"🔧 [{iteration}] 调用工具: {self._get_tool_display_name(tool_name)}")

                # 执行工具
                tool_result = self._execute_tool(tool_name, tool_input)

                # 控制台打印结果摘要
                result_summary = self._format_result_summary(tool_name, tool_result)
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

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        执行指定的工具

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            工具执行结果
        """
        try:
            if tool_name == "jadx_open_apk":
                return self.mcp_client.open_apk(tool_input["apk_path"])

            elif tool_name == "jadx_get_manifest":
                return self.mcp_client.get_manifest()

            elif tool_name == "jadx_get_permissions":
                return self.mcp_client.get_permissions()

            elif tool_name == "jadx_get_code_paths":
                return self.mcp_client.get_code_paths()

            elif tool_name == "jadx_get_strings":
                offset = tool_input.get("offset", 0)
                count = tool_input.get("count", 0)
                return self.mcp_client.get_strings(offset=offset, count=count)

            elif tool_name == "jadx_get_network_info":
                return self.mcp_client.get_network_info()

            elif tool_name == "jadx_get_apis":
                max_classes = tool_input.get("max_classes", 50)
                return self.mcp_client.get_apis(max_classes=max_classes)

            elif tool_name == "jadx_search_classes":
                search_term = tool_input["search_term"]
                package = tool_input.get("package")
                return self.mcp_client.call_tool("search_classes_by_keyword", {
                    "search_term": search_term,
                    "package": package or ""
                })

            elif tool_name == "jadx_get_class_source":
                class_name = tool_input["class_name"]
                return self.mcp_client.call_tool("get_class_source", {
                    "class_name": class_name
                })

            elif tool_name == "match_malware_rules":
                code_paths = tool_input.get("code_paths", [])
                if not code_paths:
                    return {"error": "code_paths 参数不能为空"}

                matched_rules = []
                for path in code_paths:
                    java_path = path.replace(".java", "")
                    rules = self.rule_loader.match_rules(java_path)
                    for rule in rules:
                        if rule not in matched_rules:
                            matched_rules.append(rule)

                return {
                    "total_matched": len(matched_rules),
                    "rules": [
                        {
                            "name": r.name,
                            "category": r.category,
                            "severity": r.severity,
                            "description": r.description
                        }
                        for r in matched_rules
                    ]
                }

            # 新增工具执行
            elif tool_name == "jadx_get_main_activity":
                return self.mcp_client.call_tool("get_main_activity_class", {})

            elif tool_name == "jadx_get_application_classes":
                return self.mcp_client.call_tool("get_main_application_classes_names", {})

            elif tool_name == "jadx_get_resource_files":
                offset = tool_input.get("offset", 0)
                count = tool_input.get("count", 0)
                return self.mcp_client.call_tool("get_all_resource_file_names", {
                    "offset": offset,
                    "count": count
                })

            elif tool_name == "jadx_get_resource_file":
                resource_name = tool_input["resource_name"]
                return self.mcp_client.call_tool("get_resource_file", {
                    "resource_name": resource_name
                })

            elif tool_name == "jadx_get_methods_of_class":
                class_name = tool_input["class_name"]
                return self.mcp_client.call_tool("get_methods_of_class", {
                    "class_name": class_name
                })

            elif tool_name == "jadx_get_fields_of_class":
                class_name = tool_input["class_name"]
                return self.mcp_client.call_tool("get_fields_of_class", {
                    "class_name": class_name
                })

            elif tool_name == "jadx_get_smali_of_class":
                class_name = tool_input["class_name"]
                return self.mcp_client.call_tool("get_smali_of_class", {
                    "class_name": class_name
                })

            elif tool_name == "jadx_get_xrefs_to_class":
                class_name = tool_input["class_name"]
                offset = tool_input.get("offset", 0)
                count = tool_input.get("count", 0)
                return self.mcp_client.call_tool("get_xrefs_to_class", {
                    "class_name": class_name,
                    "offset": offset,
                    "count": count
                })

            elif tool_name == "jadx_get_xrefs_to_method":
                class_name = tool_input["class_name"]
                method_name = tool_input["method_name"]
                offset = tool_input.get("offset", 0)
                count = tool_input.get("count", 0)
                return self.mcp_client.call_tool("get_xrefs_to_method", {
                    "class_name": class_name,
                    "method_name": method_name,
                    "offset": offset,
                    "count": count
                })

            else:
                return {"error": f"未知工具: {tool_name}"}

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return {"error": str(e)}

    def _get_tool_display_name(self, tool_name: str) -> str:
        """获取工具的显示名称（中文）"""
        display_names = {
            "jadx_open_apk": "打开 APK",
            "jadx_get_manifest": "获取 Manifest",
            "jadx_get_permissions": "获取权限",
            "jadx_get_code_paths": "获取代码路径",
            "jadx_get_strings": "提取字符串",
            "jadx_get_network_info": "分析网络通信",
            "jadx_get_apis": "分析 API 调用",
            "jadx_search_classes": "搜索类",
            "jadx_get_class_source": "获取类源码",
            "match_malware_rules": "匹配恶意规则",
            # 新增工具
            "jadx_get_main_activity": "获取主 Activity",
            "jadx_get_application_classes": "获取应用类列表",
            "jadx_get_resource_files": "获取资源文件列表",
            "jadx_get_resource_file": "获取资源文件内容",
            "jadx_get_methods_of_class": "获取类方法列表",
            "jadx_get_fields_of_class": "获取类字段列表",
            "jadx_get_smali_of_class": "获取 Smali 代码",
            "jadx_get_xrefs_to_class": "获取类引用",
            "jadx_get_xrefs_to_method": "获取方法引用"
        }
        return display_names.get(tool_name, tool_name)

    def _format_result_summary(self, tool_name: str, result: Any) -> str:
        """格式化工具执行结果的摘要"""
        if not result or isinstance(result, dict) and "error" in result:
            return "执行失败"

        summaries = {
            "jadx_open_apk": lambda r: f"已打开 {r.get('apk_path', '')}" if r.get('success') else "打开失败",
            "jadx_get_manifest": lambda r: f"包名: {r.get('package', 'unknown')}",
            "jadx_get_permissions": lambda r: f"共 {r.get('count', 0)} 个权限，{r.get('dangerous_count', 0)} 个危险",
            "jadx_get_code_paths": lambda r: f"找到 {len(r) if isinstance(r, list) else 0} 个类",
            "jadx_get_strings": lambda r: f"提取 {len(r) if isinstance(r, list) else 0} 个字符串",
            "jadx_get_network_info": lambda r: f"{len(r.get('urls', []))} 个 URL, {len(r.get('ips', []))} 个 IP",
            "jadx_get_apis": lambda r: f"发现 {len(r) if isinstance(r, list) else 0} 个 API 调用",
            "jadx_search_classes": lambda r: f"找到 {len(r.get('classes', [])) if isinstance(r, dict) else 0} 个类",
            "jadx_get_class_source": lambda r: f"源码长度: {len(r.get('source', '')) if isinstance(r, dict) else 0} 字符",
            "match_malware_rules": lambda r: f"匹配 {r.get('total_matched', 0)} 条恶意规则",
            # 新增工具摘要
            "jadx_get_main_activity": lambda r: f"主 Activity: {r.get('class_name', 'unknown') if isinstance(r, dict) else 'unknown'}",
            "jadx_get_application_classes": lambda r: f"{len(r) if isinstance(r, list) else 0} 个应用类",
            "jadx_get_resource_files": lambda r: f"{len(r) if isinstance(r, list) else 0} 个资源文件",
            "jadx_get_resource_file": lambda r: f"获取资源: {r.get('resource_name', 'unknown') if isinstance(r, dict) else 'unknown'}",
            "jadx_get_methods_of_class": lambda r: f"{len(r.get('methods', [])) if isinstance(r, dict) else 0} 个方法",
            "jadx_get_fields_of_class": lambda r: f"{len(r.get('fields', [])) if isinstance(r, dict) else 0} 个字段",
            "jadx_get_smali_of_class": lambda r: f"Smali 长度: {len(r.get('smali', '')) if isinstance(r, dict) else 0} 字符",
            "jadx_get_xrefs_to_class": lambda r: f"{len(r.get('xrefs', [])) if isinstance(r, dict) else 0} 个引用",
            "jadx_get_xrefs_to_method": lambda r: f"{len(r.get('xrefs', [])) if isinstance(r, dict) else 0} 个调用"
        }

        formatter = summaries.get(tool_name)
        if formatter:
            try:
                return formatter(result)
            except:
                return "结果格式化失败"
        return "执行完成"

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
