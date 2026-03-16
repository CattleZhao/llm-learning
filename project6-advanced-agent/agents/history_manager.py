"""
APK 分析历史记录管理器

负责保存和加载 APK 分析的历史记录
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HistoryManager:
    """APK 分析历史记录管理"""

    def __init__(self, history_dir: Optional[Path] = None):
        """
        初始化历史记录管理器

        Args:
            history_dir: 历史记录存储目录，默认为 memory/apk_history
        """
        if history_dir is None:
            # 默认使用项目根目录下的 memory/apk_history
            history_dir = Path(__file__).parent.parent / "memory" / "apk_history"

        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"历史记录目录: {self.history_dir}")

    def calculate_apk_hash(self, apk_path: str) -> str:
        """
        计算 APK 文件的 SHA256 hash

        Args:
            apk_path: APK 文件路径

        Returns:
            SHA256 hash 字符串
        """
        sha256_hash = hashlib.sha256()
        with open(apk_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_history_path(self, apk_hash: str) -> Path:
        """获取历史记录文件路径"""
        return self.history_dir / f"{apk_hash}.json"

    def load(self, apk_hash: str) -> Optional[Dict[str, Any]]:
        """
        加载历史分析记录

        Args:
            apk_hash: APK 文件的 hash

        Returns:
            历史记录数据，如果不存在则返回 None
        """
        history_path = self._get_history_path(apk_hash)
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"成功加载历史记录: {history_path.name}")
                    return data
            except Exception as e:
                logger.warning(f"加载历史记录失败: {e}")
        return None

    def save(
        self,
        apk_hash: str,
        apk_path: str,
        analysis: Dict[str, Any],
        report: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Dict[str, Any]
    ):
        """
        保存分析记录到历史

        Args:
            apk_hash: APK 文件的 hash
            apk_path: APK 文件路径
            analysis: 分析结果数据
            report: 分析报告文本
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
            metadata: 其他元数据
        """
        history_path = self._get_history_path(apk_hash)
        history_data = {
            "apk_hash": apk_hash,
            "apk_path": apk_path,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "report": report,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "metadata": metadata
        }

        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            logger.info(f"历史记录已保存: {history_path}")
        except Exception as e:
            logger.warning(f"保存历史记录失败: {e}")

    def clear_history(self, apk_hash: Optional[str] = None):
        """
        清除历史记录

        Args:
            apk_hash: 要清除的 APK hash，如果为 None 则清除所有历史
        """
        if apk_hash:
            history_path = self._get_history_path(apk_hash)
            if history_path.exists():
                history_path.unlink()
                logger.info(f"已清除历史记录: {history_path.name}")
        else:
            # 清除所有历史记录
            for history_file in self.history_dir.glob("*.json"):
                history_file.unlink()
            logger.info("已清除所有历史记录")

    def list_history(self) -> List[Dict[str, Any]]:
        """
        列出所有历史记录

        Returns:
            历史记录列表
        """
        history_list = []
        for history_file in self.history_dir.glob("*.json"):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history_list.append({
                        "apk_hash": data.get("apk_hash"),
                        "apk_path": data.get("apk_path"),
                        "timestamp": data.get("timestamp"),
                        "tokens": data.get("input_tokens", 0) + data.get("output_tokens", 0)
                    })
            except Exception as e:
                logger.warning(f"读取历史记录失败 {history_file.name}: {e}")
        return sorted(history_list, key=lambda x: x["timestamp"], reverse=True)
