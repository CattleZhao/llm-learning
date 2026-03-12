"""
规则加载器模块

从 JSON 文件加载恶意软件检测规则
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MalwareRule:
    """
    恶意软件规则

    定义一个检测规则，包含多个匹配模式
    """
    name: str                              # 规则名称
    category: str                          # 类别 (trojan, malware, miner, etc.)
    severity: str                          # 严重程度 (low, medium, high, critical)
    description: str                       # 规则描述
    patterns: List[str] = field(default_factory=list)  # 正则表达式模式列表
    references: List[str] = field(default_factory=list)  # 参考信息
    tags: List[str] = field(default_factory=list)          # 标签

    def matches(self, code_path: str) -> bool:
        """
        检查给定的代码路径是否匹配该规则

        Args:
            code_path: 要检查的代码路径 (如 "com/malware/trojan/Main.smali")

        Returns:
            是否匹配任何模式
        """
        import re

        for pattern in self.patterns:
            try:
                if re.search(pattern, code_path):
                    return True
            except re.error:
                print(f"[Warning] 无效的正则表达式: {pattern}")
                continue
        return False

    def get_match_details(self, code_path: str) -> Optional[Dict[str, Any]]:
        """
        获取匹配的详细信息

        Args:
            code_path: 要检查的代码路径

        Returns:
            匹配信息，如果没有匹配则返回 None
        """
        import re

        for pattern in self.patterns:
            try:
                match = re.search(pattern, code_path)
                if match:
                    return {
                        "rule_name": self.name,
                        "matched_pattern": pattern,
                        "matched_text": match.group(0),
                        "position": match.span()
                    }
            except re.error:
                continue
        return None


class RuleLoader:
    """
    规则加载器

    从 JSON 文件加载和管理恶意软件检测规则
    """

    def __init__(self, rules_dir: str = "knowledge_base/raw/rules"):
        """
        初始化规则加载器

        Args:
            rules_dir: 规则文件目录
        """
        self.rules_dir = Path(rules_dir)
        self.rules: List[MalwareRule] = []
        self._load_rules()

    def _load_rules(self):
        """从规则目录加载所有规则"""
        if not self.rules_dir.exists():
            print(f"[Warning] 规则目录不存在: {self.rules_dir}")
            return

        # 查找所有 JSON 规则文件
        rule_files = list(self.rules_dir.glob("*.json"))

        if not rule_files:
            print(f"[Info] 未找到规则文件在 {self.rules_dir}")
            return

        for rule_file in rule_files:
            self._load_from_file(rule_file)

        print(f"[Info] 已加载 {len(self.rules)} 条规则，来自 {len(rule_files)} 个文件")

    def _load_from_file(self, rule_file: Path):
        """从单个文件加载规则"""
        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "rules" in data:
                for rule_data in data["rules"]:
                    self.rules.append(MalwareRule(**rule_data))
            else:
                # 如果是单个规则的格式
                self.rules.append(MalwareRule(**data))

            print(f"[Info] 从 {rule_file.name} 加载了 {len(data.get('rules', [data]))} 条规则")

        except Exception as e:
            print(f"[Error] 加载规则文件 {rule_file} 失败: {e}")

    def add_rule(self, rule: MalwareRule):
        """
        添加一条规则

        Args:
            rule: MalwareRule 对象
        """
        self.rules.append(rule)

    def get_rules_by_category(self, category: str) -> List[MalwareRule]:
        """按类别获取规则"""
        return [r for r in self.rules if r.category == category]

    def get_rules_by_severity(self, severity: str) -> List[MalwareRule]:
        """按严重程度获取规则"""
        return [r for r in self.rules if r.severity == severity]

    def search_rules(self, keyword: str) -> List[MalwareRule]:
        """搜索规则"""
        keyword_lower = keyword.lower()
        return [
            r for r in self.rules
            if (keyword_lower in r.name.lower() or
                keyword_lower in r.description.lower() or
                any(keyword_lower in tag.lower() for tag in r.tags))
        ]

    def match_rules(self, code_path: str) -> List[MalwareRule]:
        """
        获取所有匹配给定代码路径的规则

        Args:
            code_path: 要检查的代码路径

        Returns:
            匹配的规则列表
        """
        matched = []
        for rule in self.rules:
            if rule.matches(code_path):
                matched.append(rule)
        return matched

    def match_url_rules(self, url: str) -> List[MalwareRule]:
        """
        获取所有匹配给定 URL 的规则

        Args:
            url: 要检查的 URL

        Returns:
            匹配的规则列表
        """
        import re

        # URL 相关的类别
        url_categories = {"url", "c2_server", "malicious_domain", "phishing", "tracking"}

        matched = []
        for rule in self.rules:
            # 只检查 URL 相关类别的规则
            if rule.category not in url_categories:
                continue

            for pattern in rule.patterns:
                try:
                    if re.search(pattern, url, re.IGNORECASE):
                        matched.append(rule)
                        break
                except re.error:
                    continue
        return matched

    def get_all_categories(self) -> List[str]:
        """获取所有规则类别"""
        categories = set(r.category for r in self.rules)
        return sorted(list(categories))

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for rule in self.rules:
            tags.update(rule.tags)
        return sorted(list(tags))

    def to_dict(self) -> Dict[str, Any]:
        """将规则转换为字典（用于序列化）"""
        return {
            "rules": [
                {
                    "name": r.name,
                    "category": r.category,
                    "severity": r.severity,
                    "description": r.description,
                    "patterns": r.patterns,
                    "references": r.references,
                    "tags": r.tags
                }
                for r in self.rules
            ],
            "total": len(self.rules),
            "categories": self.get_all_categories(),
            "tags": self.get_all_tags()
        }

    def save_rules(self, output_path: str):
        """
        保存当前规则到文件

        Args:
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"[Info] 已保存 {len(self.rules)} 条规则到 {output_path}")


# 便捷函数
def get_rule_loader(rules_dir: str = "knowledge_base/raw/rules") -> RuleLoader:
    """
    获取规则加载器实例

    Args:
        rules_dir: 规则目录路径

    Returns:
        RuleLoader 实例
    """
    return RuleLoader(rules_dir)
