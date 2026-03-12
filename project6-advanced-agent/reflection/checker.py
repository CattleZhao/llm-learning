"""
自我反思模块

让 Agent 能够评估自己分析的完整性和质量
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AnalysisAspect(Enum):
    """分析维度"""
    PERMISSIONS = "permissions"           # 权限分析
    NETWORK = "network"                   # 网络通信
    CODE = "code"                         # 代码分析
    API = "api"                          # API 调用
    STRINGS = "strings"                   # 字符串分析
    MANIFEST = "manifest"                 # 清单分析
    OBFUSCATION = "obfuscation"           # 混淆分析
    SIGNATURES = "signatures"             # 签名分析


@dataclass
class ReflectionResult:
    """反思结果"""
    is_complete: bool                    # 分析是否完整
    missing_aspects: List[str]           # 缺失的分析维度
    confidence: float                     # 分析置信度 (0-1)
    suggestions: List[str]               # 改进建议
    quality_score: float                 # 质量评分 (0-1)


class AnalysisReflection:
    """
    分析反思器

    评估 Agent 的分析是否全面，提供改进建议
    """

    # 每个 APK 分析应该覆盖的维度
    REQUIRED_ASPECTS = {
        AnalysisAspect.PERMISSIONS,
        AnalysisAspect.NETWORK,
        AnalysisAspect.CODE,
        AnalysisAspect.API,
        AnalysisAspect.STRINGS,
        AnalysisAspect.MANIFEST
    }

    # 高级分析维度（可选）
    ADVANCED_ASPECTS = {
        AnalysisAspect.OBFUSCATION,
        AnalysisAspect.SIGNATURES
    }

    def __init__(self, enable_advanced: bool = False):
        """
        初始化反思器

        Args:
            enable_advanced: 是否启用高级分析检查
        """
        self.enable_advanced = enable_advanced
        self.all_aspects = self.REQUIRED_ASPECTS.copy()
        if enable_advanced:
            self.all_aspects.update(self.ADVANCED_ASPECTS)

    def reflect(
        self,
        analysis_data: Dict[str, Any],
        apk_info: Dict[str, Any]
    ) -> ReflectionResult:
        """
        对分析结果进行反思

        Args:
            analysis_data: Agent 的分析数据
            apk_info: APK 基本信息

        Returns:
            ReflectionResult 对象
        """
        # 检查缺失的分析维度
        covered_aspects = self._get_covered_aspects(analysis_data)
        missing_aspects = self._get_missing_aspects(covered_aspects)

        # 计算完整性
        required_covered = covered_aspects & self.REQUIRED_ASPECTS
        completeness = len(required_covered) / len(self.REQUIRED_ASPECTS)

        # 生成建议
        suggestions = self._generate_suggestions(missing_aspects, analysis_data)

        # 计算置信度
        confidence = self._calculate_confidence(analysis_data, completeness)

        # 计算质量评分
        quality_score = self._calculate_quality_score(
            completeness, confidence, analysis_data
        )

        return ReflectionResult(
            is_complete=len(missing_aspects) == 0,
            missing_aspects=[a.value for a in missing_aspects],
            confidence=confidence,
            suggestions=suggestions,
            quality_score=quality_score
        )

    def _get_covered_aspects(self, analysis_data: Dict[str, Any]) -> set:
        """获取已覆盖的分析维度"""
        covered = set()

        if analysis_data.get("permissions"):
            covered.add(AnalysisAspect.PERMISSIONS)
        if analysis_data.get("network_info"):
            covered.add(AnalysisAspect.NETWORK)
        if analysis_data.get("code_analysis"):
            covered.add(AnalysisAspect.CODE)
        if analysis_data.get("api_calls"):
            covered.add(AnalysisAspect.API)
        if analysis_data.get("suspicious_strings"):
            covered.add(AnalysisAspect.STRINGS)
        if analysis_data.get("manifest"):
            covered.add(AnalysisAspect.MANIFEST)
        if analysis_data.get("obfuscation_level"):
            covered.add(AnalysisAspect.OBFUSCATION)
        if analysis_data.get("signatures"):
            covered.add(AnalysisAspect.SIGNATURES)

        return covered

    def _get_missing_aspects(self, covered: set) -> set:
        """获取缺失的分析维度"""
        return self.all_aspects - covered

    def _generate_suggestions(
        self,
        missing_aspects: set,
        analysis_data: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        aspect_suggestions = {
            AnalysisAspect.PERMISSIONS: "需要分析 APK 声明的权限，检查是否有危险权限组合",
            AnalysisAspect.NETWORK: "需要分析网络通信，检查URL、IP和加密情况",
            AnalysisAspect.CODE: "需要进行代码结构分析，检查是否存在可疑代码模式",
            AnalysisAspect.API: "需要检查API调用，特别是隐私和敏感API",
            AnalysisAspect.STRINGS: "需要提取和分析硬编码字符串，寻找可疑内容",
            AnalysisAspect.MANIFEST: "需要深入分析Manifest，检查组件和配置",
            AnalysisAspect.OBFUSCATION: "需要评估代码混淆程度",
            AnalysisAspect.SIGNATURES: "需要检查APK签名和证书信息"
        }

        for aspect in missing_aspects:
            if aspect in aspect_suggestions:
                suggestions.append(aspect_suggestions[aspect])

        # 根据已有数据生成针对性建议
        if not suggestions:
            if analysis_data.get("risk_level") == "unknown":
                suggestions.append("未能确定风险等级，需要更深入的分析")

        return suggestions

    def _calculate_confidence(
        self,
        analysis_data: Dict[str, Any],
        completeness: float
    ) -> float:
        """计算分析置信度"""
        base_confidence = completeness

        # 根据分析质量调整
        quality_factors = 0.0

        # 如果找到明确的恶意行为，提高置信度
        if analysis_data.get("malicious_behaviors"):
            quality_factors += 0.1

        # 如果有详细的证据，提高置信度
        if analysis_data.get("evidence"):
            if len(analysis_data["evidence"]) > 3:
                quality_factors += 0.1

        # 如果给出了明确的风险等级，提高置信度
        if analysis_data.get("risk_level") in ["low", "medium", "high", "critical"]:
            quality_factors += 0.1

        return min(base_confidence + quality_factors, 1.0)

    def _calculate_quality_score(
        self,
        completeness: float,
        confidence: float,
        analysis_data: Dict[str, Any]
    ) -> float:
        """计算整体质量评分"""
        # 完整性占40%
        # 置信度占30%
        # 结果明确性占30%

        clarity_score = 0.0
        if analysis_data.get("risk_level"):
            clarity_score = 0.3
        if analysis_data.get("verdict"):
            clarity_score += 0.2
        if analysis_data.get("malicious_behaviors"):
            clarity_score += 0.1

        return (
            completeness * 0.4 +
            confidence * 0.3 +
            min(clarity_score, 0.3)
        )


# 便捷函数
def create_reflection_checker(
    enable_advanced: bool = False
) -> AnalysisReflection:
    """
    创建反思检查器

    Args:
        enable_advanced: 是否启用高级检查

    Returns:
        AnalysisReflection 实例
    """
    return AnalysisReflection(enable_advanced=enable_advanced)
