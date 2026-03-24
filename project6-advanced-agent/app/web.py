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
import logging
from pathlib import Path
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.apk_agent import create_apk_agent
from agents.apk_agent_llm import create_llm_agent
from agents.langchain_agent import create_langchain_agent
from knowledge_base import get_rule_loader

# 页面配置
st.set_page_config(
    page_title="APK 恶意行为分析",
    page_icon="🔍",
    layout="wide"
)

# 自定义 CSS - 浅色主题
st.markdown("""
<style>
/* 页面背景 - 浅色渐变 */
.stApp {
    background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
}

/* 主标题区域 */
.main-header {
    text-align: center;
    color: #1e293b;
    padding: 2rem 0;
    background: white;
    border-radius: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.main-header h1 {
    color: #0f172a;
    margin-bottom: 0.5rem;
}

.main-header p {
    color: #64748b;
    font-size: 1.1rem;
}

/* 按钮样式 */
.stButton>k {
    background-color: #3b82f6;
    color: white;
    border-radius: 0.5rem;
    font-weight: 500;
}

.stButton>k:hover {
    background-color: #2563eb;
}

/* 状态框 - 清晰可读 */
.status-box {
    background: white;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    border-left: 4px solid #3b82f6;
    color: #1e293b;
    font-size: 0.95rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* 侧边栏样式 */
.css-1d391kg {
    background-color: #f8fafc;
}

.css-1d391kg .css-1v0mbdj {
    color: #1e293b;
}

/* 标题颜色 */
h1, h2, h3 {
    color: #0f172a !important;
}

/* 文本颜色 */
.stMarkdown {
    color: #334155;
}

/* 代码块样式 */
.stCode {
    background: #f1f5f9;
    border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


def show_history_view():
    """显示历史分析记录"""
    try:
        from memory import get_vector_store

        vector_store = get_vector_store()

        # 显示统计信息
        stats = vector_store.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 总分析数", stats["total_count"])
        with col2:
            st.metric("🔴 高风险样本", stats["high_risk_count"])

        st.markdown("---")

        # 搜索历史
        search_query = st.text_input("🔍 搜索相似分析")

        if search_query:
            with st.spinner("搜索中..."):
                results = vector_store.search_similar(search_query, n_results=5)

            if results:
                for i, result in enumerate(results):
                    with st.expander(
                        f"{result['metadata'].get('package', 'unknown')} - "
                        f"{result['metadata'].get('risk_level', 'UNKNOWN')}"
                    ):
                        st.markdown(f"**摘要:** {result.get('content', '')[:300]}")
                        st.caption(f"时间: {result['metadata'].get('timestamp', 'unknown')}")
            else:
                st.info("未找到相似记录")
    except Exception as e:
        st.warning(f"⚠️ 长记忆功能暂不可用: {e}")
        st.caption("请确保 Ollama 正在运行: `ollama serve`")


def show_document_import():
    """文档导入界面"""
    try:
        from memory import DocumentImporter, get_vector_store

        vector_store = get_vector_store()
        importer = DocumentImporter(vector_store=vector_store)

        uploaded_files = st.file_uploader(
            "上传历史分析文档",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
            help="支持 PDF、TXT、MD 格式的历史分析文档"
        )

        if uploaded_files:
            st.info(f"已选择 {len(uploaded_files)} 个文件")

            if st.button("📥 开始导入", type="primary"):
                progress_bar = st.progress(0)
                success_count = 0

                uploads_dir = Path("uploads")
                uploads_dir.mkdir(exist_ok=True)

                for i, uploaded_file in enumerate(uploaded_files):
                    # 保存临时文件
                    temp_path = uploads_dir / uploaded_file.name
                    with open(str(temp_path), "wb") as f:
                        f.write(uploaded_file.getvalue())

                    # 导入
                    try:
                        with st.spinner(f"处理 {uploaded_file.name}..."):
                            if uploaded_file.name.endswith(".pdf"):
                                importer.import_pdf(str(temp_path))
                            else:
                                importer.import_text_file(str(temp_path))

                        success_count += 1
                        st.success(f"✅ {uploaded_file.name} 导入成功")

                    except Exception as e:
                        st.error(f"❌ {uploaded_file.name} 导入失败: {e}")

                    # 清理临时文件
                    temp_path.unlink()

                    progress_bar.progress((i + 1) / len(uploaded_files))

                st.info(f"导入完成: {success_count}/{len(uploaded_files)} 成功")
    except Exception as e:
        st.warning(f"⚠️ 文档导入功能暂不可用: {e}")
        st.caption("请确保 Ollama 正在运行: `ollama serve`")


def show_rule_review():
    """规则审核界面"""
    try:
        from memory import get_rule_learner

        rule_learner = get_rule_learner()
        candidates = rule_learner.load_pending_rules()

        if not candidates:
            st.info("暂无待审核规则")
            return

        st.info(f"有 {len(candidates)} 条候选规则待审核")

        for candidate in candidates:
            rule_id = candidate.get("id", "unknown")

            with st.expander(f"📋 {candidate.get('name', '未命名规则')}"):
                # 显示规则详情
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**类别:**", candidate.get("category", "unknown"))
                    st.write("**严重程度:**", candidate.get("severity", "unknown"))

                with col2:
                    pattern = candidate.get("pattern", "无")
                    if pattern and pattern != "无":
                        st.code(pattern, language="regex")
                    else:
                        st.write("**模式:** 无")

                st.markdown("**描述:**")
                st.markdown(candidate.get("description", ""))

                if candidate.get("reason"):
                    st.markdown("**理由:**")
                    st.caption(candidate["reason"])

                indicators = candidate.get("indicators", {})
                if indicators and (indicators.get("domains") or indicators.get("ips") or indicators.get("urls")):
                    st.markdown("**威胁指标:**")
                    if indicators.get("domains"):
                        st.write("- 域名:", ", ".join(indicators["domains"]))
                    if indicators.get("ips"):
                        st.write("- IP:", ", ".join(indicators["ips"]))
                    if indicators.get("urls"):
                        st.write("- URL:", ", ".join(indicators["urls"]))

                # 审核按钮
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    if st.button("✅ 批准", key=f"approve_{rule_id}"):
                        try:
                            rule_learner.approve_rule(rule_id)
                            st.success("规则已添加到规则库")
                            st.rerun()
                        except Exception as e:
                            st.error(f"批准失败: {e}")

                with btn_col2:
                    if st.button("❌ 拒绝", key=f"reject_{rule_id}"):
                        if rule_learner.reject_rule(rule_id):
                            st.success("规则已删除")
                            st.rerun()
                        else:
                            st.error("删除失败")
    except Exception as e:
        st.warning(f"⚠️ 规则审核功能暂不可用: {e}")
        st.caption("请确保 Ollama 正在运行: `ollama serve`")


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

    # 状态更新回调（记录并触发显示更新）
    def update_status(msg: str):
        import time
        timestamp = time.strftime("%H:%M:%S")
        st.session_state.analysis_status.append(f"[{timestamp}] {msg}")
        # 触发进度显示更新（如果状态容器存在）
        if hasattr(st.session_state, 'progress_container'):
            with st.session_state.progress_container.container():
                st.header("📊 分析进度")
                for status in st.session_state.analysis_status:
                    st.markdown(f"<div class='status-box'>{status}</div>", unsafe_allow_html=True)

    # 侧边栏 - 配置
    with st.sidebar:
        st.header("⚙️ 分析配置")

        # RAG 检索选项
        enable_rag = st.checkbox(
            "启用 RAG 检索",
            value=False,
            help="在分析前检索相关恶意软件知识库"
        )

        # Agent 类型选择
        agent_type = st.radio(
            "Agent 类型",
            ["硬编码流程", "LLM 驱动", "LangChain"],
            horizontal=True,
            help="硬编码: 固定步骤 | LLM驱动: AI自主决策 | LangChain: 自动循环管理"
        )

        # 初始化自定义 prompt（所有模式共用）
        custom_system_prompt = None

        # LLM System Prompt 配置（LLM 驱动模式显示）
        if agent_type == "LLM 驱动":
            with st.expander("📝 自定义 System Prompt", expanded=False):
                st.info("""
                自定义 LLM 的 System Prompt，指定分析步骤和输出格式。
                留空则使用默认 prompt。
                """)

                # 加载默认 prompt 作为占位符
                from agents.apk_agent_llm import USER_SYSTEM_PROMPT

                custom_system_prompt = st.text_area(
                    "System Prompt",
                    value="",
                    placeholder=USER_SYSTEM_PROMPT,
                    height=300,
                    help="输入自定义的 System Prompt，包含分析步骤和输出格式"
                )
        elif agent_type == "LangChain":
            # LangChain 模式 - 支持自定义 prompt
            with st.expander("📝 自定义 System Prompt (可选)", expanded=False):
                st.info("""
                **LangChain Agent** 支持自定义 System Prompt。
                留空则使用内置的专业分析 Prompt。
                """)

                # 加载 LangChain 默认 prompt 作为占位符
                from agents.langchain_agent import ANALYST_SYSTEM_PROMPT

                langchain_custom_prompt = st.text_area(
                    "System Prompt",
                    value="",
                    placeholder=ANALYST_SYSTEM_PROMPT,
                    height=300,
                    help="输入自定义的 System Prompt，留空使用默认"
                )

                # 显示输出格式说明
                st.markdown("""
                **推荐输出格式：**
                ```
                # APK 安全分析报告

                ## 基本信息
                - 包名: `xxx`
                - 版本: `xxx`

                ## 风险评估
                - 风险等级: [LOW/MEDIUM/HIGH/CRITICAL]
                - 判定: [总结]

                ## 安全发现
                1. **[严重程度]** [描述]
                ```
                """)
        else:
            custom_system_prompt = None

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
        1. 配置上方 MCP Server 目录路径
        2. 选择 APK 文件
        3. 点击"开始分析"按钮
        4. 如勾选"自动打开"，会先启动 JADX-GUI 打开 APK
        5. Agent 自动连接 MCP Server 并开始分析
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

        st.markdown("---")
        st.header("📚 长记忆管理")

        memory_tab1, memory_tab2, memory_tab3 = st.tabs(["历史记录", "导入文档", "候选规则"])

        with memory_tab1:
            show_history_view()

        with memory_tab2:
            show_document_import()

        with memory_tab3:
            show_rule_review()

    # 主区域
    st.markdown("---")

    # 实时状态显示区域（分析时实时更新）
    if "progress_container" not in st.session_state:
        st.session_state.progress_container = st.empty()

    # 更新进度显示的函数
    def update_progress_display():
        if st.session_state.analysis_status:
            with st.session_state.progress_container.container():
                st.header("📊 分析进度")
                for status in st.session_state.analysis_status:
                    st.markdown(f"<div class='status-box'>{status}</div>", unsafe_allow_html=True)

    # 显示现有进度
    update_progress_display()

    # 如果分析完成，显示分隔线
    if st.session_state.analysis_status and st.session_state.analysis_result:
        st.markdown("---")

    # 文件上传区域
    st.header("📁 选择 APK 文件")

    upload_method = st.radio(
        "上传方式",
        ["上传文件", "输入路径"],
        horizontal=True
    )

    apk_path = None
    uploaded_file = None  # 初始化为 None，避免 NameError

    if upload_method == "上传文件":
        uploaded_file = st.file_uploader(
            "选择 APK 文件",
            type=["apk"],
            help="选择要分析的 APK 文件"
        )

        if uploaded_file is not None:
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)

            # 清理文件名：移除或替换特殊字符
            import re
            import time
            safe_name = re.sub(r'[<>:"/\\|?*()\[\]{}]', '_', uploaded_file.name)

            # 添加时间戳避免文件名冲突和锁定问题
            name_without_ext = Path(safe_name).stem
            ext = Path(safe_name).suffix
            timestamp = int(time.time())
            safe_name = f"{name_without_ext}_{timestamp}{ext}"

            apk_path = upload_dir / safe_name

            # 如果文件已存在，先删除（Windows 文件锁定问题）
            if apk_path.exists():
                try:
                    apk_path.unlink()
                except:
                    pass

            with open(str(apk_path), "wb") as f:
                f.write(uploaded_file.getvalue())

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
                    # 创建 Agent - 根据用户选择
                    if agent_type == "LangChain":
                        # LangChain Agent（自动循环管理）
                        system_prompt = langchain_custom_prompt if langchain_custom_prompt else None
                        agent = create_langchain_agent(
                            mcp_server_path=mcp_server_path,
                            system_prompt=system_prompt,
                            on_status_update=update_status
                        )
                        update_status("🔄 使用 LangChain Agent (自动循环管理)")
                        if system_prompt:
                            update_status("📝 使用自定义 System Prompt")
                    elif agent_type == "LLM 驱动":
                        # LLM 驱动 Agent（手动循环）
                        system_prompt = custom_system_prompt if custom_system_prompt else None
                        agent = create_llm_agent(
                            mcp_server_path=mcp_server_path,
                            system_prompt=system_prompt,
                            on_status_update=update_status
                        )
                        update_status("🤖 使用 LLM 驱动 Agent")
                        if system_prompt:
                            update_status("📝 使用自定义 System Prompt")
                    else:
                        # 硬编码流程 Agent
                        agent = create_apk_agent(
                            mcp_server_path=mcp_server_path,
                            jadx_gui_path=jadx_gui_path if jadx_gui_path else None,
                            enable_rag=enable_rag,
                            enable_advanced=enable_advanced,
                            on_status_update=update_status
                        )
                        update_status("⚙️ 使用硬编码流程 Agent")

                    # 执行分析
                    start_time = time.time()

                    try:
                        # 确保使用绝对路径
                        apk_path_abs = str(Path(apk_path).resolve())
                        response = agent.think(
                            f"请分析 APK 文件: {apk_path_abs}",
                            context={"apk_path": apk_path_abs}
                        )

                        elapsed_time = time.time() - start_time

                        update_status(f"✅ 分析完成！(耗时: {elapsed_time:.2f} 秒)")
                        st.session_state.analysis_result = response

                        # 调试：显示返回信息
                        update_status(f"📄 报告内容长度: {len(response.content) if response.content else 0}")
                        if hasattr(response, 'metadata'):
                            update_status(f"📊 风险等级: {response.metadata.get('risk_level', 'unknown')}")

                        # 关闭 JADX-GUI 和 MCP Server（先关闭才能删除文件）
                        try:
                            agent.mcp_client.close()
                            update_status("✅ JADX-GUI 和 MCP Server 已关闭")
                        except Exception as e:
                            logger.warning(f"关闭 MCP 客户端失败: {e}")

                        # 删除上传的 APK 文件（关闭后才能删除）
                        try:
                            apk_file = Path(apk_path_abs)
                            if apk_file.exists():
                                apk_file.unlink()
                                update_status("🗑️ 已删除上传的 APK 文件")
                        except Exception as e:
                            logger.warning(f"删除 APK 文件失败: {e}")

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

        # 调试：显示响应状态
        st.caption(f"Content 长度: {len(response.content) if response.content else 0} | 类型: {type(response.content)}")

        # 直接显示 LLM 生成的报告（按用户定义的格式）
        if response.content:
            st.markdown(response.content)

            # 下载 Markdown 按钮
            st.markdown("---")
            try:
                # 获取 APK 名称和时间戳
                apk_path_str = response.metadata.get("apk_path", "unknown")
                if apk_path_str and apk_path_str != "unknown":
                    apk_name = Path(str(apk_path_str)).stem
                else:
                    apk_name = "unknown"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"apk_report_{apk_name}_{timestamp}.md"
            except Exception as e:
                st.error(f"生成文件名失败: {e}")
                apk_name = "report"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"apk_report_{timestamp}.md"

            # 添加元数据到 markdown
            markdown_content = response.content
            metadata = f"""---
# APK 安全分析报告

**APK 文件:** {apk_name}
**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent:** {response.metadata.get('model', 'unknown')}

---

"""

            st.download_button(
                label="📥 下载 Markdown 报告",
                data=metadata + markdown_content,
                file_name=filename,
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.warning("⚠️ 报告内容为空")
            st.error("LLM 没有生成报告内容，请检查：")
            st.markdown("""
            1. System Prompt 是否正确定义了输出格式
            2. LLM 是否正确调用工具获取数据
            3. 查看下方调试信息了解详情
            """)
            st.json(response.metadata)

        # 可选：显示原始元数据（折叠）
        with st.expander("🔧 调试信息", expanded=False):
            st.json(response.metadata)

        # 显示 Token 使用量
        token_usage = response.metadata.get("token_usage")
        if token_usage:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📥 输入 Tokens", token_usage.get("input_tokens", 0))
            with col2:
                st.metric("📤 输出 Tokens", token_usage.get("output_tokens", 0))
            with col3:
                st.metric("💰 总计 Tokens", token_usage.get("total_tokens", 0))

            # 计算成本（基于 Claude Sonnet 4 定价）
            input_cost = token_usage.get("input_tokens", 0) * 3 / 1_000_000  # $3/1M tokens
            output_cost = token_usage.get("output_tokens", 0) * 15 / 1_000_000  # $15/1M tokens
            total_cost = input_cost + output_cost
            st.caption(f"💵 预估成本: ${total_cost:.4f} (输入 ${input_cost:.4f} + 输出 ${output_cost:.4f})")

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
