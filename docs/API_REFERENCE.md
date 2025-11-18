# API Reference

Complete API documentation for all classes and functions in the Java Codebase Analyzer.

---

## Table of Contents

1. [Utils](#utils)
2. [Parser](#parser)
3. [Knowledge Graph](#knowledge-graph)
4. [Inference](#inference)
5. [RAG System](#rag-system)
6. [Agents](#agents)

---

## Utils

### GitHubCloner

**Location**: `src/utils/github_cloner.py`

Class for cloning GitHub repositories.

#### `__init__(workspace_dir: Optional[str] = None)`

Initialize the GitHub cloner.

**Parameters**:
- `workspace_dir` (str, optional): Directory to clone repos into. If None, uses `/tmp/codebase_analysis`

**Example**:
```python
from src.utils.github_cloner import GitHubCloner

cloner = GitHubCloner()  # Uses default temp directory
# or
cloner = GitHubCloner("/path/to/workspace")  # Custom directory
```

#### `validate_github_url(url: str) -> Dict[str, Any]`

Validate if URL is a valid GitHub repository URL.

**Parameters**:
- `url` (str): GitHub repository URL

**Returns**:
- `Dict[str, Any]`: Validation result with keys:
  - `valid` (bool): Whether URL is valid
  - `owner` (str): Repository owner (if valid)
  - `repo` (str): Repository name (if valid)
  - `clone_url` (str): Git clone URL (if valid)
  - `error` (str): Error message (if invalid)

**Example**:
```python
result = cloner.validate_github_url("https://github.com/spring-projects/spring-petclinic")
# Returns: {"valid": True, "owner": "spring-projects", "repo": "spring-petclinic", ...}
```

#### `clone_repository(github_url: str) -> Dict[str, Any]`

Clone a GitHub repository.

**Parameters**:
- `github_url` (str): GitHub repository URL

**Returns**:
- `Dict[str, Any]`: Clone result with keys:
  - `success` (bool): Whether clone succeeded
  - `local_path` (str): Local path to cloned repo (if success)
  - `owner` (str): Repository owner (if success)
  - `repo` (str): Repository name (if success)
  - `github_url` (str): Original URL (if success)
  - `error` (str): Error message (if failed)

**Example**:
```python
result = cloner.clone_repository("https://github.com/spring-projects/spring-petclinic")
if result["success"]:
    print(f"Cloned to: {result['local_path']}")
```

#### `cleanup_repository(local_path: str) -> None`

Remove cloned repository to free up space.

**Parameters**:
- `local_path` (str): Path to cloned repository

---

## Parser

### GenericJavaParser

**Location**: `src/parser/generic_java_parser.py`

Framework-agnostic Java parser using tree-sitter.

#### `__init__()`

Initialize the parser with tree-sitter Java grammar.

**Example**:
```python
from src.parser.generic_java_parser import GenericJavaParser

parser = GenericJavaParser()
```

#### `parse_directory(directory: str, knowledge_graph: KnowledgeGraph) -> None`

Parse all Java files in a directory and add to knowledge graph.

**Parameters**:
- `directory` (str): Path to directory containing Java files
- `knowledge_graph` (KnowledgeGraph): Knowledge graph to populate

**Example**:
```python
from src.knowledge_graph.graph import KnowledgeGraph

kg = KnowledgeGraph()
parser.parse_directory("/path/to/java/project", kg)
```

#### `parse_file(file_path: str) -> Optional[ClassNode]`

Parse a single Java file and return class information.

**Parameters**:
- `file_path` (str): Path to Java file

**Returns**:
- `Optional[ClassNode]`: Class node if parsing succeeds, None otherwise

---

### RelationshipExtractor

**Location**: `src/parser/relationship_extractor.py`

Extract relationships between code elements.

#### `__init__(parser: GenericJavaParser)`

Initialize relationship extractor.

**Parameters**:
- `parser` (GenericJavaParser): Parser instance with parsed code

**Example**:
```python
from src.parser.relationship_extractor import RelationshipExtractor

extractor = RelationshipExtractor(parser)
```

#### `extract_all_relationships(knowledge_graph: KnowledgeGraph) -> None`

Extract all relationships and add to knowledge graph.

**Parameters**:
- `knowledge_graph` (KnowledgeGraph): Knowledge graph to update

**Extracts**:
- Method calls (CALLS)
- Class inheritance (EXTENDS)
- Interface implementation (IMPLEMENTS)
- Field access (ACCESSES)

**Example**:
```python
extractor.extract_all_relationships(kg)
```

---

## Knowledge Graph

### KnowledgeGraph

**Location**: `src/knowledge_graph/graph.py`

Central data structure for storing codebase structure.

#### `__init__()`

Initialize empty knowledge graph.

**Example**:
```python
from src.knowledge_graph.graph import KnowledgeGraph

kg = KnowledgeGraph()
```

#### `add_class(class_node: ClassNode) -> str`

Add a class node to the graph.

**Parameters**:
- `class_node` (ClassNode): Class information

**Returns**:
- `str`: Node ID

**Example**:
```python
from src.knowledge_graph.graph import ClassNode

class_node = ClassNode(
    name="UserController",
    package="com.example.controller",
    file_path="/path/to/UserController.java",
    class_type="Controller",
    annotations=["@RestController"]
)
kg.add_class(class_node)
```

#### `add_method(method_node: MethodNode, class_id: str) -> str`

Add a method node to the graph.

**Parameters**:
- `method_node` (MethodNode): Method information
- `class_id` (str): ID of parent class

**Returns**:
- `str`: Node ID

#### `add_edge(from_id: str, to_id: str, edge_type: EdgeType, **metadata) -> None`

Add an edge (relationship) between two nodes.

**Parameters**:
- `from_id` (str): Source node ID
- `to_id` (str): Target node ID
- `edge_type` (EdgeType): Type of relationship
- `**metadata`: Additional edge metadata

**Example**:
```python
from src.knowledge_graph.graph import EdgeType

kg.add_edge(method_id, other_method_id, EdgeType.CALLS)
```

#### `get_stats() -> Dict[str, int]`

Get graph statistics.

**Returns**:
- `Dict[str, int]`: Statistics with keys:
  - `classes`: Total classes
  - `classes_only`: Classes (not interfaces/enums)
  - `interfaces`: Total interfaces
  - `enums`: Total enums
  - `methods`: Total methods
  - `fields`: Total fields
  - `total_edges`: Total relationships

**Example**:
```python
stats = kg.get_stats()
print(f"Classes: {stats['classes']}, Methods: {stats['methods']}")
```

#### `export_to_dict() -> Dict[str, Any]`

Export entire graph as dictionary (JSON-serializable).

**Returns**:
- `Dict[str, Any]`: Complete graph data

**Example**:
```python
import json

graph_data = kg.export_to_dict()
with open("graph.json", "w") as f:
    json.dump(graph_data, f, indent=2)
```

---

## Inference

### FrameworkDetectorV2

**Location**: `src/inference/framework_detector_v2.py`

AI-powered framework detection using Google Gemini.

#### `__init__()`

Initialize framework detector with Gemini LLM.

**Environment Variables Required**:
- `CODEBASE_GEMINI_KEY` or `GOOGLE_API_KEY`

**Example**:
```python
from src.inference.framework_detector_v2 import FrameworkDetectorV2

detector = FrameworkDetectorV2()
```

#### `detect_framework(knowledge_graph: KnowledgeGraph) -> Dict[str, Any]`

Detect framework used in the codebase.

**Parameters**:
- `knowledge_graph` (KnowledgeGraph): Knowledge graph of codebase

**Returns**:
- `Dict[str, Any]`: Detection result with keys:
  - `framework` (str): Detected framework name
  - `confidence` (float): Confidence score (0-1)
  - `reasoning` (str): Explanation of detection
  - `source` (str): Detection method used
  - `architecture_patterns` (List[str]): Identified patterns

**Example**:
```python
result = detector.detect_framework(kg)
print(f"Framework: {result['framework']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Reasoning: {result['reasoning']}")
```

### GraphSummarizer

**Location**: `src/inference/graph_summarizer.py`

Create structured summaries of knowledge graphs.

#### `create_structured_summary(knowledge_graph: KnowledgeGraph) -> Dict[str, Any]`

Create a structured summary for LLM analysis.

**Parameters**:
- `knowledge_graph` (KnowledgeGraph): Knowledge graph to summarize

**Returns**:
- `Dict[str, Any]`: Structured summary with:
  - Statistics (class counts, method counts)
  - Annotation usage
  - Package structure
  - Common patterns

**Example**:
```python
from src.inference.graph_summarizer import create_structured_summary

summary = create_structured_summary(kg)
```

---

## RAG System

### VectorStoreManager

**Location**: `src/rag/vectorstore_manager.py`

Manages FAISS vector store and embeddings.

#### `__init__(output_dimensionality: int = 768, use_local: bool = False)`

Initialize vector store manager.

**Parameters**:
- `output_dimensionality` (int): Embedding dimensions (default: 768)
- `use_local` (bool): Force use of local embeddings (default: False)

**Example**:
```python
from src.rag.vectorstore_manager import VectorStoreManager

# Use Gemini embeddings
manager = VectorStoreManager()

# Use local embeddings
manager = VectorStoreManager(use_local=True)
```

#### `create_vectorstore(documents: List[Document], repo_name: str) -> FAISS`

Create FAISS vector store from documents.

**Parameters**:
- `documents` (List[Document]): LangChain documents to index
- `repo_name` (str): Repository name for storage

**Returns**:
- `FAISS`: FAISS vector store instance

**Example**:
```python
from src.rag.graph_to_documents import convert_graph_to_documents

documents = convert_graph_to_documents(kg)
vectorstore = manager.create_vectorstore(documents, "spring-petclinic")
```

#### `load_vectorstore(repo_name: str) -> Optional[FAISS]`

Load existing vector store from disk.

**Parameters**:
- `repo_name` (str): Repository name

**Returns**:
- `Optional[FAISS]`: Vector store if exists, None otherwise

### Graph to Documents

**Location**: `src/rag/graph_to_documents.py`

#### `convert_graph_to_documents(knowledge_graph: KnowledgeGraph) -> List[Document]`

Convert knowledge graph to LangChain documents.

**Parameters**:
- `knowledge_graph` (KnowledgeGraph): Knowledge graph to convert

**Returns**:
- `List[Document]`: List of LangChain documents

**Example**:
```python
from src.rag.graph_to_documents import convert_graph_to_documents

documents = convert_graph_to_documents(kg)
print(f"Created {len(documents)} documents")
```

### Retriever Tool

**Location**: `src/rag/retriever_tool.py`

#### `create_codebase_retriever_tool(vectorstore: FAISS, search_kwargs: Dict = None) -> Tool`

Create LangChain tool for RAG retrieval.

**Parameters**:
- `vectorstore` (FAISS): FAISS vector store
- `search_kwargs` (Dict, optional): Search parameters (e.g., {"k": 5})

**Returns**:
- `Tool`: LangChain tool for agents

**Example**:
```python
from src.rag.retriever_tool import create_codebase_retriever_tool

tool = create_codebase_retriever_tool(vectorstore, search_kwargs={"k": 10})
```

---

## Agents

### ArchitectureAgent

**Location**: `src/rag/agents/architecture_agent.py`

Basic architecture analysis agent.

#### `__init__(vectorstore: FAISS)`

Initialize architecture agent.

**Parameters**:
- `vectorstore` (FAISS): Vector store with codebase data

**Example**:
```python
from src.rag.agents.architecture_agent import ArchitectureAgent

agent = ArchitectureAgent(vectorstore)
```

#### `analyze(query: str) -> Dict[str, Any]`

Analyze architecture based on query.

**Parameters**:
- `query` (str): Analysis question

**Returns**:
- `Dict[str, Any]`: Analysis result with keys:
  - `success` (bool): Whether analysis succeeded
  - `query` (str): Original query
  - `answer` (str): Analysis answer
  - `intermediate_steps` (list): Agent reasoning steps
  - `error` (str): Error message (if failed)

**Example**:
```python
result = agent.analyze("What architecture patterns are used?")
if result["success"]:
    print(result["answer"])
```

#### `ask(question: str) -> str`

Convenience method to just get the answer.

**Parameters**:
- `question` (str): Architecture question

**Returns**:
- `str`: Answer string

**Example**:
```python
answer = agent.ask("How many controllers are there?")
print(answer)
```

### FrameworkAwareArchitectureAgent

**Location**: `src/rag/agents/framework_aware_architecture_agent.py`

Main agent for framework-specific analysis.

#### `__init__(vectorstore: FAISS)`

Initialize framework-aware agent.

**Parameters**:
- `vectorstore` (FAISS): Vector store with codebase data

#### `analyze_architecture(project_name: str = "Java Project") -> Dict[str, Any]`

Analyze architecture with framework detection.

**Parameters**:
- `project_name` (str): Name of the project

**Returns**:
- `Dict[str, Any]`: Comprehensive analysis with keys:
  - `project_name` (str): Project name
  - `framework` (str): Detected framework
  - `analysis` (str): Comprehensive analysis text
  - `findings` (str): Detailed findings

**Example**:
```python
from src.rag.agents.framework_aware_architecture_agent import FrameworkAwareArchitectureAgent

agent = FrameworkAwareArchitectureAgent(vectorstore)
result = agent.analyze_architecture("Spring PetClinic")
print(f"Framework: {result['framework']}")
print(result['analysis'])
```

### Report Generator

**Location**: `src/rag/report_generator.py`

#### ArchitectureReportGenerator

##### `__init__(vectorstore: FAISS)`

Initialize report generator.

**Parameters**:
- `vectorstore` (FAISS): Vector store with codebase data

##### `generate_report(project_name: str = "Java Project") -> ArchitectureReport`

Generate comprehensive architecture report.

**Parameters**:
- `project_name` (str): Name of the project

**Returns**:
- `ArchitectureReport`: Structured report with:
  - `project_name` (str)
  - `executive_summary` (str)
  - `architecture_patterns` (List[str])
  - `layers` (List[LayerInfo])
  - `key_components` (List[ComponentInfo])
  - `data_flow` (str)
  - `technology_stack` (List[str])
  - `strengths` (List[str])
  - `recommendations` (List[str])

**Example**:
```python
from src.rag.report_generator import ArchitectureReportGenerator

generator = ArchitectureReportGenerator(vectorstore)
report = generator.generate_report("Spring PetClinic")

print(report.executive_summary)
for pattern in report.architecture_patterns:
    print(f"- {pattern}")
```

#### MermaidDiagramGenerator

##### `__init__()`

Initialize diagram generator.

##### `generate_component_diagram(report: ArchitectureReport) -> MermaidDiagram`

Generate component/layered architecture diagram.

**Parameters**:
- `report` (ArchitectureReport): Architecture report

**Returns**:
- `MermaidDiagram`: Mermaid diagram with:
  - `diagram_type` (str): "flowchart"
  - `title` (str): Diagram title
  - `mermaid_code` (str): Mermaid syntax
  - `description` (str): What diagram shows

**Example**:
```python
from src.rag.report_generator import MermaidDiagramGenerator

generator = MermaidDiagramGenerator()
diagram = generator.generate_component_diagram(report)

print(diagram.mermaid_code)
# Save to file
with open("component_diagram.mmd", "w") as f:
    f.write(diagram.mermaid_code)
```

##### `generate_class_diagram(report: ArchitectureReport) -> MermaidDiagram`

Generate class diagram showing entities.

**Parameters**:
- `report` (ArchitectureReport): Architecture report

**Returns**:
- `MermaidDiagram`: Mermaid class diagram

---

## Data Models

### ClassNode

**Location**: `src/knowledge_graph/graph.py`

Represents a Java class/interface/enum.

**Attributes**:
- `name` (str): Class name
- `package` (str): Package name
- `file_path` (str): File path
- `class_type` (str): Controller, Service, etc.
- `java_type` (str): "class", "interface", "enum", "annotation"
- `modifiers` (List[str]): public, abstract, etc.
- `annotations` (List[str]): @RestController, etc.
- `interfaces` (List[str]): Implemented interfaces
- `superclass` (Optional[str]): Parent class
- `is_abstract` (bool): Is abstract class

### MethodNode

Represents a Java method.

**Attributes**:
- `name` (str): Method name
- `class_name` (str): Parent class
- `signature` (str): Full signature
- `return_type` (str): Return type
- `parameters` (List[Dict]): Parameter list
- `modifiers` (List[str]): public, static, etc.
- `annotations` (List[str]): @Override, etc.
- `body` (Optional[str]): Method body
- `line_start` (int): Start line number
- `line_end` (int): End line number

### FieldNode

Represents a Java field.

**Attributes**:
- `name` (str): Field name
- `class_name` (str): Parent class
- `field_type` (str): Field type
- `modifiers` (List[str]): private, final, etc.
- `annotations` (List[str]): @Autowired, etc.
- `initial_value` (Optional[str]): Initial value

### ArchitectureReport

**Location**: `src/rag/report_generator.py`

Complete architecture report (Pydantic model).

**Attributes**:
- `project_name` (str): Name of project
- `executive_summary` (str): High-level overview
- `architecture_patterns` (List[str]): Patterns used
- `layers` (List[LayerInfo]): Architectural layers
- `key_components` (List[ComponentInfo]): Key components
- `data_flow` (str): Data flow description
- `technology_stack` (List[str]): Technologies used
- `strengths` (List[str]): Architecture strengths
- `recommendations` (List[str]): Improvements

---

## Complete Usage Example

```python
# 1. Clone repository
from src.utils.github_cloner import GitHubCloner

cloner = GitHubCloner()
result = cloner.clone_repository("https://github.com/spring-projects/spring-petclinic")
local_path = result["local_path"]

# 2. Parse and create knowledge graph
from src.knowledge_graph.graph import KnowledgeGraph
from src.parser.generic_java_parser import GenericJavaParser
from src.parser.relationship_extractor import RelationshipExtractor

kg = KnowledgeGraph()
parser = GenericJavaParser()
parser.parse_directory(local_path, kg)

extractor = RelationshipExtractor(parser)
extractor.extract_all_relationships(kg)

# 3. Detect framework
from src.inference.framework_detector_v2 import FrameworkDetectorV2

detector = FrameworkDetectorV2()
framework_result = detector.detect_framework(kg)
print(f"Framework: {framework_result['framework']} ({framework_result['confidence']:.0%})")

# 4. Create RAG index
from src.rag.graph_to_documents import convert_graph_to_documents
from src.rag.vectorstore_manager import VectorStoreManager

documents = convert_graph_to_documents(kg)
manager = VectorStoreManager()
vectorstore = manager.create_vectorstore(documents, "spring-petclinic")

# 5. Query with agent
from src.rag.agents.architecture_agent import ArchitectureAgent

agent = ArchitectureAgent(vectorstore)
answer = agent.ask("What architecture patterns are used?")
print(answer)

# 6. Generate report
from src.rag.report_generator import ArchitectureReportGenerator

report_generator = ArchitectureReportGenerator(vectorstore)
report = report_generator.generate_report("Spring PetClinic")

print(report.executive_summary)
for pattern in report.architecture_patterns:
    print(f"- {pattern}")

# 7. Generate diagrams
from src.rag.report_generator import MermaidDiagramGenerator

diagram_generator = MermaidDiagramGenerator()
component_diagram = diagram_generator.generate_component_diagram(report)

# Save diagram
with open("component_diagram.mmd", "w") as f:
    f.write(component_diagram.mermaid_code)

# 8. Export graph
import json

graph_data = kg.export_to_dict()
with open("graph.json", "w") as f:
    json.dump(graph_data, f, indent=2)

# 9. Cleanup
cloner.cleanup_repository(local_path)
```

---

**Last Updated**: November 2025
