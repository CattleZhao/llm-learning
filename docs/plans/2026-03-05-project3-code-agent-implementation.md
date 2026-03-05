# 项目3：代码助手Agent - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 构建一个能自主分析代码、生成测试、提供重构建议的智能Agent

**架构:** ReAct框架（推理+行动循环）+ 工具调用 + 记忆管理

**Tech Stack:** Python, LangChain Agent, Tree-of-Thoughts, AST解析, Git集成

---

## 前置准备

### Task 1: 环境设置

**Files:**
- Create: `project3-code-agent/requirements.txt`
- Create: `project3-code-agent/.env.example`
- Create: `project3-code-agent/README.md`
- Create: `project3-code-agent/src/__init__.py`

**Step 1: 创建项目目录**

```bash
cd /root/Learn/llm-learning
mkdir -p project3-code-agent/src
mkdir -p project3-code-agent/src/tools
mkdir -p project3-code-agent/src/agents
mkdir -p project3-code-agent/src/memory
mkdir -p project3-code-agent/workspace
mkdir -p project3-code-agent/tests
```

**Step 2: 创建 requirements.txt**

```txt
# LangChain核心
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
langchain-experimental>=0.0.40

# 代码分析
ast
black
pylint
pytest

# Git操作
gitpython>=3.1.0

# Web框架（可选）
streamlit>=1.31.0

# 其他
python-dotenv>=1.0.0
pytest>=7.4.0
```

**Step 3: 创建 .env.example**

```env
# LLM配置
OPENAI_API_KEY=your_openai_api_key_here

# Agent配置
DEFAULT_MODEL=gpt-4o
MAX_ITERATIONS=10
VERBOSE=true

# 代码分析配置
MAX_FILE_SIZE=10000
PYTHON_VERSION=3.10

# 工作目录
WORKSPACE_DIR=./workspace
```

**Step 4: 创建 README.md**

```markdown
# 项目3：代码助手Agent

> 基于ReAct框架的智能代码分析Agent

## 功能

- 🔍 代码结构分析
- 🧪 自动生成测试
- 💡 重构建议
- 📊 代码质量评估

## 技术栈

- LangChain Agent: 框架
- ReAct: 推理+行动循环
- AST: 代码解析
- Git: 版本控制集成

## 快速开始

```bash
pip install -r requirements.txt
python -m src.main
```

## 学习要点

- ReAct框架原理
- Tool设计和实现
- Agent记忆管理
- 多步推理规划
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat(project3): initialize code agent project structure"
```

---

## 模块1：工具集

### Task 2: 实现代码分析工具

**Files:**
- Create: `project3-code-agent/src/tools/code_analyzer.py`
- Create: `project3-code-agent/tests/test_code_analyzer.py`

**Step 1: 编写测试**

```python
# tests/test_code_analyzer.py
import pytest
from src.tools.code_analyzer import CodeAnalyzer

def test_analyze_function():
    """测试分析函数"""
    analyzer = CodeAnalyzer()
    code = """
def hello(name):
    return f"Hello, {name}!"
"""
    result = analyzer.analyze_functions(code)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "hello"

def test_count_lines():
    """测试统计代码行数"""
    analyzer = CodeAnalyzer()
    code = "line1\nline2\nline3"
    assert analyzer.count_lines(code) == 3
```

**Step 2: 实现代码分析工具**

```python
# src/tools/code_analyzer.py
import ast
from typing import List, Dict, Any
from langchain_core.tools import tool

class CodeAnalyzer:
    """代码分析工具"""

    @tool
    def analyze_functions(self, code: str) -> List[Dict[str, Any]]:
        """
        分析代码中的函数

        Args:
            code: Python代码字符串

        Returns:
            函数信息列表
        """
        try:
            tree = ast.parse(code)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "lineno": node.lineno,
                        "args_count": len(node.args.args),
                        "has_docstring": ast.get_docstring(node) is not None,
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d)
                                     for d in node.decorator_list]
                    }
                    functions.append(func_info)

            return functions
        except SyntaxError:
            return [{"error": "Invalid Python syntax"}]

    @tool
    def count_lines(self, code: str) -> Dict[str, int]:
        """
        统计代码行数

        Args:
            code: 代码字符串

        Returns:
            行数统计字典
        """
        lines = code.split('\n')
        return {
            "total": len(lines),
            "non_empty": len([l for l in lines if l.strip()]),
            "comment": len([l for l in lines if l.strip().startswith('#')])
        }

    @tool
    def get_imports(self, code: str) -> List[str]:
        """
        获取代码中的导入语句

        Args:
            code: Python代码字符串

        Returns:
            导入的模块列表
        """
        try:
            tree = ast.parse(code)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")

            return imports
        except SyntaxError:
            return []

    def get_tools(self):
        """获取所有工具"""
        return [
            self.analyze_functions,
            self.count_lines,
            self.get_imports
        ]
```

**Step 3: 运行测试**

```bash
cd project3-code-agent
pytest tests/test_code_analyzer.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project3): implement code analyzer tools"
```

---

### Task 3: 实现测试生成工具

**Files:**
- Create: `project3-code-agent/src/tools/test_generator.py`
- Create: `project3-code-agent/tests/test_test_generator.py`

**Step 1: 编写测试**

```python
# tests/test_test_generator.py
import pytest
from src.tools.test_generator import TestGenerator

def test_generate_test_case():
    """测试生成测试用例"""
    generator = TestGenerator()
    function_code = """
def add(a, b):
    return a + b
"""
    test = generator.generate_test(function_code, "add")

    assert "def test_add" in test
    assert "assert" in test

def test_generate_edge_cases():
    """测试生成边界情况"""
    generator = TestGenerator()
    function_code = "def divide(a, b): return a / b"
    tests = generator.generate_edge_cases(function_code, "divide")

    assert isinstance(tests, list)
```

**Step 2: 实现测试生成工具**

```python
# src/tools/test_generator.py
from typing import List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os

class TestGenerator:
    """测试生成工具"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    @tool
    def generate_test(self, function_code: str, function_name: str) -> str:
        """
        为函数生成测试用例

        Args:
            function_code: 函数代码
            function_name: 函数名

        Returns:
            生成的测试代码
        """
        prompt = f"""为以下Python函数生成完整的单元测试（使用pytest）：

```python
{function_code}
```

要求：
1. 函数名：test_{function_name}
2. 包含正常情况测试
3. 使用assert进行断言
4. 只返回测试代码，不要解释

测试代码："""

        return self.llm.invoke(prompt).content

    @tool
    def generate_edge_cases(self, function_code: str, function_name: str) -> List[str]:
        """
        生成边界测试场景

        Args:
            function_code: 函数代码
            function_name: 函数名

        Returns:
            边界场景描述列表
        """
        prompt = f"""分析以下函数，列出需要测试的边界情况：

```python
{function_code}
```

请返回一个JSON格式的边界场景列表，例如：
["空输入", "None值", "负数", "零值"]

边界场景："""

        response = self.llm.invoke(prompt).content
        # 简单解析，实际应该更robust
        return [s.strip() for s in response.split('\n') if s.strip()]

    @tool
    def check_test_coverage(self, test_code: str) -> dict:
        """
        评估测试覆盖率

        Args:
            test_code: 测试代码

        Returns:
            覆盖率评估
        """
        # 简单检查测试质量指标
        return {
            "has_assertions": "assert" in test_code,
            "test_count": test_code.count("def test_"),
            "has_edge_cases": any(keyword in test_code.lower()
                                for keyword in ["zero", "empty", "none", "negative"])
        }

    def get_tools(self):
        """获取所有工具"""
        return [
            self.generate_test,
            self.generate_edge_cases,
            self.check_test_coverage
        ]
```

**Step 3: 运行测试**

```bash
pytest tests/test_test_generator.py -v
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project3): implement test generation tools"
```

---

### Task 4: 实现代码重构工具

**Files:**
- Create: `project3-code-agent/src/tools/refactor_tools.py`
- Create: `project3-code-agent/tests/test_refactor_tools.py`

**Step 1: 编写测试**

```python
# tests/test_refactor_tools.py
import pytest
from src.tools.refactor_tools import RefactorTools

def test_suggest_refactoring():
    """测试重构建议"""
    tools = RefactorTools()
    code = """
def bad_name(x):
    return x*2
"""
    suggestions = tools.suggest_refactoring(code)

    assert isinstance(suggestions, list)
```

**Step 2: 实现重构工具**

```python
# src/tools/refactor_tools.py
from typing import List, Dict
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os

class RefactorTools:
    """代码重构工具"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    @tool
    def suggest_refactoring(self, code: str) -> List[Dict[str, str]]:
        """
        提供重构建议

        Args:
            code: 代码字符串

        Returns:
            建议列表
        """
        prompt = f"""分析以下代码并提供重构建议：

```python
{code}
```

请返回JSON格式的建议列表：
[
    {{"type": "命名", "issue": "变量名不清晰", "suggestion": "使用描述性名称"}},
    {{"type": "结构", "issue": "函数过长", "suggestion": "拆分成小函数"}}
]

重构建议："""

        response = self.llm.invoke(prompt).content
        # 简化处理，实际应更robust
        return [
            {
                "type": "general",
                "suggestion": response
            }
        ]

    @tool
    def apply_refactoring(self, code: str, description: str) -> str:
        """
        应用重构

        Args:
            code: 原始代码
            description: 重构描述

        Returns:
            重构后的代码
        """
        prompt = f"""根据以下描述重构代码：

原始代码：
```python
{code}
```

重构要求：{description}

只返回重构后的代码，不要解释。"""

        return self.llm.invoke(prompt).content

    @tool
    def check_code_smells(self, code: str) -> List[str]:
        """
        检测代码异味

        Args:
            code: 代码字符串

        Returns:
            检测到的问题列表
        """
        smells = []

        # 简单检查
        if "def " in code and len(code.split('\n')) > 50:
            smells.append("函数过长")

        if code.count("class ") > 3:
            smells.append("类数量过多")

        if "import *" in code:
            smells.append("使用了通配符导入")

        return smells

    def get_tools(self):
        """获取所有工具"""
        return [
            self.suggest_refactoring,
            self.apply_refactoring,
            self.check_code_smells
        ]
```

**Step 3: 运行测试并提交**

```bash
pytest tests/test_refactor_tools.py -v
git add .
git commit -m "feat(project3): implement refactoring tools"
```

---

### Task 5: 实现文件操作工具

**Files:**
- Create: `project3-code-agent/src/tools/file_tools.py`

**Step 1: 实现文件工具**

```python
# src/tools/file_tools.py
import os
from pathlib import Path
from typing import List, Optional
from langchain_core.tools import tool

class FileTools:
    """文件操作工具"""

    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    @tool
    def read_file(self, filepath: str) -> str:
        """
        读取文件内容

        Args:
            filepath: 相对于workspace的文件路径

        Returns:
            文件内容
        """
        full_path = self.workspace_dir / filepath
        if not full_path.exists():
            return f"Error: File not found: {filepath}"

        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    @tool
    def write_file(self, filepath: str, content: str) -> str:
        """
        写入文件

        Args:
            filepath: 相对于workspace的文件路径
            content: 文件内容

        Returns:
            确认消息
        """
        full_path = self.workspace_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote {filepath}"

    @tool
    def list_files(self, directory: str = "") -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 相对于workspace的目录路径

        Returns:
            文件列表
        """
        target_dir = self.workspace_dir / directory
        if not target_dir.exists():
            return []

        return [
            str(p.relative_to(self.workspace_dir))
            for p in target_dir.rglob("*")
            if p.is_file()
        ]

    @tool
    def search_files(self, pattern: str) -> List[str]:
        """
        搜索包含特定模式的文件

        Args:
            pattern: 搜索模式（简单字符串匹配）

        Returns:
            匹配的文件路径列表
        """
        matching_files = []

        for file_path in self.workspace_dir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding='utf-8')
                if pattern in content:
                    matching_files.append(str(file_path.relative_to(self.workspace_dir)))
            except Exception:
                continue

        return matching_files

    def get_tools(self):
        """获取所有工具"""
        return [
            self.read_file,
            self.write_file,
            self.list_files,
            self.search_files
        ]
```

**Step 2: 提交**

```bash
git add .
git commit -m "feat(project3): implement file operation tools"
```

---

## 模块2：Agent核心

### Task 6: 实现ReAct Agent

**Files:**
- Create: `project3-code-agent/src/agents/react_agent.py`
- Create: `project3-code-agent/tests/test_react_agent.py`

**Step 1: 编写测试**

```python
# tests/test_react_agent.py
import pytest
from src.agents.react_agent import CodeAssistantAgent

def test_agent_initialization():
    """测试Agent初始化"""
    agent = CodeAssistantAgent()
    assert agent is not None

def test_agent_simple_task():
    """测试Agent执行简单任务"""
    agent = CodeAssistantAgent()
    result = agent.run("分析workspace目录下的代码")
    assert result is not None
```

**Step 2: 实现ReAct Agent**

```python
# src/agents/react_agent.py
import os
from typing import List, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from src.tools.code_analyzer import CodeAnalyzer
from src.tools.test_generator import TestGenerator
from src.tools.refactor_tools import RefactorTools
from src.tools.file_tools import FileTools

# ReAct提示词模板
REACT_TEMPLATE = PromptTemplate.from_template(
    """你是一个专业的代码助手Agent。你可以使用以下工具帮助用户分析代码、生成测试和提供重构建议。

可用工具：
{tools}

工具名称：{tool_names}

请使用以下格式回复：

Question: 用户的问题
Thought: 我应该思考什么
Action: 要使用的工具名称
Action Input: 工具的输入
Observation: 工具的输出
... (可以重复Thought/Action/Action Input/Observation)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终回答

开始！

Question: {input}
Thought: {agent_scratchpad}"""
)

class CodeAssistantAgent:
    """代码助手Agent - 基于ReAct框架"""

    def __init__(
        self,
        model: str = "gpt-4o",
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        初始化Agent

        Args:
            model: 使用的模型
            max_iterations: 最大迭代次数
            verbose: 是否显示详细输出
        """
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose

        # 初始化LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # 初始化所有工具
        self.tools = self._initialize_tools()

        # 创建Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=REACT_TEMPLATE
        )

        # 创建执行器
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            max_iterations=max_iterations,
            handle_parsing_errors=True
        )

    def _initialize_tools(self) -> List[Any]:
        """初始化所有工具"""
        all_tools = []

        # 代码分析工具
        code_analyzer = CodeAnalyzer()
        all_tools.extend(code_analyzer.get_tools())

        # 测试生成工具
        test_generator = TestGenerator()
        all_tools.extend(test_generator.get_tools())

        # 重构工具
        refactor_tools = RefactorTools()
        all_tools.extend(refactor_tools.get_tools())

        # 文件工具
        file_tools = FileTools()
        all_tools.extend(file_tools.get_tools())

        return all_tools

    def run(self, query: str) -> str:
        """
        运行Agent

        Args:
            query: 用户查询

        Returns:
            Agent的最终回答
        """
        try:
            result = self.executor.invoke({"input": query})
            return result.get("output", "No output generated")
        except Exception as e:
            return f"Error: {str(e)}"

    def stream(self, query: str):
        """
        流式运行Agent（用于实时反馈）

        Args:
            query: 用户查询

        Yields:
            中间步骤
        """
        for step in self.executor.iter({"input": query}):
            yield step
```

**Step 3: 运行测试**

```bash
pytest tests/test_react_agent.py -v -s
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat(project3): implement ReAct code assistant agent"
```

---

## 模块3：记忆管理

### Task 7: 实现Agent记忆系统

**Files:**
- Create: `project3-code-agent/src/memory/conversation_memory.py`
- Create: `project3-code-agent/src/memory/project_memory.py`

**Step 1: 实现对话记忆**

```python
# src/memory/conversation_memory.py
from typing import List, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class ConversationMemory:
    """对话记忆管理"""

    def __init__(self, max_history: int = 10):
        """
        初始化对话记忆

        Args:
            max_history: 保存的最大历史记录数
        """
        self.max_history = max_history
        self.messages: List[BaseMessage] = []

    def add_message(self, message: BaseMessage):
        """添加消息"""
        self.messages.append(message)

        # 限制历史长度
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message(HumanMessage(content=content))

    def add_ai_message(self, content: str):
        """添加AI消息"""
        self.add_message(AIMessage(content=content))

    def get_history(self) -> List[BaseMessage]:
        """获取历史记录"""
        return self.messages.copy()

    def get_summary(self) -> str:
        """获取对话摘要"""
        if not self.messages:
            return "无对话历史"

        summary = []
        for msg in self.messages:
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            summary.append(f"{role}: {msg.content[:100]}...")

        return "\n".join(summary)

    def clear(self):
        """清空记忆"""
        self.messages = []
```

**Step 2: 实现项目记忆**

```python
# src/memory/project_memory.py
from typing import Dict, List, Any
from pathlib import Path
import json

class ProjectMemory:
    """项目级记忆 - 跨会话持久化"""

    def __init__(self, project_path: str = "./workspace"):
        """
        初始化项目记忆

        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
        self.memory_file = self.project_path / ".agent_memory.json"
        self.memory: Dict[str, Any] = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """加载记忆"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "files_analyzed": [],
            "suggestions_made": [],
            "user_preferences": {},
            "project_context": {}
        }

    def _save_memory(self):
        """保存记忆"""
        self.project_path.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def add_file_analyzed(self, filepath: str, summary: str):
        """记录分析的文件"""
        self.memory["files_analyzed"].append({
            "path": filepath,
            "summary": summary,
            "timestamp": self._get_timestamp()
        })
        self._save_memory()

    def add_suggestion(self, suggestion: str, applied: bool = False):
        """记录建议"""
        self.memory["suggestions_made"].append({
            "suggestion": suggestion,
            "applied": applied,
            "timestamp": self._get_timestamp()
        })
        self._save_memory()

    def set_preference(self, key: str, value: Any):
        """设置用户偏好"""
        self.memory["user_preferences"][key] = value
        self._save_memory()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self.memory["user_preferences"].get(key, default)

    def get_context(self) -> str:
        """获取项目上下文"""
        context_parts = []

        if self.memory["files_analyzed"]:
            context_parts.append(f"已分析 {len(self.memory['files_analyzed'])} 个文件")

        if self.memory["suggestions_made"]:
            applied = sum(1 for s in self.memory["suggestions_made"] if s["applied"])
            context_parts.append(f"已提供 {len(self.memory['suggestions_made'])} 条建议，{applied} 条已采纳")

        return "\n".join(context_parts) if context_parts else "新项目，暂无上下文"

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def clear(self):
        """清空记忆"""
        self.memory = {
            "files_analyzed": [],
            "suggestions_made": [],
            "user_preferences": {},
            "project_context": {}
        }
        self._save_memory()
```

**Step 3: 提交**

```bash
git add .
git commit -m "feat(project3): implement agent memory system"
```

---

## 模块4：主程序和界面

### Task 8: 实现命令行界面

**Files:**
- Create: `project3-code-agent/src/main.py`
- Create: `project3-code-agent/run.sh`

**Step 1: 创建主程序**

```python
# src/main.py
import os
import sys
from dotenv import load_dotenv

from src.agents.react_agent import CodeAssistantAgent
from src.memory.conversation_memory import ConversationMemory
from src.memory.project_memory import ProjectMemory

# 加载环境变量
load_dotenv()

def print_banner():
    """打印欢迎横幅"""
    print("""
╔═══════════════════════════════════════════════════════╗
║         🤖 代码助手Agent - Code Assistant            ║
║                                                       ║
║   分析代码 | 生成测试 | 重构建议                      ║
╚═══════════════════════════════════════════════════════╝
    """)

def print_menu():
    """打印菜单"""
    print("\n命令:")
    print("  /chat    - 与Agent对话")
    print("  /analyze - 分析代码文件")
    print("  /test    - 生成测试")
    print("  /refactor- 重构建议")
    print("  /history - 查看对话历史")
    print("  /context - 查看项目上下文")
    print("  /clear   - 清空对话历史")
    print("  /exit    - 退出")

def chat_mode(agent: CodeAssistantAgent, conv_memory: ConversationMemory):
    """对话模式"""
    print("\n--- 对话模式 (输入 /back 返回) ---")

    while True:
        query = input("\n你: ").strip()

        if query == "/back":
            break

        if not query:
            continue

        # 添加用户消息到记忆
        conv_memory.add_user_message(query)

        # 运行Agent
        print("\nAgent: ", end="", flush=True)
        response = agent.run(query)
        print(response)

        # 添加AI回复到记忆
        conv_memory.add_ai_message(response)

def analyze_mode(agent: CodeAssistantAgent):
    """分析模式"""
    print("\n--- 代码分析模式 ---")
    filepath = input("文件路径 (相对于workspace): ").strip()

    if not filepath:
        print("已取消")
        return

    query = f"请分析workspace/{filepath}的代码结构"
    response = agent.run(query)
    print(f"\n分析结果:\n{response}")

def test_mode(agent: CodeAssistantAgent):
    """测试生成模式"""
    print("\n--- 测试生成模式 ---")
    filepath = input("文件路径: ").strip()

    if not filepath:
        print("已取消")
        return

    query = f"为workspace/{filepath}中的函数生成完整的单元测试"
    response = agent.run(query)
    print(f"\n生成的测试:\n{response}")

def refactor_mode(agent: CodeAssistantAgent):
    """重构模式"""
    print("\n--- 重构建议模式 ---")
    filepath = input("文件路径: ").strip()

    if not filepath:
        print("已取消")
        return

    query = f"分析workspace/{filepath}并提供具体的重构建议"
    response = agent.run(query)
    print(f"\n重构建议:\n{response}")

def main():
    """主函数"""
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请在.env文件中配置OPENAI_API_KEY")
        sys.exit(1)

    print_banner()

    # 初始化组件
    print("初始化中...")
    agent = CodeAssistantAgent()
    conv_memory = ConversationMemory()
    proj_memory = ProjectMemory()
    print("✅ 初始化完成")

    print_menu()

    # 主循环
    while True:
        try:
            command = input("\n> ").strip()

            if not command:
                continue

            if command == "/exit":
                print("再见！")
                break

            elif command == "/chat":
                chat_mode(agent, conv_memory)

            elif command == "/analyze":
                analyze_mode(agent)

            elif command == "/test":
                test_mode(agent)

            elif command == "/refactor":
                refactor_mode(agent)

            elif command == "/history":
                print("\n--- 对话历史 ---")
                print(conv_memory.get_summary())

            elif command == "/context":
                print("\n--- 项目上下文 ---")
                print(proj_memory.get_context())

            elif command == "/clear":
                conv_memory.clear()
                print("对话历史已清空")

            elif command == "/help":
                print_menu()

            else:
                # 直接作为对话处理
                conv_memory.add_user_message(command)
                response = agent.run(command)
                print(f"\n{response}")
                conv_memory.add_ai_message(response)

        except KeyboardInterrupt:
            print("\n使用 /exit 退出")
        except Exception as e:
            print(f"\n错误: {e}")

if __name__ == "__main__":
    main()
```

**Step 2: 创建运行脚本**

```bash
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python -m src.main
EOF
chmod +x run.sh
```

**Step 3: 提交**

```bash
git add .
git commit -m "feat(project3): implement CLI interface"
```

---

### Task 9: 完善文档

**Files:**
- Modify: `project3-code-agent/README.md`

**Step 1: 更新README**

```markdown
# 项目3：代码助手Agent

> 基于ReAct框架的智能代码分析Agent

## 🎯 项目目标

掌握Agent开发的核心技术，让AI能够自主规划和执行多步骤代码分析任务。

## ✨ 功能特性

- 🔍 **代码分析**: 自动分析代码结构和复杂度
- 🧪 **测试生成**: 为函数自动生成单元测试
- 💡 **重构建议**: 提供代码改进建议
- 🧠 **记忆管理**: 跨会话的项目级记忆
- 🛠️ **工具调用**: 使用多种工具完成复杂任务

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ReAct Agent Loop                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Thought: 分析问题，规划步骤                     │   │
│  │  Action:   选择并执行工具                       │   │
│  │  Observation: 观察结果，决定下一步               │   │
│  │  Repeat until: 找到最终答案                     │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Analyzer│  │ Generator│  │ Refactor │
   │  Tools  │  │  Tools   │  │  Tools  │
   └─────────┘  └─────────┘  └─────────┘
        └────────────┼────────────┘
                     ▼
              ┌───────────────┐
              │  File Tools   │
              └───────────────┘
```

## 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Agent框架 | LangChain | ReAct Agent |
| LLM | OpenAI GPT-4o | 推理和生成 |
| 工具 | 自定义 | 代码分析、测试、重构 |
| 记忆 | 自定义 | 对话和项目记忆 |
| 代码解析 | AST | Python语法分析 |

## 📦 安装运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑.env，填入OPENAI_API_KEY

# 运行
./run.sh
# 或
python -m src.main
```

## 🎓 学习要点

### 1. ReAct框架
**Reasoning + Acting**: 让模型在行动前先思考

```
Question: 如何优化这段代码？
Thought 1: 我需要先分析代码结构
Action 1: analyze_functions(code)
Observation 1: 发现有3个函数，其中函数A过长
Thought 2: 我应该检查函数A的复杂度
Action 2: check_complexity(function_A)
...
Final Answer: 函数A有50行，建议拆分成3个子函数...
```

### 2. Tool设计原则
- **单一职责**: 每个工具只做一件事
- **明确输入输出**: 类型提示和文档字符串
- **错误处理**: 优雅处理失败情况
- **可组合性**: 工具可以组合使用

### 3. Agent调试技巧
- 使用 `verbose=True` 查看思考过程
- 限制 `max_iterations` 防止无限循环
- 分析中间步骤找出问题
- 测试每个工具单独工作正常

### 4. 记忆管理策略
- **短期记忆**: 当前会话的对话
- **长期记忆**: 跨会话的项目信息
- **总结压缩**: 长对话定期总结
- **选择性保留**: 只保存重要信息

## 📁 项目结构

```
project3-code-agent/
├── src/
│   ├── agents/
│   │   └── react_agent.py      # ReAct Agent
│   ├── tools/
│   │   ├── code_analyzer.py    # 代码分析工具
│   │   ├── test_generator.py   # 测试生成工具
│   │   ├── refactor_tools.py   # 重构工具
│   │   └── file_tools.py       # 文件操作工具
│   ├── memory/
│   │   ├── conversation_memory.py  # 对话记忆
│   │   └── project_memory.py      # 项目记忆
│   └── main.py                 # CLI入口
├── workspace/                  # 工作目录
├── tests/
├── requirements.txt
└── README.md
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 测试特定模块
pytest tests/test_react_agent.py -v -s
```

## 🚀 使用示例

```
> /chat
你: 帮我分析workspace/utils.py的代码
Agent: 我来分析这个文件...
[使用analyze_functions工具]
[使用count_lines工具]
分析完成：该文件包含5个函数，共120行代码...

> /test
文件路径: workspace/utils.py
Agent: 正在为函数生成测试...
[使用generate_test工具]
[使用write_file工具]
测试已生成到workspace/test_utils.py
```

## 🔮 进阶方向

- 添加更多代码质量检查工具
- 支持多文件批量分析
- 集成Git diff分析
- 添加代码可视化
- 支持其他编程语言

## 📝 参考资料

- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Agent Design Patterns](https://python.langchain.com/docs/modules/agents/agent_types/)
```

**Step 2: 最终提交**

```bash
git add .
git commit -m "docs(project3): complete documentation"
git push origin master
```

---

## 项目3完成检查清单

- [ ] 工具集完整（分析、测试、重构、文件）
- [ ] ReAct Agent正常工作
- [ ] 记忆系统正常
- [ ] CLI界面可用
- [ ] 所有测试通过
- [ ] 文档完善
- [ ] 代码已推送到GitHub

---

## 🎉 全部项目完成！

恭喜你完成了三个递进式项目：

1. ✅ **基础API应用** - 理解大模型调用
2. ✅ **RAG系统** - 掌握检索增强生成
3. ✅ **代码Agent** - 实现智能自主Agent

你现在拥有：
- 3个完整的可展示项目
- 扎实的大模型应用开发技能
- 清晰的代码和文档

准备好开始你的AI工程师转型之旅了！🚀
