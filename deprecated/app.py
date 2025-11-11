"""
Streamlit Web UI for Java Codebase Analysis
"""
import streamlit as st
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.github_cloner import GitHubCloner
from src.knowledge_graph.graph import KnowledgeGraph
from src.parser.java_parser import JavaParser
from src.parser.relationship_extractor import RelationshipExtractor
from src.domain_analyzer.domain_graph import DomainGraph
from src.domain_analyzer.business_analyzer import DomainBusinessAnalyzer


# Page config
st.set_page_config(
    page_title="Java Codebase Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'domain_graph' not in st.session_state:
    st.session_state.domain_graph = None
if 'knowledge_graph' not in st.session_state:
    st.session_state.knowledge_graph = None
if 'repo_info' not in st.session_state:
    st.session_state.repo_info = None
if 'analyzed_domains' not in st.session_state:
    st.session_state.analyzed_domains = {}


def analyze_repository(github_url: str):
    """
    Main analysis workflow
    """
    # Step 1: Clone repository
    with st.spinner("Cloning repository from GitHub..."):
        cloner = GitHubCloner()
        clone_result = cloner.clone_repository(github_url)

        if not clone_result["success"]:
            st.error(f"Failed to clone repository: {clone_result['error']}")
            return False

        st.session_state.repo_info = clone_result
        local_path = clone_result["local_path"]
        st.success(f"✓ Cloned {clone_result['owner']}/{clone_result['repo']}")

    # Step 2: Parse codebase
    with st.spinner("Parsing Java files..."):
        knowledge_graph = KnowledgeGraph()
        java_parser = JavaParser()

        try:
            java_parser.parse_directory(local_path, knowledge_graph)
            relationship_extractor = RelationshipExtractor(java_parser)
            relationship_extractor.extract_all_relationships(knowledge_graph)

            stats = knowledge_graph.get_stats()
            st.session_state.knowledge_graph = knowledge_graph

            st.success(f"✓ Parsed {stats['classes']} classes, {stats['methods']} methods, {stats['endpoints']} endpoints")

        except Exception as e:
            st.error(f"Error parsing codebase: {str(e)}")
            return False

    # Step 3: Discover domains
    with st.spinner("Discovering business domains..."):
        try:
            domain_graph = DomainGraph(knowledge_graph)
            domain_graph.discover_domains()

            st.session_state.domain_graph = domain_graph
            st.session_state.analysis_complete = True

            st.success(f"✓ Discovered {len(domain_graph.domains)} business domain(s)")
            return True

        except Exception as e:
            st.error(f"Error discovering domains: {str(e)}")
            return False


def analyze_domain_business_logic(domain_name: str):
    """
    Analyze business logic for a specific domain
    """
    domain_graph = st.session_state.domain_graph
    knowledge_graph = st.session_state.knowledge_graph

    if domain_name in st.session_state.analyzed_domains:
        return st.session_state.analyzed_domains[domain_name]

    domain_info = domain_graph.domains[domain_name]

    with st.spinner(f"Analyzing business logic for {domain_name} domain..."):
        try:
            analyzer = DomainBusinessAnalyzer()
            business_analysis = analyzer.analyze_domain(
                domain_info.to_dict(),
                knowledge_graph
            )

            st.session_state.analyzed_domains[domain_name] = business_analysis
            return business_analysis

        except Exception as e:
            st.error(f"Error analyzing business logic: {str(e)}")
            return None


def display_domain_card(domain_name: str, domain_info):
    """
    Display a domain card in the UI
    """
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        st.subheader(f"🏢 {domain_name} Domain")

    with col2:
        complexity = domain_info.complexity_score
        if complexity > 50:
            st.metric("Complexity", complexity, delta="High", delta_color="inverse")
        elif complexity > 20:
            st.metric("Complexity", complexity, delta="Medium", delta_color="off")
        else:
            st.metric("Complexity", complexity, delta="Low", delta_color="normal")

    with col3:
        st.metric("Endpoints", domain_info.endpoint_count)

    with col4:
        st.metric("Methods", domain_info.method_count)

    # Architecture
    with st.expander("🏗️ Architecture", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Entity:**")
            st.code(domain_info.entity_class, language="text")

            st.write("**Controller:**")
            if domain_info.controller:
                st.code(domain_info.controller, language="text")
            else:
                st.warning("Not Found")

        with col2:
            st.write("**Service:**")
            if domain_info.service:
                st.code(domain_info.service, language="text")
            else:
                st.warning("Not Found")

            st.write("**Repository:**")
            if domain_info.repository:
                st.code(domain_info.repository, language="text")
            else:
                st.warning("Not Found")

    # Fields
    with st.expander(f"📊 Entity Fields ({len(domain_info.fields)})"):
        if domain_info.fields:
            for field in domain_info.fields:
                annotations = f" [{', '.join(field['annotations'])}]" if field['annotations'] else ""
                st.write(f"• `{field['name']}`: **{field['type']}**{annotations}")
        else:
            st.info("No fields found")

    # Endpoints
    with st.expander(f"🌐 REST Endpoints ({len(domain_info.endpoints)})"):
        if domain_info.endpoints:
            for endpoint in domain_info.endpoints:
                method_color = {
                    "GET": "🟢",
                    "POST": "🔵",
                    "PUT": "🟡",
                    "DELETE": "🔴",
                    "PATCH": "🟣"
                }.get(endpoint["http_method"], "⚪")

                st.write(f"{method_color} **{endpoint['http_method']}** `{endpoint['path']}`")
                st.caption(f"   → {endpoint['handler_method']}()")
        else:
            st.info("No endpoints found")

    # Business Logic Analysis Button
    st.write("---")
    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button(f"🧠 Analyze Business Logic", key=f"analyze_{domain_name}", use_container_width=True):
            business_analysis = analyze_domain_business_logic(domain_name)
            if business_analysis and "error" not in business_analysis:
                st.session_state[f"show_business_{domain_name}"] = True
                st.rerun()

    with col2:
        if domain_name in st.session_state.analyzed_domains:
            st.success("✓ Business logic analyzed")

    # Show business logic if analyzed
    if st.session_state.get(f"show_business_{domain_name}", False):
        if domain_name in st.session_state.analyzed_domains:
            business_analysis = st.session_state.analyzed_domains[domain_name]

            with st.expander("🧠 Business Logic Analysis", expanded=True):
                # Business Rules
                if business_analysis.get("business_rules"):
                    st.write("**📋 Business Rules:**")
                    for rule in business_analysis["business_rules"]:
                        st.write(f"• {rule}")
                    st.write("")

                # Endpoints Analysis
                if business_analysis.get("endpoints"):
                    st.write("**🌐 Endpoint Details:**")
                    for endpoint in business_analysis["endpoints"]:
                        with st.container():
                            st.write(f"**{endpoint['http_method']} {endpoint['path']}**")
                            if endpoint.get("purpose"):
                                st.write(f"*Purpose:* {endpoint['purpose']}")
                            if endpoint.get("business_logic"):
                                st.write(f"*Logic:* {endpoint['business_logic']}")
                            if endpoint.get("business_rules"):
                                st.write("*Rules:*")
                                for rule in endpoint["business_rules"]:
                                    st.write(f"  • {rule}")
                            st.write("")

                # Business Methods
                if business_analysis.get("business_methods"):
                    st.write("**⚙️ Business Methods:**")
                    for method in business_analysis["business_methods"]:
                        with st.container():
                            st.write(f"**{method['method']}**")
                            if method.get("purpose"):
                                st.write(f"*Purpose:* {method['purpose']}")
                            if method.get("operations"):
                                st.write("*Operations:*")
                                for op in method["operations"]:
                                    st.write(f"  • {op}")
                            st.write("")


# Main UI
st.title("🔍 Java Codebase Analyzer")
st.markdown("Analyze Java Spring Boot codebases from GitHub repositories")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    This tool analyzes Java Spring Boot codebases to:
    - 🏢 Discover business domains
    - 🏗️ Map architecture layers
    - 🌐 Extract REST endpoints
    - 🧠 Analyze business logic (on-demand)
    - 📄 Generate reports
    """)

    st.write("---")

    if st.session_state.analysis_complete:
        st.success("✓ Analysis Complete")

        if st.button("🔄 Analyze New Repository", use_container_width=True):
            # Reset state
            st.session_state.analysis_complete = False
            st.session_state.domain_graph = None
            st.session_state.knowledge_graph = None
            st.session_state.repo_info = None
            st.session_state.analyzed_domains = {}
            st.rerun()

# Main content
if not st.session_state.analysis_complete:
    # Input form
    st.write("### 🔗 Enter GitHub Repository URL")

    github_url = st.text_input(
        "GitHub URL",
        placeholder="https://github.com/owner/repository",
        help="Public GitHub repository URL (e.g., https://github.com/spring-projects/spring-petclinic)"
    )

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        analyze_button = st.button("🚀 Analyze Repository", type="primary", use_container_width=True)

    if analyze_button:
        if not github_url:
            st.error("Please enter a GitHub URL")
        else:
            analyze_repository(github_url)

    # Examples
    st.write("---")
    st.write("### 📚 Example Repositories")

    examples = {
        "Spring PetClinic": "https://github.com/spring-projects/spring-petclinic",
        "Spring Boot Sample": "https://github.com/spring-guides/gs-rest-service"
    }

    for name, url in examples.items():
        if st.button(f"Try: {name}", key=f"example_{name}"):
            st.session_state.example_url = url
            st.rerun()

    if 'example_url' in st.session_state:
        analyze_repository(st.session_state.example_url)
        del st.session_state.example_url

else:
    # Display analysis results
    domain_graph = st.session_state.domain_graph
    repo_info = st.session_state.repo_info

    # Header
    st.success(f"✓ Analysis complete for **{repo_info['owner']}/{repo_info['repo']}**")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Business Domains", len(domain_graph.domains))

    with col2:
        total_endpoints = sum(d.endpoint_count for d in domain_graph.domains.values())
        st.metric("Total Endpoints", total_endpoints)

    with col3:
        total_methods = sum(d.method_count for d in domain_graph.domains.values())
        st.metric("Total Methods", total_methods)

    with col4:
        analyzed_count = len(st.session_state.analyzed_domains)
        st.metric("Analyzed Domains", f"{analyzed_count}/{len(domain_graph.domains)}")

    st.write("---")

    # Display each domain
    if domain_graph.domains:
        st.write("### 🏢 Discovered Domains")

        # Sort by complexity
        sorted_domains = sorted(
            domain_graph.domains.items(),
            key=lambda x: x[1].complexity_score,
            reverse=True
        )

        for domain_name, domain_info in sorted_domains:
            with st.container():
                display_domain_card(domain_name, domain_info)
                st.write("")

        # Export options
        st.write("---")
        st.write("### 📥 Export Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            # JSON export
            catalog_data = domain_graph.export_domain_catalog()
            json_str = json.dumps(catalog_data, indent=2, default=str)

            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name=f"{repo_info['repo']}_analysis.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            # PDF export (placeholder)
            st.button(
                label="📕 Download PDF",
                disabled=True,
                help="PDF export coming soon",
                use_container_width=True
            )

        with col3:
            # Markdown export (placeholder)
            st.button(
                label="📝 Download Markdown",
                disabled=True,
                help="Markdown export coming soon",
                use_container_width=True
            )

    else:
        st.warning("No business domains found in this repository")
