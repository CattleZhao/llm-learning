"""
APK 恶意行为分析 Agent

结合 MCP 工具调用、恶意软件知识库和自我反思机制
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Any, Optional
from agents.base import BaseAgent, AgentResponse
from tools.mcp.jadx_client import JMCPClient
from knowledge_base.malware_patterns import MalwareKnowledgeBase, get_knowledge_base
from reflection.checker import AnalysisReflection, create_reflection_checker, ReflectionResult
from config import get_settings


class APKAnalysisAgent(BaseAgent):
    """
    APK 恶意行为分析 Agent

    使用 MCP 工具进行 APK 反编译和分析，
    结合知识库和自我反思生成全面的安全报告
    """

    def __init__(
        self,
        mcp_server_url: str = "http://localhost:3000",
        enable_advanced_analysis: bool = False
    ):
        super().__init__(
            name="APK 安全分析专家",
            description="专门检测 Android APK 中恶意行为的安全分析 Agent",
            role="security_analyst",
            enable_memory=True,
            enable_reflection=True
        )

        # 初始化 MCP 客户端
        self.mcp_client = JMCPClient(mcp_server_url)
        self.mcp_client.connect()

        # 获取知识库
        self.knowledge_base = get_knowledge_base()

        # 创建反思检查器
        self.reflection_checker = create_reflection_checker(enable_advanced_analysis)

        # 当前分析状态
        self.current_analysis: Dict[str, Any] = {}

    def think(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> AgentResponse:
        """
        执行 APK 分析

        Args:
            input_text: 用户输入（APK 文件路径或分析请求）
            context: 额外上下文

        Returns:
            AgentResponse 对象
        """
        # 解析用户输入
        apk_path = self._extract_apk_path(input_text, context)

        if not apk_path:
            return AgentResponse(
                content="请提供要分析的 APK 文件路径",
                metadata={"error": "no_apk_path"}
            )

        # 执行分析
        try:
            self._analyze_apk(apk_path)
            return self._generate_response()
        except Exception as e:
            return AgentResponse(
                content=f"分析过程中出错: {str(e)}",
                metadata={"error": str(e)}
            )

    def _extract_apk_path(
        self,
        input_text: str,
        context: Optional[Dict]
    ) -> Optional[str]:
        """从输入中提取 APK 路径"""
        # 如果 context 中有 apk_path
        if context and "apk_path" in context:
            return context["apk_path"]

        # 从输入文本中提取
        if input_text.endswith(".apk"):
            return input_text

        # 简单命令解析
        if "分析" in input_text:
            parts = input_text.split()
            for part in parts:
                if part.endswith(".apk"):
                    return part

        return None

    def _analyze_apk(self, apk_path: str):
        """
        执行完整的 APK 分析

        Args:
            apk_path: APK 文件路径
        """
        # 1. 反编译并获取基本信息
        manifest = self.mcp_client.get_manifest(apk_path)
        self.current_analysis["manifest"] = manifest

        # 2. 权限分析
        permissions = self.mcp_client.get_permissions(apk_path)
        self._analyze_permissions(permissions)

        # 3. 网络通信分析
        network_info = self.mcp_client.get_network_info(apk_path)
        self.current_analysis["network_info"] = network_info
        self._analyze_network(network_info)

        # 4. API 调用分析
        api_calls = self.mcp_client.get_apis(apk_path)
        self.current_analysis["api_calls"] = api_calls
        self._analyze_apis(api_calls)

        # 5. 字符串分析
        strings = self.mcp_client.get_strings(apk_path)
        self.current_analysis["suspicious_strings"] = []
        self._analyze_strings(strings)

        # 6. 代码结构分析
        decompile_info = self.mcp_client.decompile_apk(apk_path)
        self.current_analysis["code_analysis"] = decompile_info

        # 7. 匹配恶意模式
        self._match_malware_patterns()

        # 8. 计算风险等级
        self._calculate_risk_level()

    def _analyze_permissions(self, permissions: List[str]):
        """分析权限"""
        dangerous_perms = [
            "READ_PHONE_STATE", "READ_SMS", "SEND_SMS",
            "ACCESS_FINE_LOCATION", "READ_CONTACTS",
            "RECORD_AUDIO", "CAMERA", "READ_CALENDAR"
        ]

        found_dangerous = [p for p in permissions if any(d in p for d in dangerous_perms)]

        self.current_analysis["permissions"] = {
            "all": permissions,
            "dangerous": found_dangerous,
            "count": len(permissions),
            "dangerous_count": len(found_dangerous)
        }

        if found_dangerous:
            self.current_analysis.setdefault("findings", []).append({
                "category": "permissions",
                "severity": "high" if len(found_dangerous) >= 3 else "medium",
                "description": f"发现 {len(found_dangerous)} 个危险权限",
                "evidence": found_dangerous
            })

    def _analyze_network(self, network_info: Dict[str, Any]):
        """分析网络通信"""
        findings = []

        # 检查是否使用 HTTPS
        urls = network_info.get("urls", [])
        has_encryption = network_info.get("has_encryption", False)

        non_https_urls = [u for u in urls if not u.startswith("https://")]
        if non_https_urls:
            findings.append({
                "category": "network",
                "severity": "high",
                "description": "发现使用非 HTTPS 的网络通信",
                "evidence": non_https_urls
            })

        # 检查是否有硬编码IP
        ips = network_info.get("ips", [])
        if ips:
            findings.append({
                "category": "network",
                "severity": "medium",
                "description": "发现硬编码 IP 地址",
                "evidence": ips
            })

        self.current_analysis.setdefault("findings", []).extend(findings)

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
                "description": "发现隐私敏感 API 调用",
                "evidence": suspicious_apis
            })

    def _analyze_strings(self, strings: List[str]):
        """分析字符串"""
        suspicious_patterns = [
            "password", "token", "deviceId", "imei",
            "http://", "192.168", "10.0.0"
        ]

        found_suspicious = [
            s for s in strings
            if any(pattern.lower() in s.lower() for pattern in suspicious_patterns)
        ]

        if found_suspicious:
            self.current_analysis["suspicious_strings"] = found_suspicious[:20]  # 最多保存20个

    def _match_malware_patterns(self):
        """匹配恶意软件模式"""
        # 提取当前分析的指标
        indicators = []

        perms = self.current_analysis.get("permissions", {})
        if isinstance(perms, dict) and perms.get("dangerous"):
            indicators.extend(perms["dangerous"])

        strings = self.current_analysis.get("suspicious_strings", [])
        if strings and isinstance(strings, list):
            indicators.extend(strings)

        # 在知识库中匹配
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

        # 计算风险分数
        risk_score = 0
        severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        for finding in findings:
            risk_score += severity_scores.get(finding.get("severity", "low"), 0)

        # 确定风险等级
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

        # 生成判定
        if risk_level in ["high", "critical"]:
            self.current_analysis["verdict"] = "检测到可疑行为，建议进一步人工审查"
        else:
            self.current_analysis["verdict"] = "未检测到明显恶意行为"

    def _generate_response(self) -> AgentResponse:
        """生成响应"""
        # 执行自我反思
        reflection = self.reflection_checker.reflect(
            self.current_analysis,
            self.current_analysis.get("manifest", {})
        )

        # 构建响应内容
        content = self._format_report(reflection)

        # 如果不完整，添加改进建议
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

        # 基本信息
        manifest = self.current_analysis.get("manifest", {})
        report.append("## 基本信息")
        report.append(f"- 包名: {manifest.get('package', 'unknown')}")
        report.append(f"- 版本: {manifest.get('version_name', 'unknown')}")
        report.append(f"- 风险等级: {self.current_analysis.get('risk_level', 'unknown').upper()}")
        report.append(f"- 判定: {self.current_analysis.get('verdict', '')}")
        report.append("")

        # 权限分析
        if "permissions" in self.current_analysis:
            report.append("## 权限分析")
            perms = self.current_analysis["permissions"]
            report.append(f"- 总权限数: {perms['count']}")
            report.append(f"- 危险权限: {perms['dangerous_count']}")
            if perms["dangerous"]:
                report.append(f"- 危险权限列表:")
                for p in perms["dangerous"][:5]:  # 只显示前5个
                    report.append(f"  - {p}")
            report.append("")

        # 发现
        findings = self.current_analysis.get("findings", [])
        if findings:
            report.append("## 安全发现")
            for i, finding in enumerate(findings[:10], 1):  # 最多显示10个
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                icon = severity_icon.get(finding.get("severity", ""), "⚪")
                report.append(f"{i}. {icon} [{finding.get('severity', '').upper()}] {finding['description']}")
            report.append("")

        # 分析质量
        report.append("## 分析质量")
        report.append(f"- 完整性: {reflection.confidence * 100:.1f}%")
        report.append(f"- 置信度: {reflection.confidence * 100:.1f}%")
        report.append(f"- 质量评分: {reflection.quality_score * 100:.1f}%")

        return "\n".join(report)


# 便捷函数
def create_apk_agent(
    mcp_server_url: str = "http://localhost:3000",
    enable_advanced: bool = False
) -> APKAnalysisAgent:
    """
    创建 APK 分析 Agent

    Args:
        mcp_server_url: MCP Server 地址
        enable_advanced: 是否启用高级分析

    Returns:
        APKAnalysisAgent 实例
    """
    return APKAnalysisAgent(
        mcp_server_url=mcp_server_url,
        enable_advanced_analysis=enable_advanced
    )
