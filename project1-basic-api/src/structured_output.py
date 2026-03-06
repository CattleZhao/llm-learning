# src/structured_output.py
import json
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Any
from .llm_client import get_client

class StructuredExtractor:
    """结构化信息提取模块"""

    def __init__(self, provider: str = "openai"):
        """
        初始化结构化提取模块

        Args:
            provider: LLM提供商 (openai | anthropic | glm | zhipu)
        """
        self.client = get_client(provider)

    def extract_person_info(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取人物信息

        Args:
            text: 包含人物信息的文本

        Returns:
            包含姓名、性别、年龄、职业等信息的字典
        """
        prompt = self._build_extraction_prompt(text)
        response = self.client.generate(
            prompt,
            temperature=0.3  # 低温度提高结构化输出稳定性
        )
        return self._parse_json_response(response)

    def _build_extraction_prompt(self, text: str) -> str:
        """
        构建信息提取提示词

        Args:
            text: 待提取的文本

        Returns:
            完整的提示词
        """
        return f"""从以下文本中提取人物信息，输出为JSON格式：

文本：{text}

请提取以下信息（如果文本中不存在则填null）：
- name: 姓名
- gender: 性别
- age: 年龄
- occupation: 职业
- location: 居住地

只输出JSON，不要其他内容："""

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        解析JSON响应

        Args:
            response: LLM返回的响应文本

        Returns:
            解析后的字典
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            # 如果还是失败，返回一个部分解析的结果
            return {
                "raw_response": response,
                "error": "Failed to parse as JSON"
            }
