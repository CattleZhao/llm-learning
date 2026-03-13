@echo off
REM APK 分析 Agent 启动脚本 (Windows)

echo ========================================
echo   APK 分析 Agent 启动脚本
echo ========================================
echo.

REM 检查 .env 文件
if not exist ".env" (
    echo [INFO] 未找到 .env 文件，从 .env.example 复制...
    copy .env.example .env
    echo [INFO] 请编辑 .env 文件，配置以下变量:
    echo        - JADX_MCP_SERVER_PATH
    echo        - JADX_GUI_PATH (可选)
    echo.
)

REM 检查 uv 是否安装
where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv 未安装，请先安装: pip install uv
    pause
    exit /b 1
)

REM 检查 streamlit 是否安装
where streamlit >nul 2>nul
if errorlevel 1 (
    echo [ERROR] streamlit 未安装，请先安装: pip install streamlit
    pause
    exit /b 1
)

REM 启动 Web UI
echo [INFO] 启动 Web UI...
echo        在 Web UI 中配置 jadx-mcp-server 路径后即可使用
echo.
streamlit run app/web.py
pause
