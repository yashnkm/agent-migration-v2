"""
Framework-Aware Architecture Agent
Detects framework first, then uses framework-specific analysis strategies
"""
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS


# Framework-specific analysis plans
FRAMEWORK_QUERIES = {
    "Spring Boot": {
        "queries": [
            ("Entry Points", "@SpringBootApplication main class entry point"),
            ("REST Controllers", "@RestController @RequestMapping @GetMapping @PostMapping"),
            ("Business Services", "@Service @Transactional business logic"),
            ("Data Repositories", "@Repository JPA CrudRepository JpaRepository"),
            ("Domain Entities", "@Entity @Table JPA entities"),
            ("Configuration", "@Configuration @Bean application properties"),
            ("Security", "@EnableWebSecurity SecurityConfig authentication authorization"),
            ("Dependencies", "@Autowired dependency injection")
        ],
        "patterns": ["Layered Architecture", "Dependency Injection", "MVC", "REST API"]
    },
    "Struts": {
        "queries": [
            ("Action Classes", "extends ActionSupport Action execute method struts"),
            ("Struts Configuration", "struts.xml action-mapping result-type"),
            ("JSP Views", "jsp struts tags s:form s:textfield"),
            ("Form Beans", "ActionForm struts form validation"),
            ("Interceptors", "interceptor struts-config"),
            ("DAO Layer", "DAO Data Access Object database"),
            ("Business Logic", "service manager business logic"),
            ("Validation", "validate method validation.xml")
        ],
        "patterns": ["MVC", "Front Controller", "Action-based"]
    },
    "JAX-RS": {
        "queries": [
            ("REST Resources", "@Path @GET @POST @PUT @DELETE JAX-RS"),
            ("Resource Methods", "@Produces @Consumes MediaType"),
            ("Request/Response", "Response Entity javax.ws.rs"),
            ("Configuration", "Application ResourceConfig"),
            ("Providers", "@Provider ExceptionMapper MessageBodyReader"),
            ("Business Logic", "service business logic"),
            ("Data Access", "DAO repository database"),
            ("DTOs", "DTO data transfer object")
        ],
        "patterns": ["REST API", "Resource-Oriented"]
    },
    "Servlet/JSP": {
        "queries": [
            ("Servlets", "extends HttpServlet doGet doPost"),
            ("JSP Pages", "jsp scriptlet expression declaration"),
            ("Filters", "implements Filter doFilter"),
            ("Listeners", "ServletContextListener HttpSessionListener"),
            ("web.xml", "web.xml servlet-mapping url-pattern"),
            ("Business Logic", "business logic service"),
            ("DAO", "DAO database JDBC"),
            ("Beans", "JavaBean getter setter")
        ],
        "patterns": ["MVC", "Front Controller", "Servlet-based"]
    },
    "Generic Java": {
        "queries": [
            ("Main Classes", "public static void main class entry"),
            ("Packages", "package structure organization"),
            ("Classes", "public class interface abstract"),
            ("Methods", "public private method function"),
            ("Data Access", "database JDBC SQL connection"),
            ("Business Logic", "business logic service manager"),
            ("Utilities", "util helper utility"),
            ("Configuration", "properties config configuration")
        ],
        "patterns": ["Object-Oriented", "Modular"]
    }
}


class FrameworkAwareArchitectureAgent:
    """
    Agent that detects framework and uses framework-specific analysis
    """

    def __init__(self, vectorstore: FAISS):
        """
        Initialize agent

        Args:
            vectorstore: FAISS vectorstore with codebase
        """
        load_dotenv()

        # Get API key
        self.api_key = (
            os.getenv('CODEBASE_GEMINI_KEY') or
            os.getenv('GOOGLE_GENAI_API_KEY') or
            os.getenv('GOOGLE_API_KEY')
        )

        if not self.api_key:
            raise ValueError("CODEBASE_GEMINI_KEY must be set in .env")

        # Get model name
        model_name = os.getenv('CODEBASE_GEMINI_MODEL', 'gemini-2.0-flash-exp')

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0.3
        )

        self.vectorstore = vectorstore

    def analyze_architecture(self, project_name: str = "Java Project") -> Dict[str, Any]:
        """
        Analyze architecture with framework detection

        Args:
            project_name: Name of the project

        Returns:
            Comprehensive architecture analysis
        """
        print(f"Starting framework-aware architecture analysis for {project_name}...")
        print("=" * 80)

        # Step 1: Detect Framework
        print("\n🔍 STEP 1: Detecting Framework...")
        framework = self._detect_framework()
        print(f"   ✓ Detected Framework: {framework}")

        # Step 2: Framework-specific analysis
        print(f"\n🔍 STEP 2: Performing {framework}-specific analysis...")
        findings = self._analyze_with_framework(framework)

        # Step 3: Synthesize report
        print("\n🔄 STEP 3: Synthesizing comprehensive architecture report...")
        analysis = self._synthesize_report(project_name, framework, findings)

        print("\n" + "=" * 80)
        print("✓ Framework-aware analysis complete!")

        return {
            "project_name": project_name,
            "framework": framework,
            "analysis": analysis,
            "findings": findings
        }

    def _detect_framework(self) -> str:
        """
        Detect which framework the project uses

        Returns:
            Framework name
        """
        # Search for framework indicators
        framework_checks = {
            "Spring Boot": "@SpringBootApplication @EnableAutoConfiguration spring-boot",
            "Struts": "struts.xml ActionSupport struts2 struts-config",
            "JAX-RS": "@Path @GET @POST javax.ws.rs JAX-RS",
            "Servlet/JSP": "extends HttpServlet web.xml servlet-mapping"
        }

        scores = {}

        for framework, query in framework_checks.items():
            results = self.vectorstore.similarity_search(query, k=5)
            scores[framework] = len(results)

        # Find framework with most matches
        if max(scores.values()) > 0:
            detected = max(scores, key=scores.get)
            print(f"   Framework scores: {scores}")
            return detected
        else:
            return "Generic Java"

    def _analyze_with_framework(self, framework: str) -> str:
        """
        Perform framework-specific analysis

        Args:
            framework: Detected framework

        Returns:
            Combined findings
        """
        framework_plan = FRAMEWORK_QUERIES.get(framework, FRAMEWORK_QUERIES["Generic Java"])

        all_findings = []
        all_findings.append(f"**Framework**: {framework}\n")
        all_findings.append(f"**Expected Patterns**: {', '.join(framework_plan['patterns'])}\n\n")

        for section_name, query in framework_plan['queries']:
            print(f"   🔍 Analyzing: {section_name}...")

            # Query vectorstore
            results = self.vectorstore.similarity_search(query, k=8)

            section_findings = f"\n### {section_name}\n"
            section_findings += f"Query: `{query}`\n\n"

            if results:
                for i, doc in enumerate(results[:5], 1):  # Limit to top 5
                    content = doc.page_content[:400]
                    metadata = doc.metadata
                    section_findings += f"**Result {i}**: `{metadata.get('file_path', 'Unknown')}`\n"
                    section_findings += f"Type: {metadata.get('node_type', 'Unknown')}\n"
                    section_findings += f"```\n{content}...\n```\n\n"
            else:
                section_findings += "_No results found_\n\n"

            all_findings.append(section_findings)

        print(f"   ✓ Completed {len(framework_plan['queries'])} framework-specific searches")

        return "\n".join(all_findings)

    def _synthesize_report(self, project_name: str, framework: str, findings: str) -> str:
        """
        Synthesize findings into comprehensive report

        Args:
            project_name: Project name
            framework: Detected framework
            findings: All findings

        Returns:
            Comprehensive analysis
        """
        framework_plan = FRAMEWORK_QUERIES.get(framework, FRAMEWORK_QUERIES["Generic Java"])

        prompt = f"""You are an expert {framework} architect. Analyze this {project_name} codebase.

DETECTED FRAMEWORK: {framework}

EXPECTED PATTERNS FOR {framework}:
{', '.join(framework_plan['patterns'])}

SEARCH RESULTS:
{findings}

Create a comprehensive architecture analysis with:

1. **Executive Summary**: 2-3 sentences about this {framework} application
2. **Architecture Patterns**: Which {framework} patterns are used (cite evidence from results)
3. **Framework-Specific Layers**:
   - For Spring Boot: Presentation (@RestController), Business (@Service), Data (@Repository), Domain (@Entity)
   - For Struts: Actions, Forms, JSPs, Business Logic, DAO
   - For JAX-RS: Resources, Providers, Business Logic, Data Access
   - For Servlet/JSP: Servlets, Filters, JSPs, Business Logic, DAO
4. **Key Components**: List actual classes/files found with their responsibilities
5. **Data Flow**: Describe request → response flow for this framework
6. **Technology Stack**: {framework} version, dependencies, databases, etc.
7. **Strengths**: What's well-implemented
8. **Recommendations**: {framework}-specific improvements

CRITICAL REQUIREMENTS:
- Use ACTUAL class names, file paths, and code from the search results
- Reference specific {framework} annotations, patterns, and conventions
- Do NOT make generic statements - cite evidence
- If something wasn't found, say "Not found in analysis" instead of making assumptions"""

        response = self.llm.invoke(prompt)
        return response.content
