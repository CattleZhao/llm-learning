"""
Multi-Agent Code Development Team - Web Interface
"""
import streamlit as st
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, create_orchestrator
from src.utils import get_logger

logger = get_logger(__name__)

# 页面配置
st.set_page_config(
    page_title="Multi-Agent Code Development Team",
    page_icon="🤖",
    layout="wide",
)


def setup_session_state():
    """初始化会话状态变量"""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    if 'config' not in st.session_state:
        try:
            st.session_state.config = get_config()
        except ValueError as e:
            st.session_state.config = None
            st.session_state.config_error = str(e)
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'task_completed' not in st.session_state:
        st.session_state.task_completed = False
    if 'execution_results' not in st.session_state:
        st.session_state.execution_results = None


def render_header():
    """渲染应用标题"""
    st.title("🤖 Multi-Agent Code Development Team")
    st.markdown("""
    一个协作式 AI 团队，共同工作来编写、审查和测试代码。
    由 AutoGen 提供支持。
    """)


def render_config_warning():
    """显示配置警告（如果需要）"""
    if st.session_state.get('config_error'):
        st.error(f"⚠️ 配置错误: {st.session_state.config_error}")
        st.info("请在 .env 文件中设置 OPENAI_API_KEY")
        st.stop()
    if not st.session_state.get('config'):
        st.error("⚠️ 配置未初始化")
        st.stop()


def render_sidebar():
    """渲染侧边栏设置"""
    with st.sidebar:
        st.header("⚙️ 设置")

        # 模型设置
        st.subheader("模型设置")
        model = st.text_input(
            "模型",
            value=st.session_state.config.model if st.session_state.config else "gpt-4o",
        )
        temperature = st.slider(
            "温度",
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            value=st.session_state.config.temperature if st.session_state.config else 0.7,
        )
        max_tokens = st.number_input(
            "最大 Token",
            min_value=100,
            max_value=8000,
            value=st.session_state.config.max_tokens if st.session_state.config else 2000,
        )

        # 更新配置
        if st.session_state.config:
            st.session_state.config.model = model
            st.session_state.config.temperature = temperature
            st.session_state.config.max_tokens = max_tokens

        st.divider()

        # Agent 信息
        st.subheader("👥 Agent 团队")
        st.markdown("""
        | Agent | 角色 |
        |-------|------|
        | **UserProxy** | 协调者 |
        | **Coder** | 代码编写者 |
        | **Reviewer** | 代码审查者 |
        | **Tester** | 测试工程师 |
        """)

        st.divider()

        # 使用说明
        st.subheader("📖 使用说明")
        st.markdown("""
        1. 在主界面输入任务描述
        2. 选择执行模式
        3. 点击执行按钮
        4. 查看 Agent 对话历史
        """)


def render_task_input():
    """渲染任务输入区域"""
    st.header("📝 任务描述")

    task = st.text_area(
        "描述你想要创建的代码:",
        placeholder="例如: 实现一个带类型注解的快速排序算法",
        height=100,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        coder_first = st.checkbox("从 Coder 开始", value=True, help="直接让 Coder 开始编写代码")
    with col2:
        sequential = st.checkbox("顺序工作流", value=False, help="按顺序执行每个阶段")
    with col3:
        clear_history = st.checkbox("清除历史", value=True, help="执行前清除之前的对话历史")

    execute = st.button("🚀 执行任务", type="primary", use_container_width=True)

    return task, execute, coder_first, sequential, clear_history


def render_conversation_history():
    """渲染对话历史"""
    if not st.session_state.conversation_history:
        st.info("👋 还没有对话历史，执行一个任务开始吧！")
        return

    st.header("💬 对话历史")

    # 显示对话统计
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总消息数", len(st.session_state.conversation_history))
        with col2:
            # 统计参与对话的 Agent
            agents = set(msg.get('from', '') for msg in st.session_state.conversation_history)
            st.metric("参与 Agent", len(agents))
        with col3:
            if st.session_state.execution_results:
                status = "✅ 成功" if st.session_state.execution_results.get('success') else "❌ 失败"
                st.metric("状态", status)

    # 显示对话内容
    st.divider()

    for i, msg in enumerate(st.session_state.conversation_history):
        from_agent = msg.get('from', 'unknown')
        content = msg.get('content', '')

        # 为不同 Agent 设置不同颜色
        if from_agent == 'user':
            icon = "👤"
        elif from_agent == 'assistant':
            icon = "🤖"
        else:
            icon = "💬"

        # 如果内容包含代码，使用代码块
        if '```' in content:
            with st.chat_message(from_agent if from_agent in ['user', 'assistant'] else 'assistant'):
                st.markdown(f"{icon} **{from_agent.upper()}**")
                st.markdown(content)
        else:
            with st.chat_message(from_agent if from_agent in ['user', 'assistant'] else 'assistant'):
                st.markdown(f"{icon} **{from_agent.upper()}**")
                st.write(content)


def render_execution_status():
    """渲染执行状态"""
    if not st.session_state.execution_results:
        return

    results = st.session_state.execution_results

    st.header("📊 执行结果")

    if results.get('success'):
        st.success("✅ 任务执行成功！")
    else:
        st.error("❌ 任务执行失败")
        if results.get('error'):
            st.error(f"错误: {results['error']}")


def execute_task(task: str, coder_first: bool, sequential: bool, clear_history: bool):
    """执行任务

    Args:
        task: 任务描述
        coder_first: 是否从 Coder 开始
        sequential: 是否使用顺序工作流
        clear_history: 是否清除历史
    """
    if not task.strip():
        st.warning("⚠️ 请输入任务描述")
        return

    # 创建编排器
    if st.session_state.orchestrator is None:
        with st.spinner("正在初始化 Agent 团队..."):
            try:
                st.session_state.orchestrator = create_orchestrator(st.session_state.config)
            except Exception as e:
                st.error(f"初始化失败: {e}")
                return

    # 清除历史
    if clear_history:
        st.session_state.conversation_history = []

    # 执行任务
    with st.spinner("🤖 Agent 团队正在工作中..."):
        try:
            if sequential:
                results = st.session_state.orchestrator.execute_sequential_workflow(task)
            else:
                results = st.session_state.orchestrator.execute_task(
                    task,
                    coder_first=coder_first,
                )

            # 存储结果
            st.session_state.conversation_history = results.get('conversation_history', [])
            st.session_state.execution_results = results
            st.session_state.task_completed = True

            # 重新运行以显示结果
            st.rerun()

        except Exception as e:
            st.error(f"执行失败: {e}")
            logger.error(f"Task execution failed: {e}", exc_info=True)


def main():
    """主应用"""
    setup_session_state()
    render_header()
    render_config_warning()
    render_sidebar()

    # 任务输入
    task, execute, coder_first, sequential, clear_history = render_task_input()

    # 执行任务
    if execute and task.strip():
        execute_task(task, coder_first, sequential, clear_history)

    # 显示结果
    render_execution_status()
    render_conversation_history()


if __name__ == '__main__':
    main()
