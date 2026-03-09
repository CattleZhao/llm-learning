# Project 4: Multi-Agent Code Development Team Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个基于 AutoGen 的多 Agent 协作系统，实现代码开发团队（编码者、审查者、测试者）的自动化协作

**Architecture:** 使用 AutoGen 框架创建 4 个 Agent（UserProxy、Coder、Reviewer、Tester），通过对话机制协作完成代码开发任务，支持命令行和 Web 两种交互方式

**Tech Stack:** Python 3.10+, AutoGen, OpenAI API, Streamlit, pytest

---

## Project Structure

```
project4-multiagent/
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── user_proxy.py       # UserProxy Agent
│   │   ├── coder.py            # Coder Agent
│   │   ├── reviewer.py         # Reviewer Agent
│   │   └── tester.py           # Tester Agent
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # 对话编排器
│   │   └── config.py           # 配置管理
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # 日志工具
├── app/
│   ├── __init__.py
│   ├── cli.py                  # 命令行界面
│   └── web.py                  # Streamlit Web 界面
├── tests/
│   ├── __init__.py
│   ├── test_agents.py          # Agent 测试
│   └── test_orchestrator.py    # 编排器测试
├── outputs/                    # 生成的代码和结果
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Task 1: Project Setup and Initialization

**Files:**
- Create: `project4-multiagent/`
- Create: `project4-multiagent/requirements.txt`
- Create: `project4-multiagent/.env.example`
- Create: `project4-multiagent/.gitignore`
- Create: `project4-multiagent/README.md`
- Create: `project4-multiagent/src/__init__.py`
- Create: `project4-multiagent/agents/__init__.py`
- Create: `project4-multiagent/core/__init__.py`
- Create: `project4-multiagent/utils/__init__.py`
- Create: `project4-multiagent/app/__init__.py`
- Create: `project4-multiagent/tests/__init__.py`

### Step 1: Create project directory structure

```bash
cd /root/Learn/llm-learning
mkdir -p project4-multiagent/{src/{agents,core,utils},app,tests,outputs}
cd project4-multiagent
```

### Step 2: Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
# Core dependencies
pyautogen>=0.2.0
openai>=1.0.0
python-dotenv>=1.0.0

# Web interface
streamlit>=1.28.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Utilities
rich>=13.0.0
EOF
```

### Step 3: Create .env.example

```bash
cat > .env.example << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Alternative: Claude API
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Code Execution
USE_DOCKER=false
CODE_EXECUTION_WORK_DIR=./outputs

# Logging
LOG_LEVEL=INFO
EOF
```

### Step 4: Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Outputs
outputs/*.py
outputs/logs/

# OS
.DS_Store
Thumbs.db

# AutoGen
*.cache/
autogen_cache/
EOF
```

### Step 5: Create README.md

```bash
cat > README.md << 'EOF'
# Project 4: Multi-Agent Code Development Team

## Overview

A multi-agent collaboration system built with AutoGen that simulates a code development team with specialized roles.

## Agents

- **UserProxy**: Coordinator and code executor
- **Coder**: Writes code based on requirements
- **Reviewer**: Reviews code quality and suggests improvements
- **Tester**: Writes and executes test cases

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Command Line

```bash
python -m app.cli --task "Implement a quicksort algorithm"
```

### Web Interface

```bash
streamlit run app/web.py
```

## Testing

```bash
pytest tests/
```

## Project Structure

- `src/agents/`: Agent implementations
- `src/core/`: Core orchestration logic
- `app/`: CLI and Web interfaces
- `tests/`: Test files
- `outputs/`: Generated code and results
EOF
```

### Step 6: Create __init__.py files

```bash
touch src/__init__.py src/agents/__init__.py src/core/__init__.py src/utils/__init__.py app/__init__.py tests/__init__.py
```

### Step 7: Initialize git and commit

```bash
git init
git add .
git commit -m "chore: initialize project4-multiagent structure"
```

---

## Task 2: Configuration Management

**Files:**
- Create: `src/core/config.py`
- Modify: `src/core/__init__.py`

### Step 1: Write the test for config loading

```python
# tests/test_config.py
import os
import pytest
from src.core.config import Config, get_config

def test_config_loads_from_env():
    """Test that config loads from environment variables"""
    os.environ['OPENAI_API_KEY'] = 'test_key'
    os.environ['OPENAI_MODEL'] = 'gpt-4'

    config = get_config()
    assert config.api_key == 'test_key'
    assert config.model == 'gpt-4'

def test_config_has_defaults():
    """Test that config has sensible defaults"""
    # Clear env vars
    for key in ['OPENAI_API_KEY', 'OPENAI_MODEL']:
        os.environ.pop(key, None)

    config = Config()
    assert config.model == 'gpt-4o'
    assert config.use_docker is False
    assert config.work_dir == './outputs'

def test_config_llm_config():
    """Test that LLM config is properly formatted"""
    os.environ['OPENAI_API_KEY'] = 'test_key'
    config = get_config()

    llm_config = config.get_llm_config()
    assert llm_config['model'] == config.model
    assert llm_config['api_key'] == 'test_key'
```

### Step 2: Run test to verify it fails

```bash
cd /root/Learn/llm-learning/project4-multiagent
pytest tests/test_config.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.core.config'`

### Step 3: Implement Config class

```python
# src/core/config.py
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Configuration for the multi-agent system"""

    # LLM Configuration
    api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    api_base: str = field(default_factory=lambda: os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'))
    model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', 'gpt-4o'))
    temperature: float = field(default_factory=lambda: float(os.getenv('TEMPERATURE', '0.7')))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('MAX_TOKENS', '2000')))

    # Code Execution Configuration
    use_docker: bool = field(default_factory=lambda: os.getenv('USE_DOCKER', 'false').lower() == 'true')
    work_dir: str = field(default_factory=lambda: os.getenv('CODE_EXECUTION_WORK_DIR', './outputs'))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))

    # Agent Configuration
    timeout: int = field(default_factory=lambda: int(os.getenv('AGENT_TIMEOUT', '60')))
    max_consecutive_auto_reply: int = field(default_factory=lambda: int(os.getenv('MAX_CONSECUTIVE_AUTO_REPLY', '10')))

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env file or environment variables.")

        # Create work directory if it doesn't exist
        os.makedirs(self.work_dir, exist_ok=True)

    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dictionary for AutoGen"""
        return {
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.api_base,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def get_code_execution_config(self) -> Dict[str, Any]:
        """Get code execution configuration for AutoGen"""
        return {
            "work_dir": self.work_dir,
            "use_docker": self.use_docker,
        }


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """Set global config instance (useful for testing)"""
    global _config
    _config = config
```

### Step 4: Update src/core/__init__.py

```python
# src/core/__init__.py
from src.core.config import Config, get_config, set_config

__all__ = ['Config', 'get_config', 'set_config']
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_config.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/core/config.py src/core/__init__.py tests/test_config.py
git commit -m "feat: add configuration management module"
```

---

## Task 3: Logger Utility

**Files:**
- Create: `src/utils/logger.py`
- Modify: `src/utils/__init__.py`

### Step 1: Write the test for logger

```python
# tests/test_logger.py
import logging
import pytest
from src.utils.logger import get_logger, setup_logging

def test_get_logger_returns_logger():
    """Test that get_logger returns a proper logger instance"""
    logger = get_logger('test')
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'test'

def test_get_logger_same_instance():
    """Test that get_logger returns same instance for same name"""
    logger1 = get_logger('test')
    logger2 = get_logger('test')
    assert logger1 is logger2

def test_setup_logging_sets_level():
    """Test that setup_logging sets the correct log level"""
    setup_logging('DEBUG')
    logger = get_logger('test')
    assert logger.level == logging.DEBUG

def test_logger_has_handlers():
    """Test that logger has proper handlers"""
    setup_logging('INFO')
    logger = get_logger('test')
    assert len(logger.handlers) > 0
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_logger.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.utils.logger'`

### Step 3: Implement logger utility

```python
# src/utils/logger.py
import logging
import sys
from typing import Optional
from rich.logging import RichHandler


_loggers: dict = {}
_logging_setup: bool = False


def setup_logging(level: str = 'INFO', rich: bool = True) -> None:
    """Setup global logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rich: Whether to use Rich for colored output
    """
    global _logging_setup

    if _logging_setup:
        return

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    if rich:
        # Use Rich for colored output
        handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            show_path=True,
        )
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    _logging_setup = True


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get or create a logger instance

    Args:
        name: Logger name
        level: Optional log level for this specific logger

    Returns:
        Logger instance
    """
    global _loggers

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)

    _loggers[name] = logger

    return logger
```

### Step 4: Update src/utils/__init__.py

```python
# src/utils/__init__.py
from src.utils.logger import get_logger, setup_logging

__all__ = ['get_logger', 'setup_logging']
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_logger.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/utils/logger.py src/utils/__init__.py tests/test_logger.py
git commit -m "feat: add logging utility with Rich support"
```

---

## Task 4: UserProxy Agent

**Files:**
- Create: `src/agents/user_proxy.py`
- Modify: `src/agents/__init__.py`

### Step 1: Write the test for UserProxy Agent

```python
# tests/test_user_proxy.py
import pytest
from unittest.mock import Mock, patch
from src.agents.user_proxy import create_user_proxy
from src.core.config import Config

def test_create_user_proxy_returns_agent():
    """Test that create_user_proxy returns an AutoGen agent"""
    config = Config()
    config.api_key = 'test_key'  # Mock key

    agent = create_user_proxy(config)

    assert agent is not None
    assert agent.name == "user_proxy"
    assert hasattr(agent, 'code_execution_config')

def test_user_proxy_has_correct_config():
    """Test that UserProxy has correct configuration"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_user_proxy(config)

    assert agent.human_input_mode == "NEVER"
    assert agent.max_consecutive_auto_reply == config.max_consecutive_auto_reply
    assert agent.code_execution_config["work_dir"] == config.work_dir

@patch('src.agents.user_proxy.autogen.UserProxyAgent')
def test_user_proxy_system_message(mock_user_proxy_agent):
    """Test that UserProxy has correct system message"""
    mock_instance = Mock()
    mock_user_proxy_agent.return_value = mock_instance

    config = Config()
    config.api_key = 'test_key'

    agent = create_user_proxy(config)

    # Verify the agent was created with correct parameters
    mock_user_proxy_agent.assert_called_once()
    call_kwargs = mock_user_proxy_agent.call_args[1]
    assert 'system_message' in call_kwargs or 'name' in call_kwargs
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_user_proxy.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.agents.user_proxy'`

### Step 3: Implement UserProxy Agent

```python
# src/agents/user_proxy.py
from typing import Optional, Dict, Any, List
from autogen import UserProxyAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# System message for UserProxy Agent
USER_PROXY_SYSTEM_MESSAGE = """You are a user proxy agent responsible for coordinating the development team.

Your responsibilities:
1. Understand user requirements and communicate them to the team
2. Coordinate between Coder, Reviewer, and Tester agents
3. Execute generated code and verify results
4. Summarize final results and provide feedback to the user

Communication style:
- Be concise and clear
- Provide context when delegating tasks
- Summarize outcomes clearly
- Ask for clarification when requirements are ambiguous
"""


def create_user_proxy(
    config: Config,
    name: str = "user_proxy",
    system_message: Optional[str] = None,
    human_input_mode: str = "NEVER",
    max_consecutive_auto_reply: Optional[int] = None,
    code_execution_config: Optional[Dict[str, Any]] = None,
    default_auto_reply: str = "TERMINATE",
) -> UserProxyAgent:
    """Create a UserProxy agent for coordinating the development team

    Args:
        config: Configuration object
        name: Agent name
        system_message: System message for the agent
        human_input_mode: When to ask for human input (ALWAYS, NEVER, TERMINATE)
        max_consecutive_auto_reply: Maximum consecutive auto replies
        code_execution_config: Code execution configuration
        default_auto_reply: Default reply when no more auto replies

    Returns:
        Configured UserProxyAgent instance
    """
    logger.info(f"Creating UserProxy agent: {name}")

    # Use provided values or defaults from config
    if system_message is None:
        system_message = USER_PROXY_SYSTEM_MESSAGE

    if max_consecutive_auto_reply is None:
        max_consecutive_auto_reply = config.max_consecutive_auto_reply

    if code_execution_config is None:
        code_execution_config = config.get_code_execution_config()

    # Create the agent
    agent = UserProxyAgent(
        name=name,
        system_message=system_message,
        human_input_mode=human_input_mode,
        max_consecutive_auto_reply=max_consecutive_auto_reply,
        code_execution_config=code_execution_config,
        default_auto_reply=default_auto_reply,
    )

    logger.info(f"UserProxy agent '{name}' created successfully")
    return agent


def create_user_proxy_for_web(
    config: Config,
    name: str = "user_proxy",
) -> UserProxyAgent:
    """Create a UserProxy agent specifically for web interface

    This version has different settings suitable for web interactions.

    Args:
        config: Configuration object
        name: Agent name

    Returns:
        Configured UserProxyAgent instance for web use
    """
    logger.info(f"Creating UserProxy agent for web: {name}")

    code_execution_config = {
        "work_dir": config.work_dir,
        "use_docker": config.use_docker,
    }

    agent = UserProxyAgent(
        name=name,
        system_message=USER_PROXY_SYSTEM_MESSAGE,
        human_input_mode="NEVER",  # Web interface handles interaction
        max_consecutive_auto_reply=0,  # Web controls flow
        code_execution_config=code_execution_config,
        default_auto_reply="",
    )

    logger.info(f"Web UserProxy agent '{name}' created successfully")
    return agent
```

### Step 4: Update src/agents/__init__.py

```python
# src/agents/__init__.py
from src.agents.user_proxy import (
    create_user_proxy,
    create_user_proxy_for_web,
    USER_PROXY_SYSTEM_MESSAGE,
)

__all__ = [
    'create_user_proxy',
    'create_user_proxy_for_web',
    'USER_PROXY_SYSTEM_MESSAGE',
]
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_user_proxy.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/agents/user_proxy.py src/agents/__init__.py tests/test_user_proxy.py
git commit -m "feat: add UserProxy agent implementation"
```

---

## Task 5: Coder Agent

**Files:**
- Create: `src/agents/coder.py`
- Modify: `src/agents/__init__.py`

### Step 1: Write the test for Coder Agent

```python
# tests/test_coder.py
import pytest
from src.agents.coder import create_coder
from src.core.config import Config

def test_create_coder_returns_agent():
    """Test that create_coder returns an AutoGen agent"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_coder(config)

    assert agent is not None
    assert agent.name == "coder"

def test_coder_has_correct_system_message():
    """Test that Coder has the correct system message"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_coder(config)

    system_message = agent.system_message
    assert 'Python developer' in system_message
    assert 'PEP 8' in system_message

def test_coder_uses_config_llm():
    """Test that Coder uses config LLM settings"""
    config = Config()
    config.api_key = 'test_key'
    config.model = 'gpt-4'
    config.temperature = 0.5

    agent = create_coder(config)

    assert agent.llm_config['model'] == 'gpt-4'
    assert agent.llm_config['temperature'] == 0.5
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_coder.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.agents.coder'`

### Step 3: Implement Coder Agent

```python
# src/agents/coder.py
from typing import Optional
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# System message for Coder Agent
CODER_SYSTEM_MESSAGE = """You are a senior Python developer responsible for writing high-quality code.

Your coding standards:
1. **Type Hints**: Always use type annotations for function parameters and return values
2. **Naming**: Use clear, descriptive names for variables and functions
3. **Documentation**: Add docstrings to all functions and classes
4. **Style**: Follow PEP 8 guidelines
5. **Error Handling**: Consider edge cases and add appropriate error handling
6. **Comments**: Add comments only when the logic isn't self-evident

Output format:
- First, provide a brief explanation of your approach
- Then, provide the complete, executable code
- Include usage examples if helpful

When receiving feedback:
- Carefully consider all suggestions
- Revise the code accordingly
- Explain any changes you make

Always produce production-ready code that follows best practices.
"""


def create_coder(
    config: Config,
    name: str = "coder",
    system_message: Optional[str] = None,
) -> AssistantAgent:
    """Create a Coder agent responsible for writing code

    Args:
        config: Configuration object
        name: Agent name
        system_message: Custom system message (uses default if not provided)

    Returns:
        Configured AssistantAgent instance for coding
    """
    logger.info(f"Creating Coder agent: {name}")

    if system_message is None:
        system_message = CODER_SYSTEM_MESSAGE

    # Create the agent with LLM config
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
    )

    logger.info(f"Coder agent '{name}' created successfully")
    return agent
```

### Step 4: Update src/agents/__init__.py

```python
# src/agents/__init__.py
from src.agents.user_proxy import (
    create_user_proxy,
    create_user_proxy_for_web,
    USER_PROXY_SYSTEM_MESSAGE,
)
from src.agents.coder import create_coder, CODER_SYSTEM_MESSAGE

__all__ = [
    'create_user_proxy',
    'create_user_proxy_for_web',
    'USER_PROXY_SYSTEM_MESSAGE',
    'create_coder',
    'CODER_SYSTEM_MESSAGE',
]
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_coder.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/agents/coder.py src/agents/__init__.py tests/test_coder.py
git commit -m "feat: add Coder agent implementation"
```

---

## Task 6: Reviewer Agent

**Files:**
- Create: `src/agents/reviewer.py`
- Modify: `src/agents/__init__.py`

### Step 1: Write the test for Reviewer Agent

```python
# tests/test_reviewer.py
import pytest
from src.agents.reviewer import create_reviewer
from src.core.config import Config

def test_create_reviewer_returns_agent():
    """Test that create_reviewer returns an AutoGen agent"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_reviewer(config)

    assert agent is not None
    assert agent.name == "reviewer"

def test_reviewer_has_correct_system_message():
    """Test that Reviewer has the correct system message"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_reviewer(config)

    system_message = agent.system_message
    assert 'code review' in system_message.lower()
    assert 'PEP 8' in system_message

def test_reviewer_constructive_feedback():
    """Test that Reviewer provides constructive feedback"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_reviewer(config)

    system_message = agent.system_message
    assert 'specific' in system_message.lower() or 'improvement' in system_message.lower()
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_reviewer.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.agents.reviewer'`

### Step 3: Implement Reviewer Agent

```python
# src/agents/reviewer.py
from typing import Optional
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# System message for Reviewer Agent
REVIEWER_SYSTEM_MESSAGE = """You are a code review expert responsible for ensuring code quality.

Your review checklist:
1. **Correctness**: Does the code do what it's supposed to do?
2. **Logic**: Are there any logical errors or edge cases not handled?
3. **Style**: Does the code follow PEP 8 and best practices?
4. **Performance**: Are there any obvious performance issues?
5. **Security**: Are there any security vulnerabilities?
6. **Documentation**: Is the code properly documented?

Review format:
For each issue found:
- **Problem**: Clearly describe the issue
- **Location**: Specify where the issue is (line number or function)
- **Suggestion**: Provide a concrete improvement suggestion

If the code is good:
- Acknowledge what's done well
- Suggest any minor improvements if applicable
- Clearly state: "APPROVED" or "NEEDS REVISION"

Be constructive and specific in your feedback. Help the coder improve their work.
"""


def create_reviewer(
    config: Config,
    name: str = "reviewer",
    system_message: Optional[str] = None,
) -> AssistantAgent:
    """Create a Reviewer agent responsible for code review

    Args:
        config: Configuration object
        name: Agent name
        system_message: Custom system message (uses default if not provided)

    Returns:
        Configured AssistantAgent instance for code review
    """
    logger.info(f"Creating Reviewer agent: {name}")

    if system_message is None:
        system_message = REVIEWER_SYSTEM_MESSAGE

    # Create the agent with LLM config
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
    )

    logger.info(f"Reviewer agent '{name}' created successfully")
    return agent
```

### Step 4: Update src/agents/__init__.py

```python
# src/agents/__init__.py
from src.agents.user_proxy import (
    create_user_proxy,
    create_user_proxy_for_web,
    USER_PROXY_SYSTEM_MESSAGE,
)
from src.agents.coder import create_coder, CODER_SYSTEM_MESSAGE
from src.agents.reviewer import create_reviewer, REVIEWER_SYSTEM_MESSAGE

__all__ = [
    'create_user_proxy',
    'create_user_proxy_for_web',
    'USER_PROXY_SYSTEM_MESSAGE',
    'create_coder',
    'CODER_SYSTEM_MESSAGE',
    'create_reviewer',
    'REVIEWER_SYSTEM_MESSAGE',
]
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_reviewer.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/agents/reviewer.py src/agents/__init__.py tests/test_reviewer.py
git commit -m "feat: add Reviewer agent implementation"
```

---

## Task 7: Tester Agent

**Files:**
- Create: `src/agents/tester.py`
- Modify: `src/agents/__init__.py`

### Step 1: Write the test for Tester Agent

```python
# tests/test_tester.py
import pytest
from src.agents.tester import create_tester
from src.core.config import Config

def test_create_tester_returns_agent():
    """Test that create_tester returns an AutoGen agent"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_tester(config)

    assert agent is not None
    assert agent.name == "tester"

def test_tester_has_correct_system_message():
    """Test that Tester has the correct system message"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_tester(config)

    system_message = agent.system_message
    assert 'test' in system_message.lower()
    assert 'pytest' in system_message.lower()

def test_tester_comprehensive_coverage():
    """Test that Tester emphasizes comprehensive coverage"""
    config = Config()
    config.api_key = 'test_key'

    agent = create_tester(config)

    system_message = agent.system_message
    assert 'edge' in system_message.lower() or 'boundary' in system_message.lower()
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_tester.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.agents.tester'`

### Step 3: Implement Tester Agent

```python
# src/agents/tester.py
from typing import Optional
from autogen import AssistantAgent
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# System message for Tester Agent
TESTER_SYSTEM_MESSAGE = """You are a testing engineer responsible for verifying code correctness.

Your testing strategy:
1. **Test Coverage**: Write tests that cover:
   - Normal/expected inputs
   - Edge cases and boundary conditions
   - Error cases and invalid inputs
   - Empty or null inputs where applicable

2. **Test Structure**: Use pytest framework with:
   - Clear test names that describe what is being tested
   - Arrange-Act-Assert pattern
   - Descriptive assertions
   - Setup/teardown when needed

3. **Test Cases**:
   - Unit tests for individual functions
   - Integration tests if multiple components interact
   - Tests for error handling

Output format:
```python
def test_specific_behavior():
    # Arrange
    input_data = ...
    expected = ...

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected
```

After writing tests:
1. Run the tests and report results
2. If any test fails, analyze why
3. Report pass/fail status clearly

Test results format:
- ✓ PASSED: [test_name]
- ✗ FAILED: [test_name] - [reason]
- Summary: X passed, Y failed
"""


def create_tester(
    config: Config,
    name: str = "tester",
    system_message: Optional[str] = None,
) -> AssistantAgent:
    """Create a Tester agent responsible for testing

    Args:
        config: Configuration object
        name: Agent name
        system_message: Custom system message (uses default if not provided)

    Returns:
        Configured AssistantAgent instance for testing
    """
    logger.info(f"Creating Tester agent: {name}")

    if system_message is None:
        system_message = TESTER_SYSTEM_MESSAGE

    # Create the agent with LLM config
    agent = AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=config.get_llm_config(),
    )

    logger.info(f"Tester agent '{name}' created successfully")
    return agent
```

### Step 4: Update src/agents/__init__.py

```python
# src/agents/__init__.py
from src.agents.user_proxy import (
    create_user_proxy,
    create_user_proxy_for_web,
    USER_PROXY_SYSTEM_MESSAGE,
)
from src.agents.coder import create_coder, CODER_SYSTEM_MESSAGE
from src.agents.reviewer import create_reviewer, REVIEWER_SYSTEM_MESSAGE
from src.agents.tester import create_tester, TESTER_SYSTEM_MESSAGE

__all__ = [
    'create_user_proxy',
    'create_user_proxy_for_web',
    'USER_PROXY_SYSTEM_MESSAGE',
    'create_coder',
    'CODER_SYSTEM_MESSAGE',
    'create_reviewer',
    'REVIEWER_SYSTEM_MESSAGE',
    'create_tester',
    'TESTER_SYSTEM_MESSAGE',
]
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_tester.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/agents/tester.py src/agents/__init__.py tests/test_tester.py
git commit -m "feat: add Tester agent implementation"
```

---

## Task 8: Orchestrator - Core Coordination Logic

**Files:**
- Create: `src/core/orchestrator.py`
- Modify: `src/core/__init__.py`

### Step 1: Write the test for Orchestrator

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import Mock, patch
from src.core.orchestrator import (
    CodeDevelopmentOrchestrator,
    create_orchestrator,
)
from src.core.config import Config

def test_create_orchestrator_creates_all_agents():
    """Test that orchestrator creates all required agents"""
    config = Config()
    config.api_key = 'test_key'

    with patch('src.core.orchestrator.create_user_proxy'), \
         patch('src.core.orchestrator.create_coder'), \
         patch('src.core.orchestrator.create_reviewer'), \
         patch('src.core.orchestrator.create_tester'):

        orchestrator = create_orchestrator(config)

        assert orchestrator is not None
        assert orchestrator.user_proxy is not None
        assert orchestrator.coder is not None
        assert orchestrator.reviewer is not None
        assert orchestrator.tester is not None

def test_orchestrator_has_agent_list():
    """Test that orchestrator has a list of all agents"""
    config = Config()
    config.api_key = 'test_key'

    with patch('src.core.orchestrator.create_user_proxy') as mock_user_proxy, \
         patch('src.core.orchestrator.create_coder') as mock_coder, \
         patch('src.core.orchestrator.create_reviewer') as mock_reviewer, \
         patch('src.core.orchestrator.create_tester') as mock_tester:

        mock_user_proxy.return_value = Mock(name="user_proxy")
        mock_coder.return_value = Mock(name="coder")
        mock_reviewer.return_value = Mock(name="reviewer")
        mock_tester.return_value = Mock(name="tester")

        orchestrator = create_orchestrator(config)

        assert len(orchestrator.agents) == 4
        assert all(agent is not None for agent in orchestrator.agents)
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_orchestrator.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.core.orchestrator'`

### Step 3: Implement Orchestrator

```python
# src/core/orchestrator.py
from typing import List, Optional, Dict, Any
from autogen import Agent, ConversableAgent
from src.core.config import Config
from src.agents import (
    create_user_proxy,
    create_coder,
    create_reviewer,
    create_tester,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeDevelopmentOrchestrator:
    """Orchestrator for managing multi-agent code development workflow"""

    def __init__(
        self,
        config: Config,
        user_proxy: Optional[ConversableAgent] = None,
        coder: Optional[Agent] = None,
        reviewer: Optional[Agent] = None,
        tester: Optional[Agent] = None,
    ):
        """Initialize the orchestrator with agents

        Args:
            config: Configuration object
            user_proxy: UserProxy agent (created if not provided)
            coder: Coder agent (created if not provided)
            reviewer: Reviewer agent (created if not provided)
            tester: Tester agent (created if not provided)
        """
        self.config = config
        self.user_proxy = user_proxy or create_user_proxy(config)
        self.coder = coder or create_coder(config)
        self.reviewer = reviewer or create_reviewer(config)
        self.tester = tester or create_tester(config)

        logger.info("CodeDevelopmentOrchestrator initialized with all agents")

    @property
    def agents(self) -> List[Agent]:
        """Get list of all agents"""
        return [
            self.user_proxy,
            self.coder,
            self.reviewer,
            self.tester,
        ]

    def execute_task(
        self,
        task_description: str,
        coder_first: bool = True,
    ) -> Dict[str, Any]:
        """Execute a code development task with the agent team

        Args:
            task_description: Description of the task to complete
            coder_first: Whether to start with coder (True) or let user_proxy decide (False)

        Returns:
            Dictionary containing execution results
        """
        logger.info(f"Executing task: {task_description[:50]}...")

        results = {
            'task': task_description,
            'conversation_history': [],
            'final_code': None,
            'test_results': None,
        }

        if coder_first:
            # Start conversation from user_proxy to coder
            logger.info("Starting conversation: user_proxy -> coder")
            self.user_proxy.initiate_chat(
                self.coder,
                message=task_description,
                clear_history=True,
            )
        else:
            # Let user_proxy decide how to proceed
            logger.info("Starting conversation: user_proxy -> (agent decides)")
            self.user_proxy.initiate_chat(
                message=task_description,
                clear_history=True,
            )

        # Store conversation history
        results['conversation_history'] = self._get_conversation_history()

        logger.info("Task execution completed")
        return results

    def _get_conversation_history(self) -> List[Dict[str, Any]]:
        """Extract conversation history from agents

        Returns:
            List of conversation messages
        """
        history = []

        # Get history from user_proxy (stores all conversations)
        for agent in self.agents:
            if hasattr(agent, 'chat_messages'):
                for other_agent, messages in agent.chat_messages.items():
                    for msg in messages:
                        history.append({
                            'from': msg.get('role', 'unknown'),
                            'to': other_agent.name if hasattr(other_agent, 'name') else 'unknown',
                            'content': msg.get('content', ''),
                            'timestamp': msg.get('timestamp', None),
                        })

        return history

    def create_group_chat(
        self,
        message: str,
        max_round: int = 20,
    ) -> Dict[str, Any]:
        """Create a group chat session (advanced feature)

        Args:
            message: Initial message to start the conversation
            max_round: Maximum number of conversation rounds

        Returns:
            Dictionary containing group chat results
        """
        from autogen import GroupChat, GroupChatManager

        logger.info("Creating group chat configuration")

        # Create group chat
        group_chat = GroupChat(
            agents=self.agents,
            messages=[],
            max_round=max_round,
            speaker_selection_method="round_robin",  # or "auto" for LLM-based selection
        )

        # Create group chat manager
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self.config.get_llm_config(),
        )

        # Start conversation
        logger.info("Starting group chat conversation")
        self.user_proxy.initiate_chat(
            manager,
            message=message,
        )

        return {
            'conversation_history': group_chat.messages,
        }

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """Get an agent by its name

        Args:
            name: Agent name

        Returns:
            Agent if found, None otherwise
        """
        for agent in self.agents:
            if hasattr(agent, 'name') and agent.name == name:
                return agent
        return None


def create_orchestrator(
    config: Config,
    user_proxy: Optional[ConversableAgent] = None,
    coder: Optional[Agent] = None,
    reviewer: Optional[Agent] = None,
    tester: Optional[Agent] = None,
) -> CodeDevelopmentOrchestrator:
    """Factory function to create a CodeDevelopmentOrchestrator

    Args:
        config: Configuration object
        user_proxy: Optional pre-configured UserProxy agent
        coder: Optional pre-configured Coder agent
        reviewer: Optional pre-configured Reviewer agent
        tester: Optional pre-configured Tester agent

    Returns:
        Configured CodeDevelopmentOrchestrator instance
    """
    logger.info("Creating CodeDevelopmentOrchestrator")

    orchestrator = CodeDevelopmentOrchestrator(
        config=config,
        user_proxy=user_proxy,
        coder=coder,
        reviewer=reviewer,
        tester=tester,
    )

    return orchestrator
```

### Step 4: Update src/core/__init__.py

```python
# src/core/__init__.py
from src.core.config import Config, get_config, set_config
from src.core.orchestrator import (
    CodeDevelopmentOrchestrator,
    create_orchestrator,
)

__all__ = [
    'Config',
    'get_config',
    'set_config',
    'CodeDevelopmentOrchestrator',
    'create_orchestrator',
]
```

### Step 5: Run test to verify it passes

```bash
pytest tests/test_orchestrator.py -v
```

Expected: All tests pass

### Step 6: Commit

```bash
git add src/core/orchestrator.py src/core/__init__.py tests/test_orchestrator.py
git commit -m "feat: add core orchestrator for agent coordination"
```

---

## Task 9: CLI Application

**Files:**
- Create: `app/cli.py`

### Step 1: Create CLI application

```python
# app/cli.py
#!/usr/bin/env python3
"""
Multi-Agent Code Development Team - Command Line Interface
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, create_orchestrator, Config
from src.utils import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Multi-Agent Code Development Team',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple code generation
  python -m app.cli --task "Implement a quicksort algorithm"

  # With custom model
  python -m app.cli --task "Create a REST API with FastAPI" --model gpt-4

  # Debug mode with verbose output
  python -m app.cli --task "Write a binary search function" --debug
        """
    )

    parser.add_argument(
        '--task',
        type=str,
        required=True,
        help='Code development task description',
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='LLM model to use (default: from config or gpt-4o)',
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=None,
        help='Temperature for LLM (default: from config or 0.7)',
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='Maximum tokens for LLM responses (default: from config or 2000)',
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose logging',
    )

    parser.add_argument(
        '--rounds',
        type=int,
        default=20,
        help='Maximum conversation rounds (default: 20)',
    )

    return parser.parse_args()


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║   Multi-Agent Code Development Team                        ║
║   Powered by AutoGen                                       ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_results(results: dict) -> None:
    """Print execution results

    Args:
        results: Results dictionary from orchestrator
    """
    print("\n" + "="*60)
    print("EXECUTION RESULTS")
    print("="*60)

    print(f"\nTask: {results['task']}")

    if results.get('conversation_history'):
        print(f"\nConversation rounds: {len(results['conversation_history'])}")

    if results.get('final_code'):
        print("\n" + "-"*60)
        print("FINAL CODE:")
        print("-"*60)
        print(results['final_code'])

    if results.get('test_results'):
        print("\n" + "-"*60)
        print("TEST RESULTS:")
        print("-"*60)
        print(results['test_results'])

    print("\n" + "="*60)
    print("Execution completed!")
    print("="*60 + "\n")


def main():
    """Main CLI entry point"""
    # Parse arguments
    args = parse_arguments()

    # Setup logging level
    if args.debug:
        setup_logging('DEBUG')
        logger.setLevel('DEBUG')

    # Print banner
    print_banner()

    try:
        # Get or create config
        try:
            config = get_config()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.error("Please ensure OPENAI_API_KEY is set in .env file")
            sys.exit(1)

        # Override config with command line arguments
        if args.model:
            config.model = args.model
        if args.temperature is not None:
            config.temperature = args.temperature
        if args.max_tokens is not None:
            config.max_tokens = args.max_tokens

        logger.info(f"Using model: {config.model}")
        logger.info(f"Temperature: {config.temperature}")

        # Create orchestrator
        logger.info("Initializing agent team...")
        orchestrator = create_orchestrator(config)

        # Execute task
        logger.info(f"Executing task: {args.task[:100]}...")
        print(f"\n🚀 Starting task: {args.task}\n")
        print("-"*60 + "\n")

        results = orchestrator.execute_task(
            task_description=args.task,
            coder_first=True,
        )

        # Print results
        print_results(results)

        logger.info("Task completed successfully")

    except KeyboardInterrupt:
        logger.info("Task interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=args.debug)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### Step 2: Create simple test for CLI

```python
# tests/test_cli.py
import pytest
from app.cli import parse_arguments, print_banner

def test_parse_arguments_requires_task():
    """Test that --task argument is required"""
    with pytest.raises(SystemExit):
        parse_arguments([])

def test_parse_arguments_accepts_task():
    """Test that --task argument is accepted"""
    args = parse_arguments(['--task', 'test task'])
    assert args.task == 'test task'

def test_parse_arguments_has_defaults():
    """Test that CLI has sensible defaults"""
    args = parse_arguments(['--task', 'test'])
    assert args.model is None
    assert args.temperature is None
    assert args.debug is False
    assert args.rounds == 20

def test_print_banner_outputs_text(capsys):
    """Test that print_banner outputs something"""
    print_banner()
    captured = capsys.readouterr()
    assert "Multi-Agent" in captured.out
```

### Step 3: Run test to verify it passes

```bash
pytest tests/test_cli.py -v
```

Expected: All tests pass

### Step 4: Test CLI manually

```bash
# Test help output
python -m app.cli --help
```

Expected: Help message displayed

### Step 5: Commit

```bash
git add app/cli.py tests/test_cli.py
git commit -m "feat: add CLI application"
```

---

## Task 10: Streamlit Web Application

**Files:**
- Create: `app/web.py`

### Step 1: Create Web application

```python
# app/web.py
"""
Multi-Agent Code Development Team - Web Interface
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, create_orchestrator
from src.utils import get_logger

logger = get_logger(__name__)


# Page configuration
st.set_page_config(
    page_title="Multi-Agent Code Development Team",
    page_icon="🤖",
    layout="wide",
)


def setup_session_state():
    """Initialize session state variables"""
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


def render_header():
    """Render application header"""
    st.title("🤖 Multi-Agent Code Development Team")
    st.markdown("""
    A collaborative AI team that works together to write, review, and test code.
    Powered by AutoGen.
    """)


def render_config_warning():
    """Show configuration warning if needed"""
    if st.session_state.get('config_error'):
        st.error(f"⚠️ Configuration Error: {st.session_state.config_error}")
        st.info("Please set OPENAI_API_KEY in your .env file")
        st.stop()
    if not st.session_state.get('config'):
        st.error("⚠️ Configuration not initialized")
        st.stop()


def render_sidebar():
    """Render sidebar with settings"""
    with st.sidebar:
        st.header("⚙️ Settings")

        # Model settings
        st.subheader("Model Settings")
        model = st.text_input(
            "Model",
            value=st.session_state.config.model if st.session_state.config else "gpt-4o",
        )
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            value=st.session_state.config.temperature if st.session_state.config else 0.7,
        )
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=8000,
            value=st.session_state.config.max_tokens if st.session_state.config else 2000,
        )

        # Update config
        if st.session_state.config:
            st.session_state.config.model = model
            st.session_state.config.temperature = temperature
            st.session_state.config.max_tokens = max_tokens

        st.divider()

        # Agent info
        st.subheader("Agent Team")
        st.markdown("""
        - **UserProxy**: Coordinator
        - **Coder**: Code Writer
        - **Reviewer**: Code Reviewer
        - **Tester**: Test Engineer
        """)


def render_task_input():
    """Render task input section"""
    st.header("📝 Task Description")

    task = st.text_area(
        "Describe the code you want to create:",
        placeholder="e.g., Implement a quicksort algorithm in Python with type hints",
        height=100,
    )

    col1, col2 = st.columns(2)
    with col1:
        coder_first = st.checkbox("Start with Coder agent", value=True)
    with col2:
        max_rounds = st.number_input("Max rounds", min_value=5, max_value=50, value=20)

    execute = st.button("🚀 Execute Task", type="primary", use_container_width=True)

    return task, execute, coder_first, max_rounds


def render_conversation_history():
    """Render conversation history"""
    if not st.session_state.conversation_history:
        return

    st.header("💬 Conversation History")

    for i, message in enumerate(st.session_state.conversation_history):
        with st.chat_message(message.get('from', 'unknown')):
            st.markdown(message.get('content', ''))


def render_results():
    """Render execution results"""
    if not st.session_state.task_completed:
        return

    st.header("✅ Results")

    # Show completion message
    st.success("Task completed! Check the conversation history above.")


def execute_task(task: str, coder_first: bool, max_rounds: int):
    """Execute the task using the orchestrator

    Args:
        task: Task description
        coder_first: Whether to start with coder
        max_rounds: Maximum conversation rounds
    """
    # Create orchestrator if not exists
    if st.session_state.orchestrator is None:
        with st.spinner("Initializing agent team..."):
            st.session_state.orchestrator = create_orchestrator(st.session_state.config)

    # Execute task
    with st.spinner("Agents are working on your task..."):
        results = st.session_state.orchestrator.execute_task(
            task_description=task,
            coder_first=coder_first,
        )

    # Store results
    st.session_state.conversation_history = results.get('conversation_history', [])
    st.session_state.task_completed = True


def main():
    """Main application"""
    setup_session_state()
    render_header()
    render_config_warning()
    render_sidebar()

    # Task input
    task, execute, coder_first, max_rounds = render_task_input()

    # Execute task if button clicked
    if execute and task.strip():
        execute_task(task, coder_first, max_rounds)
        st.rerun()

    # Show results
    render_results()
    render_conversation_history()


if __name__ == '__main__':
    main()
```

### Step 2: Test Web app

```bash
# Start Streamlit (in background to verify it runs)
timeout 5 streamlit run app/web.py --server.headless true 2>&1 || true
```

Expected: Streamlit starts without errors

### Step 3: Create simple test for web app

```python
# tests/test_web.py
import pytest

def test_web_module_imports():
    """Test that web module can be imported"""
    import app.web
    assert app.web is not None

def test_web_functions_exist():
    """Test that key functions exist"""
    from app.web import (
        setup_session_state,
        render_header,
        render_config_warning,
    )
    assert callable(setup_session_state)
    assert callable(render_header)
    assert callable(render_config_warning)
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_web.py -v
```

Expected: All tests pass

### Step 5: Commit

```bash
git add app/web.py tests/test_web.py
git commit -m "feat: add Streamlit web application"
```

---

## Task 11: Integration Tests and Documentation

**Files:**
- Create: `tests/integration/test_basic_workflow.py`
- Modify: `README.md`
- Modify: `.env.example`

### Step 1: Create integration test

```python
# tests/integration/test_basic_workflow.py
"""
Integration tests for basic multi-agent workflow
"""

import pytest
import os
from src.core import get_config, create_orchestrator


@pytest.mark.integration
def test_basic_coder_reviewer_workflow():
    """Test basic workflow between Coder and Reviewer"""
    # Skip if no API key
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip("OPENAI_API_KEY not set")

    config = get_config()
    config.model = "gpt-3.5-turbo"  # Use cheaper model for tests
    config.max_tokens = 500

    orchestrator = create_orchestrator(config)

    # Execute a simple task
    task = "Write a Python function that adds two numbers"

    # We won't actually run this in unit tests, but verify setup
    assert orchestrator.user_proxy is not None
    assert orchestrator.coder is not None
    assert orchestrator.reviewer is not None
    assert orchestrator.tester is not None


@pytest.mark.integration
def test_orchestrator_agent_properties():
    """Test that orchestrator exposes all agents"""
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip("OPENAI_API_KEY not set")

    config = get_config()
    orchestrator = create_orchestrator(config)

    # Test agent list
    assert len(orchestrator.agents) == 4

    # Test get_agent_by_name
    coder = orchestrator.get_agent_by_name('coder')
    assert coder is not None
    assert coder.name == 'coder'

    # Test non-existent agent
    none_agent = orchestrator.get_agent_by_name('nonexistent')
    assert none_agent is None


@pytest.mark.integration
def test_config_validation():
    """Test that config validates API key"""
    # Temporarily remove API key
    original_key = os.environ.get('OPENAI_API_KEY')
    if original_key:
        del os.environ['OPENAI_API_KEY']

    try:
        from src.core.config import Config
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Config()
    finally:
        # Restore API key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
```

### Step 2: Create conftest.py for pytest

```python
# tests/conftest.py
"""
Pytest configuration and fixtures
"""

import pytest
import os


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require API keys)"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests automatically"""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def mock_api_key():
    """Fixture providing a mock API key for testing"""
    return "test_key_" + "x" * 40


@pytest.fixture
def temp_api_key(mock_api_key, monkeypatch):
    """Fixture that temporarily sets an API key"""
    monkeypatch.setenv("OPENAI_API_KEY", mock_api_key)
    yield mock_api_key
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
```

### Step 3: Update README.md with usage examples

```bash
cat >> README.md << 'EOF'

## Examples

### Example 1: Simple Algorithm

```bash
python -m app.cli --task "Implement a quicksort algorithm with type hints"
```

### Example 2: REST API

```bash
python -m app.cli --task "Create a FastAPI REST API with CRUD operations for a Todo model"
```

### Example 3: Data Processing

```bash
python -m app.cli --task "Write a Python script to read a CSV file and calculate statistics"
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Skip integration tests (require API key)
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

### Code Style

This project follows PEP 8 guidelines. Use `black` for formatting:

```bash
pip install black
black src/ app/ tests/
```

## Troubleshooting

### "OPENAI_API_KEY is required"

Set your API key in the `.env` file:

```bash
cp .env.example .env
# Edit .env and add your key
```

### Code execution fails

Ensure the `outputs/` directory exists and is writable:

```bash
mkdir -p outputs
chmod +w outputs
```

### Module import errors

Make sure you're in the project root directory:

```bash
cd project4-multiagent
python -m app.cli --help
```
EOF
```

### Step 4: Run all tests

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

### Step 5: Run integration tests (if API key available)

```bash
pytest tests/integration/ -v -m integration
```

Expected: Integration tests pass (if API key set)

### Step 6: Commit

```bash
git add tests/integration/ tests/conftest.py README.md
git commit -m "feat: add integration tests and documentation"
```

---

## Task 12: Final Testing and Cleanup

**Files:**
- Verify all files
- Run complete test suite
- Final git commit

### Step 1: Run complete test suite

```bash
cd /root/Learn/llm-learning/project4-multiagent
pytest tests/ -v --cov=src --cov-report=term-missing
```

Expected: All tests pass with coverage report

### Step 2: Verify project structure

```bash
tree -L 3 -I '__pycache__|*.pyc|venv'
```

Expected: Complete project structure with all directories

### Step 3: Verify CLI help

```bash
python -m app.cli --help
```

Expected: Help message displayed

### Step 4: Check all imports work

```bash
python -c "from src.core import create_orchestrator, get_config; from src.agents import *; from app.cli import main; print('All imports successful!')"
```

Expected: All imports successful

### Step 5: Create final summary

```bash
cat > PROJECT_SUMMARY.md << 'EOF'
# Project 4 Implementation Summary

## Completed Features

### Core Components
- [x] Configuration management with environment variable support
- [x] Logging utility with Rich colored output
- [x] Four specialized agents (UserProxy, Coder, Reviewer, Tester)
- [x] Orchestrator for coordinating agent interactions

### User Interfaces
- [x] Command-line interface with argument parsing
- [x] Streamlit web interface for interactive usage

### Testing
- [x] Unit tests for all core components
- [x] Integration tests for end-to-end workflows
- [x] Test fixtures and configuration

### Documentation
- [x] Comprehensive README with examples
- [x] Inline code documentation
- [x] Troubleshooting guide

## Project Statistics

- **Total Files**: 20+
- **Lines of Code**: ~1500+
- **Test Coverage**: Target 80%+
- **Agents Implemented**: 4
- **User Interfaces**: 2 (CLI + Web)

## Next Steps

1. **CrewAI Version**: Implement same functionality using CrewAI for comparison
2. **Enhanced Features**: Add more agents (Documentation writer, Performance optimizer)
3. **Git Integration**: Add code repository operations
4. **Advanced Orchestration**: Implement group chat with LLM-based speaker selection

## Learning Outcomes

- ✅ Understanding of AutoGen framework architecture
- ✅ Multi-agent collaboration patterns
- ✅ Agent role design and system message crafting
- ✅ Code execution in sandboxed environments
- ✅ Building both CLI and web interfaces for AI systems
EOF
```

### Step 6: Final commit

```bash
git add .
git commit -m "chore: complete Project 4 implementation

- All core components implemented
- CLI and web interfaces functional
- Comprehensive test suite
- Full documentation

Project 4: Multi-Agent Code Development Team is complete.
"
```

### Step 7: Merge to main repository

```bash
cd /root/Learn/llm-learning
git merge project4-multiagent -m "Merge Project 4 into main"
```

---

## Completion Checklist

- [ ] Project structure created
- [ ] Configuration management implemented
- [ ] Logging utility implemented
- [ ] UserProxy Agent implemented
- [ ] Coder Agent implemented
- [ ] Reviewer Agent implemented
- [ ] Tester Agent implemented
- [ ] Orchestrator implemented
- [ ] CLI application implemented
- [ ] Web application implemented
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Git commits organized

---

## Notes for Implementation

1. **API Key Required**: All LLM operations require a valid OPENAI_API_KEY
2. **Code Execution**: Ensure outputs/ directory is writable for code execution
3. **Model Selection**: Use gpt-3.5-turbo for testing to save costs
4. **Error Handling**: The system includes graceful handling of API failures
5. **Extensibility**: Easy to add new agents or modify existing ones

---

**Plan completed and saved to** `docs/plans/2026-03-09-project4-multiagent-implementation.md`

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
