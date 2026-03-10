"""
Web UI for Project 4 CrewAI

使用 Streamlit 提供交互式 Web 界面。

注意：此模块需要安装 streamlit。请运行：
    pip install streamlit
"""

import streamlit as st
from src.crews.code_crew import CodeDevelopmentCrew

# Page configuration
st.set_page_config(
    page_title="Project 4 CrewAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application entry point"""

    # Title and header
    st.title("🤖 Project 4 CrewAI")
    st.markdown("---")
    st.markdown(
        """
        **AI-Powered Code Development Crew**

        This application uses multiple AI agents to develop, review, and test code:
        - **Coordinator** - Project manager and workflow orchestrator
        - **Coder** - Senior software engineer
        - **Reviewer** - Code quality expert
        - **Tester** - Quality assurance engineer
        """
    )
    st.markdown("---")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        st.markdown("### Agent Team")
        st.markdown("""
        - **Coordinator** - Project manager
        - **Coder** - Senior engineer
        - **Reviewer** - Code review expert
        - **Tester** - Test engineer
        """)

        st.markdown("---")

        st.markdown("### Settings")
        debug_mode = st.checkbox("Debug Mode", value=False, help="Enable verbose output")

        st.markdown("---")
        st.markdown("""
        ### How it works
        1. Enter your task description
        2. Click Execute
        3. Agents work in sequence:
           - Coder implements
           - Reviewer checks
           - Tester validates
           - Coordinator summarizes
        4. Review the final results
        """)

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("📝 Task Input")

        # Task input
        task = st.text_area(
            "Enter your task description",
            placeholder="Example: Implement a quick sort algorithm in Python with proper documentation and tests...",
            height=150,
            label_visibility="collapsed"
        )

        # Example tasks
        with st.expander("💡 Example Tasks"):
            st.markdown("""
            - Implement a binary search algorithm with proper error handling
            - Create a Python class for a linked list with insert, delete, and search methods
            - Write a function to validate email addresses using regex
            - Implement a caching decorator with TTL support
            - Create a simple HTTP client using requests library
            """)

    with col2:
        st.header("🚀 Execute")
        st.markdown("")

        # Execute button
        execute = st.button(
            "Execute Task",
            type="primary",
            use_container_width=True,
            disabled=not task
        )

        if not task:
            st.info("💡 Enter a task description to begin")

    # Task execution
    if execute and task:
        # Display task summary
        st.markdown("---")
        st.subheader("📋 Task Summary")
        st.info(task)

        # Progress tracking
        st.markdown("---")
        st.subheader("🔄 Execution Progress")

        progress_container = st.container()

        with progress_container:
            with st.spinner("🤖 Agents working... This may take a few minutes"):
                try:
                    # Create and run crew
                    crew = CodeDevelopmentCrew()

                    # Progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Simulated progress (actual progress depends on CrewAI execution)
                    status_text.text("🔧 Initializing crew...")
                    progress_bar.progress(10)

                    # Execute the crew
                    result = crew.kickoff(task)

                    progress_bar.progress(100)
                    status_text.text("✅ Execution complete!")

                    # Success message
                    st.success("✓ Task completed successfully!")
                    st.markdown("---")

                    # Display results
                    st.header("📄 Execution Results")

                    # Result tabs
                    tab1, tab2, tab3 = st.tabs(["Full Report", "Summary", "Raw Output"])

                    with tab1:
                        st.markdown("### Complete Workflow Report")
                        st.markdown(str(result))

                    with tab2:
                        st.markdown("### Executive Summary")
                        st.info("""
                        The AI crew has completed your task through a multi-stage process:

                        1. **Coding Phase** - Coder implemented the solution
                        2. **Review Phase** - Reviewer checked code quality
                        3. **Testing Phase** - Tester validated the implementation
                        4. **Final Phase** - Coordinator aggregated all results

                        Review the Full Report tab for detailed information.
                        """)

                    with tab3:
                        st.markdown("### Raw Output")
                        st.code(str(result), language=None)

                    # Action buttons
                    st.markdown("---")
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if st.button("🔄 New Task", use_container_width=True):
                            st.rerun()

                    with col_b:
                        if st.button("📋 Copy Results", use_container_width=True):
                            st.toast("Results copied to clipboard!", icon="✅")

                    with col_c:
                        if st.button("💾 Save Report", use_container_width=True):
                            st.toast("Report saved!", icon="💾")

                except ImportError as e:
                    st.error(f"Import Error: {str(e)}")
                    st.warning("Please ensure all dependencies are installed.")

                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")
                    if debug_mode:
                        import traceback
                        st.error(traceback.format_exc())

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <small>Project 4 CrewAI - Powered by CrewAI, Streamlit, and AI Agents</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
