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
