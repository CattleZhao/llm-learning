"""
文档导入模块

从历史分析文档（PDF、TXT、MD）中提取结构化信息
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

from config import get_settings

logger = logging.getLogger(__name__)


class DocumentImporter:
    """历史文档导入器"""

    def __init__(self, vector_store=None):
        """
        初始化导入器

        Args:
            vector_store: VectorStore 实例，可选
        """
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.vector_store = vector_store

    def import_pdf(
        self,
        pdf_path: str,
        extract_structured: bool = True
    ) -> Dict[str, Any]:
        """
        导入 PDF 文档

        Args:
            pdf_path: PDF 文件路径
            extract_structured: 是否提取结构化信息

        Returns:
            导入结果
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # 提取文本
        text = self._extract_text_from_pdf(pdf_path)

        if extract_structured:
            # 使用 LLM 提取结构化信息
            structured_data = self._extract_with_llm(text)
        else:
            structured_data = {
                "raw_text": text,
                "summary": text[:500]
            }

        structured_data["source_file"] = pdf_path.name

        # 如果有 vector_store，存储进去
        if self.vector_store:
            self._store_imported_data(structured_data)

        logger.info(f"Imported PDF: {pdf_path.name}")
        return structured_data

    def import_text_file(
        self,
        file_path: str,
        extract_structured: bool = True
    ) -> Dict[str, Any]:
        """
        导入文本文件（TXT、MD）

        Args:
            file_path: 文件路径
            extract_structured: 是否提取结构化信息

        Returns:
            导入结果
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = file_path.read_text(encoding="utf-8")

        if extract_structured:
            structured_data = self._extract_with_llm(text)
        else:
            structured_data = {
                "raw_text": text,
                "summary": text[:500]
            }

        structured_data["source_file"] = file_path.name

        if self.vector_store:
            self._store_imported_data(structured_data)

        logger.info(f"Imported text file: {file_path.name}")
        return structured_data

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """从 PDF 提取文本"""
        try:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception as e:
            raise ImportError(f"Failed to parse PDF: {e}")

    def _extract_with_llm(
        self,
        text: str,
        use_mock: bool = False
    ) -> Dict[str, Any]:
        """
        使用 LLM 提取结构化信息

        Args:
            text: 原始文本
            use_mock: 是否使用 mock 模式（测试用）

        Returns:
            结构化数据
        """
        if use_mock:
            return self._mock_extract(text)

        prompt = f"""
请从以下恶意软件分析报告中提取结构化信息。

报告内容：
{text[:4000]}

请提取（如果有的话）：
- package: APK 包名
- malware_family: 恶意软件家族名称
- risk_level: 风险等级 (LOW/MEDIUM/HIGH/CRITICAL)
- ioc: 威胁指标列表，包含 domains, ips, urls
- behaviors: 恶意行为描述列表
- permissions: 相关权限列表
- summary: 简短摘要（100字以内）

以 JSON 格式返回，找不到的字段填 null。
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            content = response.content[0].text

            # 尝试解析 JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取 JSON 块
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("Could not extract JSON from LLM response")

            # 确保 summary 存在
            if not result.get("summary"):
                result["summary"] = text[:200]

            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # 降级：返回基本结构
            return {
                "package": None,
                "malware_family": None,
                "risk_level": "MEDIUM",
                "ioc": {"domains": [], "ips": [], "urls": []},
                "behaviors": [],
                "permissions": [],
                "summary": text[:200],
                "raw_text": text
            }

    def _mock_extract(self, text: str) -> Dict[str, Any]:
        """Mock 提取（测试用）"""
        return {
            "package": "com.malware.trojan",
            "malware_family": "TrojanAgent",
            "risk_level": "CRITICAL",
            "ioc": {
                "domains": ["malware.c2-server.com"],
                "ips": ["192.168.1.100"],
                "urls": []
            },
            "behaviors": ["发送 premium 短信", "窃取通讯录", "远程控制"],
            "permissions": ["SEND_SMS", "READ_CONTACTS", "ACCESS_FINE_LOCATION"],
            "summary": "该木马具有典型的短信盗窃行为，会后台发送 premium 短信并删除发送记录。"
        }

    def _store_imported_data(self, data: Dict[str, Any]):
        """将导入的数据存储到向量库"""
        if not self.vector_store:
            return

        from agents.base import AgentResponse

        # 生成文档 ID（使用文件名）
        doc_id = f"imported_{data.get('source_file', 'unknown')}"

        response = AgentResponse(
            content=data.get("summary", ""),
            metadata=data
        )

        self.vector_store.store_analysis(
            apk_hash=doc_id,
            analysis_result=response
        )

    def import_batch(
        self,
        directory: str,
        pattern: str = "*.pdf"
    ) -> List[Dict[str, Any]]:
        """
        批量导入目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            导入结果列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = list(dir_path.glob(pattern))
        results = []

        for file_path in files:
            try:
                if file_path.suffix.lower() == ".pdf":
                    result = self.import_pdf(str(file_path))
                else:
                    result = self.import_text_file(str(file_path))
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to import {file_path.name}: {e}")
                results.append({
                    "source_file": file_path.name,
                    "error": str(e)
                })

        logger.info(f"Batch import complete: {len(results)} files processed")
        return results
