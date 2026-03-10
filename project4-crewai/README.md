# Project 4: Multi-Agent Code Development Team (CrewAI Version)

> 使用 CrewAI 框架实现的多 Agent 协作系统

[![CrewAI](https://img.shields.io/badge/CrewAI-0.80.0-blue)](https://www.crewai.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)

## 项目简介

这是 Project 4 的 CrewAI 实现版本，与 [AutoGen 版本](../project4-multiagent/) 进行对比学习。

本项目展示如何使用 CrewAI 框架构建一个多 Agent 协作系统，实现自动化的代码开发流程。系统包含四个专门的 Agent，各自承担不同的角色和职责，通过协作完成从需求分析到代码测试的完整开发流程。

## Agent 角色

| Agent | 角色定位 | 主要职责 |
|-------|---------|---------|
| **Coordinator** | 项目经理 | 协调任务流程，分配任务，汇总结果 |
| **Coder** | 高级工程师 | 编写高质量 Python 代码 |
| **Reviewer** | 代码审查专家 | 检查代码质量，提出改进建议 |
| **Tester** | 测试工程师 | 编写和执行测试用例 |

## 系统架构

```
用户输入任务
    ↓
Coordinator (分析任务)
    ↓
Coder (编写代码)
    ↓
Reviewer (代码审查)
    ↓
Tester (编写测试)
    ↓
Coordinator (汇总结果)
    ↓
输出最终代码
```

## 快速开始

### 安装

```bash
cd /root/Learn/llm-learning/project4-crewai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 文件，添加 ANTHROPIC_API_KEY
```

环境变量配置示例：
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### 使用方法

#### CLI 模式

```bash
# 基础用法
python -m app.cli run --task "实现快速排序算法"

# 调试模式
python -m app.cli run --task "实现二叉树遍历" --debug

# 查看版本
python -m app.cli version
```

#### Web UI 模式

```bash
# 启动 Web 服务
streamlit run app/web.py

# 访问 http://localhost:8501
```

## 项目结构

```
project4-crewai/
├── app/                    # 应用入口
│   ├── cli.py             # CLI 接口
│   └── web.py             # Web UI
├── src/
│   ├── agents/            # Agent 定义
│   │   ├── coordinator.py
│   │   ├── coder.py
│   │   ├── reviewer.py
│   │   └── tester.py
│   ├── crews/             # Crew 组合
│   │   └── code_crew.py
│   ├── tasks/             # Task 定义
│   │   ├── coding_task.py
│   │   ├── review_task.py
│   │   ├── testing_task.py
│   │   └── final_task.py
│   └── tools/             # 工具函数
│       ├── file_writer.py
│       └── code_executor.py
├── tests/                 # 测试套件
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── fixtures/         # 测试数据
├── outputs/              # 生成的代码输出
├── docs/                 # 文档
├── requirements.txt      # 依赖列表
└── README.md            # 本文件
```

## 测试

### 运行单元测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定测试文件
pytest tests/unit/test_coder.py -v

# 运行测试并显示覆盖率
pytest tests/unit/ -v --cov=src
```

### 运行集成测试

```bash
# 运行集成测试（需要 API key）
pytest tests/integration/ -v -m integration

# 只运行单元测试（跳过集成测试）
pytest tests/ -v -m "not integration"
```

### 测试标记说明

- `@pytest.mark.integration`: 需要 API key 的集成测试
- `@pytest.mark.unit`: 单元测试（不需要 API key）

## 输出目录

生成的代码保存在 `outputs/` 目录，按时间戳组织：

```
outputs/
└── YYYYMMDD_HHMMSS/
    ├── main.py          # 主程序代码
    ├── test_main.py     # 测试代码
    └── review.md        # 代码审查报告
```

## 技术栈

- **CrewAI** - 多 Agent 编排框架
- **LangChain** - LLM 集成
- **Anthropic Claude** - LLM 提供商
- **Streamlit** - Web 界面
- **Typer** - CLI 框架
- **Pytest** - 测试框架

## 开发指南

### 添加新的 Agent

1. 在 `src/agents/` 创建新的 Agent 文件
2. 实现 `create_*_agent()` 函数
3. 在 `CodeDevelopmentCrew` 中注册新 Agent
4. 添加对应的 Task
5. 编写单元测试

### 扩展功能

- 添加新的 Tools（工具函数）
- 自定义 LLM 模型
- 集成其他代码质量工具（如 pylint, mypy）
- 添加代码格式化功能

## 与 AutoGen 版本的对比

| 特性 | CrewAI 版本 | AutoGen 版本 |
|-----|------------|-------------|
| 框架 | CrewAI | AutoGen |
| Agent 定义 | 声明式 | 编程式 |
| 任务编排 | Process 类 | 手动编排 |
| 工具集成 | Tool 装饰器 | 函数注册 |
| 学习曲线 | 较平缓 | 较陡峭 |

## 常见问题

### Q: 如何获取 Anthropic API Key？

A: 访问 [Anthropic Console](https://console.anthropic.com/) 创建 API Key。

### Q: 支持其他 LLM 提供商吗？

A: 是的，修改 `src/config/llm_setup.py` 即可切换到其他提供商。

### Q: 如何调试 Agent 行为？

A: 使用 `--debug` 标志运行 CLI，或在代码中设置 `verbose=True`。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关资源

- [CrewAI 官方文档](https://docs.crewai.com/)
- [Anthropic Claude 文档](https://docs.anthropic.com/)
- [LangChain 文档](https://python.langchain.com/)
