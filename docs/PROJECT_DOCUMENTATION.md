# Java Codebase Analyzer - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Core Components](#core-components)
6. [Data Flow](#data-flow)
7. [API Keys & Configuration](#api-keys--configuration)
8. [Deployment Guide](#deployment-guide)
9. [Usage Guide](#usage-guide)
10. [Code Conventions](#code-conventions)
11. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What It Does
An AI-powered static analysis platform that automatically parses, understands, and visualizes Java codebases from GitHub repositories. Built with LangChain agents, knowledge graphs, and Google Gemini 2.0.

### Key Features
- **GitHub Integration**: Clone and analyze any public Java repository
- **Framework Detection**: Automatically identifies Spring Boot, Struts, JAX-RS, Servlet/JSP, etc.
- **Knowledge Graph**: Creates complete structural representation (classes, methods, fields, relationships)
- **RAG System**: FAISS-based vector search with Gemini embeddings
- **Multi-Agent Architecture**: Specialized AI agents for framework-aware analysis
- **Architecture Reports**: Generates comprehensive architecture analysis
- **Mermaid Diagrams**: Creates component and class diagrams
- **JSON Export**: Export complete graph structure

### Use Cases
- **Legacy Code Analysis**: Understand old Java codebases quickly
- **Migration Planning**: Analyze architecture before migration
- **Code Documentation**: Auto-generate architecture documentation
- **Framework Detection**: Identify which framework a project uses
- **Codebase Onboarding**: Help new developers understand the structure

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                        │
│                      (app_v2.py)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   GitHub     │ │  Parser  │ │  Knowledge   │
│   Cloner     │ │ (tree-   │ │    Graph     │
│              │ │ sitter)  │ │  (NetworkX)  │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │               │
       └──────────────┴───────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Framework   │ │   RAG    │ │   Report     │
│  Detection   │ │  System  │ │  Generator   │
│  (Gemini)    │ │ (FAISS)  │ │  (Agents)    │
└──────────────┘ └──────────┘ └──────────────┘
```

### Processing Pipeline

```
1. GitHub URL Input
   └─> GitHubCloner clones repo to /tmp/codebase_analysis/

2. Parsing Phase
   ├─> GenericJavaParser (tree-sitter) extracts:
   │   ├─> Classes, Interfaces, Enums
   │   ├─> Methods, Fields
   │   └─> Annotations
   └─> RelationshipExtractor builds relationships:
       ├─> CALLS (method -> method)
       ├─> EXTENDS (class -> class)
       ├─> IMPLEMENTS (class -> interface)
       └─> DECLARES (class -> method/field)

3. Knowledge Graph Construction
   └─> KnowledgeGraph (NetworkX MultiDiGraph)
       ├─> Nodes: Classes, Methods, Fields
       └─> Edges: Relationships with metadata

4. Framework Detection (Optional)
   └─> FrameworkDetectorV2
       ├─> GraphSummarizer creates structured summary
       ├─> Gemini 2.0 Flash analyzes patterns
       └─> Returns framework + confidence score

5. RAG Index Creation (Optional)
   ├─> graph_to_documents converts graph to LangChain docs
   ├─> VectorStoreManager creates FAISS index
   │   ├─> Uses Gemini embeddings (primary)
   │   └─> Falls back to local HuggingFace embeddings
   └─> Stores vectorstore for querying

6. Agent-Based Analysis (Optional)
   └─> Framework-Aware Architecture Agent
       ├─> Detects framework from vectorstore
       ├─> Runs framework-specific queries
       └─> Synthesizes comprehensive report

7. Report Generation (Optional)
   ├─> ArchitectureReportGenerator
   │   ├─> Executive Summary
   │   ├─> Architecture Patterns
   │   ├─> Layers & Components
   │   └─> Recommendations
   └─> MermaidDiagramGenerator
       ├─> Component Diagram
       └─> Class Diagram

8. Export
   └─> JSON export of complete knowledge graph
```

---

## Technology Stack

### Core Technologies
| Technology | Purpose | Version |
|-----------|---------|---------|
| **Python** | Primary language | 3.8+ |
| **tree-sitter** | Java parsing | 0.21.3 |
| **NetworkX** | Graph data structure | 3.2.1 |
| **Google Gemini 2.0** | LLM for analysis | gemini-2.0-flash-exp |
| **LangChain** | Agent framework | 0.3.13 |
| **LangGraph** | Agent orchestration | 0.2.63 |
| **FAISS** | Vector database | 1.9.0 (CPU) |
| **Sentence Transformers** | Local embeddings | 3.3.1 |
| **PyTorch** | ML backend | 2.5.1 |
| **Streamlit** | Web UI | 1.31.0 |
| **Pydantic** | Type validation | 2.10.6 |

### Key Libraries
- **langchain-google-genai**: Gemini integration
- **langchain-community**: Vector stores and tools
- **gitpython**: Git operations
- **python-dotenv**: Environment configuration
- **streamlit-markdown**: Mermaid diagram rendering

---

## Project Structure

```
agent-migration-v2/
├── app_v2.py                          # Main Streamlit application
├── requirements.txt                   # Python dependencies
├── README.md                          # Main documentation
├── .env                              # Environment variables (not in git)
├── .env.example                      # Example environment config
├── .gitignore                        # Git ignore rules
│
├── .streamlit/
│   └── config.toml                   # Streamlit config (port: 8051)
│
├── docs/
│   └── PROJECT_DOCUMENTATION.md      # This file
│
└── src/
    ├── __init__.py
    │
    ├── utils/
    │   ├── __init__.py
    │   └── github_cloner.py          # GitHub repository cloning
    │
    ├── parser/
    │   ├── __init__.py
    │   ├── generic_java_parser.py    # Tree-sitter Java parser
    │   └── relationship_extractor.py # Extract code relationships
    │
    ├── knowledge_graph/
    │   ├── __init__.py
    │   └── graph.py                  # NetworkX graph structure
    │
    ├── inference/
    │   ├── __init__.py
    │   ├── framework_detector_v2.py  # AI framework detection
    │   └── graph_summarizer.py       # Structured summarization
    │
    └── rag/
        ├── __init__.py
        ├── graph_to_documents.py     # Graph → LangChain docs
        ├── vectorstore_manager.py    # FAISS + embeddings
        ├── retriever_tool.py         # RAG retrieval tool
        ├── report_generator.py       # Architecture reports
        ├── report_formatter.py       # Markdown formatting
        │
        └── agents/
            ├── __init__.py
            ├── agent_factory.py                        # Agent factory
            ├── architecture_agent.py                   # Basic agent
            ├── framework_aware_architecture_agent.py   # Main agent
            └── planning_architecture_agent.py          # Planning agent
```

---

## Core Components

### 1. GitHub Cloner (`src/utils/github_cloner.py`)

**Purpose**: Clone GitHub repositories for analysis

**Key Features**:
- Validates GitHub URLs
- Shallow clone (depth=1) for speed
- Stores in `/tmp/codebase_analysis/{owner}_{repo}/`
- Automatic cleanup support

**Usage**:
```python
from src.utils.github_cloner import GitHubCloner

cloner = GitHubCloner()
result = cloner.clone_repository("https://github.com/owner/repo")
# Returns: {"success": True, "local_path": "/tmp/...", "owner": "...", "repo": "..."}
```

### 2. Generic Java Parser (`src/parser/generic_java_parser.py`)

**Purpose**: Framework-agnostic Java code parsing using tree-sitter

**Key Features**:
- No hardcoded patterns (works with any Java framework)
- Extracts classes, interfaces, enums
- Extracts methods, fields, annotations
- Extracts modifiers and access levels
- No classification during parsing (delegated to AI)

**What It Extracts**:
- Class/Interface/Enum declarations
- Method signatures and bodies
- Field declarations
- Annotations (with parameters)
- Superclass and interface implementations
- Package names

### 3. Relationship Extractor (`src/parser/relationship_extractor.py`)

**Purpose**: Extract relationships between code elements

**Relationship Types**:
- `CALLS`: Method calls another method
- `EXTENDS`: Class extends superclass
- `IMPLEMENTS`: Class implements interface
- `DECLARES`: Class declares method/field
- `ACCESSES`: Method accesses field
- `ANNOTATED_WITH`: Element has annotation

### 4. Knowledge Graph (`src/knowledge_graph/graph.py`)

**Purpose**: Central data structure for storing codebase structure

**Graph Type**: NetworkX MultiDiGraph (allows multiple edges between nodes)

**Node Types**:
- `CLASS`: Java classes
- `INTERFACE`: Java interfaces
- `ENUM`: Java enums
- `METHOD`: Methods/functions
- `FIELD`: Class fields/properties

**Key Methods**:
- `add_class(ClassNode)`: Add class to graph
- `add_method(MethodNode)`: Add method to graph
- `add_edge(from, to, edge_type)`: Add relationship
- `get_stats()`: Get graph statistics
- `export_to_dict()`: Export as JSON

### 5. Framework Detector (`src/inference/framework_detector_v2.py`)

**Purpose**: AI-powered framework detection using Gemini

**How It Works**:
1. GraphSummarizer creates structured summary (class counts, annotation stats)
2. Gemini analyzes summary for framework patterns
3. Returns framework name + confidence score + reasoning

**Detected Frameworks**:
- Spring Boot
- Struts (1.x, 2.x)
- Jakarta EE / Java EE
- JAX-RS
- Servlet/JSP
- Micronaut
- Quarkus
- Play Framework
- Generic Java

**Why Structured Summary over RAG**:
- RAG retrieves top-k documents (may miss scattered patterns)
- Structured summary aggregates ALL patterns (e.g., "15 @RestController classes")
- Results in 95%+ confidence detection

### 6. RAG System

#### VectorStore Manager (`src/rag/vectorstore_manager.py`)

**Purpose**: Manages FAISS vector store and embeddings

**Features**:
- Primary: Gemini embeddings (gemini-embedding-001)
- Fallback: Local HuggingFace embeddings (sentence-transformers)
- Automatic fallback on API quota exceeded
- Persistent storage support

**Embedding Dimensions**: 768

#### Graph to Documents (`src/rag/graph_to_documents.py`)

**Purpose**: Convert knowledge graph to LangChain documents

**Document Structure**:
Each document represents a code element with:
- `page_content`: String representation (class/method/field info)
- `metadata`: Type, file path, package, annotations

**Example Document**:
```
Class: UserController
Package: com.example.controller
Type: CLASS
Annotations: @RestController, @RequestMapping("/api/users")
File: src/main/java/com/example/controller/UserController.java
```

### 7. Multi-Agent System

#### Architecture Agent (`src/rag/agents/architecture_agent.py`)

**Purpose**: Basic architecture analysis with RAG retrieval

**Capabilities**:
- Natural language queries about codebase
- Uses RAG to find relevant code
- ReAct reasoning (Thought → Action → Observation)

#### Framework-Aware Architecture Agent (`src/rag/agents/framework_aware_architecture_agent.py`)

**Purpose**: Main agent for comprehensive analysis

**How It Works**:
1. **Step 1**: Detect framework from vectorstore
2. **Step 2**: Run framework-specific queries:
   - Spring Boot: @RestController, @Service, @Repository, etc.
   - Struts: Actions, struts.xml, JSPs
   - JAX-RS: @Path, @GET, @POST
3. **Step 3**: Synthesize comprehensive report using Gemini

**Framework-Specific Queries**: Defined in `FRAMEWORK_QUERIES` dict

#### Planning Architecture Agent (`src/rag/agents/planning_architecture_agent.py`)

**Purpose**: Systematic 7-step architecture analysis

**Analysis Steps**:
1. Controllers/Entry Points
2. Business Logic Services
3. Data Access Layer
4. Domain Entities
5. Configuration
6. Security
7. Dependencies

### 8. Report Generation

#### Report Generator (`src/rag/report_generator.py`)

**Purpose**: Generate comprehensive architecture reports

**Output Structure** (Pydantic models):
- **Executive Summary**: High-level overview
- **Architecture Patterns**: MVC, Layered, etc.
- **Layers**: Presentation, Business, Data, Domain
- **Key Components**: Main classes and their purpose
- **Data Flow**: Request → Response flow
- **Technology Stack**: Frameworks, libraries
- **Strengths**: What's good
- **Recommendations**: Improvements

#### Mermaid Diagram Generator

**Purpose**: Generate Mermaid diagrams from reports

**Diagram Types**:
1. **Component Diagram**: Shows layers and components
2. **Class Diagram**: Shows entities and relationships

---

## Data Flow

### Complete User Journey

```
User enters GitHub URL
    ↓
[1] Clone Repository
    └─> /tmp/codebase_analysis/{owner}_{repo}/
    ↓
[2] Parse Java Files (tree-sitter)
    └─> Extract classes, methods, fields, annotations
    ↓
[3] Build Knowledge Graph (NetworkX)
    └─> Nodes: Classes, Methods, Fields
    └─> Edges: CALLS, EXTENDS, IMPLEMENTS, etc.
    ↓
[4] Display Graph Statistics
    └─> User sees: "50 classes, 245 methods, 412 edges"
    ↓
[Optional: User clicks "Detect Framework"]
    ↓
[5] Framework Detection
    └─> Gemini analyzes patterns
    └─> Returns: "Spring Boot (95% confidence)"
    ↓
[Optional: User clicks "Create RAG Index"]
    ↓
[6] RAG Index Creation
    ├─> Convert graph to 268 LangChain documents
    ├─> Generate embeddings (Gemini or local)
    └─> Create FAISS index
    ↓
[7] User can now:
    ├─> Ask Architecture Agent questions
    ├─> Generate Architecture Report
    ├─> Generate Mermaid Diagrams
    └─> Download Graph JSON
```

### Internal Data Flow

```
GitHub Repo (Remote)
    ↓ [GitHubCloner]
Local Files (/tmp/codebase_analysis/)
    ↓ [GenericJavaParser]
Tree-sitter AST
    ↓ [RelationshipExtractor]
Knowledge Graph (NetworkX)
    ↓ [Branching]
    ├─────────────────┬─────────────────┐
    ↓                 ↓                 ↓
[Framework        [RAG Index]      [JSON Export]
Detection]           ↓
    ↓           LangChain Docs
Gemini              ↓
Analysis        Embeddings (FAISS)
    ↓                 ↓
Framework       Agent Queries
Result              ↓
                Architecture
                Report
                    ↓
                Mermaid
                Diagrams
```

---

## API Keys & Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Google Gemini API Key
CODEBASE_GEMINI_KEY=your_gemini_api_key_here

# Optional: Specify Gemini model (default: gemini-2.0-flash-exp)
CODEBASE_GEMINI_MODEL=gemini-2.0-flash-exp

# Alternative key names (for compatibility)
GOOGLE_GENAI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Get a Free Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key to your `.env` file

**Free Tier Limits**:
- 60 requests per minute
- 1,500 requests per day
- Sufficient for analyzing 10-20 repositories per day

### Streamlit Configuration

File: `.streamlit/config.toml`

```toml
[server]
port = 8051              # Custom port (default: 8501)
address = "0.0.0.0"      # Allow external access
headless = true          # Server mode
enableCORS = false       # Disable CORS
enableXsrfProtection = false
```

---

## Deployment Guide

### Local Deployment (Development)

```bash
# 1. Clone repository
git clone <repository-url>
cd agent-migration-v2

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your CODEBASE_GEMINI_KEY

# 5. Run application
streamlit run app_v2.py

# Access at: http://localhost:8051
```

### EC2 Deployment (Production)

#### Prerequisites
- AWS EC2 instance (t2.micro or larger)
- Ubuntu 20.04+ or Amazon Linux 2
- Public IP or domain
- Security group allowing inbound traffic on port 8051

#### Deployment Steps

```bash
# 1. SSH into EC2
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# 2. Update system
sudo apt update
sudo apt upgrade -y

# 3. Install Python and Git
sudo apt install python3 python3-pip python3-venv git -y

# 4. Clone repository
git clone <repository-url>
cd agent-migration-v2

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 7. Configure environment
nano .env
# Add: CODEBASE_GEMINI_KEY=your_key_here

# 8. Configure security group
# AWS Console → EC2 → Security Groups → Add Inbound Rule:
# Type: Custom TCP
# Port: 8051
# Source: 0.0.0.0/0 (or specific IPs)

# 9. Run application (background)
nohup streamlit run app_v2.py > app.log 2>&1 &

# 10. Check logs
tail -f app.log

# Access at: http://<ec2-public-ip>:8051
```

#### Process Management with systemd

Create service file: `/etc/systemd/system/java-analyzer.service`

```ini
[Unit]
Description=Java Codebase Analyzer
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agent-migration-v2
Environment="PATH=/home/ubuntu/agent-migration-v2/venv/bin"
ExecStart=/home/ubuntu/agent-migration-v2/venv/bin/streamlit run app_v2.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable java-analyzer
sudo systemctl start java-analyzer
sudo systemctl status java-analyzer
```

#### Important Notes

**Storage Location**:
- Cloned repos stored in: `/tmp/codebase_analysis/`
- `/tmp` is cleared on reboot
- Monitor disk space: `df -h`

**Memory Considerations**:
- t2.micro: 1GB RAM (may struggle with large repos)
- Recommended: t2.small (2GB RAM) or larger
- Monitor: `free -h`

**Cleanup**:
```bash
# Clear temporary cloned repos
rm -rf /tmp/codebase_analysis/*

# Check disk usage
du -sh /tmp/codebase_analysis/
```

---

## Usage Guide

### Basic Workflow

1. **Start Application**
   ```bash
   streamlit run app_v2.py
   ```

2. **Enter GitHub URL**
   - Paste any public Java repository URL
   - Example: `https://github.com/spring-projects/spring-petclinic`

3. **Create Knowledge Graph**
   - Click "Create Graph"
   - Wait for parsing to complete (10-60 seconds)
   - View statistics: classes, methods, fields, edges

4. **Detect Framework (Optional)**
   - Click "Detect Framework"
   - AI analyzes patterns and identifies framework
   - Shows confidence score and reasoning

5. **Create RAG Index (Optional)**
   - Click "Create RAG Index"
   - Choose Gemini embeddings or local embeddings
   - Enables natural language queries

6. **Query Architecture Agent (Optional)**
   - Ask questions like:
     - "What architecture patterns are used?"
     - "How many controllers are there?"
     - "What are the main entity classes?"

7. **Generate Report (Optional)**
   - Click "Generate Report"
   - Comprehensive architecture analysis
   - Includes patterns, layers, components, recommendations

8. **Generate Diagrams (Optional)**
   - Click "Generate Component Diagram"
   - Click "Generate Class Diagram"
   - View and download Mermaid diagrams

9. **Export Graph**
   - Click "Download Graph JSON"
   - Complete knowledge graph in JSON format

### Example Queries for Architecture Agent

**Framework & Patterns**:
- "What framework is this project using?"
- "What architecture patterns are implemented?"
- "Is this MVC or layered architecture?"

**Components**:
- "List all REST controllers"
- "What services are in the business layer?"
- "Show me all repository classes"

**Structure**:
- "How is the code organized?"
- "What packages exist in this project?"
- "What are the main domain entities?"

**Relationships**:
- "How do controllers interact with services?"
- "What are the dependencies between components?"
- "Which classes use dependency injection?"

---

## Code Conventions

### Python Naming Conventions (PEP 8)

✅ **Files & Modules**: `snake_case`
```
github_cloner.py
generic_java_parser.py
framework_detector_v2.py
```

✅ **Classes**: `PascalCase`
```python
class KnowledgeGraph:
class FrameworkDetectorV2:
class ArchitectureAgent:
```

✅ **Functions & Methods**: `snake_case`
```python
def clone_repository():
def parse_directory():
def analyze_architecture():
```

✅ **Variables**: `snake_case`
```python
github_url = "..."
knowledge_graph = KnowledgeGraph()
vectorstore_manager = VectorStoreManager()
```

✅ **Constants**: `UPPER_CASE`
```python
MAX_RETRIES = 3
DEFAULT_MODEL = "gemini-2.0-flash-exp"
FRAMEWORK_QUERIES = {...}
```

✅ **Private Methods/Variables**: `_leading_underscore`
```python
def _detect_framework():
def _parse_analysis():
self._api_key = "..."
```

### Code Organization

**Import Order**:
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import os
from typing import Dict, List

# Third-party
from langchain_google_genai import ChatGoogleGenerativeAI
import networkx as nx

# Local
from src.knowledge_graph.graph import KnowledgeGraph
from src.utils.github_cloner import GitHubCloner
```

**Docstrings**: Google style
```python
def analyze_architecture(self, project_name: str) -> Dict[str, Any]:
    """
    Analyze architecture with framework detection

    Args:
        project_name: Name of the project

    Returns:
        Comprehensive architecture analysis
    """
```

**Type Hints**: Used throughout
```python
def add_class(self, class_node: ClassNode) -> str:
def get_stats(self) -> Dict[str, int]:
```

---

## Troubleshooting

### Common Issues

#### 1. PyTorch Installation Failed

**Error**: `Could not find a version that satisfies the requirement torch==2.5.1+cpu`

**Solution**: The `+cpu` suffix is not available on standard PyPI
```bash
# Already fixed in requirements.txt
# Uses: torch==2.5.1 (without +cpu suffix)
pip install -r requirements.txt
```

#### 2. Git Clone Failed

**Error**: `Could not resolve host: github.com`

**Causes**:
- No internet connection
- DNS issues
- VPN blocking GitHub
- Firewall blocking access

**Solutions**:
```bash
# Check internet
ping 8.8.8.8

# Check GitHub access
ping github.com

# Flush DNS cache (macOS)
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Try in browser
# Visit: https://github.com
```

#### 3. Gemini API Quota Exceeded

**Error**: `Resource exhausted: Quota exceeded`

**Solution**: System automatically falls back to local embeddings
```python
# In Streamlit UI, check "Use Local Embeddings"
# Uses sentence-transformers (no API required)
```

#### 4. Port Already in Use

**Error**: `Address already in use`

**Solution**: Kill existing process or change port
```bash
# Find process on port 8051
lsof -i :8051

# Kill process
kill -9 <PID>

# Or change port in .streamlit/config.toml
```

#### 5. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Run from project root
```bash
# Ensure you're in the correct directory
cd /path/to/agent-migration-v2

# Run application
streamlit run app_v2.py
```

#### 6. EC2 Cannot Access (Connection Timeout)

**Causes**:
- Security group not configured
- Port 8051 not open
- Firewall blocking

**Solution**: Configure security group
```
AWS Console → EC2 → Security Groups
→ Add Inbound Rule:
   Type: Custom TCP
   Port: 8051
   Source: 0.0.0.0/0
```

#### 7. Out of Memory (EC2 t2.micro)

**Error**: `Killed` or process crashes

**Cause**: Insufficient RAM (1GB) for large repositories

**Solutions**:
- Use t2.small (2GB RAM) or larger
- Analyze smaller repositories
- Reduce batch size in code

#### 8. Tree-sitter Build Failed

**Error**: Build errors during installation

**Solution**: Install build tools
```bash
# Ubuntu
sudo apt install build-essential

# macOS
xcode-select --install
```

---

## Performance Optimization

### Speed Improvements

**1. Shallow Clones**
```python
# Already implemented in GitHubCloner
git clone --depth 1  # Only latest commit
```

**2. Parallel Processing**
- Consider using multiprocessing for large repos
- Parse files in parallel

**3. Caching**
- Cache parsed graphs
- Cache vectorstores
- Reuse across sessions

### Memory Optimization

**1. Limit Document Count**
```python
# In graph_to_documents.py
# Consider limiting nodes processed
```

**2. Streaming Responses**
- Stream large LLM responses
- Don't load entire graph in memory

**3. Cleanup**
```python
# Clean up after analysis
cloner.cleanup_repository(local_path)
```

---

## Future Enhancements

### Planned Features

1. **Multi-Language Support**
   - Python, JavaScript, Go, C#
   - Same architecture, different parsers

2. **Database Storage**
   - PostgreSQL for persistent graphs
   - Cache analyzed repositories

3. **Comparison Mode**
   - Compare two codebases
   - Highlight differences

4. **Migration Planner**
   - Generate migration plans
   - Spring Boot → Quarkus
   - Struts → Spring Boot

5. **API Endpoints**
   - REST API for programmatic access
   - Batch processing support

6. **Authentication**
   - User accounts
   - Private repository support
   - GitHub OAuth

7. **Advanced Visualizations**
   - Interactive graph visualization
   - 3D architecture views
   - Dependency graphs

---

## Contributing

### Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/your-username/agent-migration-v2
cd agent-migration-v2

# 2. Create feature branch
git checkout -b feature/your-feature

# 3. Make changes and test
streamlit run app_v2.py

# 4. Commit changes
git add .
git commit -m "Add your feature"

# 5. Push and create PR
git push origin feature/your-feature
```

### Code Standards

- Follow PEP 8
- Add type hints
- Write docstrings
- Add unit tests (TODO)
- Update documentation

---

## License

[Add your license information here]

---

## Contact & Support

**Repository**: [Add GitHub URL]
**Issues**: [Add GitHub Issues URL]
**Documentation**: `/docs/PROJECT_DOCUMENTATION.md`

---

**Last Updated**: November 2025
**Version**: 2.0
**Maintained By**: Capgemini Discovery Agent Team
