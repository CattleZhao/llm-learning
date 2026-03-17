"""
规则学习模块

从分析结果中提取候选恶意模式规则
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

from config import get_settings

logger = logging.getLogger(__name__)


class RuleLearner:
    """规则学习器"""

    def __init__(self, pending_dir: str = None):
        """
        初始化规则学习器

        Args:
            pending_dir: 候选规则存储目录
        """
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)

        if pending_dir is None:
            pending_dir = str(settings.memory.candidate_rules_dir)

        self.pending_dir = Path(pending_dir)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def extract_candidate_rules(
        self,
        analysis_result
    ) -> List[Dict[str, Any]]:
        """
        从分析结果中提取候选规则

        Args:
            analysis_result: AgentResponse 实例

        Returns:
            候选规则列表
        """
        prompt = f"""
请从以下 APK 分析结果中提取可能的新检测规则。

分析报告：
{analysis_result.content[:3000]}

元数据：
{json.dumps(analysis_result.metadata, ensure_ascii=False, indent=2)}

对每个发现的模式，输出一个 JSON 规则：
{{
    "name": "规则名称",
    "category": "类别（trojan/ransomware/spyware等）",
    "severity": "严重程度（low/medium/high/critical）",
    "description": "规则描述",
    "pattern": "正则表达式模式（仅包路径规则）",
    "indicators": {{"domains": [], "ips": [], "urls": []}},
    "reason": "为什么这个模式可疑"
}}

只输出明确的恶意模式，不要过度泛化。
每行一个 JSON 对象。
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # 解析 JSON 规则
            rules = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        rule = json.loads(line)
                        rule["id"] = str(uuid.uuid4())
                        rules.append(rule)
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Extracted {len(rules)} candidate rules")
            return rules

        except Exception as e:
            logger.error(f"Failed to extract rules: {e}")
            return []

    def _extract_mock(self, analysis_result) -> List[Dict[str, Any]]:
        """Mock 提取（测试用）"""
        return [{
            "id": str(uuid.uuid4()),
            "name": "测试规则",
            "category": "test",
            "severity": "high",
            "description": "从分析中提取的测试规则",
            "pattern": "com/malware/.*",
            "indicators": {"domains": [], "ips": [], "urls": []},
            "reason": "测试用"
        }]

    def save_to_pending(
        self,
        rule: Dict[str, Any]
    ) -> str:
        """
        保存候选规则到待审核目录

        Args:
            rule: 规则字典

        Returns:
            保存的文件路径
        """
        rule_id = rule.get("id", str(uuid.uuid4()))
        file_path = self.pending_dir / f"{rule_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rule, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved candidate rule to {file_path}")
        return str(file_path)

    def load_pending_rules(self) -> List[Dict[str, Any]]:
        """
        加载所有待审核的规则

        Returns:
            待审核规则列表
        """
        rules = []

        for file_path in self.pending_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    rule = json.load(f)
                    rule["id"] = file_path.stem
                    rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        return rules

    def approve_rule(
        self,
        rule_id: str,
        category: str = "custom"
    ) -> str:
        """
        批准规则并添加到规则库

        Args:
            rule_id: 规则 ID
            category: 规则类别

        Returns:
            保存的文件路径
        """
        # 加载候选规则
        rule_file = self.pending_dir / f"{rule_id}.json"
        if not rule_file.exists():
            raise FileNotFoundError(f"Rule not found: {rule_id}")

        with open(rule_file, "r", encoding="utf-8") as f:
            rule = json.load(f)

        # 删除候选规则
        rule_file.unlink()

        # 保存到正式规则库
        try:
            from knowledge_base import get_rule_loader
            rule_loader = get_rule_loader()

            rules_dir = Path(rule_loader.rules_dir) / "custom"
            rules_dir.mkdir(parents=True, exist_ok=True)

            # 添加到 custom_rules.json
            custom_rules_file = rules_dir / "custom_rules.json"

            existing_rules = []
            if custom_rules_file.exists():
                with open(custom_rules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing_rules = data.get("rules", [])

            # 添加新规则
            rule["category"] = category
            existing_rules.append(rule)

            # 保存
            with open(custom_rules_file, "w", encoding="utf-8") as f:
                json.dump({"rules": existing_rules}, f, ensure_ascii=False, indent=2)

            logger.info(f"Approved rule {rule_id} added to custom rules")
            return str(custom_rules_file)

        except ImportError:
            # 如果 knowledge_base 不可用，只删除候选规则并记录
            logger.warning(f"knowledge_base not available, rule {rule_id} removed from pending but not added to rules")
            return ""

    def reject_rule(self, rule_id: str) -> bool:
        """
        拒绝并删除候选规则

        Args:
            rule_id: 规则 ID

        Returns:
            是否删除成功
        """
        rule_file = self.pending_dir / f"{rule_id}.json"

        if rule_file.exists():
            rule_file.unlink()
            logger.info(f"Rejected rule {rule_id}")
            return True

        return False


_rule_learner_singleton: Optional[RuleLearner] = None


def get_rule_learner() -> RuleLearner:
    """获取 RuleLearner 单例"""
    global _rule_learner_singleton
    if _rule_learner_singleton is None:
        _rule_learner_singleton = RuleLearner()
        logger.info("RuleLearner singleton created")
    return _rule_learner_singleton
