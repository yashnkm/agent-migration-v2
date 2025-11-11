# Framework-Agnostic Design - Complete Solution

## Problem Statement

**Current Issue**: System only works for Spring Boot because of hardcoded annotations.

**Goal**: Make it work for ANY Java framework (Spring, Jakarta EE, Struts, Micronaut, Quarkus, Play, plain Java, custom frameworks) WITHOUT hardcoding.

---

## Core Philosophy

### ❌ Wrong Approach (Current):
```
IF annotation == "@RestController" THEN class_type = "Controller"
IF annotation == "@Service" THEN class_type = "Service"
```

### ✅ Right Approach (New):
```
1. Extract ALL annotations (don't care what they are)
2. Analyze class structure, methods, relationships
3. Infer role based on behavior, not specific annotations
4. Use patterns, not exact matches
```

---

## Design Principles

### 1. **Annotation-Agnostic**
- Don't check for specific annotation names
- Store ALL annotations as-is
- Let inference engine decide what they mean

### 2. **Behavior-Based Classification**
- What does the class DO, not what it's CALLED
- Analyze method signatures, return types, parameters
- Look at relationships with other classes

### 3. **Pattern Recognition**
- Identify common patterns across frameworks
- Controllers have HTTP-related methods
- Services have business logic methods
- Entities have data fields

### 4. **Relationship Analysis**
- Who calls whom?
- What references what?
- Package structure patterns

---

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW CODE EXTRACTION                       │
│  Extract EVERYTHING without filtering or classification     │
│  - All classes                                               │
│  - All methods                                               │
│  - All fields                                                │
│  - ALL annotations (no checking)                             │
│  - All relationships                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               GENERIC KNOWLEDGE GRAPH                        │
│  Store data WITHOUT classification                           │
│  - class.annotations = ["RestController", "Path", etc.]     │
│  - class.type = UNKNOWN (initially)                         │
│  - Store all metadata                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            INTELLIGENT INFERENCE ENGINE                      │
│  Analyze and classify based on patterns                     │
│  1. Framework Detection (optional, for hints)               │
│  2. Role Inference (Controller, Service, Entity, etc.)      │
│  3. Endpoint Detection (any HTTP mapping)                   │
│  4. Relationship Analysis                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CLASSIFIED KNOWLEDGE GRAPH                      │
│  Same graph, now with inferred metadata                     │
│  - class.type = "Controller" (inferred)                     │
│  - class.framework_hints = ["Spring"]                       │
│  - class.confidence = 0.95                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Phase 1: Generic Extraction (No Hardcoding)

#### New `GenericJavaParser`:
```python
class GenericJavaParser:
    """
    Framework-agnostic Java parser
    Extracts EVERYTHING without classification
    """

    def __init__(self):
        self.language = Language(tsjava.language(), 'java')
        self.parser = Parser()
        # NO hardcoded annotation sets!

    def extract_class(self, node, source_code):
        """Extract class with ALL metadata"""
        return {
            'name': self.get_name(node),
            'package': self.get_package(node),
            'annotations': self.get_all_annotations(node),  # ALL of them
            'modifiers': self.get_modifiers(node),
            'methods': self.extract_all_methods(node),
            'fields': self.extract_all_fields(node),
            'interfaces': self.get_interfaces(node),
            'superclass': self.get_superclass(node),
            # NO class_type classification here
        }

    def get_all_annotations(self, node):
        """Get ALL annotations, don't filter"""
        annotations = []
        # Extract everything that starts with @
        # Return as-is, don't interpret
        return annotations
```

---

### Phase 2: Intelligent Inference Engine

#### `RoleInferenceEngine`:
```python
class RoleInferenceEngine:
    """
    Infers class roles based on behavior and patterns
    Works for ANY framework
    """

    def infer_class_role(self, class_node, knowledge_graph):
        """
        Infer if class is Controller, Service, Entity, etc.
        WITHOUT checking specific annotation names
        """

        scores = {
            'Controller': 0.0,
            'Service': 0.0,
            'Repository': 0.0,
            'Entity': 0.0,
            'Utility': 0.0,
            'Unknown': 0.0
        }

        # HEURISTIC 1: Check annotations (generic patterns)
        for annotation in class_node.annotations:
            annotation_lower = annotation.lower()

            # Controller patterns (any framework)
            if any(keyword in annotation_lower for keyword in
                   ['controller', 'resource', 'endpoint', 'rest', 'path', 'route']):
                scores['Controller'] += 0.4

            # Service patterns
            if any(keyword in annotation_lower for keyword in
                   ['service', 'bean', 'component', 'stateless', 'singleton']):
                scores['Service'] += 0.4

            # Repository patterns
            if any(keyword in annotation_lower for keyword in
                   ['repository', 'dao', 'mapper']):
                scores['Repository'] += 0.4

            # Entity patterns
            if any(keyword in annotation_lower for keyword in
                   ['entity', 'table', 'model', 'document']):
                scores['Entity'] += 0.4

        # HEURISTIC 2: Check class name
        class_name_lower = class_node.name.lower()

        if class_name_lower.endswith('controller'):
            scores['Controller'] += 0.3
        elif class_name_lower.endswith('resource'):
            scores['Controller'] += 0.25
        elif class_name_lower.endswith('endpoint'):
            scores['Controller'] += 0.25

        if class_name_lower.endswith('service'):
            scores['Service'] += 0.3
        elif class_name_lower.endswith('manager'):
            scores['Service'] += 0.2

        if class_name_lower.endswith('repository'):
            scores['Repository'] += 0.3
        elif class_name_lower.endswith('dao'):
            scores['Repository'] += 0.3

        if class_name_lower.endswith('entity'):
            scores['Entity'] += 0.3
        elif class_name_lower.endswith('model'):
            scores['Entity'] += 0.2

        # HEURISTIC 3: Analyze methods
        method_analysis = self.analyze_methods(class_node.methods)

        if method_analysis['has_http_mappings']:
            scores['Controller'] += 0.5

        if method_analysis['has_crud_operations']:
            scores['Repository'] += 0.3

        if method_analysis['has_business_logic']:
            scores['Service'] += 0.3

        if method_analysis['mostly_getters_setters']:
            scores['Entity'] += 0.5

        # HEURISTIC 4: Analyze fields
        if self.has_data_fields(class_node.fields):
            scores['Entity'] += 0.3

        # HEURISTIC 5: Relationship analysis
        relationship_hints = self.analyze_relationships(class_node, knowledge_graph)
        for role, score in relationship_hints.items():
            scores[role] += score

        # Determine best match
        best_role = max(scores, key=scores.get)
        confidence = scores[best_role]

        if confidence < 0.3:
            best_role = 'Unknown'

        return {
            'role': best_role,
            'confidence': confidence,
            'scores': scores
        }

    def analyze_methods(self, methods):
        """Analyze method patterns"""
        http_mapping_count = 0
        crud_count = 0
        business_logic_count = 0
        getter_setter_count = 0

        for method in methods:
            # Check for HTTP-related annotations (ANY framework)
            for annotation in method.annotations:
                ann_lower = annotation.lower()
                if any(http in ann_lower for http in
                       ['get', 'post', 'put', 'delete', 'patch',
                        'mapping', 'path', 'route', 'request']):
                    http_mapping_count += 1

            # Check method names
            method_lower = method.name.lower()

            if method_lower.startswith(('get', 'set')):
                getter_setter_count += 1

            if method_lower in ['save', 'find', 'delete', 'update',
                               'create', 'read', 'findall', 'findbyid']:
                crud_count += 1

            # Has parameters and logic = business logic
            if len(method.parameters) > 0 and method.body and len(method.body) > 50:
                business_logic_count += 1

        total = len(methods)
        if total == 0:
            return {
                'has_http_mappings': False,
                'has_crud_operations': False,
                'has_business_logic': False,
                'mostly_getters_setters': False
            }

        return {
            'has_http_mappings': http_mapping_count > 0,
            'has_crud_operations': crud_count / total > 0.3,
            'has_business_logic': business_logic_count / total > 0.3,
            'mostly_getters_setters': getter_setter_count / total > 0.6
        }

    def has_data_fields(self, fields):
        """Check if class has data fields (entity pattern)"""
        if len(fields) < 2:
            return False

        # Has multiple fields with standard types
        standard_types = ['String', 'Integer', 'Long', 'Double', 'Boolean',
                         'Date', 'LocalDate', 'BigDecimal']

        data_field_count = 0
        for field in fields:
            if any(stype in field.field_type for stype in standard_types):
                data_field_count += 1

        return data_field_count / len(fields) > 0.5

    def analyze_relationships(self, class_node, knowledge_graph):
        """Analyze how class relates to others"""
        scores = {
            'Controller': 0.0,
            'Service': 0.0,
            'Repository': 0.0,
            'Entity': 0.0
        }

        # Controllers typically call services
        # Services typically call repositories
        # Repositories typically work with entities
        # Entities are referenced by everyone

        # Count who calls this class
        callers = self.get_callers(class_node, knowledge_graph)

        # Count who this class calls
        callees = self.get_callees(class_node, knowledge_graph)

        # Controllers: called by framework, call services
        if len(callers) == 0 and len(callees) > 0:
            scores['Controller'] += 0.2

        # Services: called by controllers, call repositories
        if len(callers) > 0 and len(callees) > 0:
            scores['Service'] += 0.2

        # Repositories: called by services, minimal callees
        if len(callers) > 0 and len(callees) == 0:
            scores['Repository'] += 0.2

        # Entities: referenced by many, call nobody
        references = self.count_references(class_node, knowledge_graph)
        if references > 3:
            scores['Entity'] += 0.3

        return scores
```

---

### Phase 3: Generic Endpoint Detection

#### `EndpointInferenceEngine`:
```python
class EndpointInferenceEngine:
    """
    Detects HTTP endpoints in ANY framework
    """

    def detect_endpoints(self, class_node):
        """
        Detect if class has HTTP endpoints
        Works for Spring, JAX-RS, Struts, Play, etc.
        """

        endpoints = []

        # Get class-level path (if any)
        class_base_path = self.extract_base_path(class_node.annotations)

        for method in class_node.methods:
            endpoint = self.detect_method_endpoint(
                method,
                class_base_path,
                class_node.name
            )

            if endpoint:
                endpoints.append(endpoint)

        return endpoints

    def detect_method_endpoint(self, method, base_path, class_name):
        """
        Detect if method is an HTTP endpoint
        """

        http_method = None
        path = None

        # Check annotations for HTTP indicators
        for annotation in method.annotations:
            ann_lower = annotation.lower()

            # Detect HTTP method (generic)
            if 'get' in ann_lower:
                http_method = 'GET'
            elif 'post' in ann_lower:
                http_method = 'POST'
            elif 'put' in ann_lower:
                http_method = 'PUT'
            elif 'delete' in ann_lower:
                http_method = 'DELETE'
            elif 'patch' in ann_lower:
                http_method = 'PATCH'

            # Extract path (generic)
            # Try to find path in annotation
            path = self.extract_path_from_annotation(annotation)

        # If no explicit HTTP method, try to infer from method name
        if not http_method:
            method_lower = method.name.lower()
            if method_lower.startswith('get'):
                http_method = 'GET'
            elif method_lower.startswith('create') or method_lower.startswith('add'):
                http_method = 'POST'
            elif method_lower.startswith('update'):
                http_method = 'PUT'
            elif method_lower.startswith('delete') or method_lower.startswith('remove'):
                http_method = 'DELETE'

        # If we have an HTTP method, it's likely an endpoint
        if http_method:
            if not path:
                # Generate path from method name
                path = f"/{method.name.lower()}"

            full_path = f"{base_path}{path}" if base_path else path

            return {
                'http_method': http_method,
                'path': full_path,
                'handler_method': method.name,
                'handler_class': class_name,
                'confidence': 0.8 if path else 0.5
            }

        return None

    def extract_path_from_annotation(self, annotation):
        """
        Extract path from annotation value
        Works for @Path("/users"), @GetMapping("/users"), etc.
        """
        # Use regex to find path in annotation
        import re
        match = re.search(r'["\']([/\w\-{}]+)["\']', annotation)
        if match:
            return match.group(1)
        return None

    def extract_base_path(self, annotations):
        """Extract base path from class-level annotations"""
        for annotation in annotations:
            if 'path' in annotation.lower() or 'mapping' in annotation.lower():
                path = self.extract_path_from_annotation(annotation)
                if path:
                    return path
        return ""
```

---

### Phase 4: Smart Domain Discovery

#### `DomainDiscoveryEngine`:
```python
class DomainDiscoveryEngine:
    """
    Discovers domains without relying on naming conventions
    """

    def discover_domains(self, knowledge_graph):
        """
        Find domains based on relationships, not names
        """

        # Step 1: Find potential entity classes
        potential_entities = []

        for class_node in knowledge_graph.classes:
            if self.is_likely_entity(class_node):
                potential_entities.append(class_node)

        # Step 2: For each entity, find related classes
        domains = []

        for entity in potential_entities:
            domain = self.build_domain_from_entity(entity, knowledge_graph)
            domains.append(domain)

        return domains

    def is_likely_entity(self, class_node):
        """
        Determine if class is likely an entity
        WITHOUT checking specific annotations
        """

        score = 0.0

        # Check inferred role
        if class_node.inferred_role == 'Entity':
            score += 0.5

        # Has data fields
        if len(class_node.fields) >= 2:
            score += 0.3

        # Referenced by many other classes
        if class_node.reference_count > 3:
            score += 0.2

        # Has annotations (any)
        if len(class_node.annotations) > 0:
            for ann in class_node.annotations:
                if any(keyword in ann.lower() for keyword in
                       ['entity', 'table', 'model', 'document', 'data']):
                    score += 0.3

        return score > 0.5

    def build_domain_from_entity(self, entity, knowledge_graph):
        """
        Build domain by finding all classes related to this entity
        """

        domain = {
            'entity': entity,
            'controllers': [],
            'services': [],
            'repositories': [],
            'related_classes': []
        }

        # Find all classes that reference this entity
        for class_node in knowledge_graph.classes:
            relationship = self.analyze_relationship(class_node, entity, knowledge_graph)

            if relationship['is_related']:
                role = class_node.inferred_role

                if role == 'Controller':
                    domain['controllers'].append(class_node)
                elif role == 'Service':
                    domain['services'].append(class_node)
                elif role == 'Repository':
                    domain['repositories'].append(class_node)
                else:
                    domain['related_classes'].append(class_node)

        return domain

    def analyze_relationship(self, class_node, entity, knowledge_graph):
        """
        Check if class is related to entity
        """

        # Check if entity is used in methods
        uses_entity = False

        for method in class_node.methods:
            # Check parameters
            for param in method.parameters:
                if entity.name in param['type']:
                    uses_entity = True

            # Check return type
            if entity.name in method.return_type:
                uses_entity = True

        # Check fields
        for field in class_node.fields:
            if entity.name in field.field_type:
                uses_entity = True

        return {
            'is_related': uses_entity,
            'confidence': 0.9 if uses_entity else 0.0
        }
```

---

## Summary of Changes

### What Gets Removed:
```python
# DELETE these hardcoded sets
self.controller_annotations = {'Controller', 'RestController'}
self.service_annotations = {'Service'}
self.repository_annotations = {'Repository'}
self.entity_annotations = {'Entity', 'Table'}
```

### What Gets Added:
```python
# NEW: Generic extraction
GenericJavaParser - extracts everything, classifies nothing

# NEW: Intelligent inference
RoleInferenceEngine - infers roles from behavior
EndpointInferenceEngine - detects endpoints generically
DomainDiscoveryEngine - finds domains by relationships

# NEW: Confidence scoring
Every classification has confidence score
```

---

## Benefits

1. ✅ Works for **ANY** Java framework (Spring, Jakarta EE, Struts, Play, Micronaut, Quarkus)
2. ✅ Works for **plain Java** (no framework)
3. ✅ Works for **custom frameworks**
4. ✅ Works with **any naming convention**
5. ✅ **No hardcoding** - completely pattern-based
6. ✅ **Future-proof** - works with new frameworks automatically
7. ✅ **Confidence scores** - know how sure the system is

---

## Implementation Plan

### Phase 1: Core Changes (2-3 hours)
- Rewrite `java_parser.py` to be generic
- Add `RoleInferenceEngine`
- Update `knowledge_graph.py` to store inference metadata

### Phase 2: Endpoint Detection (1 hour)
- Add `EndpointInferenceEngine`
- Generic HTTP mapping detection

### Phase 3: Domain Discovery (1-2 hours)
- Rewrite `domain_graph.py` to use relationship analysis
- Remove name-based matching

### Phase 4: Testing (1 hour)
- Test with Spring Boot
- Test with Jakarta EE
- Test with plain Java
- Test with custom naming

**Total: 5-7 hours**

---

## Next Step

Should I implement this complete solution?

This will make your system truly universal - works on ANY Java codebase, any framework, any naming convention.
