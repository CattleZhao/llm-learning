#!/bin/bash
# APK 分析 Agent 启动脚本

echo "🚀 启动 APK 分析 Agent..."
echo ""

# 配置
MCP_SERVER_PATH="${JADX_MCP_SERVER_PATH:-/path/to/jadx-mcp-server}"
MCP_PORT="${JADX_PORT:-8650}"

# 检查 MCP Server 路径
if [ ! -d "$MCP_SERVER_PATH" ]; then
    echo "⚠️  JADX MCP Server 路径不存在: $MCP_SERVER_PATH"
    echo "请设置环境变量: JADX_MCP_SERVER_PATH"
    echo ""
    echo "或者在启动脚本中修改路径"
    exit 1
fi

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装: pip install uv"
    exit 1
fi

# 启动 MCP Server（后台）
echo "📡 启动 JADX MCP Server..."
cd "$MCP_SERVER_PATH"
uv run jadx_mcp_server.py &
MCP_PID=$!
cd - > /dev/null

# 等待 MCP Server 启动
sleep 3

# 检查 MCP Server 是否运行
if kill -0 $MCP_PID 2>/dev/null; then
    echo "✅ JADX MCP Server 已启动 (PID: $MCP_PID)"
    echo "   监听端口: $MCP_PORT"
else
    echo "❌ JADX MCP Server 启动失败"
    exit 1
fi

# 启动 Web UI
echo ""
echo "🌐 启动 Web UI..."
streamlit run app/web.py

# 清理：用户关闭 Web UI 后
echo ""
echo "🛑 停止 MCP Server..."
kill $MCP_PID 2>/dev/null
echo "✅ 已清理所有进程"
