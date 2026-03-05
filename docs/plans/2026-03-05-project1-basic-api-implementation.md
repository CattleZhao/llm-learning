# 项目1：大模型基础API应用 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 构建一个命令行工具，掌握大模型API调用和Prompt Engineering基础

**架构:** 使用Python调用大模型API（OpenAI/Claude/国产模型），实现问答、摘要、结构化输出三个功能

**Tech Stack:** Python 3.10+, OpenAI SDK/Anthropic SDK, python-dotenv

---

## 前置准备

### Task 1: 环境设置

**Files:**
- Create: `project1-basic-api/.env.example`
- Create: `project1-basic-api/requirements.txt`
- Create: `project1-basic-api/README.md`

**Step 1: 创建项目目录结构**

```bash
cd /root/Learn/llm-learning
mkdir -p project1-basic-api/src
mkdir -p project1-basic-api/tests
```

**Step 2: 创建 requirements.txt**

```txt
# 项目1依赖
openai>=1.0.0
anthropic>=0.18.0
python-dotenv>=1.0.0
pytest>=7.4.0
```

**Step 3: 创建 .env.example**

```env
# 大模型API配置
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 模型选择（可选，默认使用OpenAI）
LLM_PROVIDER=openai  # openai | anthropic

# 参数配置
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2000
```

**Step 4: 创建 README.md**

```markdown
# 项目1：大模型基础API应用

学习大模型API调用和Prompt Engineering的基础项目。

## 功能

- 基础问答：简单Q&A对话
- 文档摘要：长文本摘要生成
- 结构化输出：JSON格式数据提取

## 安装

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入你的API密钥
```

## 使用

```bash
python src/main.py
```
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat(project1): initialize project structure and dependencies"
```

---

## 功能模块1：基础问答

### Task 2: 实现LLM客户端基类

**Files:**
- Create: `project1-basic-api/src/llm_client.py`
- Create: `project1-basic-api/tests/test_llm_client.py`

**Step 1: 编写测试**

```python
# tests/test_llm_client.py
import pytest
from src.llm_client import OpenAIClient

def test_openai_client_init():
    """测试OpenAI客户端初始化"""
    client = OpenAIClient(api_key="test_key")
    assert client.client is not None

def test_openai_client_generate_requires_api_key():
    """测试没有API密钥时生成失败"""
    client = OpenAIClient(api_key="invalid_key")
    with pytest.raises(Exception):
        client.generate(prompt="test")
```

**Step 2: 运行测试确认失败**

```bash
cd project1-basic-api
pytest tests/test_llm_client.py -v
```

预期：`ModuleNotFoundError: No module named 'src'` 或类似错误

**Step 3: 实现LLM客户端**

```python
# src/llm_client.py
import os
from typing import Optional
from openai import OpenAI
from anthropic import Anthropic

class LLMClientBase:
    """LLM客户端基类"""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

class OpenAIClient(LLMClientBase):
    """OpenAI客户端"""
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """生成文本"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

class AnthropicClient(LLMClientBase):
    """Anthropic客户端"""
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """生成文本"""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")

def get_client(provider: str = "openai") -> LLMClientBase:
    """工厂函数：获取LLM客户端"""
    providers = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient
    }
    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")
    return providers[provider]()
```

**Step 4: 安装依赖并运行测试**

```bash
pip install -r requirements.txt
pytest tests/test_llm_client.py -v
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat(project1): implement LLM client base class"
```

---

### Task 3: 实现问答功能

**Files:**
- Create: `project1-basic-api/src/qa_module.py`
- Create: `project1-basic-api/tests/test_qa_module.py`

**Step 1: 编写测试**

```python
# tests/test_qa_module.py
import pytest
from src.qa_module import QAModule

def test_qa_module_answer_question():
    """测试问答功能"""
    qa = QAModule()
    answer = qa.ask("什么是人工智能？")
    assert isinstance(answer, str)
    assert len(answer) > 0

def test_qa_module_with_context():
    """测试带上下文的问答"""
    qa = QAModule()
    context = "Python是一种高级编程语言。"
    answer = qa.ask("Python是什么？", context=context)
    assert "Python" in answer or "编程" in answer
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/test_qa_module.py -v
```

**Step 3: 实现问答模块**

```python
# src/qa_module.py
from typing import Optional
from .llm_client import get_client

class QAModule:
    """问答模块"""

    def __init__(self, provider: str = "openai"):
        self.client = get_client(provider)

    def ask(self, question: str, context: Optional[str] = None) -> str:
        """
        回答问题

        Args:
            question: 用户问题
            context: 可选的上下文信息

        Returns:
            答案文本
        """
        prompt = self._build_prompt(question, context)
        return self.client.generate(prompt)

    def _build_prompt(self, question: str, context: Optional[str]) -> str:
        """构建提示词"""
        if context:
            return f"""基于以下信息回答问题：

上下文：
{context}

问题：{question}

请仅基于上下文信息回答，如果上下文没有相关信息，请说明。"""
        else:
            return f"""请回答以下问题：

{question}

请提供准确、简洁的答案。"""
```

**Step 4: 运行测试**

```bash
pytest tests/test_qa_module.py -v
```

注意：需要有效的API密钥才能通过

**Step 5: 提交**

```bash
git add .
git commit -m "feat(project1): implement Q&A module"
```

---

## 功能模块2：文档摘要

### Task 4: 实现摘要功能

**Files:**
- Create: `project1-basic-api/src/summary_module.py`
- Create: `project1-basic-api/tests/test_summary_module.py`

**Step 1: 编写测试**

```python
# tests/test_summary_module.py
import pytest
from src.summary_module import SummaryModule

def test_summary_short_text():
    """测试短文本摘要"""
    summary = SummaryModule()
    text = "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
    result = summary.summarize(text)
    assert isinstance(result, str)
    assert len(result) > 0

def test_summary_with_max_length():
    """测试指定最大长度"""
    summary = SummaryModule()
    text = "这是一段测试文本。" * 50  # 长文本
    result = summary.summarize(text, max_length=50)
    assert len(result) <= 100  # 允许一些误差
```

**Step 2: 实现摘要模块**

```python
# src/summary_module.py
from typing import Optional
from .llm_client import get_client

class SummaryModule:
    """文档摘要模块"""

    def __init__(self, provider: str = "openai"):
        self.client = get_client(provider)

    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """
        生成文本摘要

        Args:
            text: 待摘要的文本
            max_length: 摘要最大长度（字符数）

        Returns:
            摘要文本
        """
        prompt = self._build_prompt(text, max_length)
        return self.client.generate(prompt, temperature=0.5)

    def _build_prompt(self, text: str, max_length: Optional[int]) -> str:
        """构建提示词"""
        length_constraint = ""
        if max_length:
            length_constraint = f"摘要长度不超过{max_length}字。"

        return f"""请对以下文本生成简洁的摘要：

{text}

要求：
1. 准确概括原文要点
2. 保持简洁明了
3. {length_constraint}

摘要："""
```

**Step 3: 运行测试**

```bash
pytest tests/test_summary_module.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project1): implement text summarization module"
```

---

## 功能模块3：结构化输出

### Task 5: 实现结构化输出功能

**Files:**
- Create: `project1-basic-api/src/structured_output.py`
- Create: `project1-basic-api/tests/test_structured_output.py`

**Step 1: 编写测试**

```python
# tests/test_structured_output.py
import json
import pytest
from src.structured_output import StructuredExtractor

def test_extract_person_info():
    """测试提取人物信息"""
    extractor = StructuredExtractor()
    text = "张三，男，30岁，是一名软件工程师，居住在北京。"
    result = extractor.extract_person_info(text)
    assert isinstance(result, dict)
    assert "name" in result

def test_extract_with_json_output():
    """测试JSON格式输出"""
    extractor = StructuredExtractor()
    result = extractor.extract_person_info("李四是一名教师")
    # 验证是有效的JSON
    json.loads(json.dumps(result))
```

**Step 2: 实现结构化输出模块**

```python
# src/structured_output.py
import json
from typing import Dict, Any
from .llm_client import get_client

class StructuredExtractor:
    """结构化信息提取模块"""

    def __init__(self, provider: str = "openai"):
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
        """构建信息提取提示词"""
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
        """解析JSON响应"""
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
            raise ValueError(f"Failed to parse JSON from response: {response}")
```

**Step 3: 运行测试**

```bash
pytest tests/test_structured_output.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project1): implement structured output module"
```

---

## 主程序和CLI

### Task 6: 实现命令行界面

**Files:**
- Create: `project1-basic-api/src/main.py`
- Create: `project1-basic-api/tests/test_main.py`

**Step 1: 编写测试**

```python
# tests/test_main.py
from unittest.mock import patch
import pytest

def test_main_menu_exists():
    """测试主菜单函数存在"""
    from src.main import main
    assert callable(main)

def test_qa_command():
    """测试问答命令"""
    # 这个测试需要mock输入
    pass
```

**Step 2: 实现主程序**

```python
# src/main.py
import os
import sys
from dotenv import load_dotenv

from .qa_module import QAModule
from .summary_module import SummaryModule
from .structured_output import StructuredExtractor

# 加载环境变量
load_dotenv()

def print_menu():
    """打印菜单"""
    print("\n" + "="*50)
    print("大模型基础API应用")
    print("="*50)
    print("1. 问答 (Q&A)")
    print("2. 文档摘要")
    print("3. 结构化输出")
    print("4. 退出")
    print("="*50)

def qa_mode():
    """问答模式"""
    print("\n--- 问答模式 ---")
    question = input("请输入问题（或输入'back'返回）: ")
    if question.lower() == 'back':
        return

    context = input("是否有上下文信息？(直接跳过) : ") or None

    qa = QAModule()
    answer = qa.ask(question, context)
    print(f"\n答案: {answer}\n")

def summary_mode():
    """摘要模式"""
    print("\n--- 文档摘要模式 ---")
    print("请输入要摘要的文本（输入'END'结束输入）:")

    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)

    text = '\n'.join(lines)
    if not text.strip():
        print("未输入内容")
        return

    max_length = input("最大摘要长度（可选，直接跳过）: ") or None
    if max_length:
        max_length = int(max_length)

    summary = SummaryModule()
    result = summary.summarize(text, max_length)
    print(f"\n摘要: {result}\n")

def structured_mode():
    """结构化输出模式"""
    print("\n--- 结构化输出模式 ---")
    print("请输入包含人物信息的文本:")

    text = input("> ")
    if not text.strip():
        print("未输入内容")
        return

    extractor = StructuredExtractor()
    result = extractor.extract_person_info(text)
    print(f"\n提取结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    print()

def main():
    """主函数"""
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("错误: 请在.env文件中配置API密钥")
        print("复制 .env.example 到 .env 并填入你的密钥")
        sys.exit(1)

    while True:
        print_menu()
        choice = input("请选择功能 (1-4): ").strip()

        if choice == '1':
            qa_mode()
        elif choice == '2':
            summary_mode()
        elif choice == '3':
            structured_mode()
        elif choice == '4':
            print("再见！")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()
```

**Step 3: 运行测试**

```bash
pytest tests/test_main.py -v
```

**Step 4: 手动测试**

```bash
cd project1-basic-api
python -m src.main
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat(project1): implement CLI interface"
```

---

## 项目收尾

### Task 7: 完善文档和配置

**Files:**
- Create: `project1-basic-api/src/__init__.py`
- Modify: `project1-basic-api/README.md`

**Step 1: 创建 __init__.py**

```python
# src/__init__.py
"""大模型基础API应用包"""

__version__ = "0.1.0"
```

**Step 2: 更新README**

```markdown
# 项目1：大模型基础API应用

> 学习大模型API调用和Prompt Engineering的基础项目

## 功能

- **问答 (Q&A)**: 简单Q&A对话，支持上下文
- **文档摘要**: 长文本摘要生成，可指定长度
- **结构化输出**: 从文本中提取结构化信息（JSON格式）

## 技术要点

- ✅ LLM API调用（OpenAI/Claude）
- ✅ Prompt Engineering基础
- ✅ 温度和Token参数控制
- ✅ 结构化输出处理

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑.env文件，填入你的API密钥
```

## 使用

```bash
python -m src.main
```

## 测试

```bash
pytest tests/ -v
```

## 学习笔记

### Prompt技巧
- 角色设定：明确告诉AI它的角色
- 示例引导：提供示例帮助理解
- 思维链：引导AI逐步推理
- 长度控制：明确指定输出长度

### 参数影响
- temperature: 0=确定性输出，1=更随机
- max_tokens: 控制输出长度
- 模型选择: gpt-4o-mini（便宜快速）vs gpt-4o（更智能）
```

**Step 3: 最终提交**

```bash
git add .
git commit -m "docs(project1): complete documentation"

# 推送到GitHub
git push origin master
```

---

## 项目1完成检查清单

- [ ] 环境配置完成（依赖安装、API密钥配置）
- [ ] 问答功能正常工作
- [ ] 摘要功能正常工作
- [ ] 结构化输出功能正常工作
- [ ] 所有测试通过
- [ ] 文档完善
- [ ] 代码已推送到GitHub

**下一步**: 开始项目2 - RAG知识库问答系统
