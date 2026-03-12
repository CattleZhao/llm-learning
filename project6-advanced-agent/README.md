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
│  │ MCP Tool Calling (JADX MCP Server)               │   │
│  │  - 反编译 APK                                      │   │
│  │  - 提取包路径列表                                  │   │
│  │  - 提取权限信息                                    │   │
│  │  - 提取 API 调用                                   │   │
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
```

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

## 使用方法

### 1. 添加自定义规则

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
JADX MCP 反编译
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
- **MCP**: Model Context Protocol
- **JADX**: APK 反编译工具
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
