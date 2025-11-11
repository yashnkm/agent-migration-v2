# Hardcoded Issues Found - Audit Report

## Problems Identified

### 🔴 Critical Issues:

#### 1. **Hardcoded Spring Annotations** (`src/parser/java_parser.py`)
```python
# HARDCODED - Only works for Spring Framework
self.controller_annotations = {'Controller', 'RestController'}
self.service_annotations = {'Service'}
self.repository_annotations = {'Repository'}
self.entity_annotations = {'Entity', 'Table'}
self.endpoint_annotations = {
    'GetMapping', 'PostMapping', 'PutMapping',
    'DeleteMapping', 'PatchMapping', 'RequestMapping'
}
```

**Problem**: System ONLY recognizes Spring Boot annotations.

**Missing Support**:
- Jakarta EE: `@Path`, `@GET`, `@POST`, `@Stateless`, `@Singleton`
- Micronaut: `@Controller`, `@Get`, `@Post`, `@Singleton`
- Quarkus: `@Path`, `@GET`, `@POST`, `@ApplicationScoped`
- JAX-RS: `@Path`, `@GET`, `@POST`, `@PUT`, `@DELETE`
- Plain Java: No annotations at all
- Custom frameworks

---

#### 2. **Name-Based Domain Mapping** (`src/domain_analyzer/domain_graph.py`)
```python
# Line 140 - HARDCODED pattern matching
if domain_lower in class_name_lower:
    if class_node.class_type == "Controller":
        domain_info.controller = full_class_name
```

**Problem**: Assumes naming convention: `EmployeeController`, `EmployeeService`, etc.

**Fails When**:
- Classes named differently: `EmployeeResource`, `EmployeeEndpoint`, `EmployeeManager`
- Multiple words: `CustomerOrderController` - which domain? Customer or Order?
- No naming pattern: `UserHandler`, `DataProcessor`

---

#### 3. **Class Type Classification** (`src/parser/java_parser.py`)
```python
def classify_class_type(self, annotations: List[str]) -> str:
    annotation_set = set(annotations)

    if annotation_set & self.controller_annotations:
        return "Controller"
    elif annotation_set & self.service_annotations:
        return "Service"
    # ...
    else:
        return "Class"  # Default - no type
```

**Problem**: Only detects Spring-annotated classes. Plain classes get type "Class".

---

#### 4. **Endpoint Detection** (`src/parser/relationship_extractor.py`)
```python
endpoint_annotations = {
    'GetMapping': 'GET',
    'PostMapping': 'POST',
    # Only Spring mappings
}
```

**Problem**: Misses JAX-RS `@Path`, `@GET`, `@POST`, etc.

---

### 🟡 Design Issues:

#### 5. **Entity Detection**
Only looks for `@Entity` annotation. Misses:
- Plain POJOs
- Record classes (Java 14+)
- Classes without JPA annotations
- Custom entity frameworks

#### 6. **No Fallback Logic**
If annotations don't match Spring patterns:
- Class type = "Class"
- Not assigned to any domain
- Endpoints not detected
- Lost in analysis

---

## What Gets Missed:

### Example: Jakarta EE Application
```java
@Path("/employees")
@Stateless
public class EmployeeResource {

    @GET
    @Produces("application/json")
    public List<Employee> getAllEmployees() {
        // ...
    }
}
```

**Current System**:
- ❌ Not recognized as Controller
- ❌ Endpoints not extracted
- ❌ Class type = "Class"
- ❌ Not assigned to Employee domain

---

### Example: Micronaut Application
```java
@Controller("/employees")
public class EmployeeController {

    @Get
    public List<Employee> list() {
        // ...
    }
}
```

**Current System**:
- ✅ Recognized as Controller (same annotation name)
- ❌ Endpoints not extracted (@Get not recognized)
- ❌ Missing endpoint details

---

### Example: Plain Java (No Framework)
```java
public class EmployeeService {
    public Employee createEmployee(Employee emp) {
        // ...
    }
}
```

**Current System**:
- ❌ Not recognized as Service (no @Service annotation)
- ❌ Class type = "Class"
- ❌ Not included in domain analysis

---

## Impact Assessment:

### ✅ Works Fine For:
- Spring Boot with standard naming (EmployeeController, EmployeeService)
- Standard Spring annotations (@RestController, @Service, @Entity)
- Repositories following naming convention

### ⚠️ Partially Works For:
- Micronaut (same annotation names, different endpoint annotations)
- Quarkus (some overlap with Jakarta EE)

### ❌ Doesn't Work For:
- Jakarta EE / JAX-RS applications
- Plain Java applications (no framework)
- Custom naming conventions
- Non-standard architectures
- Custom frameworks

---

## Root Causes:

1. **Assumption**: System assumes Spring Boot
2. **Hardcoding**: Annotation sets are hardcoded
3. **No Configuration**: Can't configure for different frameworks
4. **Pattern Matching**: Relies on exact annotation matches
5. **Name-Based Logic**: Assumes `{Domain}{Type}` naming pattern

---

## What Needs to Change:

### 1. **Make Annotation Detection Configurable**
```python
# Instead of hardcoded sets
self.controller_annotations = {'Controller', 'RestController'}

# Use configurable patterns
self.framework_patterns = {
    'spring': {
        'controller': ['Controller', 'RestController'],
        'service': ['Service'],
        'endpoints': ['GetMapping', 'PostMapping', ...]
    },
    'jakarta': {
        'controller': ['Path'],  # Class level
        'service': ['Stateless', 'Singleton'],
        'endpoints': ['GET', 'POST', 'PUT', 'DELETE']
    },
    'micronaut': {
        'controller': ['Controller'],
        'service': ['Singleton'],
        'endpoints': ['Get', 'Post', 'Put', 'Delete']
    }
}
```

### 2. **Auto-Detect Framework**
```python
def detect_framework(self, knowledge_graph):
    """Detect which framework is being used"""
    spring_count = 0
    jakarta_count = 0
    micronaut_count = 0

    # Count framework-specific annotations
    for class_node in classes:
        if 'RestController' in annotations:
            spring_count += 1
        if 'Path' in annotations:
            jakarta_count += 1
        # ...

    return dominant_framework
```

### 3. **Improve Domain Mapping**
```python
# Don't just rely on naming
# Use actual relationships:
# - Which classes does the entity reference?
# - Which classes reference the entity?
# - Package structure analysis
```

### 4. **Add Fallback Detection**
```python
# If no annotations found, use heuristics:
# - Class name ends with "Controller" → probably a controller
# - Has methods with HTTP-like names (get, post, put) → probably endpoint handler
# - Referenced by many classes → probably a service/utility
```

### 5. **Make It Generic**
```python
# Instead of:
if class_type == "Controller"

# Use:
if class_type in ["Controller", "Resource", "Endpoint", "Handler"]
```

---

## Solutions Priority:

### High Priority (Breaks basic functionality):
1. ✅ Add Jakarta EE support
2. ✅ Add Micronaut support
3. ✅ Add JAX-RS support
4. ✅ Improve domain mapping (not just name-based)

### Medium Priority (Improves coverage):
5. ⚠️ Add fallback heuristics for plain Java
6. ⚠️ Auto-detect framework
7. ⚠️ Better relationship analysis

### Low Priority (Nice to have):
8. 📋 Support custom annotations
9. 📋 Configuration file for frameworks
10. 📋 Plugin system for new frameworks

---

## Quick Fix vs Complete Solution:

### Quick Fix (1-2 hours):
- Add more annotations to existing sets
- Include Jakarta EE, Micronaut, Quarkus patterns
- Add fallback for common naming patterns

### Complete Solution (4-6 hours):
- Redesign annotation detection system
- Make it framework-agnostic
- Add auto-detection
- Improve domain mapping logic
- Add heuristics for non-annotated code

---

## Recommendation:

**Implement Complete Solution** because:
1. Quick fix is just more hardcoding
2. Won't scale to new frameworks
3. Still breaks on custom patterns
4. User wants it to work on "any Java framework"

**Next step**: Implement configurable, framework-agnostic annotation detection.
