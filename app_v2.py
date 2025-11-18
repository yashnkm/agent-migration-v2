"""
Streamlit Web UI - Simple Graph Creator
Input: GitHub URL
Output: Knowledge Graph JSON
"""
import streamlit as st
import streamlit_markdown as stmd  # For Mermaid rendering
import sys
import json
import urllib.parse  # For Mermaid Live Editor fallback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.github_cloner import GitHubCloner
from src.knowledge_graph.graph import KnowledgeGraph
from src.parser.generic_java_parser import GenericJavaParser
from src.parser.relationship_extractor import RelationshipExtractor
from src.inference.framework_detector_v2 import FrameworkDetectorV2
from src.inference.graph_summarizer import GraphSummarizer
from src.inference.presentation_layer_extractor import extract_presentation_layer
from src.rag.agents.functional_spec_agent import (
    FunctionalSpecAgent,
    format_feature_spec_markdown,
    format_project_spec_markdown
)
from src.rag.graph_to_documents import convert_graph_to_documents
from src.rag.vectorstore_manager import VectorStoreManager
from src.rag.agents.architecture_agent import create_architecture_agent
from src.rag.report_generator import ArchitectureReportGenerator, MermaidDiagramGenerator
from src.rag.report_formatter import format_report_as_markdown, format_diagram_with_report


# Page config
st.set_page_config(
    page_title="Java Graph Creator",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better Mermaid diagram visibility
st.markdown("""
<style>
    /* Make Mermaid diagrams fully visible and scrollable */
    .stMarkdown {
        overflow-x: auto;
        overflow-y: auto;
    }

    /* Mermaid diagram container styling */
    .stMarkdown pre {
        overflow-x: auto;
        overflow-y: auto;
        max-height: 800px;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 5px;
    }

    /* Ensure Mermaid SVG is visible */
    .stMarkdown svg {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'knowledge_graph' not in st.session_state:
    st.session_state.knowledge_graph = None
if 'repo_info' not in st.session_state:
    st.session_state.repo_info = None
if 'graph_created' not in st.session_state:
    st.session_state.graph_created = False
if 'framework_detection' not in st.session_state:
    st.session_state.framework_detection = None
if 'rag_index_created' not in st.session_state:
    st.session_state.rag_index_created = False
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'architecture_agent' not in st.session_state:
    st.session_state.architecture_agent = None
if 'architecture_report' not in st.session_state:
    st.session_state.architecture_report = None
if 'diagrams' not in st.session_state:
    st.session_state.diagrams = {}
if 'presentation_layer_info' not in st.session_state:
    st.session_state.presentation_layer_info = None
if 'functional_spec' not in st.session_state:
    st.session_state.functional_spec = None
if 'single_feature_spec' not in st.session_state:
    st.session_state.single_feature_spec = None


def create_graph(github_url: str):
    """Create knowledge graph from GitHub repository"""

    # Step 1: Clone repository
    with st.spinner("🔄 Cloning repository..."):
        cloner = GitHubCloner()
        clone_result = cloner.clone_repository(github_url)

        if not clone_result["success"]:
            st.error(f"❌ Failed to clone: {clone_result['error']}")
            return False

        st.session_state.repo_info = clone_result
        local_path = clone_result["local_path"]
        st.success(f"✅ Cloned {clone_result['owner']}/{clone_result['repo']}")

    # Step 2: Parse and create graph
    with st.spinner("📝 Creating knowledge graph..."):
        knowledge_graph = KnowledgeGraph()
        java_parser = GenericJavaParser()

        try:
            # Parse Java files
            java_parser.parse_directory(local_path, knowledge_graph)

            # Extract relationships
            relationship_extractor = RelationshipExtractor(java_parser)
            relationship_extractor.extract_all_relationships(knowledge_graph)

            stats = knowledge_graph.get_stats()
            st.session_state.knowledge_graph = knowledge_graph
            st.session_state.graph_created = True

            st.success(f"✅ Graph created: {stats['classes']} classes, {stats['methods']} methods, {stats['total_edges']} edges")
            return True

        except Exception as e:
            st.error(f"❌ Error creating graph: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
            return False


# Main UI
st.title("🔍 Java Knowledge Graph Creator")
st.markdown("### Create a complete knowledge graph from any Java GitHub repository")

st.write("")
st.write("")

# Input section
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    github_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        key="github_input"
    )

    st.write("")

    if st.button("🚀 Create Graph", type="primary", use_container_width=True):
        if not github_url:
            st.error("Please enter a GitHub URL")
        else:
            create_graph(github_url)

st.write("")
st.write("---")

# Results section
if st.session_state.graph_created and st.session_state.knowledge_graph:
    kg = st.session_state.knowledge_graph
    repo_info = st.session_state.repo_info

    st.write("## 📊 Graph Statistics")

    stats = kg.get_stats()

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Classes", stats['classes_only'])
    with col2:
        st.metric("Interfaces", stats['interfaces'])
    with col3:
        st.metric("Enums", stats['enums'])
    with col4:
        st.metric("Methods", stats['methods'])
    with col5:
        st.metric("Fields", stats['fields'])
    with col6:
        st.metric("Edges", stats['total_edges'])

    st.write("")
    st.write("---")

    # Framework Detection Section
    st.write("## 🤖 Framework Analysis")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("🔍 Detect Framework", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing codebase structure with AI agent..."):
                try:
                    detector = FrameworkDetectorV2()
                    result = detector.detect_framework(kg)
                    st.session_state.framework_detection = result
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Framework detection failed: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

    with col2:
        if st.session_state.framework_detection:
            result = st.session_state.framework_detection
            framework_name = result.get('framework', 'Unknown')
            confidence = result.get('confidence', 0.0)
            source = result.get('source', 'UNKNOWN')

            # Color based on confidence
            if confidence >= 0.85:
                confidence_color = "🟢"
            elif confidence >= 0.60:
                confidence_color = "🟡"
            else:
                confidence_color = "🔴"

            st.success(f"{confidence_color} **Detected**: {framework_name} ({confidence:.0%} confidence)")

            # Show reasoning if available
            if result.get('reasoning'):
                with st.expander("📋 Detection Details"):
                    st.write(result['reasoning'])

                    # Show architecture patterns if available
                    if result.get('architecture_patterns'):
                        st.write("**Architecture Patterns:**")
                        for pattern in result['architecture_patterns']:
                            st.write(f"• {pattern}")
        else:
            st.info("Click 'Detect Framework' to analyze the codebase")

    st.write("")
    st.write("---")

    # Presentation Layer Extraction Section
    st.write("## 🎯 Presentation Layer Analysis")

    col1, col2 = st.columns([1, 3])

    with col1:
        # Only show button if framework is detected
        if st.session_state.framework_detection:
            if st.button("📊 Extract Presentation Layer", type="primary", use_container_width=True):
                with st.spinner("🔍 Extracting controllers/actions..."):
                    try:
                        framework_name = st.session_state.framework_detection.get('framework', 'Unknown')
                        presentation_info = extract_presentation_layer(kg, framework_name)
                        st.session_state.presentation_layer_info = presentation_info
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Extraction failed: {str(e)}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
        else:
            st.info("Detect framework first")

    with col2:
        if st.session_state.presentation_layer_info:
            info = st.session_state.presentation_layer_info
            st.success(f"✅ {info.summary}")

            # Show controller/action list
            if info.controllers:
                with st.expander(f"📋 {info.total_controllers} Presentation Components", expanded=True):
                    for controller in info.controllers:
                        st.write(f"### {controller.name}")
                        st.write(f"**Type**: {controller.type}")
                        st.write(f"**Package**: `{controller.package}`")

                        if controller.base_path:
                            st.write(f"**Base Path**: `{controller.base_path}`")

                        # Show endpoints
                        if controller.endpoints:
                            st.write(f"**Endpoints** ({len(controller.endpoints)}):")
                            for endpoint in controller.endpoints:
                                method_badge = f"`{endpoint.http_method}`"
                                st.write(f"  - {method_badge} `{endpoint.path}` → `{endpoint.handler_method}()`")

                        # Show dependencies
                        if controller.dependencies:
                            st.write(f"**Dependencies**: {', '.join([f'`{dep}`' for dep in controller.dependencies])}")

                        st.write("---")

                # Download button for JSON export
                json_data = {
                    "framework": info.framework,
                    "total_controllers": info.total_controllers,
                    "total_endpoints": info.total_endpoints,
                    "controllers": [
                        {
                            "name": c.name,
                            "package": c.package,
                            "type": c.type,
                            "base_path": c.base_path,
                            "file_path": c.file_path,
                            "endpoints": [
                                {
                                    "http_method": e.http_method,
                                    "path": e.path,
                                    "handler_method": e.handler_method,
                                    "return_type": e.return_type
                                } for e in c.endpoints
                            ],
                            "dependencies": c.dependencies
                        } for c in info.controllers
                    ]
                }

                st.download_button(
                    label="⬇️ Download Presentation Layer JSON",
                    data=json.dumps(json_data, indent=2),
                    file_name=f"{repo_info['repo']}_presentation_layer.json",
                    mime="application/json"
                )
        else:
            st.info("Click 'Extract Presentation Layer' to analyze controllers and endpoints")

    st.write("")
    st.write("---")

    # RAG Index Creation Section
    st.write("## 🧠 Agentic RAG System")

    col1, col2 = st.columns([1, 3])

    with col1:
        if not st.session_state.rag_index_created:
            # Checkbox for local embeddings
            use_local = st.checkbox("Use Local Embeddings (offline, no quota)", value=False,
                                   help="Use local sentence-transformers instead of Gemini (slower but no API limits)")

            if st.button("🚀 Create RAG Index", type="primary", use_container_width=True):
                spinner_text = "Creating RAG index with local embeddings..." if use_local else "Creating RAG index with Gemini embeddings..."
                with st.spinner(spinner_text):
                    try:
                        # Convert graph to documents
                        documents = convert_graph_to_documents(kg)

                        # Create vectorstore (will auto-fallback to local if Gemini fails)
                        manager = VectorStoreManager(output_dimensionality=768, use_local=use_local)
                        repo_name = repo_info['repo']
                        vectorstore = manager.create_vectorstore(documents, repo_name)

                        # Create architecture agent
                        agent = create_architecture_agent(vectorstore)

                        # Store in session
                        st.session_state.vectorstore = vectorstore
                        st.session_state.architecture_agent = agent
                        st.session_state.rag_index_created = True

                        st.success(f"RAG index created! {len(documents)} documents indexed.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to create RAG index: {str(e)}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
        else:
            st.success("✅ RAG Index Ready")

    with col2:
        if st.session_state.rag_index_created:
            st.info("RAG index is ready! Ask the Architecture Agent questions about the codebase structure and patterns.")
        else:
            st.info("Create a RAG index to enable AI-powered architecture analysis with natural language queries.")

    # Agent Query Interface
    if st.session_state.rag_index_created and st.session_state.architecture_agent:
        st.write("")
        st.write("### 💬 Ask Architecture Agent")

        # Query input
        query = st.text_input(
            "Question:",
            placeholder="e.g., What architecture patterns are used? How many controllers? What are the main entity classes?",
            key="agent_query"
        )

        col1, col2 = st.columns([1, 5])

        with col1:
            ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

        if ask_button and query:
            with st.spinner("Agent is analyzing..."):
                try:
                    agent = st.session_state.architecture_agent
                    result = agent.analyze(query)

                    if result["success"]:
                        st.write("#### Answer:")
                        st.write(result["answer"])

                        # Show intermediate steps if verbose
                        if result.get("intermediate_steps"):
                            with st.expander("🔎 Agent Reasoning Steps"):
                                for i, step in enumerate(result["intermediate_steps"], 1):
                                    st.write(f"**Step {i}:**")
                                    st.write(step)
                    else:
                        st.error(f"Agent error: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    st.error(f"Error querying agent: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

    st.write("")
    st.write("---")

    # Functional Specification Generator Section
    if st.session_state.rag_index_created and st.session_state.vectorstore and st.session_state.presentation_layer_info:
        st.write("## 📝 Functional Specification Generator")

        info = st.session_state.presentation_layer_info

        col1, col2 = st.columns([1, 3])

        with col1:
            st.write("**Single Component:**")

            # Dropdown to select a component
            controller_names = [c.name for c in info.controllers]
            if controller_names:
                selected_controller = st.selectbox(
                    "Select Component",
                    controller_names,
                    key="spec_component_select"
                )

                if st.button("🔍 Generate Spec", use_container_width=True):
                    with st.spinner(f"Analyzing {selected_controller}..."):
                        try:
                            # Find the selected controller
                            controller = next(
                                c for c in info.controllers
                                if c.name == selected_controller
                            )

                            # Generate spec
                            agent = FunctionalSpecAgent(st.session_state.vectorstore)
                            spec = agent.analyze_component(controller)
                            st.session_state.single_feature_spec = spec
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                            import traceback
                            with st.expander("Error Details"):
                                st.code(traceback.format_exc())

            st.write("")
            st.write("**Full Project:**")

            if st.button("📄 Generate Complete Spec", use_container_width=True):
                with st.spinner(f"Analyzing all {len(info.controllers)} components..."):
                    try:
                        agent = FunctionalSpecAgent(st.session_state.vectorstore)
                        project_spec = agent.analyze_full_project(
                            info.controllers,
                            repo_info['repo']
                        )
                        st.session_state.functional_spec = project_spec
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

        with col2:
            # Show single component spec
            if st.session_state.single_feature_spec:
                spec = st.session_state.single_feature_spec
                st.success(f"✅ Generated specification for {spec.feature_name}")

                with st.expander(f"📋 {spec.feature_name} Specification", expanded=True):
                    # Display full LLM analysis if available
                    if hasattr(spec, 'full_spec_text'):
                        st.markdown(spec.full_spec_text)
                    else:
                        st.write(f"**Overview**: {spec.overview}")

                    st.write("")
                    st.write("**Endpoints:**")
                    for ep in spec.endpoints:
                        st.write(f"- `{ep['method']}` `{ep['path']}` → `{ep['handler']}()`")

                    if spec.dependencies:
                        st.write("")
                        st.write(f"**Dependencies**: {', '.join([f'`{dep}`' for dep in spec.dependencies])}")

                # Download button
                spec_md = format_feature_spec_markdown(spec)
                st.download_button(
                    label="⬇️ Download Specification",
                    data=spec_md,
                    file_name=f"{spec.source_component}_spec.md",
                    mime="text/markdown",
                    key="download_single_spec"
                )

            # Show full project spec
            if st.session_state.functional_spec:
                project_spec = st.session_state.functional_spec
                st.success(f"✅ Complete specification generated: {project_spec.total_features} features, {project_spec.total_endpoints} endpoints")

                with st.expander("📄 Project Functional Specification", expanded=False):
                    st.write(f"**Project**: {project_spec.project_name}")
                    st.write(f"**Generated**: {project_spec.generated_date}")
                    st.write("")

                    st.write("**Features:**")
                    for feature in project_spec.features:
                        st.write(f"- {feature.feature_name} ({len(feature.endpoints)} endpoints)")

                    st.write("")
                    st.write("**Cross-Cutting Concerns:**")
                    for concern in project_spec.cross_cutting_concerns:
                        st.write(f"- {concern}")

                # Download button for full project spec
                full_spec_md = format_project_spec_markdown(project_spec)
                st.download_button(
                    label="⬇️ Download Complete Functional Specification",
                    data=full_spec_md,
                    file_name=f"{repo_info['repo']}_functional_specification.md",
                    mime="text/markdown",
                    key="download_full_spec"
                )

            if not st.session_state.single_feature_spec and not st.session_state.functional_spec:
                st.info("Select a component and generate spec, or generate complete project specification")

        st.write("")
        st.write("---")

    # Architecture Report & Diagram Generation
    if st.session_state.rag_index_created and st.session_state.vectorstore:
        st.write("## 📊 Architecture Report & Diagrams")

        col1, col2 = st.columns([1, 3])

        with col1:
            if st.button("📝 Generate Report", type="primary", use_container_width=True):
                with st.spinner("Generating comprehensive architecture report..."):
                    try:
                        generator = ArchitectureReportGenerator(st.session_state.vectorstore)
                        report = generator.generate_report(repo_info['repo'])
                        st.session_state.architecture_report = report
                        st.success("Report generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate report: {str(e)}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

        with col2:
            if st.session_state.architecture_report:
                st.info("Architecture report ready! Scroll down to view details and generate diagrams.")
            else:
                st.info("Generate a comprehensive architecture report to understand the system design, patterns, and structure.")

        # Display Report
        if st.session_state.architecture_report:
            report = st.session_state.architecture_report

            st.write("")
            st.write("### 📋 Architecture Report")

            # Download button for report
            md_report = format_report_as_markdown(report)
            st.download_button(
                label="⬇️ Download Report (Markdown)",
                data=md_report,
                file_name=f"{report.project_name}_architecture_report.md",
                mime="text/markdown"
            )

            st.write("")

            # Executive Summary
            with st.expander("📌 Executive Summary", expanded=True):
                st.write(report.executive_summary)

            # Architecture Patterns
            with st.expander("🏗️ Architecture Patterns"):
                for pattern in report.architecture_patterns:
                    st.write(f"- {pattern}")

            # Layers
            with st.expander("📚 Architectural Layers"):
                for layer in report.layers:
                    st.write(f"#### {layer.name}")
                    st.write(f"**Responsibilities:** {layer.responsibilities}")
                    st.write(f"**Components:**")
                    for comp in layer.components:
                        st.write(f"- {comp}")
                    st.write("")

            # Key Components
            with st.expander("🔑 Key Components"):
                for comp in report.key_components:
                    st.write(f"#### {comp.name} ({comp.type})")
                    st.write(f"**Purpose:** {comp.purpose}")
                    if comp.dependencies:
                        st.write(f"**Dependencies:** {', '.join(comp.dependencies)}")
                    st.write("")

            # Data Flow
            with st.expander("🔄 Data Flow"):
                st.write(report.data_flow)

            # Technology Stack
            with st.expander("⚙️ Technology Stack"):
                for tech in report.technology_stack:
                    st.write(f"- {tech}")

            # Strengths
            with st.expander("✅ Strengths"):
                for strength in report.strengths:
                    st.write(f"- {strength}")

            # Recommendations
            with st.expander("💡 Recommendations"):
                for rec in report.recommendations:
                    st.write(f"- {rec}")

            st.write("")
            st.write("---")

            # Diagram Generation
            st.write("### 📐 Architecture Diagrams")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔷 Generate Component Diagram", use_container_width=True):
                    with st.spinner("Generating component diagram..."):
                        try:
                            generator = MermaidDiagramGenerator()
                            diagram = generator.generate_component_diagram(report)
                            st.session_state.diagrams['component'] = diagram
                            st.success("Component diagram generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate diagram: {str(e)}")

            with col2:
                if st.button("📦 Generate Class Diagram", use_container_width=True):
                    with st.spinner("Generating class diagram..."):
                        try:
                            generator = MermaidDiagramGenerator()
                            diagram = generator.generate_class_diagram(report)
                            st.session_state.diagrams['class'] = diagram
                            st.success("Class diagram generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate diagram: {str(e)}")

            # Display Diagrams
            if 'component' in st.session_state.diagrams:
                st.write("")
                st.write("#### 🔷 Component Architecture Diagram")

                diagram = st.session_state.diagrams['component']
                st.write(f"**Description:** {diagram.description}")

                # Download button for diagram
                diagram_md = format_diagram_with_report(diagram, report)
                st.download_button(
                    label="⬇️ Download Component Diagram",
                    data=diagram_md,
                    file_name=f"{report.project_name}_component_diagram.md",
                    mime="text/markdown",
                    key="download_component"
                )

                # Render Mermaid diagram using streamlit-markdown (full width, scrollable)
                st.write("")
                try:
                    with st.container():
                        stmd.st_markdown(
                            f"""```mermaid
{diagram.mermaid_code}
```""",
                            unsafe_allow_html=True,
                            height=800  # Set explicit height for better visibility
                        )
                except Exception as e:
                    # Fallback: Provide link to Mermaid Live Editor
                    encoded_diagram = urllib.parse.quote(diagram.mermaid_code)
                    mermaid_live_url = f"https://mermaid.live/edit#pako:{encoded_diagram}"

                    st.warning("⚠️ Diagram rendering failed in the browser.")
                    st.info(f"📊 [Click here to view the diagram in Mermaid Live Editor]({mermaid_live_url})")

                    # Also show the raw code in an expander
                    with st.expander("View Raw Mermaid Code"):
                        st.code(diagram.mermaid_code, language="mermaid")

            if 'class' in st.session_state.diagrams:
                st.write("")
                st.write("#### 📦 Class Diagram")

                diagram = st.session_state.diagrams['class']
                st.write(f"**Description:** {diagram.description}")

                # Download button for diagram
                diagram_md = format_diagram_with_report(diagram, report)
                st.download_button(
                    label="⬇️ Download Class Diagram",
                    data=diagram_md,
                    file_name=f"{report.project_name}_class_diagram.md",
                    mime="text/markdown",
                    key="download_class"
                )

                # Render Mermaid diagram using streamlit-markdown (full width, scrollable)
                st.write("")
                try:
                    with st.container():
                        stmd.st_markdown(
                            f"""```mermaid
{diagram.mermaid_code}
```""",
                            unsafe_allow_html=True,
                            height=800  # Set explicit height for better visibility
                        )
                except Exception as e:
                    # Fallback: Provide link to Mermaid Live Editor
                    encoded_diagram = urllib.parse.quote(diagram.mermaid_code)
                    mermaid_live_url = f"https://mermaid.live/edit#pako:{encoded_diagram}"

                    st.warning("⚠️ Diagram rendering failed in the browser.")
                    st.info(f"📊 [Click here to view the diagram in Mermaid Live Editor]({mermaid_live_url})")

                    # Also show the raw code in an expander
                    with st.expander("View Raw Mermaid Code"):
                        st.code(diagram.mermaid_code, language="mermaid")

        st.write("")
        st.write("---")

    st.write("## 📥 Export Graph")

    # Export full graph as JSON
    graph_data = kg.export_to_dict()
    json_str = json.dumps(graph_data, indent=2, default=str)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.download_button(
            label="📄 Download Graph JSON",
            data=json_str,
            file_name=f"{repo_info['repo']}_graph.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        st.info(f"💾 Graph contains all classes, methods, fields, and relationships from {repo_info['owner']}/{repo_info['repo']}")

    st.write("")
    st.write("---")

    # Preview section
    with st.expander("🔍 Preview Graph Data", expanded=False):
        st.json(graph_data, expanded=False)

    st.write("")

    # Reset button
    if st.button("🔄 New Repository", use_container_width=False):
        st.session_state.knowledge_graph = None
        st.session_state.repo_info = None
        st.session_state.graph_created = False
        st.session_state.framework_detection = None
        st.session_state.presentation_layer_info = None
        st.session_state.functional_spec = None
        st.session_state.single_feature_spec = None
        st.session_state.rag_index_created = False
        st.session_state.vectorstore = None
        st.session_state.architecture_agent = None
        st.session_state.architecture_report = None
        st.session_state.diagrams = {}
        st.rerun()

else:
    st.info("👆 Enter a GitHub URL and click 'Create Graph' to get started")

    st.write("")
    st.write("### 📚 Example Repositories")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Try: Spring Boot Example", use_container_width=True):
            st.session_state.github_input = "https://github.com/spring-projects/spring-petclinic"
            create_graph("https://github.com/spring-projects/spring-petclinic")
            st.rerun()

    with col2:
        if st.button("Try: REST API Example", use_container_width=True):
            st.session_state.github_input = "https://github.com/callicoder/spring-boot-react-oauth2-social-login-demo"
            create_graph("https://github.com/callicoder/spring-boot-react-oauth2-social-login-demo")
            st.rerun()
