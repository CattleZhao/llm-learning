# Project3: LangChain 版本设计文档

**日期**: 2026-03-07
**目的**: 创建 LangChain 版本的代码助手 Agent，与自研 ReAct 版本对比学习

---

## 1. 项目概述

### 1.1 目标

创建 `project3-code-agent-langchain/` 项目，使用 LangChain 框架实现与原项目相同的功能，用于：
- 学习 LangChain Agent 的使用
- 对比自研 ReAct vs LangChain ReAct 的实现差异
- 理解 LangChain 如何简化 Agent 开发

### 1.2 保留组件

以下组件直接从原项目复制，保持不变：
- `code_analyzer.py` - AST 代码分析
- `test_generator.py` - 测试生成工具
- `refactor_tools.py` - 重构建议工具
- `file_tools.py` - 文件操作工具
- `conversation_memory.py` - 对话记忆
- `project_memory.py` - 项目记忆
- `embeddings.py` - 文本嵌入（自研简化版）
- `vector_store.py` - 向量存储（自研简化版）
- `document_loader.py` - 文档加载

### 1.3 新增/重写组件

| 组件 | 说明 |
|------|------|
| `agents/langchain_agent.py` | 用 LangChain 重写 Agent |
| `tools/langchain_tools.py` | 将工具包装为 LangChain Tool |
| `llm_client.py` | 简化为 LangChain LLM 初始化 |
| `main.py` | 适配 LangChain Agent |
| `examples/demo_langchain.py` | LangChain 版本演示 |
| `requirements.txt` | 新增 langchain 依赖 |

---

## 2. 项目结构

```
project3-code-agent-langchain/
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── langchain_agent.py       # 核心：LangChain Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── code_analyzer.py         # 复制
│   │   ├── test_generator.py        # 复制
│   │   ├── refactor_tools.py        # 复制
│   │   ├── file_tools.py            # 复制
│   │   └── langchain_tools.py       # 新增：Tool 包装
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── conversation_memory.py   # 复制
│   │   └── project_memory.py        # 复制
│   ├── embeddings.py                 # 复制
│   ├── vector_store.py               # 复制
│   ├── document_loader.py            # 复制
│   ├── llm_client.py                 # 简化
│   └── main.py                       # 重写
├── examples/
│   └── demo_langchain.py             # 新增
├── tests/
│   ├── test_langchain_agent.py       # 新增
│   └── ...
├── requirements.txt
├── run.py
├── .env.example
└── README.md
```

---

## 3. 核心设计

### 3.1 LangChain Agent (`agents/langchain_agent.py`)

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain import hub

class LangChainCodeAgent:
    def __init__(self, workspace_dir: str = None):
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0.3
        )

        # 创建工具
        self.tools = self._create_tools()

        # 获取 ReAct prompt
        prompt = hub.pull("hwchase17/react")

        # 创建 Agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # 创建执行器
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )

    def chat(self, user_input: str) -> str:
        """通过 Agent 处理用户输入"""
        result = self.agent_executor.invoke({"input": user_input})
        return result["output"]
```

### 3.2 Tool 包装 (`tools/langchain_tools.py`)

```python
from langchain.tools import tool
from .code_analyzer import CodeAnalyzer

@tool
def analyze_code(file_path: str) -> dict:
    """分析Python代码文件，获取完整的代码结构报告。

    Args:
        file_path: Python文件路径

    Returns:
        包含functions, classes, lines, imports, complexity的字典
    """
    analyzer = CodeAnalyzer(file_path=file_path)
    return analyzer.get_full_report()

@tool
def list_functions(file_path: str) -> list:
    """列出代码文件中的所有函数。

    Args:
        file_path: Python文件路径
    """
    analyzer = CodeAnalyzer(file_path=file_path)
    return analyzer.analyze_functions()

# ... 其他工具类似包装
```

### 3.3 LLM 客户端 (`llm_client.py`)

```python
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def create_llm(temperature: float = 0.3, model: str = None):
    """创建 LangChain LLM 实例"""
    return ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )
```

---

## 4. API 接口

### 4.1 主入口

```python
from agents.langchain_agent import LangChainCodeAgent

def main():
    agent = LangChainCodeAgent(workspace_dir="./workspace")

    # Agent 模式
    result = agent.chat("分析 demo.py 的代码结构")

    # 直接调用模式（保持兼容）
    analysis = agent.analyze_code("demo.py")
    test_code = agent.generate_test("demo.py", "calculate_sum")
```

### 4.2 方法列表

| 方法 | 说明 |
|------|------|
| `chat(user_input)` | Agent 模式，通过 ReAct 循环处理 |
| `analyze_code(file_path)` | 直接分析代码 |
| `generate_test(file_path, function_name)` | 生成测试 |
| `suggest_refactor(file_path)` | 重构建议 |
| `evaluate_quality(file_path)` | 质量评估 |
| `clear_conversation()` | 清空对话历史 |

---

## 5. 对比要点

| 特性 | 原项目 (自研 ReAct) | LangChain 版本 |
|------|---------------------|----------------|
| Agent 创建 | 手写循环 + prompt 解析 | `create_react_agent()` |
| 工具注册 | 手写 ToolRegistry + 正则解析 | `@tool` 装饰器 |
| 循环控制 | `for iteration in range(10)` | `AgentExecutor(max_iterations=10)` |
| 历史管理 | 字符串拼接 | 内置 ConversationMemory |
| Prompt 模板 | 手写字符串 | `hub.pull("hwchase17/react")` |
| 错误处理 | 手动 try-catch | `handle_parsing_errors=True` |

---

## 6. 依赖

```
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.20
openai>=1.0.0
python-dotenv>=1.0.0
numpy>=1.0.0
pytest>=7.0.0
```

---

## 7. 实现顺序

1. 创建项目目录结构
2. 复制共享组件（tools/, memory/, embeddings.py 等）
3. 实现 `tools/langchain_tools.py` - Tool 包装
4. 实现 `llm_client.py` - LLM 初始化
5. 实现 `agents/langchain_agent.py` - 核心 Agent
6. 实现 `main.py` - 主入口
7. 实现 `examples/demo_langchain.py` - 演示脚本
8. 编写测试
9. 更新 README.md
