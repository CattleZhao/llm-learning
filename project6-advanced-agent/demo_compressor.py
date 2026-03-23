"""
上下文压缩效果演示

展示压缩器如何减少 token 消耗
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.context_compressor import create_context_compressor


def demo_tool_result_compression():
    """演示工具结果压缩效果"""
    print("=" * 60)
    print("📊 工具结果压缩效果演示")
    print("=" * 60)

    compressor = create_context_compressor(
        tool_result_threshold=2000,
        max_tool_result_size=10000
    )

    # 模拟各种工具结果
    test_cases = [
        {
            "name": "jadx_get_manifest (小结果)",
            "result": {
                "package": "com.example.game",
                "version_name": "2.5.1",
                "version_code": 251,
                "min_sdk": 21,
                "target_sdk": 33
            }
        },
        {
            "name": "jadx_get_permissions (中等结果)",
            "result": {
                "count": 28,
                "normal": ["INTERNET", "ACCESS_NETWORK_STATE"],
                "dangerous": [
                    "READ_SMS", "SEND_SMS", "READ_CONTACTS",
                    "ACCESS_FINE_LOCATION", "CAMERA", "RECORD_AUDIO",
                    "READ_PHONE_STATE", "READ_CALL_LOG"
                ],
                "dangerous_count": 8
            }
        },
        {
            "name": "jadx_get_strings (超大结果)",
            "result": {
                "count": 15420,
                "strings": [f"http://server-{i}.example.com/api" * 10 for i in range(500)]
            }
        },
        {
            "name": "jadx_get_network_info",
            "result": {
                "urls": [
                    "http://api.example.com/v1",
                    "https://cdn.example.com/static",
                    "http://192.168.1.100:8080"
                ],
                "ips": ["192.168.1.100", "8.8.8.8", "1.1.1.1"],
                "has_http": True,
                "has_https": True
            }
        },
        {
            "name": "match_malware_rules",
            "result": {
                "rules": [
                    {"severity": "critical", "name": "SMS 发送恶意代码", "category": "privacy"},
                    {"severity": "high", "name": "硬编码敏感密钥", "category": "crypto"},
                    {"severity": "high", "name": "可疑 C2 通信", "category": "network"},
                    {"severity": "medium", "name": "混淆代码检测", "category": "obfuscation"},
                ]
            }
        }
    ]

    print(f"\n{'工具名称':<30} {'原始大小':>12} {'压缩后':>12} {'压缩率':>10} {'方式':<8}")
    print("-" * 80)

    total_original = 0
    total_compressed = 0

    for case in test_cases:
        tool_name = case["name"]
        result = case["result"]

        compressed, was_summarized = compressor.compress_tool_result(tool_name, result)

        original_size = len(str(result))
        compressed_size = len(compressed)
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        method = "摘要" if was_summarized else ("截断" if compressed_size < original_size else "保留")

        print(f"{tool_name:<30} {original_size:>10,} B  {compressed_size:>10,} B  {ratio:>9.1f}%  {method:<8}")

        total_original += original_size
        total_compressed += compressed_size

    print("-" * 80)
    print(f"{'总计':<30} {total_original:>10,} B  {total_compressed:>10,} B  {(1 - total_compressed / total_original) * 100:>9.1f}%")
    print()

    # 计算节省的 token (假设 1 token ≈ 4 字符)
    tokens_saved = (total_original - total_compressed) // 4
    print(f"💰 预计节省 token: ~{tokens_saved:,} tokens")
    print()


def demo_message_compression():
    """演示对话历史压缩效果"""
    print("=" * 60)
    print("📊 对话历史压缩效果演示")
    print("=" * 60)

    compressor = create_context_compressor(history_window_size=5)

    # 构建模拟对话历史
    messages = [{"role": "user", "content": "分析 app.apk"}]

    for i in range(15):
        # Assistant 工具调用
        messages.append({
            "role": "assistant",
            "content": [{"type": "tool_use", "name": f"tool_{i}", "input": {}}]
        })
        # 工具结果 (假设每个 2000 字符)
        messages.append({
            "role": "user",
            "content": [{"type": "tool_result", "content": "x" * 2000}]
        })

    original_count = len(messages)
    original_chars = sum(len(str(m)) for m in messages)

    compressed = compressor.compress_messages(messages, iteration=15)
    compressed_count = len(compressed)
    compressed_chars = sum(len(str(m)) for m in compressed)

    print(f"原始对话: {original_count} 条消息, ~{original_chars:,} 字符")
    print(f"压缩对话: {compressed_count} 条消息, ~{compressed_chars:,} 字符")
    print(f"压缩率: {(1 - compressed_count / original_count) * 100:.1f}% (消息数)")
    print(f"压缩率: {(1 - compressed_chars / original_chars) * 100:.1f}% (字符数)")
    print()

    # 计算节省的 token
    tokens_saved = (original_chars - compressed_chars) // 4
    print(f"💰 预计节省 token: ~{tokens_saved:,} tokens")
    print()


def demo_similar_samples():
    """演示相似样本注入策略"""
    print("=" * 60)
    print("📊 相似样本注入策略演示")
    print("=" * 60)

    compressor = create_context_compressor(
        enable_similar_samples=True,
        max_similar_samples=1
    )

    test_cases = [
        ("com.example.clean.app.apk", False, "正常APK + 无历史 → 不注入"),
        ("mod_game_premium.apk", False, "可疑APK + 无历史 → 注入"),
        ("hack_tool_v2.apk", True, "可疑APK + 有历史 → 不注入"),
        ("cracked_pro.apk", False, "可疑APK + 无历史 → 注入"),
    ]

    for apk_name, has_history, expected in test_cases:
        should = compressor.should_inject_similar_samples(apk_name, has_history)
        status = "✅" if should else "❌"
        print(f"{status} {apk_name:<30} | 有历史: {has_history:<5} | 注入: {should:<5} | {expected}")

    print()


if __name__ == "__main__":
    demo_tool_result_compression()
    demo_message_compression()
    demo_similar_samples()

    print("=" * 60)
    print("🎉 压缩器演示完成！")
    print("=" * 60)
    print()
    print("📝 配置建议:")
    print("  - history_window_size: 3-5 轮 (根据任务复杂度)")
    print("  - tool_result_threshold: 1000-3000 字符")
    print("  - max_similar_samples: 0-1 个 (避免注入过多)")
