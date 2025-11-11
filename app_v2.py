"""
Streamlit Web UI - Simple Graph Creator
Input: GitHub URL
Output: Knowledge Graph JSON
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
from src.inference.framework_detector_v2 import FrameworkDetectorV2
from src.inference.graph_summarizer import GraphSummarizer
from src.rag.graph_to_documents import convert_graph_to_documents
from src.rag.vectorstore_manager import VectorStoreManager
from src.rag.agents.architecture_agent import create_architecture_agent


# Page config
st.set_page_config(
    page_title="Java Graph Creator",
    page_icon="🔍",
    layout="wide"
)

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
        st.session_state.rag_index_created = False
        st.session_state.vectorstore = None
        st.session_state.architecture_agent = None
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
