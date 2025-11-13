# Java Codebase Analyzer

An AI-powered static analysis platform that automatically parses, understands, and visualizes Java codebases from GitHub repositories. Built with LangChain agents, knowledge graphs, and Google Gemini 2.0.

## Overview

This tool provides automated codebase comprehension for Java projects using a combination of static analysis and AI-powered inference. It constructs a comprehensive knowledge graph of code structure and relationships, then applies multi-agent reasoning to answer architecture questions and generate insights.

**Key Capabilities:**
- Framework-agnostic parsing using tree-sitter
- AI-powered framework detection (Spring Boot, Jakarta EE, Struts, Micronaut, Quarkus, etc.)
- Knowledge graph construction with NetworkX
- RAG-based natural language querying
- Architecture diagram generation (Mermaid)
- Complete structural export (JSON)

## Features

- **GitHub Integration** - Direct analysis of public repositories
- **AI Framework Detection** - Automatic framework identification with confidence scoring
- **Knowledge Graph** - Complete structural representation (classes, methods, fields, relationships)
- **RAG System** - FAISS-based vector search with Gemini embeddings
- **Multi-Agent Architecture** - Specialized agents for framework-aware and systematic analysis
- **Web Interface** - Streamlit-based UI for interactive exploration
- **Export Options** - JSON export of complete graph structure

## Prerequisites

- Python 3.8 or higher
- Git
- Google Gemini API key ([Get free API key](https://makersuite.google.com/app/apikey))

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Personal\ Agents
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note for Windows users:** PyTorch CPU version will be installed automatically. If you encounter issues, refer to [PyTorch installation guide](https://pytorch.org/get-started/locally/).

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
CODEBASE_GEMINI_KEY=your_gemini_api_key_here
CODEBASE_GEMINI_MODEL=gemini-2.0-flash-exp
```

## Usage

### Start the Application
```bash
streamlit run app_v2.py
```

The web interface will open at `http://localhost:8501`

### Analysis Workflow
1. **Input**: Paste a GitHub repository URL (public repositories only)
2. **Parse**: Click "Create Graph" to parse the codebase and build the knowledge graph
3. **Detect Framework**: Click "Detect Framework" for AI-powered framework identification
4. **Enable RAG**: Click "Create RAG Index" to build the vector search index
5. **Query**: Use the Architecture Agent to ask questions about the codebase
6. **Export**: Download the complete knowledge graph as JSON

## Example Output

```
Repository: https://github.com/spring-projects/spring-petclinic

Knowledge Graph Created:
  - 50 classes, 15 interfaces, 3 enums
  - 245 methods, 89 fields
  - 412 relationships

Framework Detection:
  Framework: Spring Boot
  Confidence: 95%
  Reasoning: Strong Spring patterns (@RestController, @Service, @Repository,
             JpaRepository inheritance)
  Architecture: MVC, REST API

RAG Index: 268 documents indexed

Query: "What architecture patterns are used in this codebase?"
Response: "The codebase uses a layered MVC architecture with clear separation:
   - Controllers: OwnerController, PetController, VetController
   - Services: ClinicService
   - Repositories: OwnerRepository, PetRepository, VetRepository
   - Entities: Owner, Pet, Visit, Vet
   Follows Spring Boot best practices for layered architecture."
```

## Project Structure

```
├── app_v2.py                           # Streamlit web interface
├── requirements.txt                    # Python dependencies
├── .env                                # Environment configuration (create this)
│
├── src/
│   ├── utils/
│   │   └── github_cloner.py            # GitHub repository cloning
│   │
│   ├── parser/
│   │   ├── generic_java_parser.py      # Tree-sitter Java parser
│   │   └── relationship_extractor.py   # Code relationship extraction
│   │
│   ├── knowledge_graph/
│   │   └── graph.py                    # NetworkX graph structure
│   │
│   ├── inference/
│   │   ├── graph_summarizer.py         # Structured summary generation
│   │   └── framework_detector_v2.py    # AI framework detection
│   │
│   └── rag/
│       ├── graph_to_documents.py       # Graph to LangChain documents
│       ├── vectorstore_manager.py      # FAISS vector store + embeddings
│       ├── retriever_tool.py           # RAG retrieval tool
│       ├── report_generator.py         # Architecture report generation
│       ├── report_formatter.py         # Markdown formatting
│       │
│       └── agents/
│           ├── agent_factory.py                          # Agent factory pattern
│           ├── architecture_agent.py                     # Basic analysis agent
│           ├── framework_aware_architecture_agent.py     # Framework-specific agent
│           └── planning_architecture_agent.py            # Systematic planning agent
```

## Architecture

### Analysis Pipeline

```
1. Repository Cloning
   ├─> GitHub URL input
   └─> Local repository clone

2. Static Analysis
   ├─> Tree-sitter parsing (framework-agnostic)
   ├─> Code element extraction (classes, methods, fields)
   ├─> Annotation extraction
   └─> Relationship mapping (CALLS, ACCESSES, DECLARES, EXTENDS, IMPLEMENTS)

3. Knowledge Graph Construction
   └─> NetworkX graph with typed nodes and edges

4. AI Framework Detection
   ├─> Graph summarization (structured statistics)
   ├─> Gemini 2.0 Flash inference
   └─> Framework identification + confidence scoring

5. RAG Index Creation
   ├─> Graph to LangChain documents conversion
   ├─> Gemini embeddings (gemini-embedding-001)
   ├─> FAISS vector store indexing
   └─> Fallback to local HuggingFace embeddings

6. Multi-Agent Query System
   ├─> Framework-aware agent (framework-specific patterns)
   ├─> Planning agent (systematic 7-step analysis)
   └─> ReAct reasoning with vector retrieval

7. Report Generation
   ├─> Architecture analysis
   ├─> Mermaid diagram generation
   └─> JSON export
```

### Technology Stack

- **Parser**: tree-sitter (Java)
- **Graph**: NetworkX
- **LLM**: Google Gemini 2.0 Flash
- **Agent Framework**: LangChain + LangGraph
- **Vector Store**: FAISS
- **Embeddings**: Gemini embeddings / HuggingFace (fallback)
- **UI**: Streamlit
- **Type Safety**: Pydantic

## Design Philosophy

**Structured Summary over RAG for Framework Detection:**

Traditional RAG retrieves top-k similar documents, potentially missing patterns scattered across the codebase. This system uses structured summarization to analyze all code elements, creating aggregate statistics (e.g., "15 classes use @RestController") for complete pattern recognition without information loss.

**Result:** 95%+ framework detection confidence with minimal API calls.

## Example Repositories

- [Spring PetClinic](https://github.com/spring-projects/spring-petclinic) - Classic Spring Boot MVC
- [Spring Boot OAuth2](https://github.com/callicoder/spring-boot-react-oauth2-social-login-demo) - REST API with authentication
- Any public Java repository

## Troubleshooting

**Common Issues:**

1. **PyTorch installation fails on Windows**
   - Solution: Install Visual C++ redistributables or use CPU-only version
   - See: `PYTORCH_FIX.md`

2. **Gemini API quota exceeded**
   - Solution: System automatically falls back to local HuggingFace embeddings
   - See: `LOCAL_EMBEDDINGS_FALLBACK.md`

3. **Git clone fails**
   - Ensure repository is public
   - Check network connectivity
   - Verify Git is installed and in PATH

## License

[Add your license here]

## Contributing

[Add contribution guidelines if applicable]
