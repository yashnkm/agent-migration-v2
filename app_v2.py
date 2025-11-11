"""
Streamlit Web UI for Java Codebase Analysis - V2
Rich, detailed dashboard with comprehensive information display
"""
import streamlit as st
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.github_cloner import GitHubCloner
from src.knowledge_graph.graph import KnowledgeGraph
from src.parser.generic_java_parser import GenericJavaParser
from src.parser.relationship_extractor import RelationshipExtractor
from src.domain_analyzer.universal_domain_discovery import UniversalDomainDiscovery
from src.domain_analyzer.business_analyzer import DomainBusinessAnalyzer
from src.inference.framework_detector import FrameworkDetector
from src.inference.class_classifier import LLMClassClassifier


# Page config
st.set_page_config(
    page_title="Java Codebase Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .domain-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .domain-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .method-signature {
        font-family: 'Courier New', monospace;
        background-color: #f5f5f5;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
    }
    .field-item {
        padding: 0.5rem;
        border-left: 3px solid #1f77b4;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .endpoint-card {
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .metric-box {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'input'  # 'input', 'dashboard', 'domain_detail'
if 'selected_domain' not in st.session_state:
    st.session_state.selected_domain = None
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
if 'framework_detection' not in st.session_state:
    st.session_state.framework_detection = None


def analyze_repository(github_url: str):
    """Main analysis workflow"""
    # Step 1: Clone repository
    with st.spinner("🔄 Cloning repository from GitHub..."):
        cloner = GitHubCloner()
        clone_result = cloner.clone_repository(github_url)

        if not clone_result["success"]:
            st.error(f"❌ Failed to clone: {clone_result['error']}")
            return False

        st.session_state.repo_info = clone_result
        local_path = clone_result["local_path"]
        st.success(f"✅ Cloned {clone_result['owner']}/{clone_result['repo']}")

    # Step 2: Parse codebase (using generic parser)
    with st.spinner("📝 Parsing Java files..."):
        knowledge_graph = KnowledgeGraph()
        java_parser = GenericJavaParser()

        try:
            java_parser.parse_directory(local_path, knowledge_graph)
            relationship_extractor = RelationshipExtractor(java_parser)
            relationship_extractor.extract_all_relationships(knowledge_graph)

            stats = knowledge_graph.get_stats()
            st.session_state.knowledge_graph = knowledge_graph

            st.success(f"✅ Parsed {stats['classes']} classes, {stats['methods']} methods")

        except Exception as e:
            st.error(f"❌ Error parsing: {str(e)}")
            return False

    # Step 2.5: Detect framework using AI
    with st.spinner("🤖 Detecting Java framework with AI..."):
        try:
            detector = FrameworkDetector()
            framework_result = detector.detect_framework(knowledge_graph)
            st.session_state.framework_detection = framework_result

            # Display framework detection result
            framework_name = framework_result.get('framework', 'Unknown')
            confidence = framework_result.get('confidence', 0.0)
            source = framework_result.get('source', 'UNKNOWN')

            if framework_result.get('needs_confirmation') and not framework_result.get('needs_human_selection'):
                # Medium confidence - ask for confirmation
                st.warning(f"⚠️ Detected: {framework_name} ({confidence:.0%} confidence via {source})")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm", key="confirm_framework"):
                        st.success(f"✅ Framework confirmed: {framework_name}")
                with col2:
                    if st.button("❌ Choose Different", key="reject_framework"):
                        st.info("Manual framework selection coming soon!")
            elif framework_result.get('needs_human_selection'):
                # Multiple candidates
                st.warning("⚠️ Multiple frameworks detected - manual selection needed")
                candidates = framework_result.get('candidates', [])
                selected = st.selectbox(
                    "Select the correct framework:",
                    options=[c.name if hasattr(c, 'name') else c['name'] for c in candidates]
                )
                if st.button("Confirm Selection"):
                    framework_result['framework'] = selected
                    st.session_state.framework_detection = framework_result
                    st.success(f"✅ Framework set to: {selected}")
            else:
                # High confidence - auto confirmed
                confidence_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.60 else "🔴"
                st.success(f"✅ Framework detected: {framework_name} {confidence_emoji} ({confidence:.0%} confidence via {source})")

        except Exception as e:
            st.warning(f"⚠️ Framework detection failed: {str(e)}")
            st.info("Continuing with generic analysis...")
            st.session_state.framework_detection = {
                'framework': 'Unknown',
                'confidence': 0.0,
                'source': 'ERROR',
                'error': str(e)
            }

    # Step 3: Classify classes using LLM (NO HARDCODING!)
    with st.spinner("🤖 Classifying classes using AI (no hardcoded patterns)..."):
        try:
            framework_name = framework_result.get('framework', 'Unknown')
            classifier = LLMClassClassifier()

            # Classify all UNCLASSIFIED classes using LLM
            classifications = classifier.classify_classes(
                knowledge_graph,
                framework_name,
                batch_size=20  # Process 20 classes at a time
            )

            # Get classification report
            report = classifier.get_classification_report(classifications)

            st.success(
                f"✅ AI Classified: {report['counts']['Entity']} entities, "
                f"{report['counts']['Controller']} controllers, "
                f"{report['counts']['Service']} services, "
                f"{report['counts']['Repository']} repositories"
            )

            # Show detailed classification in expander
            with st.expander("🔍 View Classification Details"):
                for class_id, class_type in classifications.items():
                    if class_type != "UNCLASSIFIED":
                        class_node = knowledge_graph.classes.get(class_id)
                        if class_node:
                            st.write(f"**{class_type}**: `{class_node.package}.{class_node.name}`")

        except Exception as e:
            st.warning(f"⚠️ AI classification failed: {str(e)}")
            st.info("Continuing without classification...")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

    # Step 4: Discover domains (Universal approach - framework-agnostic)
    with st.spinner("🏢 Discovering domains by tracing call chains..."):
        try:
            domain_discovery = UniversalDomainDiscovery(knowledge_graph)
            domain_discovery.discover_domains()

            st.session_state.domain_graph = domain_discovery
            st.session_state.analysis_complete = True
            st.session_state.page = 'dashboard'

            # Show detailed discovery info
            st.success(f"✅ Discovered {len(domain_discovery.domains)} domain(s)")

            # Show what was discovered for each domain
            with st.expander("🔍 Discovery Details"):
                for domain_name, domain in domain_discovery.domains.items():
                    st.write(f"**{domain_name}**:")
                    st.write(f"  - Entry Points: {len(domain.entry_points)}")
                    st.write(f"  - Services: {len(domain.services)}")
                    st.write(f"  - Repositories: {len(domain.repositories)}")
                    st.write(f"  - Entities: {len(domain.entities)}")

            return True

        except Exception as e:
            st.error(f"❌ Error discovering domains: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
            return False


def show_input_page():
    """Input page for GitHub URL"""
    st.title("🔍 Java Codebase Analyzer")
    st.markdown("### Analyze ANY Java codebase from GitHub with AI-powered framework detection")

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.write("#### 📦 Enter Repository")
        github_url = st.text_input(
            "GitHub URL",
            placeholder="https://github.com/owner/repository",
            label_visibility="collapsed"
        )

        st.write("")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🚀 Analyze Repository", type="primary", use_container_width=True):
                if not github_url:
                    st.error("Please enter a GitHub URL")
                else:
                    analyze_repository(github_url)
                    if st.session_state.analysis_complete:
                        st.rerun()

        with col_b:
            if st.button("📚 Try Example", use_container_width=True):
                github_url = "https://github.com/spring-projects/spring-petclinic"
                analyze_repository(github_url)
                if st.session_state.analysis_complete:
                    st.rerun()

        st.write("")
        st.write("")

        with st.expander("ℹ️ What does this tool do?"):
            st.markdown("""
            This analyzer will:
            - 🏢 **Discover** all business domains/entities
            - 🏗️ **Map** architecture layers (Controller → Service → Repository → Entity)
            - 🌐 **Extract** all REST API endpoints
            - 📊 **Catalog** all methods, fields, and relationships
            - 🧠 **Analyze** business logic using AI (optional)
            - 📥 **Export** complete analysis
            """)


def show_dashboard():
    """Dashboard overview showing all domains"""
    repo_info = st.session_state.repo_info
    domain_graph = st.session_state.domain_graph
    knowledge_graph = st.session_state.knowledge_graph
    framework_detection = st.session_state.framework_detection

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"📊 {repo_info['owner']}/{repo_info['repo']}")
        st.caption(f"🔗 {repo_info['github_url']}")

    with col2:
        if st.button("🔄 New Analysis", use_container_width=True):
            # Reset
            st.session_state.page = 'input'
            st.session_state.analysis_complete = False
            st.session_state.domain_graph = None
            st.session_state.knowledge_graph = None
            st.session_state.repo_info = None
            st.session_state.selected_domain = None
            st.session_state.analyzed_domains = {}
            st.session_state.framework_detection = None
            st.rerun()

    st.write("---")

    # Framework Detection Result
    if framework_detection:
        framework_name = framework_detection.get('framework', 'Unknown')
        confidence = framework_detection.get('confidence', 0.0)
        source = framework_detection.get('source', 'UNKNOWN')

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            confidence_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.60 else "🔴"
            st.info(f"🤖 **Framework Detected:** {framework_name} {confidence_emoji}")
        with col2:
            st.metric("Confidence", f"{confidence:.0%}")
        with col3:
            st.metric("Source", source)

        # Show reasoning if available
        if framework_detection.get('reasoning'):
            with st.expander("ℹ️ Detection Details"):
                st.write(framework_detection['reasoning'])

                # Show architecture patterns if available
                if framework_detection.get('architecture_patterns'):
                    st.write("**Architecture Patterns:**")
                    for pattern in framework_detection['architecture_patterns']:
                        st.write(f"• {pattern}")

        st.write("---")

    # Overall metrics
    stats = knowledge_graph.get_stats()
    total_endpoints = sum(d.endpoint_count for d in domain_graph.domains.values())
    total_methods = sum(d.method_count for d in domain_graph.domains.values())
    total_fields = sum(len(d.fields) for d in domain_graph.domains.values())

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🏢 Business Domains", len(domain_graph.domains))
    with col2:
        st.metric("📦 Classes", stats['classes'])
    with col3:
        st.metric("🌐 Endpoints", total_endpoints)
    with col4:
        st.metric("⚙️ Methods", total_methods)
    with col5:
        st.metric("📊 Fields", total_fields)

    st.write("---")

    # Domain list
    st.write("### 🏢 Discovered Domains")
    st.write("Click on any domain to view detailed analysis")
    st.write("")

    # Sort by complexity
    sorted_domains = sorted(
        domain_graph.domains.items(),
        key=lambda x: x[1].complexity_score,
        reverse=True
    )

    # Display domain cards
    for domain_name, domain_info in sorted_domains:
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 2])

            with col1:
                st.write(f"### 🏢 {domain_name}")
                entity_text = domain_info.entities[0] if domain_info.entities else "No entity"
                st.caption(f"`{entity_text}`")

            with col2:
                st.metric("Endpoints", domain_info.endpoint_count)

            with col3:
                st.metric("Methods", domain_info.method_count)

            with col4:
                st.metric("Fields", len(domain_info.fields))

            with col5:
                complexity = domain_info.complexity_score
                color = "🔴" if complexity > 50 else "🟡" if complexity > 20 else "🟢"
                st.metric("Complexity", f"{color} {complexity}")

            with col6:
                if st.button(f"📋 View Details →", key=f"view_{domain_name}", use_container_width=True):
                    st.session_state.selected_domain = domain_name
                    st.session_state.page = 'domain_detail'
                    st.rerun()

            st.write("")

    # Export section
    st.write("---")
    st.write("### 📥 Export Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        catalog_data = domain_graph.export_domain_catalog()
        json_str = json.dumps(catalog_data, indent=2, default=str)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"{repo_info['repo']}_analysis.json",
            mime="application/json",
            use_container_width=True
        )


def show_domain_detail():
    """Detailed view of a specific domain with tabs"""
    domain_name = st.session_state.selected_domain
    domain_graph = st.session_state.domain_graph
    knowledge_graph = st.session_state.knowledge_graph
    domain_info = domain_graph.domains[domain_name]

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"🏢 {domain_name} Domain")
        entity_text = domain_info.entities[0] if domain_info.entities else "No entity"
        st.caption(f"Complete Analysis • {entity_text}")

    with col2:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()

    st.write("---")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🌐 Endpoints", domain_info.endpoint_count)
    with col2:
        st.metric("⚙️ Methods", domain_info.method_count)
    with col3:
        st.metric("📊 Fields", len(domain_info.fields))
    with col4:
        complexity = domain_info.complexity_score
        st.metric("📈 Complexity", complexity)

    st.write("---")

    # Tabbed interface
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Overview",
        "📊 Fields",
        "⚙️ Methods",
        "🌐 Endpoints",
        "🧠 Business Logic",
        "🕸️ Graph View"
    ])

    with tab1:
        show_overview_tab(domain_info)

    with tab2:
        show_fields_tab(domain_info, knowledge_graph)

    with tab3:
        show_methods_tab(domain_info, knowledge_graph)

    with tab4:
        show_endpoints_tab(domain_info, knowledge_graph)

    with tab5:
        show_business_logic_tab(domain_name, domain_info, knowledge_graph)

    with tab6:
        show_graph_tab(domain_name, domain_info, knowledge_graph)


def show_overview_tab(domain_info):
    """Overview tab content"""
    st.write("### 🏗️ Architecture Layers")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**🎮 Entry Points (Controllers/Actions)**")
        if domain_info.entry_points:
            for ep in domain_info.entry_points:
                st.code(ep.split('.')[-1], language="text")
            st.caption(f"✅ {len(domain_info.entry_points)} entry point(s)")
        else:
            st.warning("❌ Not Found")

        st.write("")
        st.write("**⚙️ Services**")
        if domain_info.services:
            for svc in domain_info.services:
                st.code(svc.split('.')[-1], language="text")
            st.caption(f"✅ {len(domain_info.services)} service(s)")
        else:
            st.warning("❌ Not Found")

    with col2:
        st.write("**🗄️ Repositories / DAOs**")
        if domain_info.repositories:
            for repo in domain_info.repositories:
                st.code(repo.split('.')[-1], language="text")
            st.caption(f"✅ {len(domain_info.repositories)} repository(ies)")
        else:
            st.warning("❌ Not Found")

        st.write("")
        st.write("**🏛️ Entities / Models**")
        if domain_info.entities:
            for entity in domain_info.entities:
                st.code(entity.split('.')[-1], language="text")
            st.caption(f"✅ {len(domain_info.entities)} entity(ies)")
        else:
            st.warning("❌ Not Found")

    st.write("---")
    st.write("### 📊 Quick Stats")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**{len(domain_info.fields)}** Fields")
    with col2:
        st.info(f"**{domain_info.endpoint_count}** Endpoints")
    with col3:
        st.info(f"**{domain_info.method_count}** Methods")


def show_fields_tab(domain_info, knowledge_graph):
    """Fields tab with complete details"""
    st.write(f"### 📊 Entity Fields ({len(domain_info.fields)})")

    if not domain_info.fields:
        st.info("No fields found in this entity")
        return

    st.write("Complete list of all fields in the entity class")
    st.write("")

    for field in domain_info.fields:
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 3])

            with col1:
                st.write(f"**`{field['name']}`**")

            with col2:
                st.code(field['type'], language="java")

            with col3:
                if field['annotations']:
                    annotations_str = ", ".join([f"@{ann}" for ann in field['annotations']])
                    st.caption(f"🏷️ {annotations_str}")
                else:
                    st.caption("No annotations")

            st.write("")


def show_methods_tab(domain_info, knowledge_graph):
    """Methods tab with signatures and details"""
    st.write(f"### ⚙️ All Methods ({domain_info.method_count})")

    st.write("Complete list of all methods across Entity, Controller, Service, and Repository")
    st.write("")

    # Group by class
    methods_by_class = {}
    for method_full_name in domain_info.methods:
        method_id = f"method:{method_full_name}"
        if method_id in knowledge_graph.methods:
            method_node = knowledge_graph.methods[method_id]
            class_name = method_node.class_name

            if class_name not in methods_by_class:
                methods_by_class[class_name] = []

            methods_by_class[class_name].append(method_node)

    # Display by class
    for class_name, methods in methods_by_class.items():
        simple_class_name = class_name.split('.')[-1]

        # Determine class type
        if 'Controller' in class_name:
            icon = "🎮"
            class_type = "Controller"
        elif 'Service' in class_name:
            icon = "⚙️"
            class_type = "Service"
        elif 'Repository' in class_name:
            icon = "🗄️"
            class_type = "Repository"
        else:
            icon = "🏛️"
            class_type = "Entity"

        with st.expander(f"{icon} {simple_class_name} ({len(methods)} methods)", expanded=False):
            for method in methods:
                # Method signature
                params_str = ", ".join([f"{p['type']} {p['name']}" for p in method.parameters])
                signature = f"{method.return_type} {method.name}({params_str})"

                st.code(signature, language="java")

                # Annotations
                if method.annotations:
                    annotations_str = ", ".join([f"@{ann}" for ann in method.annotations])
                    st.caption(f"🏷️ {annotations_str}")

                # Modifiers
                if method.modifiers:
                    modifiers_str = " ".join(method.modifiers)
                    st.caption(f"🔧 {modifiers_str}")

                st.write("")


def show_endpoints_tab(domain_info, knowledge_graph):
    """Endpoints tab with complete request/response details"""
    st.write(f"### 🌐 REST API Endpoints ({len(domain_info.endpoints)})")

    if not domain_info.endpoints:
        st.info("No REST endpoints found in this domain")
        return

    st.write("Complete details for all REST API endpoints")
    st.write("")

    for endpoint in domain_info.endpoints:
        with st.container():
            # Method color coding
            method_colors = {
                "GET": "🟢",
                "POST": "🔵",
                "PUT": "🟡",
                "DELETE": "🔴",
                "PATCH": "🟣"
            }

            method_color = method_colors.get(endpoint["http_method"], "⚪")

            # Header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"### {method_color} {endpoint['http_method']} `{endpoint['path']}`")
            with col2:
                st.caption(f"Handler: {endpoint['handler_method']}")

            # Get method details
            handler_method_full = f"{endpoint['handler_class']}.{endpoint['handler_method']}"
            method_id = f"method:{handler_method_full}"

            if method_id in knowledge_graph.methods:
                method_node = knowledge_graph.methods[method_id]

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**📥 Request**")

                    # Parameters
                    if method_node.parameters:
                        st.write("*Parameters:*")
                        for param in method_node.parameters:
                            st.write(f"  • `{param['name']}`: `{param['type']}`")
                    else:
                        st.caption("No parameters")

                with col2:
                    st.write("**📤 Response**")
                    st.write(f"*Returns:* `{method_node.return_type}`")

                # Annotations
                if method_node.annotations:
                    st.write("**🏷️ Annotations**")
                    for ann in method_node.annotations:
                        st.code(f"@{ann}", language="java")

            st.write("---")


def show_business_logic_tab(domain_name, domain_info, knowledge_graph):
    """Business logic tab with AI analysis"""
    st.write("### 🧠 Business Logic Analysis")

    # Check if already analyzed
    if domain_name in st.session_state.analyzed_domains:
        # Show results
        business_analysis = st.session_state.analyzed_domains[domain_name]

        if "error" in business_analysis:
            st.error(business_analysis["error"])
            if "note" in business_analysis:
                st.info(business_analysis["note"])
            return

        # Business Rules
        if business_analysis.get("business_rules"):
            st.write("#### 📋 Business Rules")
            for rule in business_analysis["business_rules"]:
                st.write(f"• {rule}")
            st.write("")

        # Endpoints
        if business_analysis.get("endpoints"):
            st.write("#### 🌐 Endpoint Analysis")
            for endpoint in business_analysis["endpoints"]:
                with st.expander(f"{endpoint['http_method']} {endpoint['path']}", expanded=False):
                    if endpoint.get("purpose"):
                        st.write(f"**Purpose:** {endpoint['purpose']}")
                    if endpoint.get("business_logic"):
                        st.write(f"**Logic:** {endpoint['business_logic']}")
                    if endpoint.get("business_rules"):
                        st.write("**Rules:**")
                        for rule in endpoint["business_rules"]:
                            st.write(f"  • {rule}")

        # Methods
        if business_analysis.get("business_methods"):
            st.write("#### ⚙️ Business Method Analysis")
            for method in business_analysis["business_methods"]:
                with st.expander(f"{method['method'].split('.')[-1]}()", expanded=False):
                    if method.get("purpose"):
                        st.write(f"**Purpose:** {method['purpose']}")
                    if method.get("operations"):
                        st.write("**Operations:**")
                        for op in method["operations"]:
                            st.write(f"  • {op}")
                    if method.get("business_rules"):
                        st.write("**Rules:**")
                        for rule in method["business_rules"]:
                            st.write(f"  • {rule}")

    else:
        # Show analyze button
        st.info("Click the button below to analyze business logic using AI")
        st.write("")

        if st.button("🧠 Analyze Business Logic", type="primary", use_container_width=True):
            with st.spinner("Analyzing business logic with AI..."):
                analyzer = DomainBusinessAnalyzer()
                business_analysis = analyzer.analyze_domain(
                    domain_info.to_dict(),
                    knowledge_graph
                )
                st.session_state.analyzed_domains[domain_name] = business_analysis
                st.rerun()


def show_graph_tab(domain_name, domain_info, knowledge_graph):
    """Graph visualization tab"""
    st.write("### 🕸️ Full Domain Graph")

    st.info("📊 Graph visualization coming soon!")
    st.write("")

    st.write("This will show:")
    st.write("• Complete call graph")
    st.write("• Field access patterns")
    st.write("• Method relationships")
    st.write("• Data flow visualization")

    st.write("")
    st.write("For now, you can export the data as JSON and visualize elsewhere.")


# Main app logic
if st.session_state.page == 'input':
    show_input_page()
elif st.session_state.page == 'dashboard':
    show_dashboard()
elif st.session_state.page == 'domain_detail':
    show_domain_detail()
