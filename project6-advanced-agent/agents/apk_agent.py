"""
APK 恶意行为分析 Agent

完整流程:
1. JADX-GUI 打开 APK
2. 通过 MCP 协议进行分析
3. 输出分析报告
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import BaseAgent, AgentResponse
from tools.mcp.jadx_client_stdio import StdioMCPClient
from knowledge_base.malware_patterns import MalwareKnowledgeBase, get_knowledge_base
from knowledge_base import get_rule_loader
from reflection.checker import AnalysisReflection, create_reflection_checker, ReflectionResult


class APKAnalysisAgent(BaseAgent):
    """
    APK 恶意行为分析 Agent

    完整分析流程:
    1. 启动 JADX-GUI 并打开 APK
    2. 通过 MCP 协议获取代码信息
    3. 匹配恶意规则
    4. 生成分析报告
    """

    def __init__(
        self,
        mcp_server_path: str,
        jadx_gui_path: Optional[str] = None,
        enable_rag: bool = False,
        enable_advanced_analysis: bool = False,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        super().__init__(
            name="APK 安全分析专家",
            description="专门检测 Android APK 中恶意行为的安全分析 Agent",
            role="security_analyst",
            enable_memory=True,
            enable_reflection=True
        )

        self.on_status_update = on_status_update or (lambda msg: None)
        self.enable_rag = enable_rag

        # 初始化 MCP 客户端 (stdio 方式)
        # Windows 上使用 Python 直接运行，避免 WSAStartup 错误
        import platform
        if platform.system() == "Windows":
            command = ["python", str(Path(mcp_server_path) / "jadx_mcp_server.py")]
        else:
            command = ["uv", "--directory", mcp_server_path, "run", "jadx_mcp_server.py"]

        self.mcp_client = StdioMCPClient(
            server_command=command,
            jadx_gui_path=jadx_gui_path,
            on_status_update=self.on_status_update
        )
        self.mcp_client.connect()

        # 获取知识库
        self.knowledge_base = get_knowledge_base()
        self.rule_loader = get_rule_loader()

        # 创建反思检查器
        self.reflection_checker = create_reflection_checker(enable_advanced_analysis)

        # 当前分析状态
        self.current_analysis: Dict[str, Any] = {}

    def think(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> AgentResponse:
        """执行 APK 分析"""
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

        try:
            self._analyze_apk(apk_path)
            return self._generate_response()
        except Exception as e:
            import traceback
            return AgentResponse(
                content=f"分析过程中出错: {str(e)}",
                metadata={"error": str(e)}
            )

    def _extract_apk_path(self, input_text: str, context: Optional[Dict]) -> Optional[str]:
        """从输入中提取 APK 路径"""
        if context and "apk_path" in context:
            return context["apk_path"]
        if input_text.endswith(".apk"):
            return input_text
        if "分析" in input_text:
            parts = input_text.split()
            for part in parts:
                if part.endswith(".apk"):
                    return part
        return None

    def _analyze_apk(self, apk_path: str):
        """执行完整的 APK 分析（9步）"""
        # 1. 在 JADX-GUI 中打开 APK
        self.on_status_update("📱 步骤 1/9: 在 JADX-GUI 中打开 APK...")
        open_result = self.mcp_client.open_apk(apk_path)
        self.current_analysis["open_result"] = open_result

        # 2. 获取 Manifest 信息
        self.on_status_update("📄 步骤 2/9: 解析 AndroidManifest.xml...")
        manifest = self.mcp_client.get_manifest()
        self.current_analysis["manifest"] = manifest

        # 3. 权限分析
        self.on_status_update("🔐 步骤 3/9: 分析权限...")
        permissions = self.mcp_client.get_permissions()
        self._analyze_permissions(permissions)

        # 4. 获取包路径并匹配规则
        self.on_status_update("📂 步骤 4/9: 扫描代码路径...")
        code_paths = self.mcp_client.get_code_paths()
        self.current_analysis["code_paths"] = code_paths
        self.on_status_update(f"   找到 {len(code_paths)} 个代码文件")
        self._match_package_rules(code_paths)

        # 5. 网络通信分析
        self.on_status_update("🌐 步骤 5/9: 分析网络通信...")
        network_info = self.mcp_client.get_network_info()
        self.current_analysis["network_info"] = network_info
        self._analyze_network(network_info)

        # 6. API 调用分析
        self.on_status_update("⚙️ 步骤 6/9: 分析 API 调用...")
        api_calls = self.mcp_client.get_apis()
        self.current_analysis["api_calls"] = api_calls
        self._analyze_apis(api_calls)

        # 7. 字符串分析
        self.on_status_update("📝 步骤 7/9: 提取字符串...")
        strings = self.mcp_client.get_strings()
        self.current_analysis["all_strings"] = strings
        self.on_status_update(f"   提取了 {len(strings)} 个字符串")
        self.current_analysis["suspicious_strings"] = []
        self._analyze_strings(strings)

        # 8. 匹配恶意模式
        self.on_status_update("🎯 步骤 8/9: 匹配恶意模式...")
        self._match_malware_patterns()

        # 9. 计算风险等级
        self.on_status_update("📊 步骤 9/9: 计算风险等级...")
        self._calculate_risk_level()

        self.on_status_update("✅ 分析完成！")

    def _analyze_permissions(self, permissions: Dict[str, Any]):
        """分析权限"""
        self.current_analysis["permissions"] = permissions
        dangerous = permissions.get("dangerous", [])
        dangerous_count = len(dangerous)

        if dangerous_count > 0:
            severity = "critical" if dangerous_count >= 5 else "high" if dangerous_count >= 3 else "medium"
            self.current_analysis.setdefault("findings", []).append({
                "category": "permissions",
                "severity": severity,
                "description": f"发现 {dangerous_count} 个危险权限",
                "evidence": dangerous
            })

    def _match_package_rules(self, code_paths: List[str]):
        """使用自定义规则匹配包路径"""
        matched_rules = []
        for path in code_paths:
            java_path = path.replace(".java", "")
            rules = self.rule_loader.match_rules(java_path)
            for rule in rules:
                if rule not in matched_rules:
                    matched_rules.append(rule)

        if matched_rules:
            for rule in matched_rules:
                self.current_analysis.setdefault("findings", []).append({
                    "category": "package_pattern",
                    "severity": rule.severity,
                    "description": f"匹配到恶意包路径规则: {rule.name}",
                    "evidence": {
                        "rule": rule.name,
                        "category": rule.category,
                        "matched_patterns": rule.patterns
                    }
                })

    def _analyze_network(self, network_info: Dict[str, Any]):
        """分析网络通信"""
        urls = network_info.get("urls", [])

        for url in urls:
            rules = self.rule_loader.match_url_rules(url)
            for rule in rules:
                self.current_analysis.setdefault("findings", []).append({
                    "category": "url_blacklist",
                    "severity": rule.severity,
                    "description": f"匹配到恶意 URL 规则: {rule.name}",
                    "evidence": {"url": url, "rule": rule.name}
                })

        if network_info.get("has_http") and not network_info.get("has_https"):
            self.current_analysis.setdefault("findings", []).append({
                "category": "network",
                "severity": "medium",
                "description": "发现使用非 HTTPS 的网络通信",
                "evidence": urls
            })

        ips = network_info.get("ips", [])
        if ips:
            external_ips = [
                ip for ip in ips
                if not (ip.startswith("192.168.") or ip.startswith("10.") or
                       ip.startswith("172.16.") or ip == "127.0.0.1")
            ]
            if external_ips:
                self.current_analysis.setdefault("findings", []).append({
                    "category": "network",
                    "severity": "high",
                    "description": "发现硬编码公网 IP 地址",
                    "evidence": external_ips
                })

    def _analyze_apis(self, api_calls: List[Dict[str, Any]]):
        """分析 API 调用"""
        privacy_apis = [
            "getDeviceId", "getSubscriberId", "getLine1Number",
            "sendTextMessage", "requestLocationUpdates"
        ]

        suspicious_apis = [
            call for call in api_calls
            if any(api in call.get("method", "") for api in privacy_apis)
        ]

        if suspicious_apis:
            self.current_analysis.setdefault("findings", []).append({
                "category": "api",
                "severity": "high",
                "description": f"发现 {len(suspicious_apis)} 个隐私敏感 API 调用",
                "evidence": suspicious_apis[:5]
            })

    def _analyze_strings(self, strings: List[str]):
        """分析字符串"""
        suspicious_patterns = [
            "password", "token", "deviceId", "imei",
            "api_key", "secret", "private_key"
        ]

        found_suspicious = [
            s for s in strings
            if any(pattern.lower() in s.lower() for pattern in suspicious_patterns)
        ]

        if found_suspicious:
            self.current_analysis["suspicious_strings"] = found_suspicious[:20]

    def _match_malware_patterns(self):
        """匹配恶意软件模式"""
        indicators = []

        perms = self.current_analysis.get("permissions", {})
        if isinstance(perms, dict) and perms.get("dangerous"):
            indicators.extend(perms["dangerous"])

        strings = self.current_analysis.get("suspicious_strings", [])
        if strings and isinstance(strings, list):
            indicators.extend(strings)

        matched_patterns = self.knowledge_base.match_indicators(indicators)

        for pattern in matched_patterns:
            self.current_analysis.setdefault("findings", []).append({
                "category": "malware_pattern",
                "severity": pattern.severity,
                "description": f"匹配到已知恶意模式: {pattern.name}",
                "evidence": pattern.indicators,
                "mitigation": pattern.mitigation
            })

    def _calculate_risk_level(self):
        """计算总体风险等级"""
        findings = self.current_analysis.get("findings", [])

        if not findings:
            self.current_analysis["risk_level"] = "low"
            self.current_analysis["verdict"] = "未发现明显恶意行为"
            return

        risk_score = 0
        severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        for finding in findings:
            risk_score += severity_scores.get(finding.get("severity", "low"), 0)

        if risk_score >= 10:
            risk_level = "critical"
        elif risk_score >= 6:
            risk_level = "high"
        elif risk_score >= 3:
            risk_level = "medium"
        else:
            risk_level = "low"

        self.current_analysis["risk_level"] = risk_level
        self.current_analysis["risk_score"] = risk_score

        if risk_level in ["high", "critical"]:
            self.current_analysis["verdict"] = "检测到可疑行为，建议进一步人工审查"
        else:
            self.current_analysis["verdict"] = "未检测到明显恶意行为"

    def _generate_response(self) -> AgentResponse:
        """生成响应"""
        reflection = self.reflection_checker.reflect(
            self.current_analysis,
            self.current_analysis.get("manifest", {})
        )

        content = self._format_report(reflection)

        if not reflection.is_complete:
            content += "\n\n## 改进建议\n\n"
            content += "\n".join(f"- {s}" for s in reflection.suggestions)

        return AgentResponse(
            content=content,
            metadata={
                "risk_level": self.current_analysis.get("risk_level"),
                "risk_score": self.current_analysis.get("risk_score", 0),
                "findings_count": len(self.current_analysis.get("findings", [])),
                "quality_score": reflection.quality_score,
                "confidence": reflection.confidence
            },
            reflection=f"完整性: {reflection.is_complete}, 质量: {reflection.quality_score:.2f}"
        )

    def _format_report(self, reflection: ReflectionResult) -> str:
        """格式化分析报告"""
        report = ["# APK 安全分析报告\n"]

        manifest = self.current_analysis.get("manifest", {})
        report.append("## 基本信息")
        report.append(f"- 包名: `{manifest.get('package', 'unknown')}`")
        report.append(f"- 版本: `{manifest.get('version_name', 'unknown')}`")

        risk_level = self.current_analysis.get("risk_level", "unknown").upper()
        risk_icons = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
        icon = risk_icons.get(risk_level, "⚪")
        report.append(f"- 风险等级: {icon} {risk_level}")
        report.append(f"- 判定: {self.current_analysis.get('verdict', '')}")
        report.append("")

        if "permissions" in self.current_analysis:
            report.append("## 权限分析")
            perms = self.current_analysis["permissions"]
            report.append(f"- 总权限数: {perms.get('count', 0)}")
            report.append(f"- 危险权限: {perms.get('dangerous_count', 0)}")
            if perms.get("dangerous"):
                report.append(f"\n**危险权限列表:**")
                for p in perms["dangerous"][:5]:
                    report.append(f"  - `{p}`")
            report.append("")

        findings = self.current_analysis.get("findings", [])
        if findings:
            report.append("## 安全发现")
            for i, finding in enumerate(findings[:10], 1):
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                icon = severity_icon.get(finding.get("severity", ""), "⚪")
                report.append(f"{i}. {icon} **[{finding.get('severity', '').upper()}]** {finding['description']}")
            report.append("")

        report.append("## 分析质量")
        report.append(f"- 覆盖率: {reflection.confidence * 100:.1f}%")
        report.append(f"- 置信度: {reflection.confidence * 100:.1f}%")
        report.append(f"- 质量评分: {reflection.quality_score * 100:.1f}%")

        return "\n".join(report)


# 便捷函数
def create_apk_agent(
    mcp_server_path: str,
    jadx_gui_path: Optional[str] = None,
    enable_rag: bool = False,
    enable_advanced: bool = False,
    on_status_update: Optional[Callable[[str], None]] = None
) -> APKAnalysisAgent:
    """
    创建 APK 分析 Agent

    Args:
        mcp_server_path: jadx-mcp-server 目录路径
        jadx_gui_path: jadx-gui 可执行文件路径
        enable_rag: 是否启用 RAG 检索
        enable_advanced: 是否启用高级分析
        on_status_update: 状态更新回调

    Returns:
        APKAnalysisAgent 实例
    """
    return APKAnalysisAgent(
        mcp_server_path=mcp_server_path,
        jadx_gui_path=jadx_gui_path,
        enable_rag=enable_rag,
        enable_advanced_analysis=enable_advanced,
        on_status_update=on_status_update
    )
