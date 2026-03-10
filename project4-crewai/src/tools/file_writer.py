"""
文件写入工具

用于将代码写入文件系统。
"""
from pathlib import Path
from src.core.config import get_config


def write_file(file_path: str, content: str) -> dict:
    """
    将内容写入文件

    Args:
        file_path: 文件路径（可以是相对路径）
        content: 文件内容

    Returns:
        包含操作结果的字典
    """
    config = get_config()

    # 如果是相对路径，使用工作目录
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(config.work_dir) / path

    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    path.write_text(content, encoding='utf-8')

    return {
        "success": True,
        "file_path": str(path),
        "size": len(content)
    }


class FileWriterTool:
    """CrewAI 兼容的文件写入工具"""

    def __init__(self):
        self.name = "write_file"
        self.description = "将代码或文本内容写入文件。输入: file_path (文件路径), content (文件内容)"

    def get_schema(self) -> dict:
        """返回工具的 schema 定义"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要写入的文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                }
            },
            "required": ["file_path", "content"]
        }

    def run(self, file_path: str, content: str) -> str:
        """
        执行文件写入

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            操作结果描述
        """
        result = write_file(file_path, content)
        return f"文件已写入: {result['file_path']} ({result['size']} 字节)"
