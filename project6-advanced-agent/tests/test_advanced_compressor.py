"""
测试高级上下文压缩器
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.advanced_compressor import (
    create_advanced_compressor,
    AdvancedContextCompressor,
    AdvancedCompressionConfig,
    MessageCompressor
)
from agents.cache_manager import ToolResultCache


def test_message_compressor_placeholders():
    """测试消息占位符压缩"""
    print("=" * 60)
    print("测试消息占位符压缩")
    print("=" * 60)

    # 创建临时缓存
    temp_dir = tempfile.mkdtemp()
    try:
        cache = ToolResultCache(cache_dir=Path(temp_dir))
        compressor = MessageCompressor(cache)

        # 构建长对话历史
        messages = [{"role": "user", "content": "分析 app.apk"}]

        # 添加 10 轮工具调用
        for i in range(10):
            messages.append({
                "role": "assistant",
                "content": [{"type": "tool_use", "name": f"tool_{i % 3 + 1}", "id": f"tu_{i}"}]
            })
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "content": f"result {i}"}]
            })

        print(f"原始消息数: {len(messages)}")

        # 压缩（窗口大小 3）
        compressed = compressor.compress_with_placeholders(messages, window_size=3)
        print(f"压缩后消息数: {len(compressed)}")

        # 验证结构
        print("\n压缩后的消息结构:")
        for i, msg in enumerate(compressed):
            role = msg.get("role")
            content = msg.get("content", "")
            if isinstance(content, str):
                content_preview = content[:100].replace("\n", " ")
            else:
                content_preview = f"[{len(content)} items]"
            print(f"  {i+1}. [{role}] {content_preview}")

        # 应该包含占位符
        placeholder_found = any(
            msg.get("role") == "system" and "上下文压缩" in msg.get("content", "")
            for msg in compressed
        )
        print(f"\n包含占位符: {placeholder_found}")

        assert len(compressed) < len(messages), "应该减少消息数量"
        assert placeholder_found, "应该包含占位符消息"

        print("✅ 消息占位符压缩测试通过\n")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_disk_cache():
    """测试磁盘缓存功能"""
    print("=" * 60)
    print("测试磁盘缓存")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    try:
        cache = ToolResultCache(cache_dir=Path(temp_dir))

        # 存储工具结果
        tool_name = "jadx_get_strings"
        tool_input = {"limit": 100}
        tool_result = {"strings": [f"string_{i}" for i in range(1000)], "count": 1000}

        cache_id = cache.store(tool_name, tool_input, tool_result)
        print(f"存储工具结果，缓存 ID: {cache_id}")

        # 验证文件存在
        cache_file = Path(temp_dir) / f"{cache_id}.json"
        assert cache_file.exists(), "缓存文件应该存在"
        print(f"缓存文件大小: {cache_file.stat().st_size} bytes")

        # 加载缓存
        loaded = cache.load(cache_id)
        assert loaded is not None, "应该能加载缓存"
        assert loaded["tool_name"] == tool_name
        assert loaded["result"]["count"] == 1000
        print(f"加载成功: {loaded['tool_name']}")

        # 创建占位符
        summary = "找到 1000 个字符串"
        placeholder = cache.create_placeholder(cache_id, tool_name, summary)
        print(f"\n占位符文本:\n{placeholder}")

        assert cache_id in placeholder, "占位符应包含缓存 ID"

        # 获取统计
        stats = cache.get_cache_stats()
        print(f"\n缓存统计: {stats}")

        print("✅ 磁盘缓存测试通过\n")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_advanced_compressor():
    """测试高级压缩器"""
    print("=" * 60)
    print("测试高级压缩器")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    try:
        # 创建高级压缩器
        compressor = create_advanced_compressor(
            history_window_size=3,
            use_llm_summarizer=False,  # 使用规则摘要（不需要 API）
            enable_disk_cache=True,
            use_placeholders=True,
            cache_dir=temp_dir
        )

        # 测试工具结果压缩
        tool_name = "jadx_get_strings"
        tool_input = {"apk_path": "/path/to/app.apk"}
        tool_result = {
            "strings": [f"http://server-{i}.example.com" * 10 for i in range(100)],
            "count": 10000
        }

        result_str, cache_id = compressor.compress_tool_result(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result
        )

        print(f"原始大小: {len(str(tool_result))} 字符")
        print(f"压缩后: {len(result_str)} 字符")
        print(f"缓存 ID: {cache_id}")

        assert cache_id is not None, "应该返回缓存 ID"
        assert len(result_str) < len(str(tool_result)), "应该压缩结果"

        # 测试加载缓存
        loaded = compressor.load_cached_result(cache_id)
        assert loaded is not None, "应该能加载缓存"
        assert loaded["result"]["count"] == 10000

        # 获取统计
        stats = compressor.get_stats()
        print(f"\n压缩器统计: {stats}")

        print("✅ 高级压缩器测试通过\n")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_config_options():
    """测试配置选项"""
    print("=" * 60)
    print("测试配置选项")
    print("=" * 60)

    # 测试不同配置
    configs = [
        {
            "name": "最小配置（全部禁用）",
            "config": AdvancedCompressionConfig(
                use_llm_summarizer=False,
                enable_disk_cache=False,
                use_placeholders=False
            )
        },
        {
            "name": "仅磁盘缓存",
            "config": AdvancedCompressionConfig(
                use_llm_summarizer=False,
                enable_disk_cache=True,
                use_placeholders=False
            )
        },
        {
            "name": "全功能",
            "config": AdvancedCompressionConfig(
                use_llm_summarizer=True,
                enable_disk_cache=True,
                use_placeholders=True
            )
        }
    ]

    for cfg in configs:
        print(f"\n{cfg['name']}:")
        compressor = AdvancedContextCompressor(cfg["config"])
        stats = compressor.get_stats()
        print(f"  配置: LLM={cfg['config'].use_llm_summarizer}, "
              f"缓存={cfg['config'].enable_disk_cache}, "
              f"占位符={cfg['config'].use_placeholders}")
        print(f"  初始统计: {stats}")

    print("\n✅ 配置选项测试通过\n")


if __name__ == "__main__":
    test_message_compressor_placeholders()
    test_disk_cache()
    test_advanced_compressor()
    test_config_options()

    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
