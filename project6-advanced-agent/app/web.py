"""
APK 恶意行为分析 - Web UI

完整流程:
1. 选择 APK 文件
2. 可选: RAG 检索
3. JADX-GUI 打开 APK
4. LLM 调用 JADX-MCP 分析
5. 输出分析报告
"""
import streamlit as st
import sys
from pathlib import Path
import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.apk_agent import create_apk_agent
from knowledge_base import get_rule_loader

# 页面配置
st.set_page_config(
    page_title="APK 恶意行为分析",
    page_icon="🔍",
    layout="wide"
)

# 自定义 CSS
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #1e3a8a 0%, #2d5a87 100%);
}
.main-header {
    text-align: center;
    color: white;
    padding: 2rem 0;
}
.stButton>k {
    background-color: #ff4b4f;
    color: white;
}
.status-box {
    background: rgba(0,0,0,0.2);
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


def main():
    """主应用"""
    # 标题
    st.markdown("""
    <div class="main-header">
        <h1>🔍 APK 恶意行为分析 Agent</h1>
        <p>自动检测 Android APK 中的恶意行为</p>
    </div>
    """, unsafe_allow_html=True)

    # 初始化 session state
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "analysis_status" not in st.session_state:
        st.session_state.analysis_status = []

    # 状态更新回调（仅记录，不触发 rerun）
    def update_status(msg: str):
        st.session_state.analysis_status.append(msg)

    # 侧边栏 - 配置
    with st.sidebar:
        st.header("⚙️ 分析配置")

        # RAG 检索选项
        enable_rag = st.checkbox(
            "启用 RAG 检索",
            value=False,
            help="在分析前检索相关恶意软件知识库"
        )

        # 高级分析选项
        enable_advanced = st.checkbox(
            "启用高级分析",
            value=False,
            help="使用更深入的分析模式"
        )

        # JADX 配置
        st.markdown("---")
        st.header("🔧 MCP 配置")

        mcp_server_path = st.text_input(
            "JADX MCP Server 目录",
            value="/root/Learn/jadx-mcp-server",
            placeholder="/path/to/jadx-mcp-server",
            help="jadx-mcp-server 的目录路径（包含 jadx_mcp_server.py）"
        )

        st.info("""
        **使用流程（stdio 模式）：**
        1. 在 JADX-GUI 中打开 APK 文件（Plugin 会自动启动）
        2. 配置上方 MCP Server 目录路径
        3. 点击下方"开始分析"按钮（Agent 会自动启动 MCP Server）
        """)

        use_auto_open = st.checkbox(
            "自动在 JADX-GUI 中打开 APK",
            value=False,
            help="如果勾选，会自动启动 JADX-GUI 并打开 APK（需要配置路径）"
        )

        if use_auto_open:
            jadx_gui_path = st.text_input(
                "JADX-GUI 路径",
                value="",
                placeholder="jadx-gui 或 /path/to/jadx-gui",
                help="用于自动打开 APK"
            )
        else:
            jadx_gui_path = None

        st.markdown("---")
        st.header("📋 检测规则")

        rule_loader = get_rule_loader()
        st.info(f"已加载 {len(rule_loader.rules)} 条规则")

        # 按类别显示
        categories = rule_loader.get_all_categories()
        if categories:
            with st.expander("查看规则"):
                selected_cat = st.selectbox("规则类别", ["全部"] + categories, key="rule_category")

                if selected_cat != "全部":
                    rules = rule_loader.get_rules_by_category(selected_cat)
                else:
                    rules = rule_loader.rules

                for rule in rules[:10]:
                    severity_icons = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢"
                    }
                    icon = severity_icons.get(rule.severity, "⚪")
                    st.markdown(f"{icon} **{rule.name}**")
                    st.caption(rule.description)

    # 主区域
    st.markdown("---")

    # 状态显示区域（分析完成后显示）
    if st.session_state.analysis_status and st.session_state.analysis_result:
        st.header("📊 分析进度")
        for status in st.session_state.analysis_status:
            st.markdown(f"<div class='status-box'>{status}</div>", unsafe_allow_html=True)
        st.markdown("---")

    # 文件上传区域
    st.header("📁 选择 APK 文件")

    upload_method = st.radio(
        "上传方式",
        ["上传文件", "输入路径"],
        horizontal=True
    )

    apk_path = None

    if upload_method == "上传文件":
        uploaded_file = st.file_uploader(
            "选择 APK 文件",
            type=["apk"],
            help="选择要分析的 APK 文件"
        )

        if uploaded_file is not None:
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)

            apk_path = upload_dir / uploaded_file.name
            with open(apk_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✅ 文件已上传: {uploaded_file.name}")
            st.caption(f"文件大小: {uploaded_file.size / 1024:.1f} KB")

    else:
        apk_path = st.text_input(
            "输入 APK 文件路径:",
            placeholder="/path/to/your/app.apk",
            help="输入 APK 文件的完整路径"
        )

    # 分析按钮
    if apk_path:
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔍 开始分析", type="primary", use_container_width=True):
                # 清空之前的状态
                st.session_state.analysis_status = []
                st.session_state.analysis_result = None

                with st.spinner("正在分析 APK..."):
                    # 创建 Agent
                    agent = create_apk_agent(
                        mcp_server_path=mcp_server_path,
                        jadx_gui_path=jadx_gui_path if jadx_gui_path else None,
                        enable_rag=enable_rag,
                        enable_advanced=enable_advanced,
                        on_status_update=update_status
                    )

                    # 执行分析
                    start_time = time.time()

                    try:
                        response = agent.think(
                            f"请分析 APK 文件: {apk_path}",
                            context={"apk_path": str(apk_path)}
                        )

                        elapsed_time = time.time() - start_time

                        update_status(f"✅ 分析完成！(耗时: {elapsed_time:.2f} 秒)")
                        st.session_state.analysis_result = response
                        st.rerun()

                    except Exception as e:
                        update_status(f"❌ 分析失败: {str(e)}")
                        st.error(f"分析失败: {e}")
                        with st.expander("查看错误详情"):
                            st.code(str(e), language="python")
                        st.rerun()

        with col2:
            if st.button("🗑️ 清除", use_container_width=True):
                st.session_state.analysis_status = []
                st.session_state.analysis_result = None
                st.rerun()

    # 显示分析结果
    if st.session_state.analysis_result:
        st.markdown("---")
        st.header("📋 分析报告")

        response = st.session_state.analysis_result

        # 显示报告
        st.markdown(response.content)

        # 显示元数据
        with st.expander("📊 详细元数据", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("风险等级", response.metadata.get("risk_level", "unknown"))
            with col2:
                st.metric("发现数量", response.metadata.get("findings_count", 0))
            with col3:
                score = response.metadata.get("quality_score", 0)
                st.metric("质量评分", f"{score * 100:.1f}%")

            if response.metadata.get("risk_score"):
                st.caption(f"风险分数: {response.metadata['risk_score']}")
            if response.metadata.get("confidence"):
                st.caption(f"置信度: {response.metadata['confidence'] * 100:.1f}%")

    # 使用说明
    st.markdown("---")
    with st.expander("📖 使用说明", expanded=False):
        st.markdown("""
        ### 完整分析流程

        1. **选择 APK 文件**
           - 上传 APK 文件，或
           - 输入文件路径

        2. **配置选项（可选）**
           - 启用 RAG 检索
           - 启用高级分析
           - 配置 JADX 路径

        3. **开始分析**
           - 点击 "开始分析" 按钮
           - 观察实时进度

        4. **查看报告**
           - 风险等级判定
           - 详细安全发现
           - 分析质量评估

        ### 技术架构

        | 阶段 | 说明 |
        |------|------|
        | 1. JADX-GUI | 打开 APK 进行可视化 |
        | 2. MCP 通信 | 通过 MCP 协议获取代码信息 |
        | 3. 规则匹配 | 匹配自定义恶意特征 |
        | 4. RAG 检索 | 查询恶意软件知识库 |
        | 5. 报告生成 | 输出结构化分析报告 |

        ### 自定义规则

        将恶意特征规则放到 `knowledge_base/raw/rules/` 目录，
        支持的格式:

        - `package_rules.json` - 包路径规则
        - `url_rules.json` - URL 黑名单
        - `custom_rules.json` - 自定义规则
        """)


if __name__ == "__main__":
    main()
