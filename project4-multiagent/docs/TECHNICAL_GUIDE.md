# 技术实现说明

本文档详细说明 Project 4 的技术架构和实现细节。

**注意：本版本使用 pyautogen 0.10.0，API 与早期版本有重大差异。**

---

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
├─────────────────────────────────────────────────────────────┤
│  CLI (app/cli.py)          │   Web (app/web.py)             │
│  - 命令行参数解析           │   - Streamlit 界面             │
│  - 任务执行                 │   - 实时对话显示               │
│  - 结果展示                 │   - 配置管理                   │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      核心编排层                              │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator (src/core/orchestrator.py)                   │
│  - 管理 4 个 Agent                                          │
│  - 协调 Agent 之间的对话                                     │
│  - 记录对话历史                                             │
│  - 提供两种执行模式                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                       Agent 层                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  UserProxy   │  │    Coder     │  │  Reviewer    │     │
│  │ (协调者)     │  │  (编码者)    │  │  (审查者)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐                                          │
│  │   Tester     │                                          │
│  │  (测试者)    │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      基础设施层                              │
├─────────────────────────────────────────────────────────────┤
│  Config (src/core/config.py)   │  Logger (src/utils/logger.py)│
│  - 环境变量管理                 │  - 日志输出                 │
│  - 模型配置                     │  - 彩色格式化               │
│  - 代码执行配置                 │  - 日志级别管理             │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    外部服务层                                │
├─────────────────────────────────────────────────────────────┤
│  AutoGen 0.10.0  │  OpenAI API  │  文件系统  │  Docker(可选)│
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件详解

### 1. 配置管理 (Config)

**文件:** `src/core/config.py`

**职责:**
- 从环境变量加载配置
- 提供模型配置给 AutoGen
- 管理代码执行配置

**关键类:**

```python
@dataclass
class Config:
    # LLM 配置
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    # 代码执行配置
    use_docker: bool
    work_dir: str

    def get_model_config(self) -> dict:
        """返回 AutoGen 0.10.0 需要的模型配置
        使用 OpenAIChatCompletionClient"""
        from autogen.ext.models.openai import OpenAIChatCompletionClient
        model_client = OpenAIChatCompletionClient(
            model=self.model,
            api_key=self.api_key,
            base_url=self.api_base if self.api_base != 'https://api.openai.com/v1' else None,
        )
        return {
            'model_client': model_client,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
        }

    def get_code_execution_config(self) -> dict:
        """返回代码执行配置
        使用 CommandLineCodeExecutor 或 DockerCommandLineCodeExecutor"""
        from autogen.coding import CodeBlock, DockerCommandLineCodeExecutor, CommandLineCodeExecutor

        if self.use_docker:
            executor = DockerCommandLineCodeExecutor(work_dir=self.work_dir)
        else:
            executor = CommandLineCodeExecutor(work_dir=self.work_dir)

        return {
            'code_executor': executor,
            'use_docker': self.use_docker,
        }
```

**设计模式:**
- **单例模式**: `get_config()` 函数确保全局只有一个配置实例
- **Dataclass**: 使用 Python dataclass 简化配置类定义

**pyautogen 0.10.0 变化:**
- `get_llm_config()` → `get_model_config()`
- 返回 `model_client` 对象而非配置字典
- 使用 `OpenAIChatCompletionClient` 替代配置列表

---

### 2. 日志工具 (Logger)

**文件:** `src/utils/logger.py`

**职责:**
- 提供统一的日志接口
- 支持彩色输出（使用 Rich）
- 管理日志级别

**关键函数:**

```python
def setup_logging(level: str = 'INFO', rich: bool = None) -> None:
    """设置全局日志配置"""

def get_logger(name: str) -> logging.Logger:
    """获取或创建 Logger 实例"""
```

**特性:**
- **Rich 集成**: 美化的终端输出
- **级别控制**: DEBUG, INFO, WARNING, ERROR
- **单例管理**: 相同名称返回同一实例

---

### 3. Agent 实现

所有 Agent 都继承自 AutoGen 的基类：
- `UserProxyAgent` - 用于 UserProxy
- `AssistantAgent` - 用于 Coder, Reviewer, Tester

#### 3.1 UserProxy Agent

**文件:** `src/agents/user_proxy.py`

**特殊之处:**
- 可以执行代码（通过 `code_executor`）
- 作为对话的起点和终点
- 管理对话流程

**pyautogen 0.10.0 变化:**
```python
# 旧 API (0.2.x)
UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "./outputs"},
)

# 新 API (0.10.0)
from autogen.coding import CommandLineCodeExecutor

UserProxyAgent(
    name="user_proxy",
    code_executor=CommandLineCodeExecutor(work_dir="./outputs"),
)
```

**System Message 结构:**
```
1. 角色定位
2. 主要职责（4 点）
3. 沟通风格指南
4. 工作流程说明
5. 目标说明
```

#### 3.2 Coder Agent

**文件:** `src/agents/coder.py`

**pyautogen 0.10.0 变化:**
```python
# 旧 API (0.2.x)
AssistantAgent(
    name="coder",
    system_message=CODER_SYSTEM_MESSAGE,
    llm_config=config.get_llm_config(),
)

# 新 API (0.10.0)
model_config = config.get_model_config()
AssistantAgent(
    name="coder",
    system_message=CODER_SYSTEM_MESSAGE,
    model_client=model_config['model_client'],
)
```

**编码标准（在 System Message 中定义）:**
1. 类型注解 (Type Hints)
2. 命名规范 (Naming)
3. 文档字符串 (Documentation)
4. PEP 8 风格
5. 错误处理 (Error Handling)
6. 注释规范 (Comments)

#### 3.3 Reviewer Agent

**文件:** `src/agents/reviewer.py`

**API 变化同 Coder**

**审查清单:**
1. 正确性 (Correctness)
2. 代码风格 (Style)
3. 文档 (Documentation)
4. 性能 (Performance)
5. 安全性 (Security)
6. 错误处理 (Error Handling)

#### 3.4 Tester Agent

**文件:** `src/agents/tester.py`

**API 变化同 Coder**

**测试策略:**
1. 测试覆盖（正常、边界、错误情况）
2. 测试结构（Arrange-Act-Assert）
3. 测试命名规范
4. pytest 框架使用

---

### 4. 编排器 (Orchestrator)

**文件:** `src/core/orchestrator.py`

**核心类:** `CodeDevelopmentOrchestrator`

**职责:**
- 创建和管理所有 Agent
- 提供任务执行接口
- 记录对话历史
- 支持多种执行模式

**关键方法:**

#### 4.1 `execute_task()` - 标准执行模式

**pyautogen 0.10.0 变化:**
```python
# 旧 API (0.2.x)
self.user_proxy.initiate_chat(
    self.coder,
    message=task_description,
    clear_history=True,
)

# 新 API (0.10.0)
response = self.user_proxy.run(
    task_description,
    recipient=self.coder,
)
```

#### 4.2 对话历史提取

**pyautogen 0.10.0 变化:**
```python
# 旧 API (0.2.x)
for agent in self.agents:
    for other_agent, messages in agent.chat_messages.items():
        for msg in messages:
            history.append({...})

# 新 API (0.10.0)
if hasattr(response, 'messages'):
    for msg in response.messages:
        history.append({
            'from': getattr(msg, 'source', 'unknown'),
            'content': getattr(msg, 'content', ''),
        })
```

---

## 🔄 对话机制

### AutoGen 0.10.0 对话原理

AutoGen 0.10.0 的对话基于新的 `run()` 方法：

```python
response = agent.run(
    message="任务描述",
    recipient=target_agent,
)
```

### 对话存储

对话历史通过响应对象获取：

```python
response.messages  # 列表格式
# 每个 msg 有: source, content, recipient 等属性
```

---

## 📚 关键依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `pyautogen` | ==0.10.0 | 多 Agent 框架 |
| `openai` | >=1.0.0 | LLM API |
| `streamlit` | >=1.28.0 | Web 界面 |
| `pytest` | >=7.4.0 | 测试框架 |
| `rich` | >=13.0.0 | 终端美化 |

---

## 🚀 迁移指南 (从旧版本)

### 从 pyautogen 0.2.x 升级到 0.10.0

#### 1. 配置变化

```python
# 旧代码
llm_config = {
    "config_list": [{"model": "gpt-4", "api_key": "..."}],
    "temperature": 0.7,
}

# 新代码
from autogen.ext.models.openai import OpenAIChatCompletionClient
model_client = OpenAIChatCompletionClient(model="gpt-4", api_key="...")
```

#### 2. Agent 创建变化

```python
# 旧代码
AssistantAgent(
    name="agent",
    llm_config=llm_config,
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
)

# 新代码
AssistantAgent(
    name="agent",
    model_client=model_client,
)
```

#### 3. 对话启动变化

```python
# 旧代码
agent.initiate_chat(
    recipient,
    message="Hello",
    clear_history=True,
)

# 新代码
agent.run(
    "Hello",
    recipient=recipient,
)
```

#### 4. 代码执行变化

```python
# 旧代码
code_execution_config = {
    "work_dir": "./outputs",
    "use_docker": False,
}

# 新代码
from autogen.coding import CommandLineCodeExecutor
code_executor = CommandLineCodeExecutor(work_dir="./outputs")
```

---

## 🔍 调试技巧

### 1. 启用调试模式

```bash
# CLI
python3 -m app.cli --task "..." --debug

# Python 代码
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 查看 AutoGen 对话

```python
# pyautogen 0.10.0
response = orchestrator.user_proxy.run(task, recipient=coder)
for msg in response.messages:
    print(f"{msg.source}: {msg.content}")
```

---

本文档持续更新中...
