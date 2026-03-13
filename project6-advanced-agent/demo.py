#!/usr/bin/env python3
"""
Project 6: APK 恶意行为分析 Agent - 演示脚本

展示三大高级特性的实际应用，包括自定义规则加载
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.apk_agent import create_apk_agent
from knowledge_base import get_rule_loader, get_knowledge_base
from reflection.checker import create_reflection_checker


def demo_rule_loader():
    """演示规则加载器"""
    print("=" * 60)
    print("演示 1: 自定义规则加载器")
    print("=" * 60)

    # 加载规则
    rule_loader = get_rule_loader()

    print(f"\n✅ 已加载 {len(rule_loader.rules)} 条规则")

    # 按类别展示
    for category in rule_loader.get_all_categories():
        rules = rule_loader.get_rules_by_category(category)
        print(f"\n{category.upper()} ({len(rules)} 条):")
        for rule in rules[:3]:  # 每个类别显示前3条
            print(f"  - [{rule.severity}] {rule.name}")

    # 测试规则匹配
    print("\n" + "-" * 40)
    print("测试规则匹配:")
    test_paths = [
        "com/malware/trojan/CommunicationManager.smali",
        "com/miner/stratum/MinerService.java",
        "com/normal/app/MainActivity.java"
    ]

    for path in test_paths:
        matched = rule_loader.match_rules(path)
        if matched:
            match_info = matched[0].get_match_details(path)
            print(f"\n  {path}")
            print(f"    ✅ 匹配到: {matched[0].name}")
            print(f"    🎯 匹配模式: {match_info['matched_pattern']}")
        else:
            print(f"\n  {path}")
            print(f"    ✅ 未匹配到恶意规则")


def demo_knowledge_base():
    """演示恶意软件知识库"""
    print("\n" + "=" * 60)
    print("演示 2: 恶意软件知识库")
    print("=" * 60)

    kb = get_knowledge_base()
    rule_loader = get_rule_loader()

    # 将规则加载器集成到知识库
    print("\n将自定义规则集成到知识库...")

    # 展示知识库和规则的协作
    print(f"\n知识库模式: {len(kb.patterns)} 个")
    print(f"自定义规则: {len(rule_loader.rules)} 条")
    print(f"总计: {len(kb.patterns) + len(rule_loader.rules)} 个检测模式")


def demo_reflection():
    """演示自我反思功能"""
    print("\n" + "=" * 60)
    print("演示 3: 自我反思功能")
    print("=" * 60)

    checker = create_reflection_checker()

    # 模拟完整的分析结果
    analysis = {
        "permissions": {"all": ["INTERNET", "READ_SMS"], "dangerous": ["READ_SMS"]},
        "network_info": {"urls": ["http://api.example.com"]},
        "api_calls": [{"method": "sendTextMessage"}],
        "suspicious_strings": ["token", "password"],
        "manifest": {"package": "com.example"},
        "code_analysis": {"obfuscation_level": "medium"},
        "risk_level": "high",
        "verdict": "发现可疑行为"
    }

    result = checker.reflect(analysis, {})

    print(f"\n分析质量评估:")
    print(f"  完整性: {'✅' if result.is_complete else '❌'}")
    print(f"  缺失维度: {', '.join(result.missing_aspects) if result.missing_aspects else '无'}")
    print(f"  置信度: {result.confidence * 100:.1f}%")
    print(f"  质量评分: {result.quality_score * 100:.1f}%")


def demo_apk_analysis():
    """演示 APK 分析"""
    print("\n" + "=" * 60)
    print("演示 4: APK 恶意行为分析")
    print("=" * 60)

    # 从环境变量获取 MCP Server 路径
    import os
    from dotenv import load_dotenv
    load_dotenv()

    mcp_server_path = os.getenv("JADX_MCP_SERVER_PATH", "/path/to/jadx-mcp-server")

    if mcp_server_path == "/path/to/jadx-mcp-server":
        print("\n⚠️  请先配置 .env 文件中的 JADX_MCP_SERVER_PATH")
        print("   例如: JADX_MCP_SERVER_PATH=/home/user/jadx-mcp-server")
        return

    agent = create_apk_agent(mcp_server_path=mcp_server_path)

    print(f"\n✅ Agent 已创建: {agent.name}")

    # 执行分析
    response = agent.think(
        "请分析可疑应用 app.apk",
        context={"apk_path": "suspicious_app.apk"}
    )

    print(f"\n{agent.name}:\n")
    print(response.content[:500] + "...\n")

    # 显示元数据
    print("--- 分析元数据 ---")
    for key, value in response.metadata.items():
        if key != "error":
            print(f"{key}: {value}")


def main():
    """主函数"""
    print("\n🔍 Project 6: APK 恶意行为分析 Agent - 完整演示\n")
    print("特性:")
    print("  ✅ MCP 工具调用 - JADX 反编译")
    print("  ✅ 自定义规则加载 - 你的恶意特征")
    print("  ✅ 恶意软件知识库 - 已知模式")
    print("  ✅ 自我反思 - 分析完整性检查\n")

    # 演示 1: 规则加载器
    demo_rule_loader()

    # 演示 2: 知识库
    demo_knowledge_base()

    # 演示 3: 自我反思
    demo_reflection()

    # 演示 4: APK 分析
    demo_apk_analysis()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)

    print("\n📝 下一步:")
    print("  1. 将你的恶意特征规则放到 knowledge_base/raw/rules/")
    print("  2. 将 PDF 分析文档放到 knowledge_base/raw/analyses/")
    print("  3. 运行实际分析: python demo.py --apk your_app.apk")


if __name__ == "__main__":
    main()
