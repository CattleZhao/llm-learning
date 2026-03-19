# Project 7: Agent Skills 设计模式实践

> 基于 Google Skills.md 标准的 5 种 Agent 设计模式实现

## 项目简介

这是一个**教学性质的项目**，用于演示如何正确设计和实现 Agent Skills。

参考文章：[Agent Skills 的 5 种设计模式](https://twitter.com/GoogleCloudTech/status/2033953579824758855)

## 5 种设计模式

| 模式 | 用途 | 示例场景 |
|------|------|---------|
| **Tool Wrapper** | 让 Agent 成为特定库的专家 | FastAPI 最佳实践、Django 规范 |
| **Generator** | 生成结构化文档 | 技术报告、API 文档、PR 模板 |
| **Reviewer** | 代码审查和评分 | 代码质量检查、安全审计 |
| **Inversion** | 需求收集（Agent 采访用户） | 项目规划、需求分析 |
| **Pipeline** | 多步骤工作流 | 文档生成、代码重构流程 |

## 项目结构

```
project7-agent-skills/
├── skills/                    # Skills 目录
│   ├── __init__.py
│   ├── base.py               # Skill 基类
│   ├── registry.py           # Skill 注册中心
│   │
│   ├── tool-wrapper/         # 模式1: Tool Wrapper 示例
│   │   └── fastapi-expert/
│   │
│   ├── generator/            # 模式2: Generator 示例
│   │   └── report-generator/
│   │
│   ├── reviewer/             # 模式3: Reviewer 示例
│   │   └── code-reviewer/
│   │
│   ├── inversion/            # 模式4: Inversion 示例
│   │   └── project-planner/
│   │
│   └── pipeline/             # 模式5: Pipeline 示例
│       └── doc-pipeline/
│
├── agents/                   # Agent 实现
│   └── skills_agent.py       # 支持 Skills 的 Agent
│
├── cli.py                    # 命令行入口
├── config.py                 # 配置管理
├── requirements.txt          # 依赖
└── README.md
```

## Skill 结构规范

每个 Skill 目录遵循以下结构：

```
skill-name/
├── SKILL.md                  # Skill 元数据 + 核心指令
├── assets/                   # 可选：模板、静态资源
├── references/               # 可选：参考文档、知识库
└── tests/                    # 可选：测试用例
```

### SKILL.md 格式

```yaml
---
name: skill-name
description: 简短描述
metadata:
  pattern: tool-wrapper|generator|reviewer|inversion|pipeline
  domain: 技术领域
---

# 核心指令

Agent 的具体行为指令...
```

## 快速开始

### 1. 安装依赖

```bash
cd project7-agent-skills
pip install -r requirements.txt
```

### 2. 运行演示

```bash
# 演示 Tool Wrapper 模式
python cli.py --pattern tool-wrapper --demo fastapi

# 演示 Generator 模式
python cli.py --pattern generator --demo report

# 演示 Reviewer 模式
python cli.py --pattern reviewer --demo code

# 演示 Inversion 模式
python cli.py --pattern inversion --demo plan

# 演示 Pipeline 模式
python cli.py --pattern pipeline --demo docs
```

### 3. 交互模式

```bash
python cli.py --interactive
```

## 技术栈

- **LLM**: Anthropic Claude API
- **格式**: Skills.md 开放标准
- **Python**: 3.9+

## 学习目标

通过这个项目，你将学会：

1. ✅ 如何设计 Tool Wrapper Skills
2. ✅ 如何设计 Generator Skills
3. ✅ 如何设计 Reviewer Skills
4. ✅ 如何设计 Inversion Skills
5. ✅ 如何设计 Pipeline Skills
6. ✅ 如何组合多种模式
7. ✅ Skills 与 Agent 的集成方式

## 与 Project 6 的关系

| 项目 | 目标 | 状态 |
|------|------|------|
| **Project 6** | APK 恶意分析（实际应用） | ✅ 完成 |
| **Project 7** | Skills 模式教学（最佳实践） | 🚧 进行中 |

Project 7 可以作为 Project 6 重构的参考。

## License

MIT
