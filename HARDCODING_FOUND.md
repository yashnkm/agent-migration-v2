# Hardcoding Issues Found - Not Framework Agnostic

## Critical Issues Preventing Universal Discovery

### Issue 1: HARDCODED Spring Boot Endpoint Detection
**Location**: `src/parser/relationship_extractor.py:108-115`

```python
endpoint_annotations = {
    'GetMapping': 'GET',      # ← HARDCODED Spring Boot
    'PostMapping': 'POST',    # ← HARDCODED Spring Boot
    'PutMapping': 'PUT',      # ← HARDCODED Spring Boot
    'DeleteMapping': 'DELETE', # ← HARDCODED Spring Boot
    'PatchMapping': 'PATCH',  # ← HARDCODED Spring Boot
    'RequestMapping': 'REQUEST' # ← HARDCODED Spring Boot
}
```

**Why this breaks Struts:**
- Struts uses `@Action`, `@Actions`, `@Namespace` annotations
- Struts methods in Action classes ARE entry points but won't be detected
- No endpoints created for Struts = no entry points = no domains discovered

**What needs to happen instead:**
- Don't detect endpoints at parsing time
- Let universal discovery INFER endpoints based on:
  - Public methods in entry point classes
  - Methods that are called from outside (entry methods)
  - Methods with ANY annotation on them

---

### Issue 2: HARDCODED CRUD Verb List for Repository Detection
**Location**: `src/domain_analyzer/universal_domain_discovery.py:347-354`

```python
crud_verbs = ['save', 'find', 'get', 'delete', 'remove', 'update',
              'create', 'insert', 'select', 'read']
crud_method_count = sum(
    1 for m in methods
    if any(verb in m.name.lower() for verb in crud_verbs)
)

if crud_method_count >= 2:
    return 'repository'
```

**Why this breaks:**
- What if repository uses `persist`, `fetch`, `retrieve`, `destroy`?
- What if it's in a different language/naming convention?
- Not truly behavior-based

**What needs to happen instead:**
- Analyze what methods DO, not what they're named
- Repository = low fanout (doesn't orchestrate), called by services, has parameters/returns of entity types

---

### Issue 3: Edge Type Comparison Bug
**Location**: `src/domain_analyzer/universal_domain_discovery.py:275`

```python
if not edge_data or edge_data.get('type') != 'CALLS':
    continue
```

**Problem**: Should be `!= EdgeType.CALLS` (enum comparison)

This is inconsistent with the fix in `count_method_calls()` where we properly handle MultiDiGraph.

---

### Issue 4: Hardcoded Business Verb List
**Location**: `src/domain_analyzer/universal_domain_discovery.py:360-367`

```python
business_verbs = ['process', 'calculate', 'validate', 'execute',
                  'handle', 'manage', 'perform']
```

Same problem as Issue 2 - relies on naming, not behavior.

---

## Root Problem: Philosophy Violation

The system claims to be "framework-agnostic" and "behavior-based" but still relies on:
1. Framework-specific annotation names (Spring Boot only)
2. English naming conventions (crud_verbs, business_verbs)
3. Hardcoded patterns instead of actual behavior analysis

## What True Behavior-Based Discovery Looks Like

### For Entry Points:
- ✅ High fanout (makes many calls) - ALREADY DOING THIS
- ✅ Public methods - Can detect
- ✅ Methods with annotations (any annotation) - Can detect
- ❌ Framework-specific annotation matching - REMOVE THIS

### For Repositories:
- ✅ Low fanout (doesn't orchestrate)
- ✅ Called by services
- ✅ Returns/accepts entity types
- ❌ Name matching (crud_verbs) - SHOULD BE SECONDARY, NOT PRIMARY

### For Services:
- ✅ Medium fanout (orchestrates some calls)
- ✅ Called by entry points
- ✅ Calls repositories
- ❌ Name matching (business_verbs) - SHOULD BE SECONDARY, NOT PRIMARY

### For Entities:
- ✅ High field count
- ✅ Many getters/setters
- ✅ Low method call count
- ✅ Used as parameter/return type in repositories - ALREADY DOING THIS

---

## Why Repositories Aren't Being Found

**Hypothesis 1**: The CRUD verb list doesn't match the actual method names in the repository

**Hypothesis 2**: The edge tracing is broken due to edge type comparison bug (line 275)

**Hypothesis 3**: The method calls aren't being resolved correctly because we store simple names ("save") but try to match full qualified names ("com.example.repo.UserRepository.save")

**Most Likely**: Combination of all three

---

## Why Struts Actions Aren't Detected as Endpoints

**Root Cause**: Only Spring Boot annotations are checked

**Current Flow**:
1. Parse Struts Action class ✅ (works)
2. Parse method with `@Action` annotation ✅ (annotation stored)
3. Check if annotation matches Spring Boot list ❌ (fails - Struts annotation not in list)
4. No endpoint created ❌
5. No entry point detected ❌
6. No domain discovered ❌

**Should Be**:
1. Parse Struts Action class ✅
2. Parse method with `@Action` annotation ✅
3. Store annotation WITHOUT classification ✅
4. Universal discovery detects "Action" as entry point by:
   - Class name ends with "Action" ✅
   - Has public methods ✅
   - Methods have annotations (any annotation) ✅
   - High fanout (orchestrates calls) ✅
5. Entry point detected ✅
6. Domain discovered ✅

---

## Proposed Solution

### Step 1: Remove Hardcoded Endpoint Detection
- Delete `extract_endpoints()` method entirely
- Let universal discovery infer endpoints from entry point methods

### Step 2: Fix Edge Type Comparison
- Update line 275 to handle MultiDiGraph properly
- Use same logic as `count_method_calls()`

### Step 3: Make Repository Detection Purely Behavioral
- Primary: Low fanout + called by services + has entity types
- Secondary (optional hint): CRUD verbs

### Step 4: Make Service Detection Purely Behavioral
- Primary: Medium fanout + called by entry points + calls repositories
- Secondary (optional hint): Business verbs

### Step 5: Better Method Resolution
- When tracing calls, need to resolve simple names to full class names
- Use type inference or import analysis
- Or: Accept that we only know "a method called X was called" and that's enough for counting

---

## Testing Plan

1. Test with Spring Boot (should still work)
2. Test with Struts (should now work)
3. Test with JAX-RS/Jersey (should work)
4. Test with Play Framework (should work)
5. Test with repository methods named differently (persist, fetch, etc.)
