"""
Domain-Centric Codebase Analysis
Automatically discovers and maps all business domains
"""
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge_graph.graph import KnowledgeGraph
from src.parser.java_parser import JavaParser
from src.parser.relationship_extractor import RelationshipExtractor
from src.domain_analyzer.domain_graph import DomainGraph


def analyze_codebase_by_domains(directory_path: str):
    """
    Main analysis function - discovers domains automatically
    """
    print("=" * 70)
    print("Java Codebase Domain Analysis System")
    print("=" * 70)

    # Step 1: Parse codebase (using existing parser)
    print("\n[PHASE 1] Parsing Java codebase...")
    knowledge_graph = KnowledgeGraph()
    java_parser = JavaParser()

    print(f"Scanning directory: {directory_path}")
    java_parser.parse_directory(directory_path, knowledge_graph)

    # Extract relationships
    print("\nExtracting code relationships...")
    relationship_extractor = RelationshipExtractor(java_parser)
    relationship_extractor.extract_all_relationships(knowledge_graph)

    stats = knowledge_graph.get_stats()
    print(f"\n[OK] Parsing complete!")
    print(f"  Classes: {stats['classes']}, Methods: {stats['methods']}, Fields: {stats['fields']}")
    print(f"  Endpoints: {stats['endpoints']}")

    # Step 2: Build domain-centric graph
    print("\n[PHASE 2] Building domain-centric knowledge graph...")
    domain_graph = DomainGraph(knowledge_graph)
    domain_graph.discover_domains()

    # Step 3: Display results
    print("\n[PHASE 3] Analysis Results")
    domain_graph.print_domain_catalog()

    # Step 4: Show detailed view for each domain
    print("\n[PHASE 4] Detailed Domain Analysis")
    for domain_name in domain_graph.domains.keys():
        domain_graph.print_domain_details(domain_name)

    # Step 5: Export to JSON
    output_file = "domain_catalog.json"
    print(f"\n[PHASE 5] Exporting domain catalog...")
    with open(output_file, 'w') as f:
        catalog = domain_graph.export_domain_catalog()
        json.dump(catalog, f, indent=2, default=str)

    print(f"[OK] Domain catalog exported to: {output_file}")

    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)

    return domain_graph


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python src/analyze_domains.py <path-to-java-project>")
        print("\nExample:")
        print("  python src/analyze_domains.py test-java-project")
        sys.exit(1)

    directory_path = sys.argv[1]

    if not Path(directory_path).exists():
        print(f"Error: Directory '{directory_path}' does not exist")
        sys.exit(1)

    analyze_codebase_by_domains(directory_path)


if __name__ == "__main__":
    main()
