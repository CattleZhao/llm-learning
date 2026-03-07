# 项目3：代码助手Agent

> 基于ReAct框架的智能代码分析Agent

## 功能

- 🔍 代码结构分析
- 🧪 自动生成测试
- 💡 重构建议
- 📊 代码质量评估

## 技术栈

- LangChain Agent: 框架
- ReAct: 推理+行动循环
- AST: 代码解析
- Git: 版本控制集成

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API key

# 3. 运行（任选一种方式）

# 方式1：使用 run.py（推荐）
python run.py

# 方式2：使用模块方式
python -m src.main

# 方式3：指定工作目录
python run.py --workspace ./your-project
```

## 使用

```bash
# 推荐方式
python run.py

# 或使用模块方式
python -m src.main
```
