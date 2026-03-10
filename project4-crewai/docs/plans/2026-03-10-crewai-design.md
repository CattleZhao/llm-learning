# Project 4 CrewAI 实现设计文档

**项目名称**: project4-crewai
**创建日期**: 2026-03-10
**目的**: 使用 CrewAI 框架重新实现 project4 的多 Agent 代码开发团队功能

---

## 1. 概述

本项目是基于 CrewAI 框架的多 Agent 协作系统，模拟代码开发团队的工作流程。作为 project4-multiagent (AutoGen 版本) 的对比实现，使用 Anthropic Claude 作为 LLM 提供商。

### 1.1 目标

- 提供与 AutoGen 版本相同的功能体验
- 使用 CrewAI 和 LangChain 生态系统
- 支持 Anthropic Claude 原生 API
- 作为学习不同多 Agent 框架的对比参考

---

## 2. 架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
├─────────────────────────────────────────────────────────────┤
│  CLI (app/cli.py)          │   Web (app/web.py)             │
│  - argparse/typer          │   - Streamlit 界面             │
│  - 任务执行                 │   - 实时对话显示               │
│  - 结果展示                 │   - 配置管理                   │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      Crew 层                                 │
├─────────────────────────────────────────────────────────────┤
│  CodeDevelopmentCrew (src/crews/code_crew.py)              │
│  - 创建和管理 4 个 Agent                                     │
│  - 定义 Agent 之间的关系和工作流                             │
│  - 启动 Crew 执行任务                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                       Agent 层                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Coder       │  │  Reviewer    │  │   Tester     │     │
│  │  (编码者)    │  │  (审查者)    │  │  (测试者)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐                                          │
│  │  Coordinator │                                          │
│  │  (协调者)    │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                     Task & Tools 层                          │
├─────────────────────────────────────────────────────────────┤
│  Tasks (src/tasks/)          │  Tools (src/tools/)          │
│  - coding_task.py            │  - code_executor.py          │
│  - review_task.py            │  - file_writer.py            │
│  - testing_task.py           │  - code_analyzer.py          │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      基础设施层                              │
├─────────────────────────────────────────────────────────────┤
│  Config (src/core/config.py)   │  Logger (src/utils/)      │
│  - 环境变量管理                 │  - 日志输出                │
│  - Anthropic/LangChain 配置    │  - 彩色格式化              │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    外部服务层                                │
├─────────────────────────────────────────────────────────────┤
│  CrewAI  │  LangChain  │  Anthropic API  │  文件系统        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 与 AutoGen 版本的差异

| 特性 | AutoGen | CrewAI |
|------|---------|--------|
| 对话机制 | `initiate_chat()` / `run()` | `crew.kickoff()` |
| Agent 交互 | 对话历史 | Tasks + Tools |
| 流程控制 | 内置对话循环 | Sequential/Hierarchical Process |
| LLM 集成 | 直接配置 | 通过 LangChain |

---

## 3. 组件设计

### 3.1 Agent 定义

所有 Agent 位于 `src/agents/` 目录：

| Agent | CrewAI 类型 | 职责 | 关键属性 |
|-------|-------------|------|---------|
| **Coordinator** | `Agent` | 协调任务流程，分配任务给其他 Agent | `role="项目经理"`, `goal="确保代码高质量交付"` |
| **Coder** | `Agent` | 编写 Python 代码 | `role="高级工程师"`, `goal="编写符合最佳实践的代码"` |
| **Reviewer** | `Agent` | 审查代码质量 | `role="代码审查专家"`, `goal="确保代码符合规范"` |
| **Tester** | `Agent` | 编写和执行测试 | `role="测试工程师"`, `goal="确保代码功能正确"` |

### 3.2 Task 定义

Tasks 位于 `src/tasks/` 目录：

| Task | 描述 | 期望输出 | 依赖 |
|------|------|---------|------|
| **coding_task** | 根据 User 需求编写代码 | Python 代码文件路径 | 无 |
| **review_task** | 审查 Coder 产生的代码 | 审查报告 + 改进建议 | coding_task |
| **testing_task** | 编写测试并执行 | 测试结果报告 | review_task |
| **final_task** | 汇总最终结果 | 完整交付物 | testing_task |

### 3.3 Tools

Tools 位于 `src/tools/` 目录：

| Tool | 功能 | 实现 |
|------|------|------|
| **CodeExecutor** | 在沙箱中执行 Python 代码 | 使用 `subprocess` + 临时目录 |
| **FileWriter** | 将代码写入文件 | 标准 Python 文件操作 |
| **CodeAnalyzer** | 静态分析代码 | 可选：集成 `ruff` 或 `pylint` |

### 3.4 核心 Crew

```python
class CodeDevelopmentCrew:
    def __init__(self):
        self.agents = [coordinator, coder, reviewer, tester]
        self.tasks = [coding, review, testing, final]
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # 或 hierarchical
            verbose=True
        )

    def kickoff(self, task_description: str) -> CrewOutput:
        return self.crew.kickoff(inputs={"task": task_description})
```

---

## 4. 数据流设计

### 4.1 执行流程

```
User 输入任务
    │
    ▼
CLI / Web UI 解析
    │
    ▼
CodeDevelopmentCrew.kickoff()
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  CrewAI Process (Sequential)                                │
├─────────────────────────────────────────────────────────────┤
│  Step 1: Coder Agent                                        │
│    → FileWriter Tool → outputs/solution.py                  │
│                                                             │
│  Step 2: Reviewer Agent                                     │
│    → 分析代码 → 审查报告                                     │
│                                                             │
│  Step 3: Tester Agent                                       │
│    → CodeExecutor Tool → 运行测试 → 测试结果                │
│                                                             │
│  Step 4: Coordinator Agent                                  │
│    → 汇总结果 → 最终交付文档                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
返回结果给用户
```

### 4.2 数据流转格式

| 阶段 | CrewOutput 包含 |
|------|----------------|
| **coding_task** | `{"code": "...", "file_path": "outputs/solution.py"}` |
| **review_task** | `{"review_comments": "...", "approval": true/false}` |
| **testing_task** | `{"test_results": "...", "tests_passed": true/false}` |
| **final_task** | `{"summary": "...", "deliverables": [...]}` |

---

## 5. 错误处理

### 5.1 错误分类与处理策略

| 错误类型 | 示例 | 处理策略 |
|---------|------|---------|
| **API 错误** | Anthropic API 限流/超时 | 重试机制 (指数退避)，降级到备选模型 |
| **代码执行错误** | 代码语法错误/运行时异常 | 捕获输出 → 反馈给 Coder Agent 重新修改 |
| **文件系统错误** | 无法写入 outputs/ | 预创建目录，检查权限，优雅降级 |
| **超时错误** | Agent 响应时间过长 | 设置 Crew 级别超时，返回部分结果 |
| **验证失败** | 测试未通过 | 自动触发修复流程 → Tester → Coder 循环 |

### 5.2 代码执行沙箱

```python
def execute_code_safely(code: str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = Path(tmpdir) / "solution.py"
        code_file.write_text(code)

        result = subprocess.run(
            ["python", str(code_file)],
            capture_output=True,
            timeout=30,
            cwd=tmpdir
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
```

---

## 6. 测试策略

### 6.1 测试目录结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_agents.py       # Agent 配置测试
│   ├── test_tasks.py        # Task 定义测试
│   ├── test_tools.py        # Tool 功能测试
│   └── test_config.py       # 配置管理测试
│
├── integration/             # 集成测试
│   ├── test_crew_flow.py    # Crew 执行流程测试
│   └── test_end_to_end.py   # 端到端测试 (需要 API)
│
└── fixtures/                # 测试数据
    └── sample_tasks.yaml    # 示例任务
```

### 6.2 测试覆盖目标

| 组件 | 覆盖目标 |
|------|---------|
| Config | 100% |
| Tools | 90%+ |
| Agents | 80%+ |
| Crew | 70%+ |

### 6.3 Mock 策略

单元测试使用 Mock 避免 API 调用：

```python
@pytest.fixture
def mock_llm():
    with patch('langchain_anthropic.ChatAnthropic') as mock:
        mock.return_value.invoke.return_value = AIMessage(
            content='```python\ndef solution():\n    return True\n```'
        )
        yield mock
```

---

## 7. 项目目录结构

```
project4-crewai/
├── src/
│   ├── agents/              # Agent 定义
│   │   ├── __init__.py
│   │   ├── coordinator.py
│   │   ├── coder.py
│   │   ├── reviewer.py
│   │   └── tester.py
│   ├── crews/               # Crew 组装
│   │   ├── __init__.py
│   │   └── code_crew.py
│   ├── tasks/               # Task 定义
│   │   ├── __init__.py
│   │   ├── coding_task.py
│   │   ├── review_task.py
│   │   └── testing_task.py
│   ├── tools/               # 工具函数
│   │   ├── __init__.py
│   │   ├── code_executor.py
│   │   └── file_writer.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   └── llm_setup.py     # LangChain LLM 配置
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── app/
│   ├── cli.py               # 命令行界面
│   └── web.py               # Streamlit Web 界面
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── outputs/                 # 生成的代码
├── docs/
│   └── plans/
│       └── 2026-03-10-crewai-design.md
├── requirements.txt
├── .env.example
└── README.md
```

---

## 8. 依赖清单

```txt
# Core Framework
crewai==0.80.0
langchain>=0.3.0
langchain-anthropic>=0.2.0

# LLM Provider
anthropic>=0.40.0

# Web UI
streamlit>=1.28.0

# CLI
typer>=0.12.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Utilities
python-dotenv>=1.0.0
rich>=13.0.0
tenacity>=8.2.0  # Retry mechanism
```

---

## 9. 配置说明

### 9.1 环境变量

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxx

# 模型配置
ANTHROPIC_MODEL=claude-sonnet-4-20250514
TEMPERATURE=0.7
MAX_TOKENS=2000

# 代码执行
CODE_EXECUTION_WORK_DIR=./outputs

# 日志
LOG_LEVEL=INFO
```

---

## 10. 实现计划

下一步将创建详细的实现计划，包括：

1. 项目脚手架搭建
2. 配置和基础设施
3. Tools 实现
4. Agents 实现
5. Tasks 实现
6. Crew 组装
7. CLI 和 Web UI
8. 测试
9. 文档完善

---

**文档状态**: ✅ 已批准
**下一步**: 调用 writing-plans 技能创建实现计划
