@echo off
REM APK 分析 Agent 启动脚本 (Windows)

echo ========================================
echo   APK 分析 Agent 启动脚本
echo ========================================
echo.

REM 配置 - 请修改为你的实际路径
set MCP_SERVER_PATH=C:\path\to\jadx-mcp-server
set MCP_PORT=8650

REM 检查 MCP Server 路径
if not exist "%MCP_SERVER_PATH%" (
    echo [错误] JADX MCP Server 路径不存在: %MCP_SERVER_PATH%
    echo.
    echo 请编辑此脚本，修改 MCP_SERVER_PATH 为你的实际路径
    pause
    exit /b 1
)

REM 检查 uv 是否安装
where uv >nul 2>nul
if errorlevel 1 (
    echo [错误] uv 未安装，请先安装: pip install uv
    pause
    exit /b 1
)

REM 启动 MCP Server（后台）
echo [1/2] 启动 JADX MCP Server...
cd /d "%MCP_SERVER_PATH%"
start /B uv run jadx_mcp_server.py
cd /d "%~dp0"

REM 等待 MCP Server 启动
timeout /t 3 /nobreak >nul

echo [OK] JADX MCP Server 已启动
echo      监听端口: %MCP_PORT%
echo.

REM 启动 Web UI
echo [2/2] 启动 Web UI...
echo.
streamlit run app/web.py

REM 清理
echo.
echo 停止 MCP Server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq jadx_mcp_server*" 2>nul
echo [OK] 已清理所有进程
pause
