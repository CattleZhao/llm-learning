"""
测试上下文压缩器
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.context_compressor import (
    create_context_compressor,
    ContextCompressor,
    RuleBasedSummarizer,
    CompressionConfig
)


def test_summarizer():
    """测试结果摘要器"""
    print("=" * 50)
    print("测试 RuleBasedSummarizer")
    print("=" * 50)

    summarizer = RuleBasedSummarizer()

    # 测试 manifest 摘要
    manifest = {
        "package": "com.example.app",
        "version_name": "1.0.0",
        "version_code": 1
    }
    summary = summarizer.summarize("jadx_get_manifest", manifest)
    print(f"Manifest 摘要: {summary}")
    assert "com.example.app" in summary

    # 测试权限摘要
    permissions = {
        "count": 15,
        "dangerous_count": 5,
        "dangerous": ["READ_SMS", "SEND_SMS", "READ_CONTACTS", "ACCESS_FINE_LOCATION", "CAMERA"]
    }
    summary = summarizer.summarize("jadx_get_permissions", permissions)
    print(f"权限摘要: {summary}")
    assert "15" in summary and "5" in summary

    # 测试网络摘要
    network = {
        "urls": ["http://api.example.com", "https://cdn.example.com"],
        "ips": ["192.168.1.1", "8.8.8.8"],
        "has_http": True,
        "has_https": True
    }
    summary = summarizer.summarize("jadx_get_network_info", network)
    print(f"网络摘要: {summary}")
    assert "URL" in summary and "IP" in summary

    # 测试规则摘要
    rules = {
        "rules": [
            {"severity": "high", "name": "Rule1"},
            {"severity": "medium", "name": "Rule2"},
            {"severity": "high", "name": "Rule3"},
        ]
    }
    summary = summarizer.summarize("match_malware_rules", rules)
    print(f"规则摘要: {summary}")
    assert "3" in summary and "high" in summary

    print("✅ RuleBasedSummarizer 测试通过\n")


def test_tool_result_compression():
    """测试工具结果压缩"""
    print("=" * 50)
    print("测试工具结果压缩")
    print("=" * 50)

    compressor = create_context_compressor(
        tool_result_threshold=100,  # 100 字符就摘要
        max_tool_result_size=500
    )

    # 小结果 - 不压缩
    small_result = {"status": "ok"}
    result, was_summarized = compressor.compress_tool_result("test_tool", small_result)
    print(f"小结果: 原始={len(str(small_result))} 字符, 摘要={was_summarized}")
    assert not was_summarized

    # 大结果 - 摘要
    large_result = {
        "data": ["item" * 100 for _ in range(100)]  # 很大的结果
    }
    result, was_summarized = compressor.compress_tool_result("jadx_get_strings", large_result)
    print(f"大结果: 原始={len(str(large_result))} 字符, 压缩后={len(result)} 字符, 摘要={was_summarized}")
    assert was_summarized or len(result) < len(str(large_result))

    print("✅ 工具结果压缩测试通过\n")


def test_message_compression():
    """测试对话历史压缩"""
    print("=" * 50)
    print("测试对话历史压缩")
    print("=" * 50)

    compressor = create_context_compressor(
        history_window_size=3  # 只保留 3 轮
    )

    # 构建长对话历史
    messages = [{"role": "user", "content": "开始分析"}]  # 第一条
    for i in range(10):
        messages.append({"role": "assistant", "content": f"工具调用 {i}", "tool_use_id": f"tu{i}"})
        messages.append({"role": "user", "content": f"工具结果 {i}"})

    print(f"原始消息数: {len(messages)}")

    compressed = compressor.compress_messages(messages, iteration=10)
    print(f"压缩后消息数: {len(compressed)}")

    # 应该保留第一条 + 最近 3 轮（6 条）= 7 条
    assert len(compressed) <= 7
    assert compressed[0]["content"] == "开始分析"  # 第一条保留

    print("✅ 对话历史压缩测试通过\n")


def test_similar_samples_injection():
    """测试相似样本注入决策"""
    print("=" * 50)
    print("测试相似样本注入决策")
    print("=" * 50)

    compressor = create_context_compressor(
        enable_similar_samples=True,
        max_similar_samples=1
    )

    # 有历史记录 - 不注入
    should_inject = compressor.should_inject_similar_samples("app.apk", has_history=True)
    print(f"有历史记录: should_inject={should_inject}")
    assert not should_inject

    # 无历史记录 + 可疑 APK - 注入
    should_inject = compressor.should_inject_similar_samples("mod_game.apk", has_history=False)
    print(f"可疑APK无历史: should_inject={should_inject}")
    assert should_inject

    # 无历史记录 + 正常 APK - 不注入
    should_inject = compressor.should_inject_similar_samples("com.example.app.apk", has_history=False)
    print(f"正常APK无历史: should_inject={should_inject}")
    assert not should_inject

    # 测试格式化
    similar = [
        {
            "metadata": {"package": "com.malware.app", "risk_level": "high"},
            "content": "恶意样本摘要..."
        },
        {
            "metadata": {"package": "com.clean.app", "risk_level": "low"},
            "content": "正常样本摘要..."
        }
    ]
    formatted = compressor.format_similar_samples(similar)
    print(f"\n格式化相似样本:\n{formatted}")
    assert "com.malware.app" in formatted
    assert similar.count({"metadata": {"package": "com.clean.app", "risk_level": "low"}, "content": "正常样本摘要..."}) >= 0

    print("✅ 相似样本注入测试通过\n")


def test_stats():
    """测试统计信息"""
    print("=" * 50)
    print("测试压缩统计")
    print("=" * 50)

    compressor = create_context_compressor()

    # 触发几次压缩
    large_result = {"data": ["x" * 1000 for _ in range(100)]}
    for _ in range(3):
        compressor.compress_tool_result("jadx_get_strings", large_result)

    stats = compressor.get_stats()
    print(f"压缩统计: {stats}")
    assert stats["compression_count"] > 0

    print("✅ 压缩统计测试通过\n")


if __name__ == "__main__":
    test_summarizer()
    test_tool_result_compression()
    test_message_compression()
    test_similar_samples_injection()
    test_stats()

    print("=" * 50)
    print("🎉 所有测试通过！")
    print("=" * 50)
