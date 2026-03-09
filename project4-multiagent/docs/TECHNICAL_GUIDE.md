# 技术实现说明

本文档详细说明 Project 4 的技术架构和实现细节。

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
│  - LLM 配置                     │  - 彩色格式化               │
│  - 代码执行配置                 │  - 日志级别管理             │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    外部服务层                                │
├─────────────────────────────────────────────────────────────┤
│  AutoGen 框架  │  OpenAI API  │  文件系统  │  Docker(可选)│
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件详解

### 1. 配置管理 (Config)

**文件:** `src/core/config.py`

**职责:**
- 从环境变量加载配置
- 提供 LLM 配置给 AutoGen
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

    # Agent 配置
    max_consecutive_auto_reply: int

    def get_llm_config(self) -> Dict[str, Any]:
        """返回 AutoGen 需要的 LLM 配置"""

    def get_code_execution_config(self) -> Dict[str, Any]:
        """返回代码执行配置"""
```

**设计模式:**
- **单例模式**: `get_config()` 函数确保全局只有一个配置实例
- **Dataclass**: 使用 Python dataclass 简化配置类定义

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
- 可以执行代码（通过 `code_execution_config`）
- 作为对话的起点和终点
- 管理对话流程

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

**编码标准（在 System Message 中定义）:**
1. 类型注解 (Type Hints)
2. 命名规范 (Naming)
3. 文档字符串 (Documentation)
4. PEP 8 风格
5. 错误处理 (Error Handling)
6. 注释规范 (Comments)

**输出格式:**
- 首先提供思路说明
- 然后提供完整代码
- 最后包含使用示例

#### 3.3 Reviewer Agent

**文件:** `src/agents/reviewer.py`

**审查清单:**
1. 正确性 (Correctness)
2. 代码风格 (Style)
3. 文档 (Documentation)
4. 性能 (Performance)
5. 安全性 (Security)
6. 错误处理 (Error Handling)

**审查格式:**
```
**Problem**: 问题描述
**Location**: 位置
**Suggestion**: 改进建议
```

**决策:**
- "APPROVED" - 代码通过审查
- "NEEDS REVISION" - 需要修改

#### 3.4 Tester Agent

**文件:** `src/agents/tester.py`

**测试策略:**
1. 测试覆盖（正常、边界、错误情况）
2. 测试结构（Arrange-Act-Assert）
3. 测试命名规范
4. pytest 框架使用

**结果报告:**
```
✓ PASSED: test_name
✗ FAILED: test_name - reason
Summary: X passed, Y failed
```

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

```python
def execute_task(
    task_description: str,
    coder_first: bool = True,
) -> Dict[str, Any]:
    """
    工作流程:
    1. UserProxy 接收任务
    2. 如果 coder_first=True，直接让 Coder 开始
    3. Agent 之间自由对话协作
    4. 返回执行结果
    """
```

**对话流程:**
```
UserProxy → Coder → UserProxy → Reviewer → Coder → UserProxy → Tester → ...
         ↑                                                              ↓
         └──────────────────────────────────────────────────────────────┘
```

#### 4.2 `execute_sequential_workflow()` - 顺序执行模式

```python
def execute_sequential_workflow(
    task_description: str,
) -> Dict[str, Any]:
    """
    工作流程:
    1. UserProxy → Coder（编写代码）
    2. UserProxy → Reviewer（审查代码）
    3. UserProxy → Tester（编写测试）
    4. UserProxy（执行测试）

    更可控，按顺序执行每个阶段
    """
```

**对话流程:**
```
阶段 1: UserProxy → Coder → UserProxy
阶段 2: UserProxy → Reviewer → UserProxy
阶段 3: UserProxy → Tester → UserProxy
阶段 4: UserProxy 执行测试
```

---

## 5. 用户界面

### 5.1 CLI 界面

**文件:** `app/cli.py`

**架构:**
```
main()
  ├─ parse_arguments()      # 解析命令行参数
  ├─ get_config()           # 加载配置
  ├─ create_orchestrator()  # 创建编排器
  ├─ execute_task()         # 执行任务
  └─ print_results()        # 打印结果
```

**参数解析:** 使用 `argparse` 模块

**输出美化:** 使用表格、分隔符、图标

### 5.2 Web 界面

**文件:** `app/web.py`

**框架:** Streamlit

**状态管理:** `st.session_state`

```python
st.session_state.orchestrator      # 编排器实例
st.session_state.config            # 配置
st.session_state.conversation_history  # 对话历史
st.session_state.task_completed    # 任务完成状态
st.session_state.execution_results # 执行结果
```

**页面布局:**
```
┌─────────────┬──────────────────────────────────┐
│  侧边栏     │  主内容区                        │
│  - 设置     │  - 标题                         │
│  - 模型     │  - 任务输入                     │
│  - Agent    │  - 执行按钮                     │
│  - 说明     │  - 对话历史                     │
│             │  - 执行结果                     │
└─────────────┴──────────────────────────────────┘
```

---

## 🔄 对话机制

### AutoGen 对话原理

AutoGen 的对话基于**消息传递**：

```python
{
    'role': 'assistant',     # 消息发送者角色
    'content': '...',        # 消息内容
    'name': 'coder',         # Agent 名称
}
```

### 对话存储

每个 Agent 维护自己的对话历史：

```python
agent.chat_messages = {
    other_agent_1: [msg1, msg2, ...],
    other_agent_2: [msg3, msg4, ...],
}
```

### 对话控制

1. **`initiate_chat()`** - 发起对话
2. **`max_consecutive_auto_reply`** - 限制自动回复次数
3. **`human_input_mode`** - 控制人工干预时机

---

## 🧪 测试架构

### 测试分层

```
tests/
├── unit/              # 单元测试（每个模块）
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_user_proxy.py
│   ├── test_coder.py
│   ├── test_reviewer.py
│   ├── test_tester.py
│   └── test_orchestrator.py
├── integration/       # 集成测试
│   └── test_basic_workflow.py
└── conftest.py        # pytest 配置和 fixtures
```

### Fixtures

```python
@pytest.fixture
def mock_api_key(monkeypatch):
    """提供测试用 API Key"""

@pytest.fixture
def mock_config(temp_api_key):
    """提供测试用配置"""
```

### 测试标记

```python
@pytest.mark.integration  # 需要真实 API 的测试
@pytest.mark.slow         # 运行较慢的测试
```

---

## 📊 数据流

### 任务执行数据流

```
用户输入
  │
  ▼
CLI/Web 解析
  │
  ▼
Orchestrator.execute_task()
  │
  ├─ 创建/获取 Agent
  │
  ├─ initiate_chat(user_proxy → coder)
  │   │
  │   ├─ Coder 处理任务
  │   │  │
  │   │  ├─ 调用 LLM API
  │   │  │  │
  │   │  │  ▼
  │   │  │  LLM 返回响应
  │   │  │
  │   │  └─ 生成代码
  │   │
  │   └─ 返回给 UserProxy
  │
  ├─ initiate_chat(user_proxy → reviewer)
  │   │
  │   └─ Reviewer 审查代码
  │
  ├─ initiate_chat(user_proxy → tester)
  │   │
  │   └─ Tester 编写测试
  │
  └─ 收集对话历史
      │
      ▼
  返回结果
```

---

## 🎯 设计模式

### 1. 工厂模式

```python
# 每个 Agent 都有对应的工厂函数
create_user_proxy(config)
create_coder(config)
create_reviewer(config)
create_tester(config)
create_orchestrator(config)
```

### 2. 编排器模式

```python
# Orchestrator 协调多个 Agent
class CodeDevelopmentOrchestrator:
    def __init__(self, user_proxy, coder, reviewer, tester):
        self.user_proxy = user_proxy
        self.coder = coder
        self.reviewer = reviewer
        self.tester = tester
```

### 3. 单例模式

```python
# Config 单例
_config = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
```

### 4. 策略模式

```python
# 两种执行策略
orchestrator.execute_task()           # 自由对话
orchestrator.execute_sequential_workflow()  # 顺序执行
```

---

## 🔒 安全考虑

### 1. API Key 管理

- 使用 `.env` 文件存储
- `.env` 被 `.gitignore` 忽略
- 提供 `.env.example` 作为模板

### 2. 代码执行

- 默认不使用 Docker（`USE_DOCKER=false`）
- 代码在指定目录执行（`work_dir`）
- 可以启用 Docker 隔离

### 3. 输入验证

- Config 类验证必需参数
- CLI 参数解析和验证

---

## 🚀 性能优化

### 1. 连接复用

- LLM 客户端连接自动复用
- Agent 实例复用（通过 Orchestrator）

### 2. 对话历史管理

- 只保留必要的对话历史
- `clear_history` 参数控制是否清除

### 3. Token 控制

- `max_tokens` 限制响应长度
- `temperature` 控制随机性

---

## 📈 扩展方向

### 1. 添加新 Agent

```python
# 1. 创建新的 Agent 文件
# src/agents/optimizer.py

def create_optimizer(config):
    return AssistantAgent(
        name="optimizer",
        system_message="...",
        llm_config=config.get_llm_config(),
    )

# 2. 在 Orchestrator 中集成
# 3. 更新工作流程
```

### 2. 支持新的 LLM

```python
# 修改 Config.get_llm_config()
def get_llm_config(self):
    return {
        "model": self.model,
        "api_key": self.api_key,
        "base_url": self.api_base,  # 支持自定义 API 端点
        ...
    }
```

### 3. 添加新的执行模式

```python
# 在 Orchestrator 中添加新方法
def execute_parallel_workflow(self, task):
    """并行执行多个 Agent"""
    ...
```

---

## 📚 关键依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `pyautogen` | >=0.2.0 | 多 Agent 框架 |
| `openai` | >=1.0.0 | LLM API |
| `streamlit` | >=1.28.0 | Web 界面 |
| `pytest` | >=7.4.0 | 测试框架 |
| `rich` | >=13.0.0 | 终端美化 |

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
# 访问对话历史
orchestrator.execute_task(task)
history = orchestrator._get_conversation_history()
for msg in history:
    print(f"{msg['from']}: {msg['content']}")
```

### 3. 测试单个 Agent

```python
from src.agents import create_coder
from src.core import get_config

config = get_config()
coder = create_coder(config)
# 直接测试 Agent
```

---

本文档持续更新中...
