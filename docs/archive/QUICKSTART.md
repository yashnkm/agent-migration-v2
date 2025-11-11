# Quick Start Guide - Web UI

## What's New?

You can now analyze GitHub repositories through a **web interface**!

### Features:
- 🔗 Paste GitHub URL and analyze
- 🏢 Automatic domain discovery
- 🧠 On-demand business logic analysis per domain
- 📥 Export to JSON (PDF coming soon)
- 🎨 Clean, intuitive UI

---

## Setup (First Time)

### 1. Install Dependencies
```bash
# Activate virtual environment
venv\Scripts\activate

# Install new dependencies (includes Streamlit)
pip install -r requirements.txt
```

### 2. Set Up API Key (For Business Logic Analysis)
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

**Note**: Domain discovery works without API key. Business logic analysis requires API key.

### 3. Install Git (If Not Already Installed)
The system needs git to clone repositories.

- Windows: Download from https://git-scm.com/
- Mac: `brew install git`
- Linux: `sudo apt-get install git`

---

## How to Run

### Start the Web UI
```bash
streamlit run app.py
```

Your browser will automatically open to `http://localhost:8501`

---

## How to Use

### Step 1: Enter GitHub URL
Paste any public GitHub repository URL:
```
https://github.com/spring-projects/spring-petclinic
https://github.com/your-username/your-repo
```

### Step 2: Click "Analyze Repository"
The system will:
1. Clone the repository
2. Parse all Java files
3. Discover business domains
4. Show results

### Step 3: View Discovered Domains
For each domain, you'll see:
- Architecture (Entity, Controller, Service, Repository)
- Entity fields
- REST endpoints
- Complexity metrics

### Step 4: Analyze Business Logic (On-Demand)
Click **"Analyze Business Logic"** button on any domain to:
- Extract business rules
- Explain what each endpoint does
- Document business methods
- Show workflows

**This uses Claude AI** - requires API key in `.env` file

### Step 5: Export Results
Download analysis as JSON (PDF export coming soon)

---

## Example Workflow

```
1. Open web UI: streamlit run app.py

2. Paste URL: https://github.com/spring-projects/spring-petclinic

3. Click "Analyze Repository" → Wait ~30 seconds

4. See results:
   - Owner Domain
   - Pet Domain
   - Visit Domain
   - Vet Domain

5. Click "Analyze Business Logic" on Pet Domain

6. View extracted business rules:
   - Pet name is required
   - Pet must have owner
   - Birth date validation
   - etc.

7. Download JSON with all analysis
```

---

## What Gets Analyzed?

### Automatic (No API Key Needed):
✅ Domain discovery
✅ Architecture mapping
✅ Endpoint extraction
✅ Method cataloging
✅ Field extraction
✅ Complexity metrics

### On-Demand (Requires API Key):
🧠 Business logic explanation
🧠 Business rules extraction
🧠 Workflow documentation
🧠 Endpoint purpose analysis

---

## File Structure

```
├── app.py                          ← Streamlit web UI (NEW)
├── src/
│   ├── utils/
│   │   └── github_cloner.py        ← GitHub integration (NEW)
│   ├── domain_analyzer/
│   │   ├── domain_graph.py         ← Domain discovery
│   │   └── business_analyzer.py    ← Business logic analysis (NEW)
│   ├── parser/
│   │   ├── java_parser.py
│   │   └── relationship_extractor.py
│   └── knowledge_graph/
│       └── graph.py
└── requirements.txt                ← Updated with streamlit
```

---

## Troubleshooting

### "Git is not installed"
- Install git: https://git-scm.com/
- Restart terminal after installation

### "Clone timed out"
- Repository too large (> 5 minute clone time)
- Try a smaller repository

### "Business logic analysis failed"
- Check `.env` file has `ANTHROPIC_API_KEY`
- Verify API key is valid
- Check you have API credits

### "No domains found"
- Repository might not be Spring Boot
- No `@Entity` classes found
- Check if Java files are in standard structure

---

## Command Line Still Works!

Old way still available:
```bash
python src/analyze_domains.py path/to/local/project
```

New way (recommended):
```bash
streamlit run app.py
```

---

## What's Next?

Coming soon:
- PDF export with formatted reports
- Markdown export
- Cross-domain analysis
- Visual architecture diagrams
- Analysis history/database

---

## Summary

### Old System:
```bash
python src/analyze_domains.py local-folder
# → Console output + JSON
```

### New System:
```bash
streamlit run app.py
# → Web UI + GitHub + On-demand analysis + Export
```

**Much better!** 🎉
