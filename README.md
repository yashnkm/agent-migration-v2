# Java Codebase Analyzer 🔍

**Automatically analyze ANY Java codebase from GitHub with AI-powered framework detection and business logic extraction.**

## 🎯 Universal Framework Support

Works on **ANY Java framework**:
- ✅ Spring Boot
- ✅ Jakarta EE / JAX-RS
- ✅ Struts
- ✅ Micronaut
- ✅ Quarkus
- ✅ Play Framework
- ✅ Plain Java (no framework)
- ✅ Custom frameworks

**No hardcoding. Pure pattern recognition powered by Gemini 2.5 Flash.**

## ✨ Features

- 🔗 **GitHub Integration** - Analyze any public repository by URL
- 🤖 **AI Framework Detection** - Gemini 2.5 Flash identifies framework automatically
- 🏢 **Domain Discovery** - Automatically find all business entities
- 🏗️ **Architecture Mapping** - Map Controller → Service → Repository → Entity
- 🌐 **API Extraction** - Discover all REST endpoints (any framework)
- 🧠 **Business Logic Analysis** - AI-powered on-demand analysis per domain
- 📊 **Comprehensive Metrics** - Complexity scoring and statistics
- 📥 **Export Options** - JSON, PDF (coming soon), Markdown (coming soon)
- 🎨 **Web Interface** - Clean Streamlit UI

## 🚀 Quick Start

### 1. Install
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure (Required for AI features)
Create `.env` file:
```
CODEBASE_GEMINI_KEY=your_gemini_api_key_here
CODEBASE_GEMINI_MODEL=gemini-2.5-flash
```

Get your free API key: https://makersuite.google.com/app/apikey

### 3. Run
```bash
# New UI with framework detection (recommended)
streamlit run app_v2.py

# Or use the original UI
streamlit run app.py
```

### 4. Use
1. Open browser to `http://localhost:8501`
2. Paste GitHub URL
3. Click "Analyze Repository"
4. View discovered domains
5. Click "Analyze Business Logic" on any domain

## 📖 Example

```
Input: https://github.com/spring-projects/spring-petclinic

Output:
✓ Discovered 4 domains: Owner, Pet, Visit, Vet
✓ 15 REST endpoints
✓ 87 methods
✓ 23 entity fields

Click "Analyze Business Logic" on Pet domain:
→ Extracts business rules
→ Documents endpoints
→ Explains workflows
```

---

## 📁 Project Structure

```
├── app.py                    # Streamlit web UI (NEW)
├── src/
│   ├── utils/
│   │   └── github_cloner.py  # GitHub integration (NEW)
│   ├── domain_analyzer/
│   │   ├── domain_graph.py   # Domain discovery
│   │   └── business_analyzer.py  # Business logic AI (NEW)
│   ├── parser/
│   │   ├── java_parser.py    # Java code parser
│   │   └── relationship_extractor.py
│   └── knowledge_graph/
│       └── graph.py          # Core data structure
```

## 🛠️ Requirements

- Python 3.8+
- Git (for cloning repos)
- Google Gemini API key (free tier available, for AI features)

---

## 📚 Documentation

- **[Setup Guide](SETUP_GUIDE.md)** ⭐ - Complete setup with Gemini integration
- **[Quick Start](QUICKSTART.md)** - Fast start guide
- **[Framework-Agnostic Design](FRAMEWORK_AGNOSTIC_DESIGN.md)** - Architecture details
- **[Improved Architecture](IMPROVED_ARCHITECTURE.md)** - LLM integration design

---

## 🔄 Migration from CLI

### Old Way:
```bash
python src/analyze_domains.py local-folder
```

### New Way:
```bash
streamlit run app.py
# Paste GitHub URL in browser
```

Both still work! CLI is still available for local analysis.

## 🤝 How It Works

```
1. You paste GitHub URL
   ↓
2. System clones repository
   ↓
3. Parser extracts all code structure
   ↓
4. Domain discovery finds business entities
   ↓
5. Shows results in web UI
   ↓
6. You click "Analyze Business Logic" on any domain
   ↓
7. AI analyzes methods and extracts business rules
   ↓
8. Shows detailed analysis
   ↓
9. Download as JSON/PDF
```

---

## 💡 Examples

Try these repositories:
- `https://github.com/spring-projects/spring-petclinic` - Classic Spring Boot example
- `https://github.com/spring-guides/gs-rest-service` - Simple REST service
- Your own Spring Boot projects!

---

**Built with ❤️ to make codebase understanding automatic and easy**
