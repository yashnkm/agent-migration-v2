"""
Main entry point for Java Codebase Analysis System

DEPRECATED: This is the old parser-only entry point.
For domain-centric analysis, use: python src/analyze_domains.py <path>

This file is kept for basic parsing/testing purposes only.
"""
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge_graph.graph import KnowledgeGraph
from src.parser.java_parser import JavaParser
from src.parser.relationship_extractor import RelationshipExtractor


def analyze_codebase(directory_path: str):
    """
    Analyze a Java codebase and build knowledge graph
    """
    print("=" * 60)
    print("Java Codebase Analysis System - Phase 1")
    print("=" * 60)

    # Initialize components
    knowledge_graph = KnowledgeGraph()
    java_parser = JavaParser()

    # Parse all Java files
    print(f"\n[1/3] Parsing Java files from: {directory_path}")
    java_parser.parse_directory(directory_path, knowledge_graph)

    # Extract relationships
    print(f"\n[2/3] Extracting relationships...")
    relationship_extractor = RelationshipExtractor(java_parser)
    relationship_extractor.extract_all_relationships(knowledge_graph)

    # Display results
    print(f"\n[3/3] Analysis Complete!")
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH SUMMARY")
    print("=" * 60)

    stats = knowledge_graph.get_stats()
    print(f"\nTotal Nodes: {stats['total_nodes']}")
    print(f"Total Edges: {stats['total_edges']}")
    print(f"\nBreakdown:")
    print(f"  Classes:     {stats['classes']}")
    print(f"  Methods:     {stats['methods']}")
    print(f"  Fields:      {stats['fields']}")
    print(f"  Endpoints:   {stats['endpoints']}")
    print(f"  Entry Points: {stats['entry_points']}")

    # Display classes by type
    print(f"\n" + "-" * 60)
    print("CLASSES BY TYPE")
    print("-" * 60)

    class_types = {}
    for class_id, class_node in knowledge_graph.classes.items():
        class_type = class_node.class_type
        if class_type not in class_types:
            class_types[class_type] = []
        class_types[class_type].append(f"{class_node.package}.{class_node.name}")

    for class_type, classes in class_types.items():
        print(f"\n{class_type}s ({len(classes)}):")
        for class_name in classes:
            print(f"  - {class_name}")

    # Display endpoints
    if knowledge_graph.endpoints:
        print(f"\n" + "-" * 60)
        print("REST ENDPOINTS")
        print("-" * 60)

        for endpoint_id, endpoint in knowledge_graph.endpoints.items():
            print(f"\n{endpoint.http_method} {endpoint.path}")
            print(f"  Handler: {endpoint.handler_class}.{endpoint.handler_method}")

    # Display field access map
    if knowledge_graph.field_access_map:
        print(f"\n" + "-" * 60)
        print("FIELD ACCESS MAP (Sample)")
        print("-" * 60)

        count = 0
        for field, accessors in knowledge_graph.field_access_map.items():
            if count >= 5:  # Show only first 5 for brevity
                print(f"\n... and {len(knowledge_graph.field_access_map) - 5} more fields")
                break
            print(f"\nField: {field}")
            print(f"  Accessed by: {', '.join(accessors)}")
            count += 1

    # Export to JSON
    output_file = "knowledge_graph_output.json"
    print(f"\n" + "=" * 60)
    print(f"Exporting knowledge graph to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(knowledge_graph.export_to_dict(), f, indent=2, default=str)
    print(f"Export complete!")

    return knowledge_graph


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <path-to-java-project>")
        print("\nExample:")
        print("  python src/main.py test-java-project")
        sys.exit(1)

    directory_path = sys.argv[1]

    if not Path(directory_path).exists():
        print(f"Error: Directory '{directory_path}' does not exist")
        sys.exit(1)

    analyze_codebase(directory_path)


if __name__ == "__main__":
    main()
