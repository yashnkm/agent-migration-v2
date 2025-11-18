# Documentation Index

Welcome to the Java Codebase Analyzer documentation!

---

## Available Documentation

### 1. [Project Documentation](./PROJECT_DOCUMENTATION.md)
**Complete project overview and guide**

Covers:
- Project overview and features
- Architecture and data flow
- Technology stack
- Project structure
- Core components detailed explanation
- Configuration and environment setup
- Usage guide and examples
- Code conventions (PEP 8)
- Troubleshooting
- Performance optimization

**Start here** if you're new to the project.

---

### 2. [API Reference](./API_REFERENCE.md)
**Complete API documentation for all classes and functions**

Covers:
- GitHubCloner API
- GenericJavaParser API
- RelationshipExtractor API
- KnowledgeGraph API
- FrameworkDetectorV2 API
- RAG System APIs (VectorStore, Documents, Retriever)
- Agent APIs (Architecture, Framework-Aware, Planning)
- Report Generator API
- Data Models (ClassNode, MethodNode, etc.)
- Complete usage examples

**Use this** for programmatic usage and integration.

---

### 3. [EC2 Deployment Guide](./EC2_DEPLOYMENT.md)
**Step-by-step AWS EC2 deployment guide**

Covers:
- EC2 instance setup
- Application deployment steps
- Configuration (environment variables, ports)
- Running the application (foreground, background, systemd)
- Process management with systemd
- Monitoring and maintenance
- Troubleshooting common issues
- Security best practices
- Cost optimization
- Backup and restore

**Use this** when deploying to AWS EC2.

---

## Quick Links

### Getting Started
- [Installation Guide](../README.md#installation)
- [Usage Guide](./PROJECT_DOCUMENTATION.md#usage-guide)
- [API Examples](./API_REFERENCE.md#complete-usage-example)

### Deployment
- [Local Deployment](./PROJECT_DOCUMENTATION.md#deployment-guide)
- [EC2 Production Deployment](./EC2_DEPLOYMENT.md)

### Reference
- [Architecture Overview](./PROJECT_DOCUMENTATION.md#architecture)
- [Technology Stack](./PROJECT_DOCUMENTATION.md#technology-stack)
- [API Reference](./API_REFERENCE.md)

### Troubleshooting
- [Common Issues](./PROJECT_DOCUMENTATION.md#troubleshooting)
- [EC2 Troubleshooting](./EC2_DEPLOYMENT.md#troubleshooting)

---

## Project Structure Overview

```
agent-migration-v2/
├── app_v2.py                    # Main Streamlit application
├── requirements.txt             # Python dependencies
├── README.md                    # Main project README
├── .env                        # Environment variables (create this)
├── .env.example                # Example configuration
│
├── .streamlit/
│   └── config.toml             # Streamlit config (port 8051)
│
├── docs/                       # 📚 You are here
│   ├── README.md               # This file
│   ├── PROJECT_DOCUMENTATION.md
│   ├── API_REFERENCE.md
│   └── EC2_DEPLOYMENT.md
│
└── src/                        # Source code
    ├── utils/                  # Utilities (GitHub cloner)
    ├── parser/                 # Java parsing (tree-sitter)
    ├── knowledge_graph/        # Graph data structure
    ├── inference/              # AI framework detection
    └── rag/                    # RAG system & agents
        └── agents/             # Multi-agent system
```

---

## Documentation Standards

All documentation follows these standards:

### Markdown Format
- Clear headings hierarchy
- Code blocks with language specification
- Tables for structured data
- Examples for all features

### Code Examples
- Complete, runnable examples
- Include imports
- Show expected output
- Error handling demonstrated

### Naming Conventions (PEP 8)
- Files/modules: `snake_case`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`

---

## Support

### GitHub
- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas

### Documentation
If you find issues or have suggestions for improving documentation:
1. Open an issue on GitHub
2. Submit a pull request with improvements
3. Contact the maintainers

---

## Contributing to Documentation

### How to Contribute

1. **Found a typo?** Submit a PR with the fix
2. **Missing information?** Open an issue describing what's missing
3. **Better examples?** Add them and submit a PR

### Documentation Structure

When adding new documentation:
- Keep it organized and scannable
- Use clear headings
- Include code examples
- Add to this index (README.md)

---

## Version History

### Version 2.0 (Current)
- Complete rewrite with AI-powered analysis
- Framework-agnostic parsing
- Multi-agent RAG system
- Comprehensive documentation

### Version 1.0 (Deprecated)
- Hardcoded Spring Boot patterns
- Query-based interface
- Limited framework support

---

## Feedback

We value your feedback! Help us improve:

- 📝 Documentation clarity
- 🐛 Bug reports
- 💡 Feature suggestions
- 🎨 UI/UX improvements

---

**Last Updated**: November 2025
**Maintained By**: Capgemini Discovery Agent Team
