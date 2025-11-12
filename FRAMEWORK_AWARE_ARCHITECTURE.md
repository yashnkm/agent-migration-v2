# Framework-Aware Architecture Analysis

## Problem Solved

**Previous Issue**: Architecture analysis was too generic - used Spring-specific queries for all projects, resulting in:
- Generic reports that didn't match actual framework
- Missing framework-specific patterns
- Wrong terminology (e.g., searching for @Service in Struts project)

## New Solution: Framework Detection → Framework-Specific Analysis

### **3-Step Process:**

```
1. DETECT FRAMEWORK
   ├─ Search for framework indicators
   ├─ Score each framework by matches
   └─ Select framework with highest score

2. FRAMEWORK-SPECIFIC QUERIES
   ├─ Use framework-appropriate search terms
   ├─ Look for framework-specific components
   └─ Gather actual code with file paths

3. SYNTHESIZE REPORT
   ├─ Framework-aware analysis
   ├─ Framework-specific patterns
   └─ Framework terminology and conventions
```

---

## Supported Frameworks

### **1. Spring Boot**
**Detection**: `@SpringBootApplication`, `@EnableAutoConfiguration`, `spring-boot`

**Framework-Specific Queries**:
- Entry Points: `@SpringBootApplication main class`
- REST Controllers: `@RestController @RequestMapping @GetMapping @PostMapping`
- Business Services: `@Service @Transactional business logic`
- Data Repositories: `@Repository JPA CrudRepository JpaRepository`
- Domain Entities: `@Entity @Table JPA entities`
- Configuration: `@Configuration @Bean application properties`
- Security: `@EnableWebSecurity SecurityConfig`
- Dependencies: `@Autowired dependency injection`

**Expected Patterns**: Layered Architecture, Dependency Injection, MVC, REST API

---

### **2. Struts (Struts 1 & 2)**
**Detection**: `struts.xml`, `ActionSupport`, `struts2`, `struts-config`

**Framework-Specific Queries**:
- Action Classes: `extends ActionSupport Action execute method`
- Struts Configuration: `struts.xml action-mapping result-type`
- JSP Views: `jsp struts tags s:form s:textfield`
- Form Beans: `ActionForm struts form validation`
- Interceptors: `interceptor struts-config`
- DAO Layer: `DAO Data Access Object database`
- Business Logic: `service manager business logic`
- Validation: `validate method validation.xml`

**Expected Patterns**: MVC, Front Controller, Action-based

---

### **3. JAX-RS (REST API)**
**Detection**: `@Path`, `@GET`, `@POST`, `javax.ws.rs`, `JAX-RS`

**Framework-Specific Queries**:
- REST Resources: `@Path @GET @POST @PUT @DELETE JAX-RS`
- Resource Methods: `@Produces @Consumes MediaType`
- Request/Response: `Response Entity javax.ws.rs`
- Configuration: `Application ResourceConfig`
- Providers: `@Provider ExceptionMapper MessageBodyReader`
- Business Logic: `service business logic`
- Data Access: `DAO repository database`
- DTOs: `DTO data transfer object`

**Expected Patterns**: REST API, Resource-Oriented

---

### **4. Servlet/JSP**
**Detection**: `extends HttpServlet`, `web.xml`, `servlet-mapping`

**Framework-Specific Queries**:
- Servlets: `extends HttpServlet doGet doPost`
- JSP Pages: `jsp scriptlet expression declaration`
- Filters: `implements Filter doFilter`
- Listeners: `ServletContextListener HttpSessionListener`
- web.xml: `web.xml servlet-mapping url-pattern`
- Business Logic: `business logic service`
- DAO: `DAO database JDBC`
- Beans: `JavaBean getter setter`

**Expected Patterns**: MVC, Front Controller, Servlet-based

---

### **5. Generic Java (Fallback)**
**Detection**: No specific framework detected

**Framework-Specific Queries**:
- Main Classes: `public static void main class entry`
- Packages: `package structure organization`
- Classes: `public class interface abstract`
- Methods: `public private method function`
- Data Access: `database JDBC SQL connection`
- Business Logic: `business logic service manager`
- Utilities: `util helper utility`
- Configuration: `properties config configuration`

**Expected Patterns**: Object-Oriented, Modular

---

## How It Works

### **Step 1: Framework Detection**

```python
framework_checks = {
    "Spring Boot": "@SpringBootApplication @EnableAutoConfiguration spring-boot",
    "Struts": "struts.xml ActionSupport struts2 struts-config",
    "JAX-RS": "@Path @GET @POST javax.ws.rs JAX-RS",
    "Servlet/JSP": "extends HttpServlet web.xml servlet-mapping"
}

for framework, query in framework_checks.items():
    results = vectorstore.similarity_search(query, k=5)
    scores[framework] = len(results)

detected_framework = max(scores, key=scores.get)
```

**Output:**
```
🔍 STEP 1: Detecting Framework...
   Framework scores: {'Spring Boot': 12, 'Struts': 0, 'JAX-RS': 0, 'Servlet/JSP': 2}
   ✓ Detected Framework: Spring Boot
```

---

### **Step 2: Framework-Specific Analysis**

Uses the framework-specific query plan:

```python
if framework == "Spring Boot":
    queries = [
        ("REST Controllers", "@RestController @RequestMapping..."),
        ("Business Services", "@Service @Transactional..."),
        ...
    ]
elif framework == "Struts":
    queries = [
        ("Action Classes", "extends ActionSupport..."),
        ("Struts Configuration", "struts.xml action-mapping..."),
        ...
    ]
```

**Output:**
```
🔍 STEP 2: Performing Spring Boot-specific analysis...
   🔍 Analyzing: REST Controllers...
   🔍 Analyzing: Business Services...
   🔍 Analyzing: Data Repositories...
   ...
   ✓ Completed 8 framework-specific searches
```

---

### **Step 3: Synthesis with Framework Context**

```python
prompt = f"""You are an expert {framework} architect.

DETECTED FRAMEWORK: {framework}
EXPECTED PATTERNS FOR {framework}: {patterns}

SEARCH RESULTS:
{findings}

Create a {framework}-specific architecture analysis...
"""
```

**Result**: Report uses correct framework terminology and patterns.

---

## Example Output Differences

### **Before (Generic)**:
```
Executive Summary: This is a Java application using MVC pattern.

Architecture Patterns:
- MVC
- Layered Architecture

Key Components:
- Controllers (not found)
- Services (not found)
- Repositories (not found)
```

### **After (Spring Boot Detected)**:
```
Executive Summary: This is a Spring Boot REST API application
using Spring MVC with JPA for data persistence.

Architecture Patterns:
- Layered Architecture (Spring Boot standard)
- Dependency Injection (Spring IoC)
- REST API (@RestController pattern)

Key Components:
- UserController (@RestController) - src/main/java/com/app/controller/UserController.java
- UserService (@Service) - src/main/java/com/app/service/UserService.java
- UserRepository (@Repository, JpaRepository) - src/main/java/com/app/repository/UserRepository.java
- User (@Entity) - src/main/java/com/app/model/User.java
```

### **After (Struts Detected)**:
```
Executive Summary: This is a Struts 2 MVC web application
with Action-based architecture and JSP views.

Architecture Patterns:
- MVC (Struts 2)
- Front Controller (StrutsPrepareAndExecuteFilter)
- Action-based architecture

Key Components:
- LoginAction (extends ActionSupport) - src/main/java/com/app/action/LoginAction.java
- struts.xml (action mappings) - src/main/resources/struts.xml
- login.jsp (view) - src/main/webapp/login.jsp
- UserDAO (data access) - src/main/java/com/app/dao/UserDAO.java
```

---

## Benefits

### **1. Accurate Framework Detection**
✅ Automatically identifies the correct framework
✅ Scores based on actual codebase evidence
✅ Fallback to Generic Java if no framework detected

### **2. Framework-Specific Queries**
✅ Uses correct annotations/patterns for each framework
✅ Searches for framework-appropriate components
✅ No wasted queries on non-existent patterns

### **3. Relevant Analysis**
✅ Uses framework terminology
✅ Identifies framework-specific patterns
✅ Provides framework-appropriate recommendations

### **4. Extensible**
✅ Easy to add new frameworks
✅ Each framework has its own query plan
✅ Customizable per framework

---

## Adding New Frameworks

To add support for a new framework:

```python
FRAMEWORK_QUERIES["Play Framework"] = {
    "queries": [
        ("Controllers", "extends Controller Action play.mvc"),
        ("Routes", "routes conf play"),
        ("Views", "scala.html twirl templates"),
        ("Models", "Model Ebean JPA"),
        ...
    ],
    "patterns": ["MVC", "Reactive", "Non-blocking"]
}

# Add detection
framework_checks["Play Framework"] = "extends Controller play.mvc routes conf"
```

---

## Files Changed

### **New File**: `src/rag/agents/framework_aware_architecture_agent.py`
- `FrameworkAwareArchitectureAgent` class
- Framework detection logic
- Framework-specific query plans
- Synthesis with framework context

### **Modified**: `src/rag/report_generator.py`
- Import: `FrameworkAwareArchitectureAgent` (replaced `PlanningArchitectureAgent`)
- Updated: `generate_report()` to use framework-aware agent
- Updated: `_parse_analysis_to_report()` to include framework parameter

---

## Testing

### **Test Different Frameworks:**

1. **Spring Boot Project**:
   - Should detect "Spring Boot"
   - Find @RestController, @Service, @Repository, @Entity
   - Report uses Spring terminology

2. **Struts Project**:
   - Should detect "Struts"
   - Find Action classes, struts.xml, JSPs
   - Report uses Struts terminology

3. **Plain Java Project**:
   - Should detect "Generic Java"
   - Find main classes, packages, utilities
   - Report uses general Java terminology

### **What to Check:**
```
Console Output:
🔍 STEP 1: Detecting Framework...
   Framework scores: {...}
   ✓ Detected Framework: [Framework Name]

🔍 STEP 2: Performing [Framework]-specific analysis...
   🔍 Analyzing: [Framework-Specific Components]...

Report Should Have:
- Framework name in Executive Summary
- Framework-specific patterns
- Actual class names with correct annotations
- Framework-appropriate recommendations
```

---

## Summary

**Problem**: Generic Spring-specific queries for all projects

**Solution**:
1. Detect framework first
2. Use framework-specific queries
3. Generate framework-aware analysis

**Result**: Accurate, specific, framework-appropriate architecture reports!
