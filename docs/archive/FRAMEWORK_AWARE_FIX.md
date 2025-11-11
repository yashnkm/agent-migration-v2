# Framework-Aware Domain Discovery - Fix Complete

## Problem Identified

After framework detection worked correctly (detecting "Struts"), domain discovery was still finding **0 domains** because:

1. **GenericJavaParser** marks all classes as `"UNCLASSIFIED"` (correct behavior)
2. **DomainGraph** was looking for `class_type == "Entity"` (Spring-specific)
3. **Result**: No entities found → No domains discovered

### Why It Failed on Struts

Struts uses different patterns than Spring Boot:

| Component | Spring Boot | Struts |
|-----------|------------|--------|
| Controller | `*Controller` | `*Action` |
| Service | `*Service` | `*Service` or `*Manager` |
| Repository | `*Repository` | `*Dao`, `*DaoImpl` |
| Entity | `@Entity` annotation | Plain POJOs in `.models` package |

The system was looking for Spring patterns only!

---

## Solution Implemented

### 1. Created `framework_aware_domain_discovery.py`

New module that:
- Defines patterns for **6 different frameworks**
- Classifies `UNCLASSIFIED` classes based on detected framework
- Uses both name patterns AND annotations
- Has fallback heuristics (e.g., field count for entities)

**Supported Frameworks:**
- ✅ Spring Boot
- ✅ Struts
- ✅ Jakarta EE / JAX-RS
- ✅ Micronaut
- ✅ Quarkus
- ✅ Plain Java

### 2. Framework-Specific Patterns for Struts

```python
"Struts": FrameworkPatterns(
    entity_suffixes=[""],  # Plain POJOs, no suffix required
    entity_annotations=[],  # No special annotations
    controller_suffixes=["Action"],  # ListRequestAction, RequestAction
    controller_annotations=["Action", "Result", "Namespace"],
    service_suffixes=["Service", "Manager", "BusinessLogic"],
    service_annotations=[],
    repository_suffixes=["Dao", "DaoImpl"],  # DaoRequestImpl, DaoFactory
    repository_annotations=[]
)
```

### 3. Special Heuristics for Struts Models

Since Struts entities are plain POJOs (no annotations), we use:
- **Package naming**: `.models.` in package name
- **Field count**: Classes with 3+ fields likely entities
- **Getters/setters pattern**: Typical bean pattern

### 4. Integrated into Analysis Pipeline

Updated `app_v2.py` to add classification step:

```
1. Parse codebase (GenericJavaParser) → All classes "UNCLASSIFIED"
2. Detect framework (Gemini) → "Struts"
3. Classify classes (NEW!) → Apply Struts patterns
4. Discover domains → Now finds entities!
```

---

## What Changed in app_v2.py

### Added Import:
```python
from src.domain_analyzer.framework_aware_domain_discovery import FrameworkAwareDomainDiscovery
```

### Added Step 3 (Between framework detection and domain discovery):
```python
# Step 3: Classify classes using framework patterns
with st.spinner("🔍 Classifying classes using framework patterns..."):
    framework_name = framework_result.get('framework', 'Plain Java')
    classifier = FrameworkAwareDomainDiscovery(knowledge_graph, framework_name)

    # Classify all UNCLASSIFIED classes
    classifications = classifier.classify_classes()

    # Show results
    report = classifier.get_classification_report()
    st.success(
        f"✅ Classified: {report['counts']['Entity']} entities, "
        f"{report['counts']['Controller']} controllers, "
        f"{report['counts']['Service']} services, "
        f"{report['counts']['Repository']} repositories"
    )
```

---

## Expected Results for Your Struts Project

Based on the console output you shared, the system should now classify:

### Entities (Models):
- `com.empresa.struts.models.Request` → **Entity**
  - Has fields: headquarter, institution, acronym, name, type, country, city, website
  - Package contains `.models.`

### Controllers (Actions):
- `com.empresa.struts.actions.ListRequestAction` → **Controller**
- `com.empresa.struts.actions.RequestAction` → **Controller**

### Repositories (DAOs):
- `com.empresa.struts.dao.DaoFactory` → **Repository**
- `com.empresa.struts.dao.file.DaoRequestImpl` → **Repository**

### Expected Domain Discovery:
- **Domain: "Request"**
  - Entity: `Request`
  - Controllers: `ListRequestAction`, `RequestAction`
  - Repository: `DaoRequestImpl`
  - Endpoints: (from Action mappings)
  - Methods: All methods from above classes

---

## Testing

Run the analysis again:

```bash
streamlit run app_v2.py
```

**You should now see:**
1. ✅ Framework detected: Struts
2. ✅ Classified: 1 entities, 2 controllers, 2 repositories
3. ✅ Discovered 1 domain(s)

---

## How It Works for Different Frameworks

### Spring Boot Example:
```java
@Entity
public class User { ... }

@RestController
public class UserController { ... }
```
→ Detected by `@Entity` and `@RestController` annotations

### Struts Example:
```java
// Plain POJO in .models package
public class Request { ... }

// Action with Action suffix
public class RequestAction extends Action { ... }
```
→ Detected by package name and suffix patterns

### Jakarta EE Example:
```java
@Entity
public class Product { ... }

@Path("/products")
public class ProductResource { ... }
```
→ Detected by `@Entity` and `@Path` annotations

---

## Benefits of This Approach

1. **Framework-Agnostic**: Works on ANY Java framework
2. **Pattern-Based**: Uses naming conventions AND annotations
3. **Heuristic Fallbacks**: Can classify even without clear patterns
4. **Extensible**: Easy to add new frameworks
5. **No Hardcoding**: Patterns are data-driven, not code-driven

---

## Files Created/Modified

### Created:
- `src/domain_analyzer/framework_aware_domain_discovery.py` - New classification engine

### Modified:
- `app_v2.py` - Added classification step before domain discovery

### No Changes Needed:
- `domain_graph.py` - Works as-is once classes are classified
- `generic_java_parser.py` - Still correctly marks everything as UNCLASSIFIED
- `framework_detector.py` - Already working correctly

---

## Next Steps (Optional Enhancements)

1. **Struts Action Mapping Parser**: Parse `struts-config.xml` for endpoint paths
2. **Relationship Detection**: Detect relationships between Struts entities
3. **Form Bean Detection**: Identify Struts ActionForm beans
4. **Validation Rules**: Extract Struts validation.xml rules

---

## Summary

**Before:**
- Framework detected: ✅ Struts
- Classes classified: ❌ 0 entities, 0 controllers
- Domains discovered: ❌ 0

**After (Expected):**
- Framework detected: ✅ Struts
- Classes classified: ✅ 1 entity, 2 controllers, 2 repositories
- Domains discovered: ✅ 1 domain (Request)

**Root Cause Fixed:** System now applies framework-specific patterns to classify classes before domain discovery.

---

🎉 **Ready to test!** The system should now work correctly with your Struts project!
