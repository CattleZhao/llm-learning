"""
磁盘缓存管理器

将完整的工具结果保存到磁盘，供后续追溯使用。
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ToolResultCache:
    """
    工具结果磁盘缓存

    将完整的工具结果保存到磁盘，使用占位符在对话中引用。
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径，默认为 memory/tool_cache/
        """
        if cache_dir is None:
            # 默认缓存目录
            project_root = Path(__file__).parent.parent
            cache_dir = project_root / "memory" / "tool_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话的缓存索引
        self._session_index: Dict[str, Dict[str, Any]] = {}

        logger.info(f"[ToolResultCache] 缓存目录: {self.cache_dir}")

    def store(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储工具结果到磁盘

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            tool_result: 工具执行结果（完整数据）
            metadata: 额外元数据

        Returns:
            cache_id: 缓存 ID，用于后续检索
        """
        cache_id = str(uuid.uuid4())[:8]  # 短 ID
        timestamp = datetime.now().isoformat()

        # 准备缓存数据
        cache_data = {
            "cache_id": cache_id,
            "tool_name": tool_name,
            "timestamp": timestamp,
            "input": self._sanitize_for_json(tool_input),
            "result": self._sanitize_for_json(tool_result),
            "metadata": metadata or {}
        }

        # 保存到磁盘
        cache_file = self.cache_dir / f"{cache_id}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            # 记录到会话索引
            self._session_index[cache_id] = {
                "tool_name": tool_name,
                "timestamp": timestamp,
                "file": str(cache_file)
            }

            logger.debug(f"[ToolResultCache] 已缓存: {tool_name} -> {cache_id}")
            return cache_id

        except Exception as e:
            logger.error(f"[ToolResultCache] 缓存失败: {e}")
            # 即使缓存失败也返回 ID，保持流程继续
            return cache_id

    def load(self, cache_id: str) -> Optional[Dict[str, Any]]:
        """
        从磁盘加载缓存结果

        Args:
            cache_id: 缓存 ID

        Returns:
            缓存数据，如果不存在返回 None
        """
        cache_file = self.cache_dir / f"{cache_id}.json"

        if not cache_file.exists():
            logger.warning(f"[ToolResultCache] 缓存不存在: {cache_id}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"[ToolResultCache] 加载失败: {e}")
            return None

    def create_placeholder(
        self,
        cache_id: str,
        tool_name: str,
        summary: str
    ) -> str:
        """
        创建占位符文本

        这个占位符会被发送给 LLM，告诉它之前执行过什么操作。

        Args:
            cache_id: 缓存 ID
            tool_name: 工具名称
            summary: 结果摘要

        Returns:
            占位符文本
        """
        return f"[{tool_name}] 已完成，结果摘要: {summary} (完整数据见缓存: {cache_id})"

    def get_session_index(self) -> Dict[str, Dict[str, Any]]:
        """获取当前会话的缓存索引"""
        return self._session_index.copy()

    def clear_session(self):
        """清空会话索引（不删除磁盘文件）"""
        self._session_index.clear()

    def cleanup_old_cache(self, max_age_hours: int = 24):
        """
        清理旧缓存文件

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                # 读取时间戳
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    timestamp_str = data.get("timestamp", "")

                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp < cutoff_time:
                        cache_file.unlink()
                        deleted_count += 1
            except Exception as e:
                logger.warning(f"[ToolResultCache] 清理文件失败: {cache_file}, {e}")

        if deleted_count > 0:
            logger.info(f"[ToolResultCache] 清理了 {deleted_count} 个旧缓存文件")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_dir": str(self.cache_dir),
            "cache_count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "session_entries": len(self._session_index)
        }

    def _sanitize_for_json(self, data: Any) -> Any:
        """
        清理数据使其可 JSON 序列化

        Args:
            data: 原始数据

        Returns:
            可序列化的数据
        """
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, dict):
            return {k: self._sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_for_json(item) for item in data]
        else:
            # 其他类型转为字符串
            return str(data)


# ============================================================
# 便捷函数
# ============================================================

_default_cache: Optional[ToolResultCache] = None


def get_tool_cache() -> ToolResultCache:
    """获取默认缓存实例（单例）"""
    global _default_cache
    if _default_cache is None:
        _default_cache = ToolResultCache()
    return _default_cache


def create_tool_cache(cache_dir: Optional[Path] = None) -> ToolResultCache:
    """
    创建工具缓存实例

    Args:
        cache_dir: 缓存目录路径

    Returns:
        ToolResultCache 实例
    """
    return ToolResultCache(cache_dir=cache_dir)
