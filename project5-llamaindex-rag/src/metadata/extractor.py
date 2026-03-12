"""
元数据提取器

从文档中提取和增强元数据
"""
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DocumentMetadata:
    """文档元数据"""

    # 文档基本信息
    file_name: str
    file_path: str
    file_type: str
    file_size: int

    # 内容信息
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: list = field(default_factory=list)

    # 时间信息
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    year: Optional[int] = None

    # 内容统计
    word_count: int = 0
    char_count: int = 0

    # 自定义元数据
    custom: Dict[str, Any] = field(default_factory=dict)


class MetadataExtractor:
    """
    元数据提取器

    从 Markdown 文档中提取元数据，包括：
    - YAML frontmatter
    - 文件系统信息
    - 内容统计信息
    """

    # 常见的标题模式
    TITLE_PATTERNS = [
        r'^#\s+(.+)$',           # Markdown H1
        r'^title:\s*(.+)$',      # YAML frontmatter
        r'^Title:\s*(.+)$',      # 其他格式
    ]

    # 常见的作者模式
    AUTHOR_PATTERNS = [
        r'^author:\s*(.+)$',
        r'^Author:\s*(.+)$',
        r'^作者[:：]\s*(.+)$',
    ]

    # 常见的分类模式
    CATEGORY_PATTERNS = [
        r'^category:\s*(.+)$',
        r'^Category:\s*(.+)$',
        r'^分类[:：]\s*(.+)$',
    ]

    # 标签模式
    TAG_PATTERNS = [
        r'^tags:\s*\[(.+)\]$',           # YAML array
        r'^tags:\s*(.+)$',               # YAML string
        r'^tag:\s*(.+)$',
        r'^标签[:：]\s*(.+)$',
    ]

    def extract_from_file(self, file_path: str) -> DocumentMetadata:
        """
        从文件中提取元数据

        Args:
            file_path: 文件路径

        Returns:
            DocumentMetadata 对象
        """
        path = Path(file_path)

        # 基本文件信息
        metadata = DocumentMetadata(
            file_name=path.name,
            file_path=str(path.absolute()),
            file_type=path.suffix.lstrip('.'),
            file_size=path.stat().st_size,
        )

        # 读取文件内容
        try:
            content = path.read_text(encoding='utf-8')
            self._extract_from_content(content, metadata)
            self._add_filesystem_metadata(path, metadata)
        except Exception as e:
            print(f"[Warning] 无法读取文件 {file_path}: {e}")

        return metadata

    def _extract_from_content(self, content: str, metadata: DocumentMetadata):
        """从内容中提取元数据"""
        lines = content.split('\n')

        # 检查 YAML frontmatter
        if content.startswith('---'):
            self._extract_yaml_frontmatter(content, metadata)

        # 提取标题
        if not metadata.title:
            metadata.title = self._extract_title(content)

        # 提取作者
        if not metadata.author:
            metadata.author = self._extract_author(content)

        # 提取分类
        if not metadata.category:
            metadata.category = self._extract_category(content)

        # 提取标签
        if not metadata.tags:
            metadata.tags = self._extract_tags(content)

        # 内容统计
        metadata.word_count = len(re.findall(r'\w+', content))
        metadata.char_count = len(content)

    def _extract_yaml_frontmatter(self, content: str, metadata: DocumentMetadata):
        """提取 YAML frontmatter"""
        # 找到 YAML 块
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return

        yaml_content = match.group(1)
        try:
            yaml_data = yaml.safe_load(yaml_content)
            if not isinstance(yaml_data, dict):
                return

            # 提取常见字段
            if 'title' in yaml_data:
                metadata.title = yaml_data['title']
            if 'author' in yaml_data:
                metadata.author = yaml_data['author']
            if 'category' in yaml_data:
                metadata.category = yaml_data['category']
            if 'tags' in yaml_data:
                metadata.tags = yaml_data['tags'] if isinstance(yaml_data['tags'], list) else [yaml_data['tags']]
            if 'date' in yaml_data:
                metadata.created_date = str(yaml_data['date'])
                try:
                    metadata.year = datetime.fromisoformat(str(yaml_data['date'])).year
                except:
                    pass

            # 保存其他自定义元数据
            for key, value in yaml_data.items():
                if key not in ['title', 'author', 'category', 'tags', 'date']:
                    metadata.custom[key] = value

        except yaml.YAMLError as e:
            print(f"[Warning] YAML 解析失败: {e}")

    def _extract_title(self, content: str) -> Optional[str]:
        """提取标题"""
        for pattern in self.TITLE_PATTERNS:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_author(self, content: str) -> Optional[str]:
        """提取作者"""
        for pattern in self.AUTHOR_PATTERNS:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_category(self, content: str) -> Optional[str]:
        """提取分类"""
        for pattern in self.CATEGORY_PATTERNS:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_tags(self, content: str) -> list:
        """提取标签"""
        for pattern in self.TAG_PATTERNS:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                tags_str = match.group(1)
                # 处理不同的标签格式
                if '[' in tags_str:
                    # YAML array 格式: [tag1, tag2]
                    tags = [t.strip().strip('"\'') for t in tags_str.strip('[]').split(',')]
                else:
                    # 逗号分隔: tag1, tag2
                    tags = [t.strip() for t in tags_str.split(',')]
                return [t for t in tags if t]
        return []

    def _add_filesystem_metadata(self, path: Path, metadata: DocumentMetadata):
        """添加文件系统元数据"""
        stat = path.stat()

        # 修改时间
        modified_timestamp = stat.st_mtime
        metadata.modified_date = datetime.fromtimestamp(modified_timestamp).isoformat()

        # 创建时间
        try:
            created_timestamp = stat.st_ctime
            metadata.created_date = datetime.fromtimestamp(created_timestamp).isoformat()
            if not metadata.year:
                metadata.year = datetime.fromtimestamp(created_timestamp).year
        except:
            pass

    def extract_from_directory(self, directory: str) -> Dict[str, DocumentMetadata]:
        """
        从目录中所有文件提取元数据

        Args:
            directory: 目录路径

        Returns:
            字典，key 为文件路径，value 为 DocumentMetadata
        """
        path = Path(directory)
        metadata_map = {}

        for file_path in path.rglob('*.md'):
            try:
                metadata = self.extract_from_file(str(file_path))
                metadata_map[str(file_path)] = metadata
            except Exception as e:
                print(f"[Warning] 无法提取 {file_path} 的元数据: {e}")

        return metadata_map
