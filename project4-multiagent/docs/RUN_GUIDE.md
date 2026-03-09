# 运行说明

## 环境要求

- Python 3.10 或更高版本
- pip (Python 包管理器)
- OpenAI API Key

---

## 安装步骤

### 1. 克隆/进入项目目录

```bash
cd /root/Learn/llm-learning/project4-multiagent
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

**依赖列表：**
- `pyautogen` - AutoGen 多 Agent 框架
- `openai` - OpenAI API 客户端
- `python-dotenv` - 环境变量管理
- `streamlit` - Web 界面框架
- `pytest` - 测试框架
- `rich` - 彩色终端输出

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的 API Key：

```bash
# 必填：OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here

# 可选：其他配置
OPENAI_MODEL=gpt-4o
TEMPERATURE=0.7
MAX_TOKENS=2000
```

---

## 运行方式

### 方式 1: 命令行界面 (CLI)

#### 基础用法

```bash
python3 -m app.cli --task "你的任务描述"
```

#### 完整示例

```bash
# 实现快速排序
python3 -m app.cli --task "实现一个带类型注解的快速排序算法"

# 创建 REST API
python3 -m app.cli --task "使用 FastAPI 创建一个 Todo CRUD API"

# 数据处理脚本
python3 -m app.cli --task "写一个 Python 脚本读取 CSV 并计算统计数据"
```

#### 高级选项

```bash
# 使用特定模型
python3 -m app.cli --task "实现二分查找" --model gpt-4

# 调整温度参数（越高越随机）
python3 -m app.cli --task "写一个创意函数" --temperature 0.9

# 顺序工作流模式（更可控）
python3 -m app.cli --task "实现链表" --sequential

# 调试模式（显示详细日志）
python3 -m app.cli --task "实现栈" --debug
```

#### CLI 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--task` | 任务描述（必填） | - |
| `--model` | 使用的模型 | gpt-4o |
| `--temperature` | 温度参数 (0-2) | 0.7 |
| `--max-tokens` | 最大 token 数 | 2000 |
| `--sequential` | 使用顺序工作流 | False |
| `--debug` | 调试模式 | False |

---

### 方式 2: Web 界面

#### 启动 Web 服务

```bash
streamlit run app/web.py
```

#### 访问界面

打开浏览器访问：`http://localhost:8501`

#### Web 界面功能

| 功能区域 | 说明 |
|----------|------|
| **侧边栏** | 模型设置、Agent 团队介绍 |
| **任务输入** | 输入你的代码需求 |
| **执行模式** | 选择执行方式 |
| **对话历史** | 实时查看 Agent 协作过程 |
| **执行结果** | 查看最终结果和状态 |

#### Web 界面操作流程

1. 在侧边栏配置模型参数
2. 在主界面输入任务描述
3. 选择执行模式（从 Coder 开始 / 顺序工作流）
4. 点击 "执行任务" 按钮
5. 实时查看 Agent 对话过程
6. 查看最终执行结果

---

## 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行测试并查看覆盖率

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### 只运行单元测试（不需要 API Key）

```bash
pytest tests/ -m "not integration"
```

### 只运行集成测试（需要 API Key）

```bash
pytest tests/ -m integration
```

---

## 常见问题

### Q1: 提示 "OPENAI_API_KEY is required"

**解决方法：**

```bash
# 检查 .env 文件是否存在
cat .env

# 确保 API Key 已设置
grep OPENAI_API_KEY .env
```

### Q2: 提示模块未找到

**解决方法：**

```bash
# 确保在项目根目录
pwd
# 应该显示: .../project4-multiagent

# 确保虚拟环境已激活
which python
# 应该显示: .../venv/bin/python

# 重新安装依赖
pip install -r requirements.txt
```

### Q3: Streamlit 无法启动

**解决方法：**

```bash
# 检查 Streamlit 是否安装
pip show streamlit

# 重新安装
pip install --upgrade streamlit

# 检查端口是否被占用
lsof -i :8501
```

### Q4: 代码执行失败

**解决方法：**

```bash
# 确保 outputs 目录存在且可写
mkdir -p outputs
chmod +w outputs

# 检查磁盘空间
df -h
```

### Q5: Agent 对话卡住

**解决方法：**

```bash
# 使用 Ctrl+C 中断
# 使用 --sequential 模式更可控
python3 -m app.cli --task "你的任务" --sequential

# 减少 max_consecutive_auto_reply（在 .env 中）
echo "MAX_CONSECUTIVE_AUTO_REPLY=5" >> .env
```

---

## 输出文件

生成的代码和执行结果会保存在 `outputs/` 目录：

```
outputs/
├── *.py              # 生成的 Python 代码
├── logs/             # 执行日志
└── ...               # 其他输出文件
```

---

## 停止运行

### 停止 CLI

按 `Ctrl+C` 中断执行

### 停止 Web 界面

在终端按 `Ctrl+C`

---

## 下一步

运行成功后，你可以：

1. 尝试不同的任务描述
2. 调整模型参数观察效果
3. 查看 `outputs/` 目录生成的代码
4. 阅读技术实现文档了解原理
5. 修改 Agent 的 System Message 自定义行为

---

## 获取帮助

如果遇到问题：

1. 查看本文档的"常见问题"部分
2. 使用 `--debug` 模式查看详细日志
3. 查看项目 README.md
4. 查看 AutoGen 官方文档：https://github.com/microsoft/autogen
