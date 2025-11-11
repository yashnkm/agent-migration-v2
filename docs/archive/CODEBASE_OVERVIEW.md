# Java Codebase Analysis System - Complete Overview

## Table of Contents
1. [Project Overview](#project-overview)
2. [Current System Status](#current-system-status)
3. [Architecture](#architecture)
4. [File Structure & Explanation](#file-structure--explanation)
5. [How Everything Works Together](#how-everything-works-together)
6. [Usage Guide](#usage-guide)
7. [Recent Changes & Evolution](#recent-changes--evolution)

---

## Project Overview

### What Is This System?
This is an **AI-powered multi-agent system** that automatically analyzes Java Spring Boot codebases. It understands your code structure, business logic, data flows, and architectural patterns without requiring any queries - it proactively discovers everything.

### The Vision
Transform from a **reactive query-based system** to a **proactive automatic analysis system** that:
- Automatically discovers all business domains/entities in your codebase
- Maps complete architecture (Controller → Service → Repository → Entity) for each domain
- Extracts business logic, endpoints, methods, and fields automatically
- Generates comprehensive documentation and analysis reports
- Provides deep technical and functional understanding

### Current Status: Phase 2 Complete ✓
**Completed:**
- ✓ Phase 1: Foundation parser with tree-sitter + knowledge graph
- ✓ Phase 2: Query system with orchestrator and agents (now deprecated)
- ✓ **Phase 2.5: Domain-Centric Analysis (NEW DIRECTION)**

**What Works Now:**
- Automatic domain discovery from any Java Spring Boot codebase
- Complete architectural mapping per domain
- Endpoint, method, and field extraction
- JSON export of domain catalog
- Complexity metrics calculation

---

## Current System Status

### What's Currently Implemented

#### ✓ Core Foundation (Fully Working)
1. **Java Parser** - Parses Java files using tree-sitter
2. **Knowledge Graph** - Stores all code elements and relationships
3. **Relationship Extractor** - Maps method calls and field accesses
4. **Domain Discovery System** - Automatically identifies all business domains

#### ✓ Domain-Centric Analysis (Latest Feature)
- **Automatic Entity Discovery**: Finds all @Entity classes
- **Architecture Mapping**: Maps Controller/Service/Repository for each entity
- **Endpoint Extraction**: Identifies all REST API endpoints per domain
- **Method Cataloging**: Lists all methods belonging to each domain
- **Field Extraction**: Extracts all entity fields with types and annotations
- **Complexity Metrics**: Calculates complexity scores per domain

#### ✓ AI-Powered Agents (Available but Not Main Focus)
- **Business Logic Analyzer**: Uses Claude AI to explain code
- **API Documentation Agent**: Generates API documentation
- **Data Flow Tracer**: Traces data flows through the system
- **Orchestrator**: Coordinates all agents for queries (deprecated approach)

### What's NOT Implemented Yet
- Related entity detection (JPA relationships like @OneToMany)
- Cross-domain analysis
- Automatic business logic extraction per domain
- Visual diagram generation
- Comprehensive markdown reports per domain

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    USER PROVIDES CODEBASE                    │
│                    (Java Spring Boot)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   PHASE 1: PARSING           │
        │   - Java Parser              │
        │   - Relationship Extractor   │
        │   - Knowledge Graph Builder  │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   PHASE 2: DOMAIN DISCOVERY  │
        │   - Entity Identification    │
        │   - Architecture Mapping     │
        │   - Endpoint Extraction      │
        │   - Method/Field Cataloging  │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   OUTPUT                     │
        │   - Domain Catalog (JSON)    │
        │   - Console Report           │
        │   - Detailed Analysis        │
        └──────────────────────────────┘
```

### Domain-Centric Model

Each discovered domain contains:
```
Domain (e.g., "Employee")
├── Entity Class (e.g., com.example.Employee)
├── Controller (e.g., EmployeeController)
├── Service (e.g., EmployeeService)
├── Repository (e.g., EmployeeRepository)
├── Endpoints (All REST APIs for this domain)
│   ├── POST /employees
│   ├── GET /employees/{id}
│   └── PUT /employees/{id}
├── Methods (All methods across all classes)
├── Fields (All entity fields)
└── Metrics (Complexity, counts, etc.)
```

---

## File Structure & Explanation

### Root Directory Files

#### `requirements.txt`
**Purpose**: Python dependencies for the project
**Contents**:
- `tree-sitter==0.21.3` - Parser for Java code
- `tree-sitter-java==0.21.0` - Java language grammar
- `networkx==3.2.1` - Graph library for knowledge graph
- `anthropic==0.34.0` - Claude AI SDK for business logic analysis
- `python-dotenv==1.0.0` - Environment variable management

#### `context/desc.txt`
**Purpose**: Original Software Requirements Specification (SRS)
**Contents**:
- Complete vision for multi-agent analysis system
- 8 specialized agents design (Orchestrator, Parser, Architecture Analyzer, etc.)
- Workflow descriptions for various query types
- Impact analysis examples
- Original plan for query-based reactive system

**Note**: This was the original design. The system has evolved to be **proactive** instead of **reactive**.

#### `domain_catalog.json`
**Purpose**: Output file from domain analysis
**Contents**:
- Summary of all discovered domains
- Complete details for each domain (entity, controller, service, endpoints, methods, fields)
- Complexity metrics per domain

**Example Output**:
```json
{
  "summary": {
    "total_domains": 1,
    "domains": [
      {
        "name": "Employee",
        "has_controller": true,
        "has_service": true,
        "endpoint_count": 6,
        "method_count": 22
      }
    ]
  }
}
```

#### `knowledge_graph_output.json`
**Purpose**: Raw knowledge graph export (from old main.py)
**Contents**: All parsed classes, methods, fields, and relationships
**Status**: Generated by `src/main.py` (legacy approach)

---

### `src/` Directory - Core Source Code

#### **`src/knowledge_graph/graph.py`** ⭐ (CORE FOUNDATION)
**Purpose**: The heart of the system - stores all code structure

**Key Classes**:

1. **`NodeType` (Enum)**: Types of nodes
   - CLASS, METHOD, FIELD, ENDPOINT, ANNOTATION, INTERFACE, ENUM

2. **`EdgeType` (Enum)**: Types of relationships
   - CALLS (method → method)
   - DEPENDS_ON (class → class)
   - ACCESSES (method → field)
   - DECLARES (class → method/field)
   - HANDLES (endpoint → method)

3. **`ClassNode` (Dataclass)**: Represents a Java class
   ```python
   name: str                    # e.g., "Employee"
   package: str                 # e.g., "com.example.entity"
   class_type: str              # Controller/Service/Repository/Entity
   annotations: List[str]       # e.g., ["Entity", "Table"]
   ```

4. **`MethodNode` (Dataclass)**: Represents a Java method
   ```python
   name: str                    # e.g., "createEmployee"
   class_name: str              # Full qualified name
   signature: str               # e.g., "createEmployee(Employee)"
   return_type: str             # e.g., "Employee"
   body: str                    # Actual method code
   ```

5. **`FieldNode` (Dataclass)**: Represents a Java field
   ```python
   name: str                    # e.g., "email"
   class_name: str              # e.g., "com.example.Employee"
   field_type: str              # e.g., "String"
   ```

6. **`EndpointNode` (Dataclass)**: Represents a REST endpoint
   ```python
   http_method: str             # GET/POST/PUT/DELETE
   path: str                    # e.g., "/api/employees"
   handler_method: str          # Controller method name
   ```

7. **`KnowledgeGraph` (Main Class)**: The graph itself

   **Key Data Structures**:
   ```python
   graph: nx.MultiDiGraph       # NetworkX graph
   classes: Dict                # All classes indexed by ID
   methods: Dict                # All methods indexed by ID
   fields: Dict                 # All fields indexed by ID
   endpoints: Dict              # All endpoints indexed by ID
   entry_points: Set            # All entry points (endpoints)
   ```

   **Key Methods**:
   - `add_class()` - Add a class node
   - `add_method()` - Add a method node and link to class
   - `add_field()` - Add a field node and link to class
   - `add_endpoint()` - Add an endpoint and mark as entry point
   - `backtrack_to_entry_points()` - Find all paths to entry points (for data flow)
   - `forward_trace()` - Trace forward from an entry point
   - `export_to_dict()` - Export entire graph to JSON

---

#### **`src/parser/java_parser.py`** ⭐ (PARSING ENGINE)
**Purpose**: Parses Java files using tree-sitter and extracts structure

**Main Class**: `JavaParser`

**Key Functionality**:

1. **Initialization**:
   ```python
   language = Language(tsjava.language(), 'java')
   parser = Parser()
   parser.set_language(language)
   ```

2. **Annotation Recognition**:
   - Controller annotations: `@Controller`, `@RestController`
   - Service annotations: `@Service`
   - Repository annotations: `@Repository`
   - Entity annotations: `@Entity`, `@Table`
   - Endpoint annotations: `@GetMapping`, `@PostMapping`, etc.

3. **Extraction Methods**:

   - `get_package_name()` - Extract package declaration
   - `get_annotations()` - Extract all annotations from a node
   - `get_modifiers()` - Extract modifiers (public, private, static, etc.)
   - `classify_class_type()` - Determine if class is Controller/Service/etc.
   - `extract_classes()` - Extract all class declarations
   - `extract_methods()` - Extract all methods with signatures and bodies
   - `extract_fields()` - Extract all field declarations

4. **Main Entry Points**:

   - `parse_java_file(file_path, knowledge_graph)` - Parse single file
   - `parse_directory(directory_path, knowledge_graph)` - Parse entire directory recursively

**How It Works**:
```python
# For each .java file:
1. Read file content as bytes
2. Parse with tree-sitter to get AST
3. Query AST for package name
4. Query AST for all classes
5. For each class:
   - Extract annotations
   - Classify type (Controller/Service/etc.)
   - Extract superclass and interfaces
   - Add to knowledge graph
6. Query AST for all methods in class
7. For each method:
   - Extract signature, parameters, return type
   - Extract annotations (for endpoints)
   - Extract method body
   - Add to knowledge graph
8. Query AST for all fields
9. Add fields to knowledge graph
```

---

#### **`src/parser/relationship_extractor.py`**
**Purpose**: Extracts relationships between code elements

**Main Class**: `RelationshipExtractor`

**Key Methods**:

1. `extract_method_calls()` - Find all method invocations in a method body
2. `extract_field_accesses()` - Find all field reads/writes in a method
3. `extract_endpoints()` - Extract REST endpoint info from controller methods
4. `extract_all_relationships()` - Main orchestrator that processes all methods

**How It Works**:
```python
For each method in knowledge graph:
    1. Check if it's a controller method (has @GetMapping, etc.)
       → Extract endpoint information
    2. Parse method body to find:
       → Field accesses (this.field = value)
       → Method calls (service.doSomething())
    3. Add relationships to knowledge graph
```

---

#### **`src/domain_analyzer/domain_graph.py`** ⭐ (NEW - MOST IMPORTANT)
**Purpose**: The new domain-centric analysis system

**Main Classes**:

1. **`DomainInfo` (Dataclass)**: All information about a business domain
   ```python
   name: str                     # e.g., "Employee"
   entity_class: str             # Full entity class name
   controller: Optional[str]     # Associated controller
   service: Optional[str]        # Associated service
   repository: Optional[str]     # Associated repository
   related_entities: List[str]   # Related entities via JPA
   endpoints: List[Dict]         # All REST endpoints
   methods: List[str]            # All methods
   fields: List[Dict]            # All entity fields
   complexity_score: int         # Calculated complexity
   ```

2. **`DomainGraph` (Main Class)**: Discovers and organizes domains

**The 7-Step Discovery Process**:

```python
def discover_domains():
    # Step 1: Find all entity classes
    # Searches knowledge graph for classes with @Entity annotation
    # Creates a DomainInfo for each entity

    # Step 2: Map domain classes
    # For each domain, finds associated Controller/Service/Repository
    # Matches by name (e.g., "Employee" → "EmployeeController")

    # Step 3: Map endpoints to domains
    # For each REST endpoint, finds which domain it belongs to
    # Matches by controller class

    # Step 4: Map methods to domains
    # Collects all methods from entity, controller, service, repository

    # Step 5: Extract entity fields
    # Gets all fields from the entity class with types and annotations

    # Step 6: Find related entities
    # TODO: Parse JPA relationships (@OneToMany, @ManyToOne, etc.)

    # Step 7: Calculate complexity metrics
    # Score = (endpoints * 3) + (methods * 1) + (fields * 2)
```

**Key Methods**:

- `discover_domains()` - Main entry point, runs all 7 steps
- `get_domain_summary()` - Returns summary of all domains
- `get_domain_details(domain_name)` - Get details for specific domain
- `export_domain_catalog()` - Export to JSON
- `print_domain_catalog()` - Pretty print to console
- `print_domain_details(domain_name)` - Detailed console output

**Output Example**:
```
======================================================================
DOMAIN CATALOG
======================================================================

Total Business Domains: 1

1. Employee Domain
   ------------------------------------------------------------
   Entity:     com.example.demo.entity.Employee
   Controller: com.example.demo.controller.EmployeeController
   Service:    com.example.demo.service.EmployeeService
   Repository: [X] Not Found

   Endpoints:  6
   Methods:    22
   Fields:     5
   Complexity: 50 [MED] MEDIUM
```

---

#### **`src/analyze_domains.py`** ⭐ (NEW MAIN ENTRY POINT)
**Purpose**: Main script for automatic domain-centric analysis

**How to Use**:
```bash
python src/analyze_domains.py test-java-project
```

**What It Does**:
```python
def analyze_codebase_by_domains(directory_path):
    # PHASE 1: Parse codebase
    1. Initialize KnowledgeGraph and JavaParser
    2. Parse all Java files in directory
    3. Extract relationships (method calls, field accesses)

    # PHASE 2: Build domain-centric graph
    4. Create DomainGraph from KnowledgeGraph
    5. Run discover_domains() (7 steps)

    # PHASE 3: Display results
    6. Print domain catalog to console

    # PHASE 4: Detailed analysis
    7. Print detailed view for each domain

    # PHASE 5: Export
    8. Save domain catalog to domain_catalog.json
```

**This is the NEW way to use the system** - fully automatic, no queries needed.

---

#### **`src/main.py`** (LEGACY - OLD APPROACH)
**Purpose**: Original parsing script (still works but not the main focus)

**What It Does**:
- Parses codebase
- Builds knowledge graph
- Exports to `knowledge_graph_output.json`
- Prints summary statistics

**Status**: Still functional but `analyze_domains.py` is the new recommended entry point.

---

#### **`src/query_interface.py`** (DEPRECATED)
**Purpose**: Interactive CLI for asking queries about the codebase

**What It Was**:
- Query-based interface: "What endpoints modify Employee.email?"
- Used Orchestrator to route queries to specialized agents
- Interactive prompt system

**Why It's Deprecated**:
User explicitly said: "i dont want to query anything, i just want that we understand the code base" - so we pivoted to automatic proactive analysis instead.

---

### Agent System (Available but Not Primary Focus)

#### **`src/agents/base_agent.py`**
**Purpose**: Base class for all agents
**Functionality**: Common logging and initialization

#### **`src/agents/orchestrator.py`**
**Purpose**: Master coordinator for query-based system
**Functionality**:
- Pattern matching to detect query intent
- Routes queries to appropriate specialized agents
- Aggregates results from multiple agents
- Formats final response

**Status**: Built but user doesn't want query-based system.

#### **`src/agents/data_flow_tracer.py`**
**Purpose**: Traces data flows through the codebase
**Key Methods**:
- `backtrack_from_field()` - Find all entry points that can access a field
- `backtrack_from_method()` - Find all entry points that call a method
- `forward_trace_from_endpoint()` - Find all entities accessed by an endpoint
- `analyze_impact()` - Analyze impact of changing a method

**Could Be Reused**: For automatic analysis in the future.

#### **`src/agents/business_logic_analyzer.py`**
**Purpose**: Uses Claude AI to understand code
**Key Methods**:
- `explain_method()` - Natural language explanation of what a method does
- `extract_business_rules()` - Extract business rules from code
- `explain_flow()` - Explain end-to-end flow

**Requires**: `ANTHROPIC_API_KEY` environment variable
**Status**: Works but not integrated into automatic domain analysis yet.

#### **`src/agents/api_documentation_agent.py`**
**Purpose**: Auto-generates API documentation
**Key Methods**:
- `document_endpoint()` - Document single endpoint
- `document_all_endpoints()` - Document all endpoints

---

## How Everything Works Together

### Current Workflow (Domain-Centric Analysis)

```
1. USER RUNS:
   python src/analyze_domains.py test-java-project

2. PARSING PHASE:
   JavaParser scans all .java files
   → Extracts classes, methods, fields
   → Builds KnowledgeGraph

   RelationshipExtractor analyzes method bodies
   → Finds method calls
   → Finds field accesses
   → Identifies REST endpoints

3. DOMAIN DISCOVERY PHASE:
   DomainGraph.discover_domains() runs:

   Step 1: Find all @Entity classes
   → Employee.java found → creates "Employee" domain

   Step 2: Map domain classes
   → Finds EmployeeController (has "Employee" in name)
   → Finds EmployeeService (has "Employee" in name)
   → Associates them with Employee domain

   Step 3: Map endpoints
   → POST /createemployee → Employee domain
   → GET /getemployee → Employee domain
   → (6 total endpoints)

   Step 4: Map methods
   → 6 methods from EmployeeController
   → 6 methods from EmployeeService
   → 10 methods from Employee entity (getters/setters)
   → Total: 22 methods

   Step 5: Extract fields
   → id: Long [@Id, @GeneratedValue]
   → name: String [@Column]
   → email: String [@Column]
   → department: String
   → salary: Double

   Step 6: Find related entities
   → Not yet implemented

   Step 7: Calculate metrics
   → Complexity = (6 endpoints * 3) + (22 methods * 1) + (5 fields * 2)
   → Complexity = 18 + 22 + 10 = 50

4. OUTPUT PHASE:
   Console: Pretty-printed domain catalog
   File: domain_catalog.json with complete details
```

### Data Flow Through the System

```
Java Files (.java)
    ↓
[JavaParser] - Uses tree-sitter to parse
    ↓
AST (Abstract Syntax Tree)
    ↓
[JavaParser Extractors] - Query AST
    ↓
ClassNode, MethodNode, FieldNode objects
    ↓
[KnowledgeGraph] - Stores everything
    ↓
Graph with nodes and edges
    ↓
[RelationshipExtractor] - Analyzes connections
    ↓
Enhanced graph with relationships
    ↓
[DomainGraph] - Groups by business domain
    ↓
DomainInfo objects (one per entity)
    ↓
[Export & Display]
    ↓
Console output + domain_catalog.json
```

---

## Usage Guide

### Prerequisites
```bash
# Install Python 3.8+
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage - Domain Analysis (RECOMMENDED)

```bash
# Run domain-centric analysis
python src/analyze_domains.py path/to/your/java/project

# Example with test project
python src/analyze_domains.py test-java-project
```

**What You Get**:
- Console output with domain catalog
- `domain_catalog.json` with complete analysis
- Detailed breakdown per domain

### Alternative - Raw Knowledge Graph (OLD WAY)

```bash
# Run basic parsing
python src/main.py test-java-project
```

**What You Get**:
- Console output with statistics
- `knowledge_graph_output.json` with raw graph data

### Using AI Features (Optional)

```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# The system will now use Claude AI for business logic analysis
# (When integrated into automatic analysis in the future)
```

---

## Recent Changes & Evolution

### Evolution of the System

#### Phase 1: Original Design (From desc.txt)
- **Vision**: Multi-agent reactive query system
- **Approach**: User asks queries, system responds
- **Agents**: 8 specialized agents (Orchestrator, Parser, Business Logic, etc.)
- **Example Query**: "What endpoints can modify Employee.email?"

#### Phase 2: Implementation of Query System
- Built Orchestrator agent with pattern matching
- Implemented Data Flow Tracer for backtracking
- Added Business Logic Analyzer with Claude AI
- Created interactive query interface

#### Phase 2.5: PIVOT TO PROACTIVE ANALYSIS (Current)
- **User Feedback**: "i dont want to query anything, i just want that we understand the code base"
- **New Direction**: Automatic proactive analysis instead of reactive queries
- **Key Insight**: "first build a knowledge graph that would recognize and jot down all the module\entity or entrypoint to entity specific graph"

#### What Changed:
1. **New Main Entry Point**: `analyze_domains.py` instead of `query_interface.py`
2. **Domain-Centric Organization**: Everything grouped by business entity
3. **Automatic Discovery**: No user queries needed - system discovers everything
4. **Structured Output**: JSON catalog of all domains with complete details

### Files Created in Latest Session
- `src/domain_analyzer/domain_graph.py` - Domain discovery logic
- `src/analyze_domains.py` - New main entry point
- `domain_catalog.json` - Output from domain analysis

### Files Deprecated
- `src/query_interface.py` - Query-based interface (user doesn't want this)
- Some of the orchestrator patterns (but code still exists for future use)

---

## Next Steps (Not Yet Implemented)

Based on user's stated goals:

### Immediate Next Steps:
1. **Automatic Deep Analysis Per Domain**
   - For each discovered domain, automatically:
   - Send ALL methods to Claude AI for business logic extraction
   - Generate complete workflow documentation
   - Extract all business rules
   - Create technical summary

2. **Related Entity Detection**
   - Implement Step 6 of domain discovery
   - Parse JPA relationships (@OneToMany, @ManyToOne, @ManyToMany)
   - Map entity relationships

3. **Cross-Domain Analysis**
   - Detect how domains interact with each other
   - Map data flows between domains

4. **Comprehensive Reports**
   - Generate markdown reports per domain
   - Include technical details, business logic, workflows
   - Visual architecture diagrams

### User's End Goal:
"create a way to understand the code base in a much better way, like technical and functional with business logic everything"

**Translation**: Build a system that automatically generates a complete encyclopedia of the codebase - technical architecture + functional business logic - without requiring any user queries.

---

## Summary

### What This System Does NOW:
✅ Automatically discovers all business domains in a Java Spring Boot codebase
✅ Maps complete architecture (Entity → Service → Controller → Repository) per domain
✅ Extracts all REST endpoints, methods, and fields per domain
✅ Calculates complexity metrics
✅ Exports structured JSON catalog
✅ Provides detailed console reports

### What This System Will Do NEXT:
🔄 Automatically extract business logic for all methods (using AI)
🔄 Generate comprehensive documentation per domain
🔄 Detect and map entity relationships
🔄 Create visual architecture diagrams
🔄 Produce complete codebase encyclopedia (technical + functional)

### How to Use It:
```bash
python src/analyze_domains.py your-java-project
```

That's it! The system does everything automatically.

---

**Last Updated**: After completing domain discovery system
**Status**: Domain discovery foundation complete, ready for next phase
