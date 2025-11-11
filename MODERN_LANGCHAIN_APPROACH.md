# Modern LangChain Approach for Framework Detection

## What Was Implemented

### Using LangChain `with_structured_output`

Based on the MCP LangChain docs, I created a modern framework detector using:

**File**: `src/inference/framework_detector_v2.py`

### Key Features:

1. **Structured Output with Pydantic Models**
   - Uses `llm.with_structured_output(Pydantic_Model)`
   - Guarantees typed, validated responses
   - No manual parsing needed

2. **Structured Summary Input**
   - Uses `GraphSummarizer` to create comprehensive codebase analysis
   - Sends ALL patterns to LLM (annotations, packages, inheritance, etc.)
   - Better than RAG for complete codebase analysis

3. **Fallback to Heuristics**
   - If LLM fails (API issues, etc.), falls back to rule-based detection
   - Ensures system always works

## Code Structure

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# Define output schema
class FrameworkCandidate(BaseModel):
    name: str = Field(description="Framework name")
    confidence: float = Field(description="0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Why detected")

class FrameworkDetectionResult(BaseModel):
    primary_framework: FrameworkCandidate
    secondary_frameworks: List[FrameworkCandidate] = []
    architecture_patterns: List[str] = []

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=api_key,
    temperature=0
)

# Create structured LLM
structured_llm = llm.with_structured_output(FrameworkDetectionResult)

# Invoke with prompt
result: FrameworkDetectionResult = structured_llm.invoke(prompt)

# Get typed, validated output
print(result.primary_framework.name)  # "Spring Boot"
print(result.primary_framework.confidence)  # 0.95
```

## Why This Approach?

### Compared to Old Approach (ChatPromptTemplate + OutputParser):

**Old**:
```python
# Manual prompt formatting
prompt = ChatPromptTemplate.from_messages([...])
parser = PydanticOutputParser(pydantic_object=Model)

# Chain them
chain = prompt | llm | parser

# Hope parsing works
result = chain.invoke({
    "class_annotations": ", ".join(...),  # Manual formatting
    "method_annotations": ", ".join(...),
    "format_instructions": parser.get_format_instructions()  # Extra prompt
})
```

**New**:
```python
# Direct structured output
structured_llm = llm.with_structured_output(Model)

# Just invoke
result = structured_llm.invoke(prompt_string)
```

### Benefits:

1. ✅ **Simpler**: No manual prompt template construction
2. ✅ **Reliable**: LLM natively generates structured output
3. ✅ **Type-safe**: Pydantic validation built-in
4. ✅ **Cleaner**: Less boilerplate code
5. ✅ **Modern**: Uses latest LangChain patterns

## From MCP Docs

According to the LangChain MCP documentation:

> **Structured output** allows agents to return data in a specific, predictable format. Instead of parsing natural language responses, you get structured data in the form of JSON objects, Pydantic models, or dataclasses that your application can directly use.

Key patterns from docs:

```python
# Pattern 1: Direct Pydantic model
model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("Tell me about Inception")
# response is a Movie instance

# Pattern 2: With agents (create_agent - requires LangChain 1.0+)
agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_tool],
    response_format=ToolStrategy(ContactInfo)
)

# Pattern 3: With include_raw for metadata
model_with_structure = model.with_structured_output(Movie, include_raw=True)
result = model_with_structure.invoke(...)
# result = {"parsed": Movie(...), "raw": AIMessage(...)}
```

## UI Integration

The button in `app_v2.py` now uses:

```python
detector = FrameworkDetectorV2()  # Uses with_structured_output
result = detector.detect_framework(kg)

# Result is typed dict with:
# - framework: str
# - confidence: float
# - reasoning: str
# - architecture_patterns: List[str]
# - source: "LLM" or "HEURISTIC"
```

## Testing

To test:

```bash
streamlit run app_v2.py
```

1. Enter GitHub URL
2. Click "Create Graph"
3. Click "Detect Framework"
4. See structured result with confidence

## Current Status

- ✅ Structured summary generator created
- ✅ Modern LangChain approach implemented
- ✅ Pydantic models defined
- ✅ Fallback to heuristics
- ✅ UI integrated
- ⚠️ Needs valid GOOGLE_GENAI_API_KEY to test LLM path
- ✅ Heuristic fallback works without API key

## Next Steps

1. **Test with valid API key**: See full LLM structured output
2. **Fine-tune prompt**: Improve framework detection accuracy
3. **Add more frameworks**: Expand detection to more frameworks
4. **GraphRAG**: Build on this for user queries (future)

## Comparison: RAG vs Structured Summary

For framework detection specifically:

| Aspect | RAG | Structured Summary |
|--------|-----|-------------------|
| **Coverage** | Top-k docs | Complete codebase |
| **Accuracy** | May miss patterns | Sees all patterns |
| **Speed** | Embedding + retrieval | Direct analysis |
| **Complexity** | High | Low |
| **Best For** | User queries ("Find X") | Analysis tasks |

**Conclusion**: Use structured summary for framework detection, save RAG for user queries!
