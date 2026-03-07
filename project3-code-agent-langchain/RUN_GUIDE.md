# LangChain 版本运行指南

## 环境准备

### 1. 安装依赖

```bash
cd /root/Learn/llm-learning/project3-code-agent-langchain

# 方式1: 使用 venv（推荐）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 方式2: 直接安装（需要 --break-system-packages）
pip install -r requirements.txt --break-system-packages
```

### 2. 配置 API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用 vim
```

填入你的 OpenAI API Key：
```
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4
```

---

## 运行方式

### 方式1: 交互模式

```bash
python run.py
# 或
python -m src.main
# 或
source venv/bin/activate && python run.py
```

进入交互模式后：
```
============================================================
  LangChain 代码助手 Agent
  基于 LangChain ReAct Agent 实现
============================================================

进入交互模式（输入 'exit' 或 'quit' 退出）

👤 用户: 分析 demo.py 的代码结构

🤖 Agent: [LangChain Agent 的回复]
```

**支持的问题示例**：
- "分析 examples/workspace/demo.py 的代码结构"
- "这个文件有多少个函数？"
- "列出所有的类和方法"
- "代码的复杂度如何？"

---

### 方式2: 单次查询模式

```bash
python run.py --query "分析 examples/workspace/demo.py 的代码结构"
# 或
python run.py -q "这个文件有多少个函数？"
```

---

### 方式3: 直接分析模式

```bash
python run.py --analyze examples/workspace/demo.py
# 或
python run.py -a examples/workspace/demo.py
```

输出示例：
```
分析文件: examples/workspace/demo.py

1. 代码结构分析
   函数数: 2
   类数: 1
   总行数: 31

2. 生成测试代码
   [生成的测试代码...]

3. 重构建议
   [重构建议...]

4. 质量评估
   分数: 85
   等级: 良好
```

---

### 方式4: 运行演示脚本

```bash
python examples/demo_langchain.py
```

演示脚本包含：
1. 工具列表展示
2. 直接调用模式演示
3. Agent 模式演示（需要 API Key）

---

## 运行测试

```bash
# 确保激活了虚拟环境（如果使用）
source venv/bin/activate

# 运行所有测试
pytest tests/test_langchain_agent.py -v

# 运行特定测试
pytest tests/test_langchain_agent.py::TestLangChainTools::test_tools_count -v
```

---

## 项目结构对比

### 与原项目的主要差异

```
原项目                          LangChain 版本
─────────────────────────────────────────────────
自研 ReAct 循环                 create_react_agent()
手动 ToolRegistry                @tool 装饰器
正则解析响应                     AgentExecutor 自动处理
手写 Prompt 模板                 hub.pull("hwchase17/react")
```

### 代码对比示例

**原项目 (自研 ReAct)**:
```python
# 400+ 行手写实现
for iteration in range(self.MAX_ITERATIONS):
    prompt = self.REACT_PROMPT_TEMPLATE.format(...)
    response = self.llm_client.generate(prompt)
    thought, action, action_input = self._parse_response(response)  # 正则解析
    observation = self._execute_action(action, action_input)
    history += ...
```

**LangChain 版本**:
```python
# 20 行配置
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, max_iterations=10)
result = executor.invoke({"input": user_input})
```

---

## 常见问题

### Q1: ModuleNotFoundError: No module named 'langchain'

**解决**:
```bash
# 确保安装了依赖
pip install langchain langchain-openai langchain-community
```

### Q2: OPENAI_API_KEY not found

**解决**:
```bash
# 检查 .env 文件是否存在
ls -la .env

# 确保填入了正确的 API Key
cat .env
```

### Q3: 如何调试？

**启用详细日志**:
```python
# 在 src/llm_client.py 中设置 verbose=True
llm = ChatOpenAI(..., verbose=True)
```

**查看 Agent 思考过程**:
```bash
# AgentExecutor 默认 verbose=True
# 会显示每一步的 Thought, Action, Observation
```

---

## 快速开始示例

```bash
# 1. 进入项目目录
cd /root/Learn/llm-learning/project3-code-agent-langchain

# 2. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env
nano .env  # 填入 OPENAI_API_KEY

# 4. 运行演示
python examples/demo_langchain.py

# 5. 运行交互模式
python run.py
```

---

## 与原项目切换

```bash
# 切换到原项目
cd ../project3-code-agent

# 切换到 LangChain 版本
cd ../project3-code-agent-langchain
```

对比两个项目的实现可以直观地看到 LangChain 如何简化 Agent 开发！
