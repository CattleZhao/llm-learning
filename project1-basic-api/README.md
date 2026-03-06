# 项目1：大模型基础API应用

> 学习大模型API调用和Prompt Engineering的基础项目

## 功能

- **问答 (Q&A)**: 简单Q&A对话，支持上下文
- **文档摘要**: 长文本摘要生成，可指定长度
- **结构化输出**: 从文本中提取结构化信息（JSON格式）

## 技术要点

- ✅ LLM API调用（OpenAI/Claude/GLM）
- ✅ Prompt Engineering基础
- ✅ 温度和Token参数控制
- ✅ 结构化输出处理

## 安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑.env文件，填入你的API密钥
```

## 使用

```bash
# 方式1: 直接运行
python -m src.main

# 方式2: 激活虚拟环境后运行
source venv/bin/activate
python -m src.main
```

## 测试

```bash
# 运行所有测试
PYTHONPATH=. pytest tests/ -v

# 运行特定测试
PYTHONPATH=. pytest tests/test_qa_module.py -v
```

## 项目结构

```
project1-basic-api/
├── src/
│   ├── __init__.py
│   ├── llm_client.py         # LLM客户端基类
│   ├── qa_module.py          # 问答模块
│   ├── summary_module.py     # 摘要模块
│   ├── structured_output.py  # 结构化输出模块
│   └── main.py               # CLI主程序
├── tests/                    # 测试文件
├── .env                      # API密钥配置
├── .env.example             # 配置模板
├── requirements.txt         # Python依赖
└── README.md
```

## 学习笔记

### Prompt技巧
- **角色设定**: 明确告诉AI它的角色
- **示例引导**: 提供示例帮助理解
- **思维链**: 引导AI逐步推理
- **长度控制**: 明确指定输出长度

### 参数影响
- `temperature`: 0=确定性输出，1=更随机
- `max_tokens`: 控制输出长度
- `模型选择`: gpt-4o-mini（便宜快速）vs gpt-4o（更智能）

### 支持的大模型

| 提供商 | 标识 | 环境变量 | 说明 |
|--------|------|----------|------|
| OpenAI | `openai` | `OPENAI_API_KEY` | GPT模型 |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | Claude模型 |
| 智谱AI | `glm`, `zhipu`, `zhipuai` | `ZHIPUAI_API_KEY` | GLM模型 |

## 下一步

完成此项目后，可以继续学习：
- **项目2**: RAG知识库问答系统
- **项目3**: 代码助手Agent
