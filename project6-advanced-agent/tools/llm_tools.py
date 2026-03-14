"""
LLM 工具定义和执行模块

将 MCP 客户端方法包装为 LLM 可调用的工具
"""
from typing import Any, Dict, List
from pathlib import Path


# ============================================================
# 工具定义类 - 定义所有 LLM 可调用的工具
# ============================================================

class ToolDefinitions:
    """工具定义类 - 定义所有 LLM 可调用的工具"""

    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """获取所有可用工具的定义"""
        return [
            # 基础分析工具
            ToolDefinitions.jadx_open_apk(),
            ToolDefinitions.jadx_get_manifest(),
            ToolDefinitions.jadx_get_permissions(),
            ToolDefinitions.jadx_get_code_paths(),
            ToolDefinitions.jadx_get_strings(),
            ToolDefinitions.jadx_get_network_info(),
            ToolDefinitions.jadx_get_apis(),
            # 搜索和源码工具
            ToolDefinitions.jadx_search_classes(),
            ToolDefinitions.jadx_get_class_source(),
            # 应用信息工具
            ToolDefinitions.jadx_get_main_activity(),
            ToolDefinitions.jadx_get_application_classes(),
            ToolDefinitions.jadx_get_resource_files(),
            ToolDefinitions.jadx_get_resource_file(),
            # 深度分析工具
            ToolDefinitions.jadx_get_methods_of_class(),
            ToolDefinitions.jadx_get_fields_of_class(),
            ToolDefinitions.jadx_get_smali_of_class(),
            # 引用追踪工具
            ToolDefinitions.jadx_get_xrefs_to_class(),
            ToolDefinitions.jadx_get_xrefs_to_method(),
            # 规则检测工具
            ToolDefinitions.match_malware_rules(),
        ]

    # ============ 基础分析工具 ============

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

    # ============ 搜索和源码工具 ============

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

    # ============ 应用信息工具 ============

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

    # ============ 深度分析工具 ============

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

    # ============ 引用追踪工具 ============

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

    # ============ 规则检测工具 ============

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


# ============================================================
# 工具执行器 - 执行工具调用
# ============================================================

class ToolExecutor:
    """工具执行器 - 负责执行工具并返回结果"""

    def __init__(self, mcp_client, rule_loader, logger=None):
        """
        初始化工具执行器

        Args:
            mcp_client: MCP 客户端实例
            rule_loader: 规则加载器实例
            logger: 日志记录器（可选）
        """
        self.mcp_client = mcp_client
        self.rule_loader = rule_loader
        self.logger = logger

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        执行指定的工具

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            工具执行结果
        """
        try:
            # ============ 基础分析工具 ============
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

            # ============ 搜索和源码工具 ============
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

            # ============ 应用信息工具 ============
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

            # ============ 深度分析工具 ============
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

            # ============ 引用追踪工具 ============
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

            # ============ 规则检测工具 ============
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

            else:
                return {"error": f"未知工具: {tool_name}"}

        except Exception as e:
            if self.logger:
                self.logger.error(f"工具执行出错: {e}")
            return {"error": str(e)}


# ============================================================
# 工具格式化器 - 格式化工具执行结果
# ============================================================

class ToolFormatter:
    """工具格式化器 - 负责格式化工具显示名称和执行结果"""

    # 工具显示名称（中文）
    DISPLAY_NAMES = {
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

    @staticmethod
    def get_display_name(tool_name: str) -> str:
        """获取工具的显示名称（中文）"""
        return ToolFormatter.DISPLAY_NAMES.get(tool_name, tool_name)

    @staticmethod
    def format_result_summary(tool_name: str, result: Any) -> str:
        """
        格式化工具执行结果的摘要

        Args:
            tool_name: 工具名称
            result: 工具执行结果

        Returns:
            结果摘要字符串
        """
        if not result or isinstance(result, dict) and "error" in result:
            return "执行失败"

        summaries = {
            # 基础分析工具
            "jadx_open_apk": lambda r: f"已打开 {r.get('apk_path', '')}" if r.get('success') else "打开失败",
            "jadx_get_manifest": lambda r: f"包名: {r.get('package', 'unknown')}",
            "jadx_get_permissions": lambda r: f"共 {r.get('count', 0)} 个权限，{r.get('dangerous_count', 0)} 个危险",
            "jadx_get_code_paths": lambda r: f"找到 {len(r) if isinstance(r, list) else 0} 个类",
            "jadx_get_strings": lambda r: f"提取 {len(r) if isinstance(r, list) else 0} 个字符串",
            "jadx_get_network_info": lambda r: f"{len(r.get('urls', []))} 个 URL, {len(r.get('ips', []))} 个 IP",
            "jadx_get_apis": lambda r: f"发现 {len(r) if isinstance(r, list) else 0} 个 API 调用",
            # 搜索和源码工具
            "jadx_search_classes": lambda r: f"找到 {len(r.get('classes', [])) if isinstance(r, dict) else 0} 个类",
            "jadx_get_class_source": lambda r: f"源码长度: {len(r.get('source', '')) if isinstance(r, dict) else 0} 字符",
            # 应用信息工具
            "jadx_get_main_activity": lambda r: f"主 Activity: {r.get('class_name', 'unknown') if isinstance(r, dict) else 'unknown'}",
            "jadx_get_application_classes": lambda r: f"{len(r) if isinstance(r, list) else 0} 个应用类",
            "jadx_get_resource_files": lambda r: f"{len(r) if isinstance(r, list) else 0} 个资源文件",
            "jadx_get_resource_file": lambda r: f"获取资源: {r.get('resource_name', 'unknown') if isinstance(r, dict) else 'unknown'}",
            # 深度分析工具
            "jadx_get_methods_of_class": lambda r: f"{len(r.get('methods', [])) if isinstance(r, dict) else 0} 个方法",
            "jadx_get_fields_of_class": lambda r: f"{len(r.get('fields', [])) if isinstance(r, dict) else 0} 个字段",
            "jadx_get_smali_of_class": lambda r: f"Smali 长度: {len(r.get('smali', '')) if isinstance(r, dict) else 0} 字符",
            # 引用追踪工具
            "jadx_get_xrefs_to_class": lambda r: f"{len(r.get('xrefs', [])) if isinstance(r, dict) else 0} 个引用",
            "jadx_get_xrefs_to_method": lambda r: f"{len(r.get('xrefs', [])) if isinstance(r, dict) else 0} 个调用",
            # 规则检测工具
            "match_malware_rules": lambda r: f"匹配 {r.get('total_matched', 0)} 条恶意规则"
        }

        formatter = summaries.get(tool_name)
        if formatter:
            try:
                return formatter(result)
            except:
                return "结果格式化失败"
        return "执行完成"
