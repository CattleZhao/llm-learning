#!/bin/bash
# APK 分析 Agent 启动脚本

echo "🚀 启动 APK 分析 Agent..."
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件，配置以下变量："
    echo "   - JADX_MCP_SERVER_PATH"
    echo "   - JADX_GUI_PATH (可选)"
    echo ""
fi

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装: pip install uv"
    exit 1
fi

# 检查 streamlit 是否安装
if ! command -v streamlit &> /dev/null; then
    echo "❌ streamlit 未安装，请先安装: pip install streamlit"
    exit 1
fi

# 启动 Web UI
echo "🌐 启动 Web UI..."
echo "   在 Web UI 中配置 jadx-mcp-server 路径后即可使用"
echo ""
streamlit run app/web.py
