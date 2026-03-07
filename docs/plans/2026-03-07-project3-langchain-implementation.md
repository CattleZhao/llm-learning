# Project3: LangChain 版本实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 创建 LangChain 版本的代码助手 Agent，用于与自研 ReAct 版本对比学习

**架构:**
- 新建 `project3-code-agent-langchain/` 项目
- Agent 用 LangChain 实现，其他组件（embeddings、vector_store、memory 等）从原项目复制
- 使用 LangChain 的 `create_react_agent` 和 `AgentExecutor` 替代自研 ReAct 循环
- 用 `@tool` 装饰器包装工具函数

**技术栈:**
- LangChain 0.1+ (Agent、Tool、OpenAI 集成)
- LangChain OpenAI 0.0.5+
- Python 3.13+
- AST (代码解析)

---

## Task 1: 创建项目目录结构

**Files:**
- Create: `project3-code-agent-langchain/`
- Create: `project3-code-agent-langchain/src/`
- Create: `project3-code-agent-langchain/src/agents/`
- Create: `project3-code-agent-langchain/src/tools/`
- Create: `project3-code-agent-langchain/src/memory/`
- Create: `project3-code-agent-langchain/examples/`
- Create: `project3-code-agent-langchain/tests/`
- Create: `project3-code-agent-langchain/data/`

**Step 1: 创建项目根目录**

```bash
cd /root/Learn/llm-learning
mkdir -p project3-code-agent-langchain
cd project3-code-agent-langchain
```

**Step 2: 创建所有子目录**

```bash
mkdir -p src/agents src/tools src/memory examples tests data
mkdir -p examples/workspace
```

**Step 3: 验证目录结构**

```bash
tree -L 2
```

Expected output:
```
.
├── data/
├── examples/
│   └── workspace/
├── src/
│   ├── agents/
│   ├── tools/
│   └── memory/
└── tests/
```

**Step 4: 创建初始 __init__.py 文件**

```bash
touch src/__init__.py
touch src/agents/__init__.py
touch src/tools/__init__.py
touch src/memory/__init__.py
touch tests/__init__.py
```

**Step 5: 初始化 Git 仓库**

```bash
git init
git add .
git commit -m "feat: initialize project structure"
```

---

## Task 2: 创建 requirements.txt 和配置文件

**Files:**
- Create: `project3-code-agent-langchain/requirements.txt`
- Create: `project3-code-agent-langchain/.env.example`
- Create: `project3-code-agent-langchain/.gitignore`

**Step 1: 创建 requirements.txt**

```bash
cat > requirements.txt << 'EOF'
# LangChain core
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.20

# OpenAI SDK for LLM API calls
openai>=1.0.0

# Environment variable management
python-dotenv>=1.0.0

# Numerical computing
numpy>=1.0.0

# Testing framework
pytest>=7.0.0
EOF
```

**Step 2: 创建 .env.example**

```bash
cat > .env.example << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Optional: Use custom API endpoint
# OPENAI_API_BASE=https://api.openai.com/v1
EOF
```

**Step 3: 创建 .gitignore**

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
data/
*.db
*.log

# Test coverage
.coverage
htmlcov/
.pytest_cache/
EOF
```

**Step 4: 提交**

```bash
git add requirements.txt .env.example .gitignore
git commit -m "feat: add dependencies and configuration"
```

---

## Task 3: 复制共享组件 - embeddings.py

**Files:**
- Create: `project3-code-agent-langchain/src/embeddings.py`
- Reference: `project3-code-agent/src/embeddings.py`

**Step 1: 复制 embeddings.py**

```bash
cp /root/Learn/llm-learning/project3-code-agent/src/embeddings.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/embeddings.py
```

**Step 2: 验证文件存在**

```bash
cat src/embeddings.py | head -20
```

Expected output should contain:
```python
# src/embeddings.py
import hashlib
import numpy as np
from typing import List

class EmbeddingModel:
    """文本嵌入模型 - 简化版实现"""
    ...
```

**Step 3: 运行简单测试**

```bash
python3 -c "
from src.embeddings import EmbeddingModel
model = EmbeddingModel()
result = model.embed_query('test')
print(f'Vector dimension: {len(result)}')
print(f'First 3 values: {result[:3]}')
"
```

Expected: Vector dimension: 384

**Step 4: 提交**

```bash
git add src/embeddings.py
git commit -m "feat: add embedding model"
```

---

## Task 4: 复制共享组件 - vector_store.py

**Files:**
- Create: `project3-code-agent-langchain/src/vector_store.py`
- Reference: `project3-code-agent/src/vector_store.py`

**Step 1: 复制 vector_store.py**

```bash
cp /root/Learn/llm-learning/project3-code-agent/src/vector_store.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/vector_store.py
```

**Step 2: 验证文件存在**

```bash
cat src/vector_store.py | head -20
```

**Step 3: 运行简单测试**

```bash
python3 -c "
from src.vector_store import VectorStore
from src.embeddings import EmbeddingModel
from src.document_loader import Document

vs = VectorStore(collection_name='test')
doc = Document(page_content='test content', metadata={'source': 'test'})
vs.add_documents([doc], EmbeddingModel())
print(f'Document count: {vs.count()}')
vs.clear()
"
```

**Step 4: 提交**

```bash
git add src/vector_store.py
git commit -m "feat: add vector store"
```

---

## Task 5: 复制共享组件 - document_loader.py

**Files:**
- Create: `project3-code-agent-langchain/src/document_loader.py`
- Reference: `project3-code-agent/src/document_loader.py`

**Step 1: 复制 document_loader.py**

```bash
cp /root/Learn/llm-learning/project3-code-agent/src/document_loader.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/document_loader.py
```

**Step 2: 验证并测试**

```bash
python3 -c "
from src.document_loader import DocumentLoader
loader = DocumentLoader()
print(f'Supported formats: {loader.SUPPORTED_FORMATS}')
"
```

Expected: `Supported formats: {'.txt': 'text', '.md': 'markdown'}`

**Step 3: 提交**

```bash
git add src/document_loader.py
git add src/embeddings.py  # 修正：需要包含依赖
git commit -m "feat: add document loader"
```

---

## Task 6: 复制共享组件 - memory 模块

**Files:**
- Create: `project3-code-agent-langchain/src/memory/conversation_memory.py`
- Create: `project3-code-agent-langchain/src/memory/project_memory.py`
- Reference: `project3-code-agent/src/memory/`

**Step 1: 复制 memory 文件**

```bash
cp /root/Learn/llm-learning/project3-code-agent/src/memory/conversation_memory.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/memory/conversation_memory.py

cp /root/Learn/llm-learning/project3-code-agent/src/memory/project_memory.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/memory/project_memory.py
```

**Step 2: 测试 conversation_memory**

```bash
python3 -c "
from src.memory.conversation_memory import ConversationMemory
mem = ConversationMemory()
mem.add_user_message('hello')
mem.add_assistant_message('hi there')
messages = mem.get_messages()
print(f'Message count: {len(messages)}')
"
```

**Step 3: 提交**

```bash
git add src/memory/
git commit -m "feat: add memory modules"
```

---

## Task 7: 复制工具 - code_analyzer.py

**Files:**
- Create: `project3-code-agent-langchain/src/tools/code_analyzer.py`
- Reference: `project3-code-agent/src/tools/code_analyzer.py`

**Step 1: 复制 code_analyzer.py**

```bash
cp /root/Learn/llm-learning/project3-code-agent/src/tools/code_analyzer.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/tools/code_analyzer.py
```

**Step 2: 测试基本功能**

```bash
# 创建测试文件
echo 'def test_func(): pass' > /tmp/test_code.py

python3 -c "
from src.tools.code_analyzer import CodeAnalyzer
analyzer = CodeAnalyzer(file_path='/tmp/test_code.py')
funcs = analyzer.analyze_functions()
print(f'Functions found: {len(funcs)}')
print(f'Function name: {funcs[0][\"name\"] if funcs else \"none\"}')
"
```

Expected: Functions found: 1, Function name: test_func

**Step 3: 提交**

```bash
git add src/tools/code_analyzer.py
git commit -m "feat: add code analyzer tool"
```

---

## Task 8: 复制其他工具文件

**Files:**
- Create: `project3-code-agent-langchain/src/tools/test_generator.py`
- Create: `project3-code-agent-langchain/src/tools/refactor_tools.py`
- Create: `project3-code-agent-langchain/src/tools/file_tools.py`
- Reference: `project3-code-agent/src/tools/`

**Step 1: 复制所有工具文件**

```bash
cp /root/Learn/llm-learning/project3-code-agent/src/tools/test_generator.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/tools/test_generator.py

cp /root/Learn/llm-learning/project3-code-agent/src/tools/refactor_tools.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/tools/refactor_tools.py

cp /root/Learn/llm-learning/project3-code-agent/src/tools/file_tools.py \
   /root/Learn/llm-learning/project3-code-agent-langchain/src/tools/file_tools.py
```

**Step 2: 验证导入**

```bash
python3 -c "
from src.tools import test_generator, refactor_tools, file_tools
print('All tool modules imported successfully')
"
```

**Step 3: 提交**

```bash
git add src/tools/
git commit -m "feat: add remaining tools (test_generator, refactor_tools, file_tools)"
```

---

## Task 9: 实现 llm_client.py (LangChain 版本)

**Files:**
- Create: `project3-code-agent-langchain/src/llm_client.py`

**Step 1: 创建 llm_client.py**

```bash
cat > src/llm_client.py << 'EOF'
"""
LLM 客户端 - LangChain 版本

使用 LangChain 的 ChatOpenAI 替代自研实现
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def create_llm(temperature: float = 0.3, model: str = None, verbose: bool = False):
    """
    创建 LangChain LLM 实例

    Args:
        temperature: 生成温度 (0-1)
        model: 模型名称，默认从环境变量读取
        verbose: 是否打印详细日志

    Returns:
        ChatOpenAI 实例
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Please set it in .env file or environment variables."
        )

    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        verbose=verbose,
    )


# 简单的 LLM 客户端包装类（保持与原项目接口兼容）
class SimpleLLMClient:
    """简单的 LLM 客户端包装"""

    def __init__(self, temperature: float = 0.3, model: str = None):
        self.llm = create_llm(temperature=temperature, model=model)

    def generate(self, prompt: str, temperature: float = None) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            temperature: 温度（覆盖初始化时的值）

        Returns:
            生成的文本
        """
        from langchain.schema import HumanMessage

        if temperature is not None:
            original_temp = self.llm.temperature
            self.llm.temperature = temperature
            result = self.llm.invoke([HumanMessage(content=prompt)])
            self.llm.temperature = original_temp
        else:
            result = self.llm.invoke([HumanMessage(content=prompt)])

        return result.content

    def chat(self, messages: list) -> str:
        """
        聊天模式

        Args:
            messages: 消息列表，每个消息是 {"role": "...", "content": "..."} 格式

        Returns:
            AI 回复
        """
        from langchain.schema import HumanMessage, AIMessage, SystemMessage

        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user
                langchain_messages.append(HumanMessage(content=content))

        result = self.llm.invoke(langchain_messages)
        return result.content
EOF
```

**Step 2: 测试 LLM 客户端（需要 API key）**

```bash
cat > test_llm.py << 'EOF'
import os
from src.llm_client import create_llm, SimpleLLMClient

# 测试 create_llm
print("Testing create_llm...")
llm = create_llm()
print(f"LLM created: {type(llm)}")
print(f"Model: {llm.model_name}")
print(f"Temperature: {llm.temperature}")

# 测试 SimpleLLMClient (需要有效的 API key 才能实际调用)
if os.getenv("OPENAI_API_KEY", "test-key") != "test-key":
    print("\nTesting SimpleLLMClient.generate()...")
    client = SimpleLLMClient()
    response = client.generate("Say 'test successful' in JSON format")
    print(f"Response: {response}")
else:
    print("\nSkipping generate test (no API key)")
EOF

python3 test_llm.py
rm test_llm.py
```

Expected: LLM created successfully

**Step 3: 提交**

```bash
git add src/llm_client.py
git commit -m "feat: add LangChain LLM client"
```

---

## Task 10: 实现 langchain_tools.py - Tool 包装层

**Files:**
- Create: `project3-code-agent-langchain/src/tools/langchain_tools.py`

**Step 1: 创建 langchain_tools.py**

```bash
cat > src/tools/langchain_tools.py << 'EOF'
"""
LangChain Tool 包装层

将原项目的工具函数包装为 LangChain Tool
"""
from langchain.tools import tool
from .code_analyzer import CodeAnalyzer
from typing import Dict, List, Any


@tool
def analyze_code(file_path: str) -> Dict[str, Any]:
    """
    分析Python代码文件，获取完整的代码结构报告。

    Args:
        file_path: Python文件的路径

    Returns:
        包含functions, classes, lines, imports, complexity的完整报告字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.get_full_report()
    except Exception as e:
        return {"error": str(e)}


@tool
def list_functions(file_path: str) -> List[Dict[str, Any]]:
    """
    列出代码文件中的所有函数。

    Args:
        file_path: Python文件的路径

    Returns:
        函数信息列表，每个函数包含 name, args_count, line_number, is_method
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.analyze_functions()
    except Exception as e:
        return [{"error": str(e)}]


@tool
def list_classes(file_path: str) -> List[Dict[str, Any]]:
    """
    列出代码文件中的所有类。

    Args:
        file_path: Python文件的路径

    Returns:
        类信息列表，每个类包含 name, line_number, methods_count, base_classes
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.analyze_classes()
    except Exception as e:
        return [{"error": str(e)}]


@tool
def count_lines(file_path: str) -> Dict[str, int]:
    """
    统计代码文件的行数（总行数、代码行、注释行等）。

    Args:
        file_path: Python文件的路径

    Returns:
        包含 total, non_empty, comments, code 的统计字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.count_lines()
    except Exception as e:
        return {"error": str(e)}


@tool
def get_imports(file_path: str) -> Dict[str, List[Dict]]:
    """
    获取代码文件中的所有import语句。

    Args:
        file_path: Python文件的路径

    Returns:
        包含 standard_imports 和 from_imports 的字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.get_imports()
    except Exception as e:
        return {"error": str(e), "standard_imports": [], "from_imports": []}


@tool
def get_complexity(file_path: str) -> Dict[str, Any]:
    """
    计算代码的圈复杂度。

    Args:
        file_path: Python文件的路径

    Returns:
        包含 cyclomatic_complexity 和 level 的字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.get_complexity()
    except Exception as e:
        return {"error": str(e), "cyclomatic_complexity": 0, "level": "unknown"}


@tool
def read_file(file_path: str) -> str:
    """
    读取文件内容。

    Args:
        file_path: 文件的路径

    Returns:
        文件内容字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 限制长度避免 token 溢出
        if len(content) > 5000:
            content = content[:5000] + "\n... (内容过长，已截断)"
        return content
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def get_all_tools() -> List:
    """
    获取所有 LangChain 工具

    Returns:
        LangChain Tool 列表
    """
    return [
        analyze_code,
        list_functions,
        list_classes,
        count_lines,
        get_imports,
        get_complexity,
        read_file,
    ]
EOF
```

**Step 2: 测试工具创建**

```bash
cat > test_tools.py << 'EOF'
from src.tools.langchain_tools import get_all_tools

tools = get_all_tools()
print(f"Total tools: {len(tools)}")
print("\nTools:")
for t in tools:
    print(f"  - {t.name}: {t.description[:50]}...")

# 测试单个工具
print("\nTesting analyze_code tool...")
test_file = "/root/Learn/llm-learning/project3-code-agent/examples/workspace/demo.py"
result = analyze_code(test_file)
print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
EOF

python3 test_tools.py
rm test_tools.py
```

Expected: Total tools: 7

**Step 3: 提交**

```bash
git add src/tools/langchain_tools.py
git commit -m "feat: add LangChain tool wrappers"
```

---

## Task 11: 实现 LangChain Agent

**Files:**
- Create: `project3-code-agent-langchain/src/agents/langchain_agent.py`

**Step 1: 创建 langchain_agent.py**

```bash
cat > src/agents/langchain_agent.py << 'EOF'
"""
LangChain 版本的代码分析 Agent

使用 LangChain 的 create_react_agent 和 AgentExecutor
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import create_llm
from tools.langchain_tools import get_all_tools
from tools.code_analyzer import CodeAnalyzer
from memory.conversation_memory import ConversationMemory
from memory.project_memory import ProjectMemory


class LangChainCodeAgent:
    """
    使用 LangChain 实现的代码分析 Agent
    """

    def __init__(self, workspace_dir: str = None):
        """
        初始化 Agent

        Args:
            workspace_dir: 工作目录路径
        """
        # 初始化 LLM
        self.llm = create_llm(temperature=0.3)

        # 创建工具列表
        self.tools = get_all_tools()

        # 创建 Agent
        from langchain.agents import create_react_agent
        from langchain import hub

        # 获取标准 ReAct prompt 模板
        self.prompt = hub.pull("hwchase17/react")

        # 创建 ReAct Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # 创建 Agent 执行器
        from langchain.agents import AgentExecutor

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )

        # 记忆（用于非 Agent 模式的功能）
        self.conversation_memory = ConversationMemory()
        self.project_memory = ProjectMemory(workspace_dir)
        self.current_file = None

        # 系统提示词（用于直接调用模式）
        self.system_prompt = """你是一个专业的代码分析助手，具备以下能力：

1. 代码结构分析 - 分析函数、类、导入等代码结构
2. 代码质量评估 - 评估复杂度、可读性等
3. 测试用例生成 - 为函数自动生成测试代码
4. 重构建议 - 提供代码改进建议

请使用工具获取信息后，给出清晰、有价值的分析结果。"""

    def chat(self, user_input: str) -> str:
        """
        通过 Agent 处理用户输入

        Args:
            user_input: 用户输入

        Returns:
            Agent 回复
        """
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result.get("output", "未能获取回复")
        except Exception as e:
            return f"执行出错: {str(e)}"

    def analyze_code(self, file_path: str = None, source_code: str = None) -> Dict[str, Any]:
        """
        分析代码（直接调用，不使用 Agent）

        Args:
            file_path: 文件路径
            source_code: 源代码字符串

        Returns:
            分析结果
        """
        if file_path:
            self.current_file = file_path
            analyzer = CodeAnalyzer(file_path=file_path)
        elif source_code:
            analyzer = CodeAnalyzer(source_code=source_code)
        else:
            return {"error": "必须提供file_path或source_code"}

        report = analyzer.get_full_report()

        if file_path:
            self.project_memory.save_file_summary(file_path, report)

        return report

    def generate_test(self, file_path: str, function_name: str = None) -> str:
        """
        生成测试代码

        Args:
            file_path: 文件路径
            function_name: 函数名，None表示为所有函数生成

        Returns:
            测试代码
        """
        analysis = self.analyze_code(file_path=file_path)
        functions = analysis.get("functions", [])

        if function_name:
            func_info = next((f for f in functions if f["name"] == function_name), None)
            if not func_info:
                return f"未找到函数: {function_name}"
            prompt = f"为以下函数生成完整的单元测试代码（使用pytest）:\n\n函数名: {func_info['name']}\n参数数量: {func_info['args_count']}"
        else:
            func_list = "\n".join([f"- {f['name']}" for f in functions])
            prompt = f"为以下所有函数生成完整的单元测试代码（使用pytest）:\n\n{func_list}"

        from langchain.schema import HumanMessage
        result = self.llm.invoke([HumanMessage(content=prompt)])

        self.project_memory.add_analysis_history("test_generation", file_path, {"response": result.content})

        return result.content

    def suggest_refactor(self, file_path: str) -> str:
        """
        提供重构建议

        Args:
            file_path: 文件路径

        Returns:
            重构建议
        """
        analysis = self.analyze_code(file_path=file_path)

        prompt = f"""基于以下代码分析结果，提供详细的重构建议：

代码统计: {analysis.get('lines', {})}
复杂度: {analysis.get('complexity', {})}
函数: {analysis.get('functions', [])}
类: {analysis.get('classes', [])}

请针对以下方面提供建议：
1. 复杂度过高的函数
2. 可以改进的代码结构
3. 潜在的设计模式应用
4. 性能优化建议
5. 可读性改进建议"""

        from langchain.schema import HumanMessage
        result = self.llm.invoke([HumanMessage(content=prompt)])

        self.project_memory.add_analysis_history("refactor_suggestion", file_path, {"response": result.content})

        return result.content

    def evaluate_quality(self, file_path: str) -> Dict[str, Any]:
        """
        评估代码质量

        Args:
            file_path: 文件路径

        Returns:
            质量评估结果
        """
        analysis = self.analyze_code(file_path=file_path)

        complexity = analysis.get('complexity', {})
        lines = analysis.get('lines', {})
        functions = analysis.get('functions', [])

        score = 100
        issues = []

        if complexity.get('cyclomatic_complexity', 0) > 20:
            score -= 20
            issues.append("复杂度过高，建议拆分函数")
        elif complexity.get('cyclomatic_complexity', 0) > 10:
            score -= 10
            issues.append("复杂度较高")

        for func in functions:
            if isinstance(func, dict) and func.get('args_count', 0) > 5:
                score -= 5
                issues.append(f"函数 {func.get('name')} 参数过多")

        if lines:
            code_ratio = lines.get('code', 0) / max(lines.get('total', 1), 1)
            if code_ratio < 0.3:
                score -= 10
                issues.append("注释比例过高或空行过多")

        result = {
            "score": max(0, score),
            "level": "优秀" if score >= 90 else "良好" if score >= 70 else "需改进" if score >= 50 else "差",
            "issues": issues,
            "analysis": analysis
        }

        self.project_memory.add_analysis_history("quality_evaluation", file_path, result)

        return result

    def get_context(self) -> Dict[str, Any]:
        """
        获取当前上下文信息

        Returns:
            上下文字典
        """
        return {
            "conversation_summary": self.conversation_memory.get_summary(),
            "project_stats": self.project_memory.get_stats(),
            "current_file": self.current_file,
            "recent_analyses": self.project_memory.get_analysis_history(limit=5)
        }

    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_memory.clear()
        self.conversation_memory.add_system_message(self.system_prompt)
EOF
```

**Step 2: 测试 Agent 创建**

```bash
cat > test_agent.py << 'EOF'
from src.agents.langchain_agent import LangChainCodeAgent

print("Creating LangChain Agent...")
agent = LangChainCodeAgent()

print(f"LLM: {type(agent.llm)}")
print(f"Tools count: {len(agent.tools)}")
print(f"Agent: {type(agent.agent)}")
print(f"Executor: {type(agent.agent_executor)}")

print("\n✓ Agent created successfully!")
EOF

python3 test_agent.py
rm test_agent.py
```

Expected: Agent created successfully!

**Step 3: 提交**

```bash
git add src/agents/langchain_agent.py
git commit -m "feat: add LangChain Agent implementation"
```

---

## Task 12: 实现 main.py

**Files:**
- Create: `project3-code-agent-langchain/src/main.py`

**Step 1: 创建 main.py**

```bash
cat > src/main.py << 'EOF'
"""
主入口 - LangChain 版本代码助手
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.langchain_agent import LangChainCodeAgent


def print_banner():
    """打印欢迎信息"""
    print("=" * 60)
    print("  LangChain 代码助手 Agent")
    print("  基于 LangChain ReAct Agent 实现")
    print("=" * 60)
    print()


def interactive_mode(agent: LangChainCodeAgent):
    """
    交互式对话模式

    Args:
        agent: Agent 实例
    """
    print("进入交互模式（输入 'exit' 或 'quit' 退出）")
    print()

    while True:
        try:
            user_input = input("\n👤 用户: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break

            print("\n🤖 Agent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


def single_query_mode(agent: LangChainCodeAgent, query: str):
    """
    单次查询模式

    Args:
        agent: Agent 实例
        query: 用户查询
    """
    print(f"查询: {query}\n")
    response = agent.chat(query)
    print(f"回复: {response}\n")


def direct_mode(agent: LangChainCodeAgent, file_path: str):
    """
    直接调用模式（不使用 Agent）

    Args:
        agent: Agent 实例
        file_path: 文件路径
    """
    print(f"分析文件: {file_path}\n")

    # 分析代码
    print("1. 代码结构分析")
    analysis = agent.analyze_code(file_path=file_path)
    print(f"   函数数: {len(analysis.get('functions', []))}")
    print(f"   类数: {len(analysis.get('classes', []))}")
    print(f"   总行数: {analysis.get('lines', {}).get('total', 0)}")

    # 生成测试
    print("\n2. 生成测试代码")
    test_code = agent.generate_test(file_path)
    print(f"   {test_code[:100]}...")

    # 重构建议
    print("\n3. 重构建议")
    suggestions = agent.suggest_refactor(file_path)
    print(f"   {suggestions[:100]}...")

    # 质量评估
    print("\n4. 质量评估")
    quality = agent.evaluate_quality(file_path)
    print(f"   分数: {quality.get('score', 0)}")
    print(f"   等级: {quality.get('level', '未知')}")


def main():
    """主函数"""
    print_banner()

    # 检查 API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置 OPENAI_API_KEY")
        print("请在 .env 文件中设置 OPENAI_API_KEY")
        return

    # 初始化 Agent
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "workspace")
    agent = LangChainCodeAgent(workspace_dir=workspace_dir)

    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--interactive" or command == "-i":
            interactive_mode(agent)

        elif command == "--query" or command == "-q":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                single_query_mode(agent, query)
            else:
                print("错误: --query 需要提供查询内容")

        elif command == "--analyze" or command == "-a":
            if len(sys.argv) > 2:
                direct_mode(agent, sys.argv[2])
            else:
                print("错误: --analyze 需要提供文件路径")

        else:
            # 默认为查询模式
            query = " ".join(sys.argv[1:])
            single_query_mode(agent, query)
    else:
        # 默认进入交互模式
        interactive_mode(agent)


if __name__ == "__main__":
    main()
EOF
```

**Step 2: 创建快捷运行脚本 run.py**

```bash
cat > run.py << 'EOF'
#!/usr/bin/env python3
"""
快捷运行脚本
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import main

if __name__ == "__main__":
    main()
EOF

chmod +x run.py
```

**Step 3: 测试主入口（显示帮助信息）**

```bash
python3 run.py --help 2>&1 || echo "Script runs without --help, testing basic execution..."
```

**Step 4: 提交**

```bash
git add src/main.py run.py
git commit -m "feat: add main entry point and run script"
```

---

## Task 13: 创建演示脚本

**Files:**
- Create: `project3-code-agent-langchain/examples/demo_langchain.py`

**Step 1: 创建演示脚本**

```bash
cat > examples/demo_langchain.py << 'EOF'
"""
LangChain Agent 演示脚本

展示 LangChain ReAct Agent 的基本使用
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.langchain_agent import LangChainCodeAgent


def demo_agent_mode():
    """演示 Agent 模式"""
    print("=" * 60)
    print("演示 1: Agent 模式")
    print("=" * 60)

    agent = LangChainCodeAgent()

    # 创建测试文件
    test_file = Path(__file__).parent / "workspace" / "demo.py"
    test_file.parent.mkdir(exist_ok=True)

    test_file.write_text('''"""演示模块"""

import os
from typing import List, Dict


def calculate_sum(numbers: List[int]) -> int:
    """计算列表中数字的总和"""
    total = 0
    for num in numbers:
        total += num
    return total


class DataProcessor:
    """数据处理器类"""

    def __init__(self, name: str):
        self.name = name
        self.data = []

    def add_data(self, item: Dict) -> None:
        self.data.append(item)

    def get_summary(self) -> Dict:
        return {
            "name": self.name,
            "count": len(self.data)
        }
''')

    print(f"\n测试文件: {test_file}")
    print("\n查询: 分析这个文件的代码结构\n")

    response = agent.chat(f"分析文件 {test_file} 的代码结构")
    print(f"回复: {response}\n")


def demo_direct_mode():
    """演示直接调用模式"""
    print("=" * 60)
    print("演示 2: 直接调用模式")
    print("=" * 60)

    agent = LangChainCodeAgent()

    test_file = Path(__file__).parent / "workspace" / "demo.py"

    print("\n1. 代码分析")
    analysis = agent.analyze_code(str(test_file))
    print(f"   函数: {len(analysis.get('functions', []))} 个")
    print(f"   类: {len(analysis.get('classes', []))} 个")
    print(f"   复杂度: {analysis.get('complexity', {}).get('level', 'unknown')}")

    print("\n2. 质量评估")
    quality = agent.evaluate_quality(str(test_file))
    print(f"   分数: {quality.get('score', 0)}")
    print(f"   等级: {quality.get('level', 'unknown')}")


def demo_tools():
    """演示工具列表"""
    print("\n" + "=" * 60)
    print("演示 3: 可用工具")
    print("=" * 60)

    from tools.langchain_tools import get_all_tools

    tools = get_all_tools()
    print(f"\n共有 {len(tools)} 个工具:\n")
    for tool in tools:
        print(f"  - {tool.name}")
        print(f"    描述: {tool.description[:60]}...\n")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█  LangChain 代码助手 Agent - 演示程序".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60 + "\n")

    demo_tools()
    demo_direct_mode()
    # demo_agent_mode()  # 需要 API key

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
EOF
```

**Step 2: 运行演示**

```bash
python3 examples/demo_langchain.py
```

Expected: 演示脚本正常运行，显示工具列表和代码分析结果

**Step 3: 提交**

```bash
git add examples/demo_langchain.py
git commit -m "feat: add LangChain demo script"
```

---

## Task 14: 编写测试

**Files:**
- Create: `project3-code-agent-langchain/tests/test_langchain_agent.py`

**Step 1: 创建测试文件**

```bash
cat > tests/test_langchain_agent.py << 'EOF'
"""
LangChain Agent 测试
"""
import sys
from pathlib import Path
import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.langchain_agent import LangChainCodeAgent
from tools.langchain_tools import get_all_tools


class TestLangChainTools:
    """测试 LangChain 工具"""

    def test_tools_count(self):
        """测试工具数量"""
        tools = get_all_tools()
        assert len(tools) == 7

    def test_tool_names(self):
        """测试工具名称"""
        tools = get_all_tools()
        tool_names = [t.name for t in tools]
        expected = [
            "analyze_code",
            "list_functions",
            "list_classes",
            "count_lines",
            "get_imports",
            "get_complexity",
            "read_file"
        ]
        for name in expected:
            assert name in tool_names

    def test_analyze_code_tool(self):
        """测试 analyze_code 工具"""
        from tools.langchain_tools import analyze_code
        from tools.code_analyzer import CodeAnalyzer

        # 创建测试文件
        test_file = Path("/tmp/test_langchain_code.py")
        test_file.write_text("def test(): pass")

        result = analyze_code(str(test_file))
        assert isinstance(result, dict)
        assert "functions" in result

        # 清理
        test_file.unlink()


class TestLangChainAgent:
    """测试 LangChain Agent"""

    def test_agent_creation(self):
        """测试 Agent 创建"""
        agent = LangChainCodeAgent()
        assert agent.llm is not None
        assert len(agent.tools) > 0
        assert agent.agent is not None
        assert agent.agent_executor is not None

    def test_analyze_code_direct(self):
        """测试直接分析代码"""
        agent = LangChainCodeAgent()

        # 创建测试文件
        test_file = Path("/tmp/test_langchain_analyze.py")
        test_file.write_text('''
def hello():
    print("hello")

class TestClass:
    pass
''')

        result = agent.analyze_code(str(test_file))
        assert isinstance(result, dict)
        assert "functions" in result
        assert len(result["functions"]) >= 1

        # 清理
        test_file.unlink()

    def test_evaluate_quality(self):
        """测试质量评估"""
        agent = LangChainCodeAgent()

        # 创建测试文件
        test_file = Path("/tmp/test_langchain_quality.py")
        test_file.write_text("def simple(): pass")

        result = agent.evaluate_quality(str(test_file))
        assert isinstance(result, dict)
        assert "score" in result
        assert "level" in result
        assert 0 <= result["score"] <= 100

        # 清理
        test_file.unlink()

    def test_context(self):
        """测试获取上下文"""
        agent = LangChainCodeAgent()
        context = agent.get_context()
        assert isinstance(context, dict)
        assert "conversation_summary" in context
        assert "project_stats" in context


class TestLLMClient:
    """测试 LLM 客户端"""

    def test_create_llm(self):
        """测试创建 LLM"""
        from llm_client import create_llm
        llm = create_llm()
        assert llm is not None
        assert llm.temperature == 0.3

    def test_simple_llm_client(self):
        """测试 SimpleLLMClient"""
        from llm_client import SimpleLLMClient
        client = SimpleLLMClient()
        assert client.llm is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

**Step 2: 运行测试**

```bash
cd /root/Learn/llm-learning/project3-code-agent-langchain
python3 -m pytest tests/test_langchain_agent.py -v
```

Expected: 所有测试通过

**Step 3: 提交**

```bash
git add tests/test_langchain_agent.py
git commit -m "test: add LangChain Agent tests"
```

---

## Task 15: 编写 README.md

**Files:**
- Create: `project3-code-agent-langchain/README.md`

**Step 1: 创建 README.md**

```bash
cat > README.md << 'EOF'
# Project3: 代码助手 Agent (LangChain 版本)

> 使用 LangChain 框架实现的智能代码分析 Agent

## 📚 项目说明

这是 `project3-code-agent` 的 LangChain 版本，用于对比学习自研 ReAct 实现与 LangChain Agent 的差异。

### 与原项目对比

| 特性 | 原项目 (自研 ReAct) | LangChain 版本 |
|------|---------------------|----------------|
| Agent 创建 | 手写循环 + prompt 解析 | `create_react_agent()` |
| 工具注册 | 手写 ToolRegistry + 正则解析 | `@tool` 装饰器 |
| 循环控制 | `for iteration in range(10)` | `AgentExecutor(max_iterations=10)` |
| 历史管理 | 字符串拼接 | 内置 ConversationMemory |
| Prompt 模板 | 手写字符串 | `hub.pull("hwchase17/react")` |
| 错误处理 | 手动 try-catch | `handle_parsing_errors=True` |

## ✨ 功能

- 🔍 代码结构分析 - 函数、类、导入等
- 🧪 自动生成测试 - 为函数生成 pytest 测试
- 💡 重构建议 - 提供代码改进建议
- 📊 代码质量评估 - 复杂度、可读性评分

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
```

### 3. 运行

```bash
# 交互模式
python run.py

# 单次查询
python run.py --query "分析 demo.py 的代码结构"

# 直接分析
python run.py --analyze examples/workspace/demo.py
```

## 📁 项目结构

```
project3-code-agent-langchain/
├── src/
│   ├── agents/
│   │   └── langchain_agent.py       # LangChain Agent 实现
│   ├── tools/
│   │   ├── langchain_tools.py       # LangChain Tool 包装
│   │   └── ... (其他工具，从原项目复制)
│   ├── memory/                      # 记忆模块
│   ├── embeddings.py                 # 文本嵌入
│   ├── vector_store.py               # 向量存储
│   ├── llm_client.py                 # LangChain LLM 客户端
│   └── main.py                       # 主入口
├── examples/
│   └── demo_langchain.py             # 演示脚本
├── tests/
│   └── test_langchain_agent.py      # 测试
└── requirements.txt
```

## 🔑 核心代码

### Agent 创建

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_openai import ChatOpenAI

# 创建 LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.3)

# 获取 ReAct prompt
prompt = hub.pull("hwchase17/react")

# 创建 Agent
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# 创建执行器
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10
)
```

### Tool 定义

```python
from langchain.tools import tool

@tool
def analyze_code(file_path: str) -> dict:
    """
    分析Python代码文件，获取完整的代码结构报告。

    Args:
        file_path: Python文件的路径
    """
    analyzer = CodeAnalyzer(file_path=file_path)
    return analyzer.get_full_report()
```

## 🧪 运行测试

```bash
pytest tests/test_langchain_agent.py -v
```

## 📖 学习要点

1. **LangChain 简化了 Agent 开发** - 不需要手写循环和解析逻辑
2. **Tool 装饰器** - 自动处理参数序列化和错误
3. **AgentExecutor** - 内置的执行引擎，处理重试和错误恢复
4. **标准化 Prompt** - 使用社区验证的 prompt 模板

## 🔗 相关项目

- [原项目 (自研 ReAct)](../project3-code-agent/) - 自研 ReAct 实现
- [Project2 (RAG系统)](../project2-rag-system/) - 检索增强生成
- [Project1 (基础API)](../project1-basic-api/) - 基础 API 应用

## 📄 License

MIT
EOF
```

**Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 16: 最终验证和提交

**Files:**
- Modify: None (验证步骤)

**Step 1: 运行完整演示**

```bash
cd /root/Learn/llm-learning/project3-code-agent-langchain
python3 examples/demo_langchain.py
```

**Step 2: 运行所有测试**

```bash
python3 -m pytest tests/ -v
```

**Step 3: 验证项目结构**

```bash
tree -L 2 -I '__pycache__|*.pyc|venv|.git'
```

**Step 4: 最终 Git 提交**

```bash
git status
git add .
git commit -m "feat: complete LangChain version implementation"
```

**Step 5: 打标签（可选）**

```bash
git tag v1.0.0
git tag
```

---

## 总结

实现计划完成！主要完成了：

1. ✅ 项目结构创建
2. ✅ 复制共享组件（embeddings、vector_store、memory、tools）
3. ✅ 实现 LangChain LLM 客户端
4. ✅ 实现 Tool 包装层
5. ✅ 实现 LangChain Agent
6. ✅ 实现主入口和演示脚本
7. ✅ 编写测试
8. ✅ 编写文档

**关键改动总结：**
- Agent: 从自研 ReAct 循环 → LangChain `create_react_agent()`
- Tools: 从手动注册 → `@tool` 装饰器
- 执行: 从手动循环 → `AgentExecutor`
- Prompt: 从手写模板 → `hub.pull("hwchase17/react")`
