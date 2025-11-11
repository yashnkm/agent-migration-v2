# Deprecated Code

This folder contains deprecated code that has been replaced by the LLM-based framework-agnostic approach.

## Deprecated Files

### Scripts (Old Query-Based System)
- `app.py` - Old Streamlit UI (replaced by `app_v2.py`)
- `main.py` - Old CLI interface (query-based, user didn't want this)
- `query_interface.py` - Query interface (removed per user request)
- `analyze_domains.py` - Old domain analysis script

### Parser
- `java_parser.py` - Hardcoded Spring Boot parser (replaced by `generic_java_parser.py`)
  - Had hardcoded annotations for Spring Boot only
  - Classified classes during parsing (wrong approach)
  - **Replaced by**: `src/parser/generic_java_parser.py` (generic, no classification)

### Agents (Old Multi-Agent System)
- `orchestrator.py` - Agent orchestrator (deprecated, added deprecation warning)
- `api_documentation_agent.py` - API doc generator
- `business_logic_analyzer.py` - Business logic agent
- `data_flow_tracer.py` - Data flow tracing
- `base_agent.py` - Base agent class

**Why deprecated?**: User said "i dont want to query anything, i just want that we understand the code base"
The multi-agent query system was replaced with proactive analysis + LLM classification.

## Current Architecture (Active Code)

### Parsing
- ✅ `src/parser/generic_java_parser.py` - Framework-agnostic parser
- ✅ `src/parser/relationship_extractor.py` - Relationship extraction

### Inference (LLM-Based)
- ✅ `src/inference/framework_detector.py` - AI framework detection
- ✅ `src/inference/class_classifier.py` - AI class classification

### Domain Analysis
- ✅ `src/domain_analyzer/domain_graph.py` - Domain discovery
- ✅ `src/domain_analyzer/business_analyzer.py` - Business logic analysis

### UI
- ✅ `app_v2.py` - Main Streamlit UI (active)

## Why These Were Deprecated

1. **Hardcoded Patterns**: Old parser/agents used hardcoded Spring Boot patterns
2. **Query-Based**: User explicitly didn't want query interface
3. **Not Framework-Agnostic**: Only worked for Spring Boot
4. **Patch Work**: Required manual updates for each framework

## New Approach

**Zero Hardcoding - Pure LLM Pattern Recognition**
1. Generic parsing (extract everything, no assumptions)
2. LLM framework detection (Gemini identifies framework)
3. LLM class classification (Gemini classifies based on patterns)
4. Domain discovery (works on any framework)

---

**Note**: These files are kept for reference only. Do not use in production.
