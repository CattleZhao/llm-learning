import pytest
from pathlib import Path
from memory.rule_learner import RuleLearner
from agents.base import AgentResponse

@pytest.fixture
def rule_learner(tmp_path):
    """创建临时 RuleLearner 实例"""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    return RuleLearner(pending_dir=str(rules_dir))

def test_extract_candidate_rules(rule_learner):
    """测试候选规则提取"""
    analysis = AgentResponse(
        content="# 分析报告\n发现恶意包路径: com/malware/payload/Attack",
        metadata={
            "matched_rules": ["rule1"],
            "behaviors": ["短信盗窃"]
        }
    )

    # 使用 mock 模式（不需要真实 API）
    candidates = rule_learner._extract_mock(analysis)

    assert len(candidates) > 0
    assert "pattern" in candidates[0]

def test_save_and_load_rule(rule_learner, tmp_path):
    """测试规则保存和加载"""
    rule = {
        "id": "test-rule-123",
        "name": "测试规则",
        "pattern": "com/malware/.*",
        "category": "test",
        "severity": "high",
        "description": "测试规则描述"
    }

    file_path = rule_learner.save_to_pending(rule)

    assert Path(file_path).exists()

    loaded = rule_learner.load_pending_rules()
    assert len(loaded) > 0
    assert loaded[0]["name"] == "测试规则"

def test_approve_and_reject_rule(rule_learner):
    """测试规则批准和拒绝"""
    rule = {
        "id": "test-rule-456",
        "name": "待批准规则",
        "pattern": "com/badware/.*",
        "category": "malware",
        "severity": "critical",
        "description": "恶意软件包路径"
    }

    rule_learner.save_to_pending(rule)

    # 测试批准
    # 注意：批准需要 knowledge_base，这里只测试文件操作
    pending = rule_learner.load_pending_rules()
    assert len(pending) > 0

    # 测试拒绝
    result = rule_learner.reject_rule("test-rule-456")
    assert result == True

    # 验证已删除
    pending = rule_learner.load_pending_rules()
    assert len(pending) == 0
