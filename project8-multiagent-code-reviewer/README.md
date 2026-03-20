# Project 8: 智能代码审查与重构助手系统

> **学习目标**: 掌握 LangGraph 多子Agent协作开发模式

## 📋 项目概述

构建一个基于 LangGraph 的多Agent协作系统，对代码库进行多维度分析并生成改进报告。

## 🏗️ 系统架构

```
                    ┌─────────────────┐
                    │   主控 Agent    │
                    │  (Orchestrator) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ↓            ↓            ↓            ↓
┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ 代码分析  │ │ 安全审查 │ │ 性能优化 │ │ 风格检查 │
│   Agent   │ │  Agent   │ │  Agent   │ │  Agent   │
└───────────┘ └──────────┘ └──────────┘ └──────────┘
```

## 🤖 子Agent角色

| Agent | 职责 |
|-------|------|
| **代码分析 Agent** | 分析代码结构、复杂度、依赖关系 |
| **安全审查 Agent** | 检测安全漏洞、敏感信息泄露 |
| **性能优化 Agent** | 识别性能瓶颈、提供优化建议 |
| **风格检查 Agent** | 检查代码规范、命名风格 |
| **主控 Agent** | 协调各子Agent，聚合分析报告 |

## 📁 项目结构

```
project8-multiagent-code-reviewer/
├── src/
│   ├── agents/              # 各个子Agent实现
│   │   ├── code_analyzer.py
│   │   ├── security_auditor.py
│   │   ├── performance_optimizer.py
│   │   └── style_checker.py
│   ├── orchestrator/        # 主控层
│   │   └── coordinator.py
│   ├── utils/               # 工具函数
│   │   ├── state.py         # 共享状态定义
│   │   └── parser.py        # 代码解析工具
│   └── main.py              # 程序入口
├── tests/                   # 测试文件
├── examples/                # 示例代码供测试
├── docs/                    # 学习笔记
└── requirements.txt         # 依赖
```

## 🛠️ 技术栈

- **Python 3.10+**
- **LangGraph** - 多Agent编排
- **LangChain** - LLM集成
- **Anthropic Claude** - 模型能力

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API Key
cp .env.example .env
# 编辑 .env 文件，填入 ANTHROPIC_API_KEY

# 运行
python src/main.py --path examples/sample_code.py
```

## 📚 学习路径

| 阶段 | 主题 | 文件 |
|------|------|------|
| Day 1 | LangGraph基础 + 单Agent | `docs/day01-langgraph-basics.md` |
| Day 2 | 多Agent协作 + 状态共享 | `docs/day02-multiagent.md` |
| Day 3 | Agent间通信 + 结果聚合 | `docs/day03-communication.md` |
| Day 4 | 主控层设计 + 报告生成 | `docs/day04-orchestration.md` |
| Day 5 | 测试 + 优化 | `docs/day05-testing.md` |

## 🎯 核心学习点

1. **LangGraph StateGraph** - 如何定义和传递状态
2. **Agent节点** - 如何创建独立的分析节点
3. **边和条件边** - 如何控制Agent间的执行流程
4. **并行执行** - 如何让多个Agent同时工作
5. **错误处理** - 如何处理Agent执行失败

## 📝 进度跟踪

- [x] 项目初始化
- [ ] Day 1: 单个Agent实现
- [ ] Day 2: 多Agent协作
- [ ] Day 3: 状态管理
- [ ] Day 4: 主控层
- [ ] Day 5: 测试与优化

---

**开始时间**: 2026-03-20
