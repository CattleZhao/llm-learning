# Project 4: Multi-Agent Code Development Team

> 学习 AutoGen 多 Agent 协作框架的项目

## 📖 项目简介

这是一个基于 AutoGen 框架的多 Agent 协作系统，模拟代码开发团队的工作流程。

## 🤖 Agent 角色

| Agent | 角色定位 | 主要职责 |
|-------|---------|---------|
| **UserProxy** | 协调者 | 接收用户需求、协调对话、执行代码、汇总结果 |
| **Coder** | 编码者 | 编写高质量 Python 代码，遵循最佳实践 |
| **Reviewer** | 审查者 | 检查代码质量、提出改进建议、确保符合规范 |
| **Tester** | 测试者 | 编写和执行测试用例，验证功能正确性 |

## 🚀 快速开始

### 安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 OPENAI_API_KEY
```

### 使用方式

#### 命令行界面

```bash
# 基础使用
python3 -m app.cli --task "实现一个快速排序算法"

# 使用自定义模型
python3 -m app.cli --task "创建一个 FastAPI REST API" --model gpt-4

# 顺序工作流模式（更可控）
python3 -m app.cli --task "写一个二分查找函数" --sequential

# 调试模式
python3 -m app.cli --task "实现一个链表" --debug
```

#### Web 界面

```bash
# 启动 Streamlit
streamlit run app/web.py

# 然后在浏览器中打开 http://localhost:8501
```

## 📝 使用示例

### 示例 1: 算法实现

```bash
python3 -m app.cli --task "实现一个带类型注解的快速排序算法"
```

**Agent 协作流程:**
1. UserProxy → Coder: "请实现快速排序"
2. Coder → UserProxy: 提供代码实现
3. UserProxy → Reviewer: "请审查这段代码"
4. Reviewer → UserProxy: 提供改进建议
5. UserProxy → Tester: "请编写测试"

### 示例 2: REST API

```bash
python3 -m app.cli --task "使用 FastAPI 创建一个 Todo CRUD API"
```

### 示例 3: 数据处理

```bash
python3 -m app.cli --task "写一个 Python 脚本读取 CSV 并计算统计数据"
```

## 📁 项目结构

```
project4-multiagent/
├── src/
│   ├── agents/              # Agent 实现
│   │   ├── user_proxy.py    # 协调者 Agent
│   │   ├── coder.py         # 编码者 Agent
│   │   ├── reviewer.py      # 审查者 Agent
│   │   └── tester.py        # 测试者 Agent
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   └── orchestrator.py  # 编排器
│   └── utils/
│       └── logger.py        # 日志工具
├── app/
│   ├── cli.py               # 命令行界面
│   └── web.py               # Streamlit Web 界面
├── tests/
│   ├── test_*.py            # 单元测试
│   └── integration/         # 集成测试
├── outputs/                 # 生成的代码
├── requirements.txt         # 依赖列表
├── .env.example             # 环境变量模板
└── README.md                # 项目文档
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并查看覆盖率
pytest tests/ --cov=src --cov-report=term-missing

# 跳过需要 API key 的集成测试
pytest tests/ -m "not integration"

# 只运行集成测试
pytest tests/ -m integration
```

## 📚 学习要点

通过这个项目，你将学习到：

- ✅ **AutoGen 框架**: 理解 Agent、对话、代码执行等核心概念
- ✅ **多 Agent 协作**: 学习如何设计多个协同工作的 Agent
- ✅ **System Message 设计**: 掌握如何编写有效的系统提示词
- ✅ **编排模式**: 理解如何协调和控制 Agent 之间的交互
- ✅ **代码执行安全**: 学习如何在沙箱环境中执行生成的代码
- ✅ **用户界面**: 构建命令行和 Web 两种交互方式

## 🔧 配置说明

在 `.env` 文件中可配置以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 必填 |
| `OPENAI_MODEL` | 使用的模型 | `gpt-4o` |
| `TEMPERATURE` | LLM 温度参数 | `0.7` |
| `MAX_TOKENS` | 最大 token 数 | `2000` |
| `USE_DOCKER` | 是否使用 Docker 执行代码 | `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 🐛 故障排除

### "OPENAI_API_KEY is required"

**解决方案**: 确保在 `.env` 文件中设置了有效的 API key

```bash
cp .env.example .env
# 编辑 .env 文件，添加 OPENAI_API_KEY=sk-...
```

### 代码执行失败

**解决方案**: 确保 `outputs/` 目录存在且可写

```bash
mkdir -p outputs
chmod +w outputs
```

### 模块导入错误

**解决方案**: 确保在项目根目录运行命令

```bash
cd project4-multiagent
python3 -m app.cli --help
```

### AutoGen 相关错误

**解决方案**: 检查 AutoGen 版本

```bash
pip show pyautogen
# 如果版本过旧，重新安装
pip install --upgrade pyautogen
```

## 🔄 下一步扩展

- [ ] **CrewAI 版本**: 使用 CrewAI 实现相同功能进行对比学习
- [ ] **更多 Agent**: 添加文档撰写者、性能优化者等角色
- [ ] **Git 集成**: 支持 Git 操作，自动提交代码
- [ ] **项目支持**: 支持多文件项目的开发
- [ ] **代码重构**: 添加自动重构建议功能

## 📖 相关资源

### 项目文档

- 📘 [运行说明](docs/RUN_GUIDE.md) - 详细的安装和运行指南
- 📗 [技术实现说明](docs/TECHNICAL_GUIDE.md) - 架构和实现细节

### 外部资源

- [AutoGen 官方文档](https://github.com/microsoft/autogen)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [Streamlit 文档](https://docs.streamlit.io)

## 📝 许可证

MIT
