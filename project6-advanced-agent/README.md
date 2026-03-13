# Project 6: APK 恶意行为分析 Agent

> 基于 MCP 和高级 Agent 技术的 APK 恶意软件检测系统

## 项目简介

使用 MCP (Model Context Protocol) 连接 JADX 反编译工具，结合自定义恶意特征规则库和自我反思机制，自动化检测 Android APK 中的恶意行为。

## 核心功能

- 🔍 **MCP 工具调用** - 通过 MCP 调用 JADX 反编译 APK
- 📋 **自定义规则库** - 支持正则表达式包路径匹配
- 🧠 **恶意模式记忆** - 存储已知恶意软件特征
- 🤔 **自我反思** - 确保分析完整性
- 📊 **结构化报告** - 生成详细安全分析报告

## 检测维度

| 维度 | 检测方法 | 规则来源 |
|------|----------|----------|
| 权限分析 | 危险权限组合检测 | 内置规则 + 自定义 |
| 网络通信 | 恶意域名、C2 服务器 | URL 黑名单规则 |
| 包路径 | 恶意包路径模式 | 正则表达式规则 |
| API 调用 | 隐私敏感 API 检测 | 内置规则 |
| 代码混淆 | 混淆程度评估 | 分析启发式 |
| 恶意行为 | 已知木马特征 | 恶意软件家族库 |

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    APK 分析 Agent                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  输入: APK 文件                                          │
│     │                                                    │
│     ▼                                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ MCP Tool Calling (stdio → HTTP)                  │   │
│  │  ① Agent → MCP Server (stdio JSON-RPC)           │   │
│  │  ② MCP Server → JADX Plugin (HTTP)               │   │
│  │  ③ JADX Plugin → JADX GUI                        │   │
│  └─────────────────────────────────────────────────┘   │
│     │                                                    │
│     ▼                                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 自定义规则匹配 (你的恶意特征)                     │   │
│  │  - 包路径正则匹配                                  │   │
│  │  - URL 黑名单检查                                  │   │
│  │  - 自定义检测规则                                  │   │
│  └─────────────────────────────────────────────────┘   │
│     │                                                    │
│     ▼                                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 恶意模式知识库                                   │   │
│  │  - 已知木马家族特征                               │   │
│  │  - 行为模式匹配                                    │   │
│  └─────────────────────────────────────────────────┘   │
│     │                                                    │
│     ▼                                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 自我反思检查                                       │   │
│  │  - 分析完整性验证                                  │   │
│  │  - 改进建议生成                                    │   │
│  └─────────────────────────────────────────────────┘   │
│     │                                                    │
│     ▼                                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 生成安全分析报告                                   │   │
│  │  - 风险等级判定                                    │   │
│  │  - 详细发现列表                                    │   │
│  │  - 缓解措施建议                                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘

外部依赖（自动启动）:
┌──────────────┐     打开 APK     ┌─────────────────┐
│  用户操作    │ ───────────────→ │    JADX GUI     │
└──────────────┘                  │ (Plugin自动启动) │
                                  └────────┬─────────┘
                                           │ HTTP
                                           ▼
┌──────────────┐     stdio      ┌──────────────────┐
│ 我们的 Agent │ ←─────────────→ │  MCP Server      │
│              │                  │ (uv run...)      │
└──────────────┘                  └──────────────────┘
```

## MCP 工具列表

根据 jadx-mcp-server 的官方实现，以下 MCP 工具可用:

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `get_android_manifest()` | 无 | 获取 AndroidManifest.xml 内容 |
| `get_all_classes(offset, count)` | offset=0, count=0 | 获取所有类列表（分页） |
| `get_class_source(class_name)` | class_name | 获取指定类的源代码 |
| `get_strings(offset, count)` | offset=0, count=0 | 获取 strings.xml 内容 |
| `get_all_resource_file_names(offset, count)` | offset=0, count=0 | 获取所有资源文件名 |
| `get_resource_file(resource_name)` | resource_name | 获取资源文件内容 |
| `search_classes_by_keyword(search_term, package, search_in, offset, count)` | 多参数 | 按关键字搜索类 |
| `get_methods_of_class(class_name)` | class_name | 获取类的方法列表 |
| `get_fields_of_class(class_name)` | class_name | 获取类的字段列表 |
| `get_smali_of_class(class_name)` | class_name | 获取类的 Smali 代码 |
| `get_xrefs_to_class(class_name, offset, count)` | 多参数 | 查找类的引用 |
| `get_xrefs_to_method(class_name, method_name, offset, count)` | 多参数 | 查找方法的引用 |
| `get_main_activity_class()` | 无 | 获取主 Activity 类 |
| `get_main_application_classes_names()` | 无 | 获取应用类名称列表 |

**注意:** MCP Server 默认通过 HTTP 端口 8650 与 JADX Plugin 通信。

## 项目结构

```
project6-advanced-agent/
├── agents/                    # Agent 实现
│   ├── base.py              # Agent 基类
│   └── apk_agent.py         # APK 分析 Agent
├── tools/                     # MCP 工具集成
│   └── mcp/
│       └── jadx_client.py  # JADX MCP 客户端
├── knowledge_base/            # 恶意软件知识库
│   ├── raw/                 # 原始资源
│   │   ├── rules/           # 自定义规则 (JSON)
│   │   │   ├── package_rules.json
│   │   │   ├── url_rules.json
│   │   │   └── custom_rules.json
│   │   └── analyses/       # PDF 分析文档
│   ├── loaders/            # 资源加载器
│   │   ├── rule_loader.py  # 规则加载器
│   │   └── pdf_parser.py   # PDF 解析器 (待实现)
│   └── malware_patterns.py  # 恶意模式管理
├── reflection/                # 自我反思模块
│   └── checker.py          # 分析完整性检查器
├── config.py                 # 配置管理
├── demo.py                   # 演示脚本
└── README.md
```

## 自定义规则格式

### 规则文件结构 (JSON)

```json
{
  "rules": [
    {
      "name": "规则名称",
      "category": "类别",
      "severity": "low|medium|high|critical",
      "description": "规则描述",
      "patterns": [
        "com/malware/.*",
        ".*\\.payload/.*",
        "com/.*\\.core/.*"
      ],
      "tags": ["标签1", "标签2"],
      "references": ["参考说明"]
    }
  ],
  "metadata": {
    "version": "1.0",
    "last_updated": "2024-03-12"
  }
```

### 正则表达式模式

```javascript
// 包路径匹配示例
com/malware/trojan/.*     // 前缀匹配
.*\\.payload/.*             // 后缀匹配
com/.*\\.loader/.*          // 中间匹配
.*\\.core\\..*service       // 复杂嵌套
```

### 已创建的规则文件

| 文件 | 类型 | 数量 |
|------|------|------|
| `package_rules.json` | 包路径规则 | 6 条 |
| `url_rules.json` | URL 黑名单 | 4 条 |
| `custom_rules.json` | 自定义模板 | 1 条 |

## 快速开始

### 环境要求

- Python 3.9+
- jadx-gui（用于打开和反编译 APK）
- jadx-mcp-server（用于 MCP 通信）
- uv（用于运行 jadx-mcp-server）

### 1. 安装依赖

```bash
cd project6-advanced-agent
pip install -r requirements.txt
```

### 2. 安装 JADX

```bash
# Linux/Mac
wget https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip
unzip jadx-1.5.0.zip -d ~/jadx

# Windows
# 下载: https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip
# 解压到 C:\jadx
```

### 3. 安装 JADX MCP Server

```bash
# 克隆 jadx-ai-mcp 仓库
git clone https://github.com/zinja-coder/jadx-ai-mcp.git ~/jadx-mcp-server

# 或者下载 ZIP 后解压
# https://github.com/zinja-coder/jadx-ai-mcp
```

这个文件夹包含 `jadx_mcp_server.py`，我们的 Agent 会通过 stdio 方式调用它。

### 4. 安装 uv

```bash
pip install uv
```

### 5. 配置环境变量

```bash
cp .env.example .env

# 编辑 .env 文件
JADX_MCP_SERVER_PATH=/path/to/jadx-mcp-server    # MCP Server 目录
JADX_GUI_PATH=~/jadx/jadx-gui                     # JADX-GUI 路径
```

### 6. 启动服务

**重要：使用前必须先启动 JADX-GUI 中的 MCP Plugin**

1. 启动 JADX-GUI
2. 在菜单中找到 MCP Plugin 设置
3. 配置并启动 MCP Plugin（记下监听端口）

#### 方式一：使用启动脚本（推荐）

```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

#### 方式二：手动启动

```bash
# 直接启动 Web UI（MCP Server 会自动通过 stdio 启动）
cd project6-advanced-agent
streamlit run app/web.py
```

### 7. 运行演示

```bash
# 查看规则加载演示
python demo.py
```

## 使用方式

### 方式一：Web UI（推荐）

```bash
# 启动 Web 界面
streamlit run app/web.py
```

浏览器打开 `http://localhost:8501`，然后：

1. **选择 APK 文件** - 上传或输入路径
2. **配置选项**（可选）:
   - 启用 RAG 检索
   - 启用高级分析
   - 配置 JADX 路径
3. **点击分析** - 查看实时进度和报告

### 方式二：命令行

```python
from agents.apk_agent import create_apk_agent

# 创建 Agent（需要指定 jadx-mcp-server 目录路径）
agent = create_apk_agent(
    mcp_server_path="/path/to/jadx-mcp-server"
)

# 分析 APK
response = agent.think("分析 app.apk", context={"apk_path": "path/to/app.apk"})
print(response.content)
```

### 方式三：带状态回调

```python
from agents.apk_agent import create_apk_agent

# 状态回调
def on_status(msg):
    print(f"[状态] {msg}")

# 创建 Agent（带回调）
agent = create_apk_agent(
    mcp_server_path="/path/to/jadx-mcp-server",
    on_status_update=on_status
)

# 分析
response = agent.think("分析 app.apk", context={"apk_path": "app.apk"})
```

## 使用前准备

**重要：JADX-GUI 打开 APK 时会自动启动 MCP Plugin**

### 步骤 1：在 JADX-GUI 中打开 APK

1. 启动 JADX-GUI：
   ```bash
   # Linux/Mac
   ~/jadx/bin/jadx-gui

   # Windows
   jadx-gui.exe
   ```

2. 在 JADX-GUI 中打开你要分析的 APK 文件
   - MCP Plugin 会自动启动
   - 无需额外配置

### 步骤 2：启动我们的 Agent

```bash
streamlit run app/web.py
```

### 步骤 3：开始分析

1. 在 Web UI 中配置 jadx-mcp-server 目录路径
2. 点击"开始分析"
3. Agent 会通过 MCP Server 获取已打开 APK 的信息

### 可选：自动打开 APK

如果希望 Agent 自动在 JADX-GUI 中打开 APK，可以：
1. 勾选"自动在 JADX-GUI 中打开 APK"
2. 配置 jadx-gui 可执行文件路径

## 完整分析流程

```
1. 📱 在 JADX-GUI 中打开 APK
2. 📄 解析 AndroidManifest.xml
3. 🔐 分析权限
4. 📂 扫描代码路径
5. 🌐 分析网络通信
6. ⚙️ 分析 API 调用
7. 📝 提取字符串
8. 🎯 匹配恶意模式
9. 📊 计算风险等级
```

## Windows 配置

### JADX 安装

1. 下载 [jadx-1.5.0.zip](https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip)
2. 解压到 `C:\jadx\`
3. 确认 `C:\jadx\jadx-gui.exe` 存在

### 配置文件 (.env)

```bash
JADX_GUI_PATH=C:\jadx\jadx-gui.exe
# 或者在 PATH 中时
JADX_GUI_PATH=jadx-gui
```

### 运行

```bash
# CMD
streamlit run app/web.py

# PowerShell
streamlit run app/web.py
```

## 使用方法

将你的恶意特征规则整理成 JSON 格式，放到 `knowledge_base/raw/rules/` 目录：

```bash
# 1. 创建规则文件
cat > knowledge_base/raw/rules/my_rules.json << 'EOF'
{
  "rules": [
    {
      "name": "你的木马特征",
      "category": "trojan",
      "severity": "critical",
      "description": "检测某类木马的典型特征",
      "patterns": [
        "com/yourmalware/.*",
        ".*\\.c2client/.*"
      ],
      "tags": ["trojan", "c2"]
    }
  ]
}
EOF

# 2. 运行演示验证规则加载
python demo.py
```

### 2. 运行分析

```bash
# 基础演示
python demo.py

# 分析 APK (需要 JADX MCP Server 运行)
python demo.py --apk suspicious.apk
```

### 3. 在代码中使用

```python
from agents.apk_agent import create_apk_agent
from knowledge_base import get_rule_loader

# 创建 Agent（会自动加载规则）
agent = create_apk_agent()

# 分析 APK
response = agent.think("分析这个 APK", context={"apk_path": "app.apk"})
print(response.content)
```

## 检测流程

```
APK 文件
    ↓
JADX-GUI 打开 APK
    ↓
MCP stdio 通信 (uv run jadx_mcp_server.py)
    ↓
提取包路径列表
    ↓
┌─────────────────────────────────────────────┐
│  与你的自定义规则匹配                             │
│  - com/malware/.* 匹配? ✅                        │
│  - .*\\.c2client/.* 匹配? ✅                       │
│  - com/normal/.* 匹配? ❌                          │
└─────────────────────────────────────────────┘
    ↓
生成分析报告
```

## 输出示例

```
# APK 安全分析报告

## 基本信息
- 包名: com.example.app
- 版本: 1.0
- 风险等级: CRITICAL
- 判定: 检测到可疑行为

## 恶意特征匹配
1. 🔴 [CRITICAL] 木马_通信包_特征
   - 匹配路径: com/malware/trojan/Communication.smali

2. 🔴 [CRITICAL] 已知_C2_服务器
   - 匹配域名: *.c2server.com

## 安全发现
1. 🟠 [HIGH] 发现 3 个危险权限
2. 🟠 [HIGH] 发现使用非 HTTPS 的网络通信
3. 🟠 [HIGH] 发现隐私敏感 API 调用
```

## 技术栈

- **LLM**: Anthropic Claude
- **MCP**: Model Context Protocol (stdio 方式)
- **JADX**: APK 反编译工具 (jadx-gui + jadx-mcp-server)
- **uv**: Python 包运行器
- **规则引擎**: Python 正则表达式
- **知识存储**: JSON 文件

## 开发路线

| 阶段 | 功能 | 状态 |
|------|------|------|
| **基础框架** | Agent 基类、MCP 客户端 | ✅ |
| **自定义规则** | 规则加载器、正则匹配 | ✅ |
| **恶意模式库** | 内置恶意模式 | ✅ |
| **自我反思** | 完整性检查器 | ✅ |
| **PDF 解析** | 提取分析文档知识 | 🔜 |
| **长记忆** | 跨会话记忆存储 | 🔜 |

## License

MIT
