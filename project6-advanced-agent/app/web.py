"""
APK 恶意行为分析 - Web UI

基于 Streamlit 的简单分析界面
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

    # 侧边栏 - 规则信息
    with st.sidebar:
        st.header("📋 检测规则")

        # 加载规则
        rule_loader = get_rule_loader()

        st.info(f"已加载 {len(rule_loader.rules)} 条规则")

        # 按类别显示
        categories = rule_loader.get_all_categories()
        if categories:
            selected_cat = st.selectbox("规则类别", ["全部"] + categories)

            if selected_cat != "全部":
                rules = rule_loader.get_rules_by_category(selected_cat)
            else:
                rules = rule_loader.rules

            # 显示规则列表
            st.markdown("**规则列表:**")
            for rule in rules[:10]:  # 最多显示10条
                severity_icons = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                icon = severity_icons.get(rule.severity, "⚪")
                st.markdown(f"{icon} **{rule.name}**")
                st.caption(rule.description)
                if rule.patterns:
                    with st.expander("查看模式"):
                    for pattern in rule.patterns[:5]:
                        st.code(pattern)

        st.markdown("---")

        # 统计信息
        st.header("📊 统计")

        severity_counts = {}
        for rule in rule_loader.rules:
            severity_counts[rule.severity] = severity_counts.get(rule.severity, 0) + 1

        for severity, count in sorted(severity_counts.items()):
            color = {
                "critical": "red",
                "high": "orange",
                "medium": "yellow",
                "low": "green"
            }.get(severity, "gray")
            st.markdown(f":{color}: **{severity.upper()}**: {count} 条")

    # 主区域 - 文件上传和分析
    st.markdown("---")

    # 文件上传区域
    st.header("📁 选择 APK 文件")

    # 上传方式选择
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
            # 保存上传的文件
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
        if st.button("🔍 开始分析", type="primary", use_container_width=True):
            with st.spinner("正在分析 APK..."):
                # 创建 Agent
                agent = create_apk_agent()

                # 执行分析
                start_time = time.time()

                try:
                    response = agent.think(
                        f"请分析 APK 文件: {apk_path}",
                        context={"apk_path": str(apk_path)}
                    )

                    elapsed_time = time.time() - start_time

                    # 显示分析结果
                    st.success(f"✅ 分析完成！(耗时: {elapsed_time:.2f} 秒)")

                    # 显示报告
                    st.markdown(response.content)

                    # 显示元数据
                    with st.expander("📊 分析元数据", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("风险等级", response.metadata.get("risk_level", "unknown"))
                        with col2:
                            st.metric("发现数量", response.metadata.get("findings_count", 0))

                        if response.metadata.get("risk_score"):
                            st.caption(f"风险分数: {response.metadata['risk_score']}")
                        if response.metadata.get("quality_score"):
                            st.caption(f"质量评分: {response.metadata['quality_score']:.2f}")

                except Exception as e:
                    st.error(f"❌ 分析失败: {str(e)}")

                    # 显示调试信息
                    with st.expander("查看错误详情"):
                        st.code(str(e), language="python")

    # 使用说明
    st.markdown("---")
    st.markdown("""
    ### 📖 使用说明

    1. **选择 APK 文件**
       - 上传 APK 文件，或
       - 输入文件路径

    2. **开始分析**
       - 点击 "开始分析" 按钮
       - 等待分析完成

    3. **查看报告**
       - 风险等级判定
       - 详细安全发现
       - 分析质量评估

    ### ⚙️ 技术架构

    - **MCP 工具调用** - JADX 反编译
    - **自定义规则** - 你的恶意特征
    - **知识库检索** - 已知恶意模式
    - **自我反思** - 分析完整性检查

    ### 🔧 自定义规则

    将你的恶意特征规则放到 `knowledge_base/raw/rules/` 目录，
    系统会自动加载并用于分析检测。
    """)


if __name__ == "__main__":
    main()
