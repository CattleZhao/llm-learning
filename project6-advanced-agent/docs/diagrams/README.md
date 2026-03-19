# Project 6: APK Malicious Behavior Analysis System - Architecture Diagrams

This directory contains 4 architectural diagrams for the APK Malicious Behavior Analysis System, created using draw.io format.

## Diagrams Overview

### 1. System Architecture Diagram (`system_architecture.drawio`)
**Purpose**: Shows the high-level three-tier architecture of the system.

**Components**:
- **Web UI Layer (Streamlit)**: User interface components including file upload, configuration, status display, and report viewer
- **Agent Layer**: Core analysis components including BaseAgent, APKAnalysisAgent (hardcoded flow), LLMAPKAnalysisAgent (LLM-driven), Anthropic Claude, and memory components
- **Tools Layer**: MCP Server, JADX-GUI, JADX AI MCP Plugin, and APK file handling

**Key Relationships**:
- HTTP requests from Web UI to Agent layer
- MCP calls (stdio) from Agent to MCP Server
- HTTP communication (Port 8650) between MCP Server and JADX Plugin
- APK loading into JADX-GUI

**Color Coding**:
- Blue: Web UI components
- Orange: Agent layer
- Green: Tools layer

---

### 2. Data Flow Diagram (`data_flow.drawio`)
**Purpose**: Illustrates how data flows through the system during APK analysis.

**Flow Sequence** (numbered 1-10):
1. **APK Input**: User uploads or provides APK path
2. **JADX Decompilation**: Open APK in JADX-GUI, extract source code and manifest
3. **MCP Server**: Expose JADX tools and handle tool calls
4. **Agent Analysis**: Call MCP tools, match rules, analyze patterns
5. **Collect Data**: Gather manifest, code paths, network info, API calls, strings
6. **Store Vectors**: Save analysis results to Chroma DB (long memory)
7. **Match Rules**: Apply package rules, URL blacklist, malware signatures
8. **Pattern Matching**: Use regex patterns, URL matching, risk calculation
9. **Generate Report**: Create security report with risk level, findings, mitigation
10. **Display**: Show report in Web UI with download option

**Data Storage**:
- **Chroma DB**: Vector embeddings for similarity search
- **Rule Base**: JSON files for detection rules
- **History Manager**: File-based history tracking

**Color Coding**:
- Red: APK input path
- Orange/Yellow: Analysis pipeline
- Green: Memory storage
- Dashed lines: Rule matching and references

---

### 3. Agent Class Diagram (`agent_class_diagram.drawio`)
**Purpose**: UML class diagram showing the main classes and their relationships.

**Key Classes**:

#### Abstract Base Class
- **BaseAgent**: Abstract base class with core agent interface
  - Methods: `think()`, `execute()`, `get_history()`, `reset()`
  - State management via `AgentState`

#### Concrete Agent Implementations
- **APKAnalysisAgent** (extends BaseAgent): Hardcoded 9-step analysis flow
  - Uses: StdioMCPClient, MalwareKnowledgeBase, RuleLoader
  - Methods: `_analyze_apk()`, `_analyze_permissions()`, `_match_package_rules()`

- **LLMAPKAnalysisAgent** (extends BaseAgent): LLM-driven analysis
  - Uses: Anthropic client, ToolExecutor, VectorStore, RuleLearner, HistoryManager
  - Methods: `_run_tool_loop()`, `_generate_fallback_report()`

#### Supporting Classes
- **StdioMCPClient**: MCP protocol client for JADX tool calls
  - Methods: `connect()`, `get_manifest()`, `get_permissions()`, `get_code_paths()`

- **HistoryManager**: APK analysis history management
  - Methods: `calculate_apk_hash()`, `load()`, `save()`, `list_history()`

- **VectorStore**: Chroma DB wrapper for vector storage
  - Methods: `store_analysis()`, `search_similar()`, `get_by_hash()`

#### Data Classes
- **AgentResponse**: Response dataclass (content, tool_calls, metadata)
- **AgentState**: State tracking dataclass

**UML Relationships**:
- **Inheritance** (dashed arrow with block): APKAnalysisAgent and LLMAPKAnalysisAgent extend BaseAgent
- **Composition** (solid line with diamond): Agents have MCP clients, memory managers
- **Association** (dashed line): BaseAgent uses AgentState, returns AgentResponse

---

### 4. Deployment Architecture Diagram (`deployment_architecture.drawio`)
**Purpose**: Shows how components are deployed in a local development environment.

**Deployment Components** (all on User's Machine):

#### User Interface
- **User Browser**: Chrome/Firefox/Edge accessing localhost:8501
- **Web UI Container**: Streamlit server on port 8501

#### Backend Services
- **Agent Service**: Python process running APK analysis agents
- **MCP Server**: jadx-mcp-server (uv run), stdio interface
- **JADX-GUI**: Desktop app with embedded plugin, HTTP server on port 8650
- **JADX AI MCP Plugin**: Tool implementations embedded in JADX-GUI

#### Data Storage
- **Chroma DB**: Vector database at `memory/chroma_db/`
- **History Storage**: JSON files at `memory/apk_history/`
- **Rule Base**: JSON files at `knowledge_base/raw/rules/`
- **Uploads Directory**: Temporary APK storage at `uploads/`

#### External Services
- **Anthropic API**: External Claude API (HTTPS)
- **Ollama Service** (optional): Embedding generation on port 11434

**Communication Protocols**:
- HTTP: Browser ↔ Web UI (8501)
- Python Call: Web UI → Agent
- stdio (JSON-RPC): Agent → MCP Server
- HTTP (8650): MCP Server ↔ JADX Plugin
- HTTPS: Agent → Anthropic API
- HTTP (11434): Chroma DB → Ollama (embeddings)

**Production Recommendations**:
- Web UI: Docker containerization
- Agent Service: API service (FastAPI/Flask)
- MCP Server: Process management (systemd/supervisord)
- Chroma DB: Persistent storage with backups
- Security: API key management, HTTPS

---

## How to View These Diagrams

### Option 1: Draw.io Web (Recommended)
1. Go to [app.diagrams.net](https://app.diagrams.net/)
2. Click "Open Existing Diagram"
3. Browse to the `.drawio` file and open it

### Option 2: Draw.io Desktop
1. Download [draw.io desktop](https://github.com/jgraph/drawio-desktop/releases)
2. Open the `.drawio` file directly

### Option 3: VS Code Extension
1. Install the "Draw.io Integration" extension
2. Open the `.drawio` file in VS Code
3. Right-click and select "Open Preview"

## Technical Details

- **Format**: Draw.io XML format
- **Compatibility**: Works with draw.io web, desktop, and VS Code extension
- **Editable**: All diagrams are fully editable and can be customized
- **Export**: Can be exported to PNG, SVG, PDF, etc. from draw.io

## Architecture Highlights

### Dual Agent Design
The system supports two agent modes:
1. **APKAnalysisAgent**: Fixed 9-step analysis pipeline, deterministic output
2. **LLMAPKAnalysisAgent**: LLM-driven tool selection, flexible analysis

### MCP Integration
- Uses Model Context Protocol (MCP) for tool communication
- stdio interface between Agent and MCP Server
- HTTP interface between MCP Server and JADX Plugin

### Memory System
- **Short-term**: HistoryManager (file-based JSON)
- **Long-term**: VectorStore (Chroma DB with embeddings)
- **Rule Learning**: RuleLearner extracts candidate rules from analysis

### Security Focus
- APK files deleted after analysis
- Sensitive info not logged
- Local deployment option (data stays on-premise)
- API keys via environment variables

---

**Created**: March 19, 2026
**Project**: Project 6 - APK Malicious Behavior Analysis System
**Technology**: MCP + LLM + JADX + Streamlit
