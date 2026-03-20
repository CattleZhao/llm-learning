# Day 1: LangGraph 基础 + 单个 Agent 实现

## 📚 学习目标

1. 理解 LangGraph 的核心概念
2. 掌握 StateGraph 的使用方法
3. 实现第一个 Agent：代码分析 Agent

---

## 🎯 LangGraph 核心概念

### 什么是 LangGraph？

LangGraph 是一个**状态机框架**，用于构建有状态的、多步骤的 LLM 应用。

```
传统 LangChain Chain:
输入 → 步骤1 → 步骤2 → 步骤3 → 输出
(线性执行，状态隐式传递)

LangGraph StateGraph:
    ┌─────┐
    │状态 │ ← 显式状态，可在任意节点读写
    └──┬──┘
       │
   ┌───┴────┬────────┬────────┐
   ↓        ↓        ↓        ↓
 节点1    节点2    节点3    节点4
   │        │        │        │
   └────────┴────────┴────────┘
       ↓
    输出
(图结构，状态共享，条件分支)
```

### 核心组件

| 组件 | 说明 | 代码示例 |
|------|------|---------|
| **State(状态)** | 在节点间共享的数据 | `class AgentState(TypedDict)` |
| **Node(节点)** | 处理函数，接收/修改状态 | `def my_node(state: AgentState) -> AgentState` |
| **Edge(边)** | 连接节点，定义执行流向 | `graph.add_edge("node_a", "node_b")` |
| **ConditionalEdge** | 基于条件的动态路由 | `graph.add_conditional_edges(...)` |

---

## 💡 State 详解

State 是 LangGraph 的核心，它是一个 TypedDict：

```python
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    # 普通字段：会被覆盖
    messages: list[str]

    # 聚合字段：会累加 (使用 Annotated)
    all_findings: Annotated[list[str], add]

    # 可选字段
    error: str | None
```

**关键点**：
- 不带 `Annotated` 的字段会被**覆盖**
- 带 `Annotated[...add]` 的字段会**累加**
- 节点函数返回的字典会**合并**到 state

---

## 🏗️ 基础图结构

```python
from langgraph.graph import StateGraph, END

# 1. 定义状态
class MyState(TypedDict):
    input: str
    output: str

# 2. 定义节点
def node_a(state: MyState) -> MyState:
    return {"output": f"Processed: {state['input']}"}

def node_b(state: MyState) -> MyState:
    return {"output": f"Final: {state['output']}"}

# 3. 构建图
graph = StateGraph(MyState)
graph.add_node("process", node_a)
graph.add_node("finalize", node_b)

# 4. 添加边
graph.set_entry_point("process")      # 入口点
graph.add_edge("process", "finalize") # 连接节点
graph.add_edge("finalize", END)       # 结束点

# 5. 编译并运行
app = graph.compile()
result = app.invoke({"input": "Hello"})
```

---

## 🚀 实战：代码分析 Agent

### 任务定义

创建一个 Agent，能够：
1. 读取 Python 代码文件
2. 分析代码结构（函数、类、复杂度）
3. 生成分析报告

### 实现步骤

1. **定义 State** - 存储代码和分析结果
2. **创建节点** - 代码分析逻辑
3. **构建图** - 连接节点
4. **运行测试** - 验证功能

---

## 📝 今日练习

- [ ] 创建 `src/utils/state.py` - 定义共享状态
- [ ] 创建 `src/utils/parser.py` - 代码解析工具
- [ ] 创建 `src/agents/code_analyzer.py` - 代码分析 Agent
- [ ] 创建 `src/main.py` - 程序入口
- [ ] 测试单个 Agent 功能

---

## 🎓 知识检查

1. State 中 `Annotated[list, add]` 的作用是什么？
2. 节点函数的返回值如何影响状态？
3. `set_entry_point` 和 `add_edge` 的区别？

---

**下一步**: Day 2 - 添加更多 Agent 并实现协作
