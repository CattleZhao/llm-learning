# 使用指南

本文档详细介绍如何使用 Project 4 CrewAI 版本的多 Agent 代码开发系统。

## 目录

- [CLI 用法](#cli-用法)
- [Web UI 用法](#web-ui-用法)
- [输出目录说明](#输出目录说明)
- [常见使用场景](#常见使用场景)
- [故障排查](#故障排查)

## CLI 用法

### 基础用法

```bash
# 最简单的使用方式
python -m app.cli run --task "实现快速排序算法"
```

### 调试模式

```bash
# 启用详细输出，查看 Agent 思考过程
python -m app.cli run --task "实现二叉树遍历" --debug
```

### 查看版本信息

```bash
python -m app.cli version
```

### 命令行参数说明

| 参数 | 说明 | 必需 |
|-----|------|------|
| `--task` | 要实现的任务描述 | 是 |
| `--debug` | 启用调试模式，显示详细日志 | 否 |

## Web UI 用法

### 启动 Web 服务

```bash
streamlit run app/web.py
```

### 使用步骤

1. **启动服务**
   ```bash
   streamlit run app/web.py
   ```

2. **打开浏览器**
   - 访问 http://localhost:8501
   - 如果在远程服务器，使用端口转发

3. **输入任务描述**
   - 在文本框中输入你的需求
   - 例如："实现一个计算斐波那契数列的函数"

4. **执行任务**
   - 点击"执行任务"按钮
   - 等待 Agent 协作完成

5. **查看结果**
   - 左侧面板显示执行过程
   - 右侧面板显示最终代码

### Web UI 功能

- **实时进度显示**: 查看 Agent 工作进度
- **代码高亮**: 美化的代码展示
- **下载功能**: 下载生成的代码文件
- **历史记录**: 查看之前的执行结果

## 输出目录说明

生成的代码保存在 `outputs/` 目录，按时间戳组织：

```
outputs/
└── 20240310_143022/          # 时间戳目录
    ├── main.py               # 主程序代码
    ├── test_main.py          # 单元测试
    └── review.md             # 代码审查报告
```

### 输出文件说明

#### main.py
- Coder Agent 生成的主程序代码
- 包含完整的实现和注释

#### test_main.py
- Tester Agent 生成的测试代码
- 使用 pytest 框架
- 包含边界条件测试

#### review.md
- Reviewer Agent 的审查报告
- 包含代码质量评估
- 改进建议（如有）

## 常见使用场景

### 1. 算法实现

```bash
python -m app.cli run --task "实现快速排序算法，包含详细注释"
```

**预期输出**:
- 完整的快速排序实现
- 时间复杂度分析
- 使用示例

### 2. 数据处理

```bash
python -m app.cli run --task "创建一个读取 CSV 文件并计算平均值的脚本"
```

**预期输出**:
- CSV 读取代码
- 数据处理逻辑
- 错误处理

### 3. Web API 客户端

```bash
python -m app.cli run --task "实现调用 REST API 的客户端代码"
```

**预期输出**:
- HTTP 请求封装
- 错误处理
- 响应解析

### 4. 数据结构

```bash
python -m app.cli run --task "实现一个二叉搜索树类"
```

**预期输出**:
- BST 类定义
- 插入、查找、删除方法
- 测试用例

## 故障排查

### 问题 1: ImportError: No module named 'crewai'

**原因**: CrewAI 未安装

**解决方案**:
```bash
pip install crewai>=1.10.0
```

### 问题 2: API Key 错误

**原因**: 未设置 ANTHROPIC_API_KEY

**解决方案**:
```bash
# 方式 1: 设置环境变量
export ANTHROPIC_API_KEY=your_key_here

# 方式 2: 创建 .env 文件
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### 问题 3: Agent 响应超时

**原因**: 网络问题或 API 限流

**解决方案**:
- 检查网络连接
- 稍后重试
- 检查 API 配额

### 问题 4: 生成的代码有错误

**原因**: LLM 生成的不完美代码

**解决方案**:
- Reviewer Agent 会指出问题
- 可以重新运行
- 手动修复并提交反馈

### 问题 5: 内存不足

**原因**: 处理大型任务时内存占用高

**解决方案**:
- 分解任务为更小的子任务
- 使用更小的模型
- 增加系统内存

## 最佳实践

### 1. 任务描述要清晰

❌ 不好的例子:
```bash
python -m app.cli run --task "写代码"
```

✅ 好的例子:
```bash
python -m app.cli run --task "实现一个计算斐波那契数列的函数，要求使用递归和迭代两种方法，并包含时间复杂度分析"
```

### 2. 使用调试模式

遇到问题时启用调试模式：
```bash
python -m app.cli run --task "你的任务" --debug
```

### 3. 检查输出代码

生成的代码应该：
- 阅读 `review.md` 了解审查意见
- 运行测试验证功能
- 根据需要手动调整

### 4. 版本控制

将生成的代码纳入 Git：
```bash
cd outputs/20240310_143022
git add main.py test_main.py
git commit -m "Add: 快速排序实现"
```

## 高级用法

### 自定义 Agent 配置

编辑 `src/agents/` 中的文件，调整 Agent 行为：

```python
# 修改 Coder 的温度参数
def create_coder_agent():
    return Agent(
        role="高级工程师",
        goal="编写高质量 Python 代码",
        backstory="...",
        temperature=0.3,  # 降低随机性
        # ...
    )
```

### 添加自定义工具

在 `src/tools/` 创建新工具：

```python
from crewai_tools import tool

@tool("自定义工具")
def my_custom_tool(input: str) -> str:
    """工具描述"""
    # 实现逻辑
    return result
```

### 批量处理

创建脚本批量处理任务：

```python
# batch_process.py
from app.cli import run_task

tasks = [
    "实现快速排序",
    "实现归并排序",
    "实现堆排序",
]

for task in tasks:
    print(f"处理: {task}")
    run_task(task)
```

## 相关文档

- [README.md](../README.md) - 项目概览
- [API 文档](API.md) - API 参考
- [开发指南](DEVELOPMENT.md) - 贡献指南

## 获取帮助

- 查看 [CrewAI 文档](https://docs.crewai.com/)
- 提交 [Issue](https://github.com/your-repo/issues)
- 加入社区讨论
