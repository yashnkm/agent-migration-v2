# Root Issue Found: CALLS Edges Not in Graph

## The Problem

When running universal domain discovery on a Spring Boot project:

### What Relationship Extractor Reports:
```
Analyzing: com.example.restservice.GreetingController.greeting
  com.example.restservice.GreetingController.greeting calls incrementAndGet
  com.example.restservice.GreetingController.greeting calls format
```

### What's Actually in the Graph:
```
method:com.example.restservice.GreetingController.greeting
  Total out edges: 0  ← NO EDGES!
  Total CALLS edges: 0
```

## Root Cause

**The CALLS edges are being detected but NOT being stored in the NetworkX graph.**

This means:
1. ✅ Parsing works (methods found)
2. ✅ Relationship extraction finds calls (prints "calls incrementAndGet")
3. ❌ **Graph storage fails** (edges not added to NetworkX)
4. ❌ Universal discovery can't find high-fanout methods (no edges to count)
5. ❌ No entry points detected (0 domains found)

## Why Universal Discovery Failed

```python
def count_method_calls(self, method) -> int:
    method_id = f"method:{method.class_name}.{method.name}"

    # Count CALLS edges
    for edge in self.knowledge_graph.graph.out_edges(method_id):
        edge_data = self.knowledge_graph.graph.get_edge_data(*edge)
        if edge_data and edge_data.get('type') == 'CALLS':
            call_count += 1

    return call_count  # Returns 0 because no edges exist!
```

## What Needs to be Fixed

### Check `src/parser/relationship_extractor.py`

The relationship extractor needs to:
1. ✅ Find method calls (currently working)
2. ❌ **Add them to knowledge_graph.graph** (NOT WORKING)

Look for where it should call:
```python
knowledge_graph.graph.add_edge(
    source_method_id,
    target_method_id,
    type=EdgeType.CALLS
)
```

## Expected Behavior

After fixing, we should see:
```
method:com.example.restservice.GreetingController.greeting
  Total out edges: 2
  CALLS: method:some.class.incrementAndGet
  CALLS: method:some.class.format
  Total CALLS edges: 2
```

Then:
- `count_method_calls()` returns 2
- `greeting` method detected as high-fanout
- `GreetingController` detected as entry point
- Domain "Greeting" discovered!

## The Fix Needed

Either:
1. **Fix relationship_extractor.py** to properly add edges to the graph
2. **Or** ensure the print statements indicate edges ARE being added but we're querying wrong

Need to trace through the relationship extraction code to see where edges should be stored.
