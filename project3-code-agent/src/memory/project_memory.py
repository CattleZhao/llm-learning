# src/memory/project_memory.py
"""
项目记忆模块 - 跨会话的项目级记忆，持久化到workspace/.agent_memory.json
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class ProjectMemory:
    """
    项目记忆管理器
    跨会话持久化存储项目相关信息
    """

    def __init__(self, workspace_dir: str = None, memory_file: str = ".agent_memory.json"):
        """
        初始化项目记忆

        Args:
            workspace_dir: 工作目录路径
            memory_file: 记忆文件名
        """
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir)
        else:
            # 默认使用当前目录下的workspace
            self.workspace_dir = Path(__file__).parent.parent.parent / "workspace"

        self.memory_file = self.workspace_dir / memory_file
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        self.data: Dict[str, Any] = {
            "project_info": {},
            "file_summaries": {},
            "analysis_history": [],
            "user_preferences": {},
            "learnings": [],
            "last_updated": None
        }

        self._load()

    def _load(self):
        """从文件加载记忆"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"加载项目记忆失败: {e}")

    def _save(self):
        """保存记忆到文件"""
        self.data["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存项目记忆失败: {e}")

    def set_project_info(self, key: str, value: Any):
        """
        设置项目信息

        Args:
            key: 信息键
            value: 信息值
        """
        self.data["project_info"][key] = value
        self._save()

    def get_project_info(self, key: str = None) -> Any:
        """
        获取项目信息

        Args:
            key: 信息键，None表示返回全部

        Returns:
            项目信息
        """
        if key:
            return self.data["project_info"].get(key)
        return self.data["project_info"]

    def save_file_summary(self, file_path: str, summary: Dict[str, Any]):
        """
        保存文件分析摘要

        Args:
            file_path: 文件路径
            summary: 分析摘要
        """
        self.data["file_summaries"][file_path] = {
            "summary": summary,
            "last_analyzed": datetime.now().isoformat()
        }
        self._save()

    def get_file_summary(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件分析摘要

        Args:
            file_path: 文件路径

        Returns:
            文件摘要，不存在返回None
        """
        return self.data["file_summaries"].get(file_path)

    def add_analysis_history(self, analysis_type: str, file_path: str, result: Dict[str, Any]):
        """
        添加分析历史记录

        Args:
            analysis_type: 分析类型
            file_path: 文件路径
            result: 分析结果
        """
        record = {
            "type": analysis_type,
            "file": file_path,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.data["analysis_history"].append(record)

        # 限制历史长度
        if len(self.data["analysis_history"]) > 100:
            self.data["analysis_history"] = self.data["analysis_history"][-100:]

        self._save()

    def get_analysis_history(self, file_path: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取分析历史

        Args:
            file_path: 文件路径过滤，None表示全部
            limit: 返回数量限制

        Returns:
            历史记录列表
        """
        history = self.data["analysis_history"]

        if file_path:
            history = [h for h in history if h["file"] == file_path]

        return history[-limit:]

    def set_user_preference(self, key: str, value: Any):
        """
        设置用户偏好

        Args:
            key: 偏好键
            value: 偏好值
        """
        self.data["user_preferences"][key] = value
        self._save()

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """
        获取用户偏好

        Args:
            key: 偏好键
            default: 默认值

        Returns:
            偏好值
        """
        return self.data["user_preferences"].get(key, default)

    def add_learning(self, topic: str, content: str):
        """
        添加学习笔记

        Args:
            topic: 主题
            content: 内容
        """
        learning = {
            "topic": topic,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.data["learnings"].append(learning)
        self._save()

    def get_learnings(self, topic: str = None) -> List[Dict[str, Any]]:
        """
        获取学习笔记

        Args:
            topic: 主题过滤，None表示全部

        Returns:
            学习笔记列表
        """
        if topic:
            return [l for l in self.data["learnings"] if l["topic"] == topic]
        return self.data["learnings"]

    def search_memory(self, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜索记忆中的关键词

        Args:
            keyword: 关键词

        Returns:
            搜索结果字典
        """
        results = {
            "file_summaries": [],
            "analysis_history": [],
            "learnings": []
        }

        keyword_lower = keyword.lower()

        # 搜索文件摘要
        for path, data in self.data["file_summaries"].items():
            if keyword_lower in path.lower() or keyword_lower in str(data).lower():
                results["file_summaries"].append({"path": path, "data": data})

        # 搜索分析历史
        for record in self.data["analysis_history"]:
            if keyword_lower in str(record).lower():
                results["analysis_history"].append(record)

        # 搜索学习笔记
        for learning in self.data["learnings"]:
            if keyword_lower in learning["topic"].lower() or keyword_lower in learning["content"].lower():
                results["learnings"].append(learning)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_files_analyzed": len(self.data["file_summaries"]),
            "total_analyses": len(self.data["analysis_history"]),
            "total_learnings": len(self.data["learnings"]),
            "last_updated": self.data["last_updated"],
            "memory_file": str(self.memory_file)
        }

    def clear(self):
        """清空项目记忆"""
        self.data = {
            "project_info": {},
            "file_summaries": {},
            "analysis_history": [],
            "user_preferences": {},
            "learnings": [],
            "last_updated": None
        }
        self._save()

    def export(self, filepath: str):
        """
        导出记忆到文件

        Args:
            filepath: 导出文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def import_data(self, filepath: str):
        """
        从文件导入记忆

        Args:
            filepath: 导入文件路径
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            imported = json.load(f)
            self.data.update(imported)
            self._save()
