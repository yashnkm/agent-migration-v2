# PyTorch DLL Error Fix (Windows)

## 🐛 Error

```
[WinError 1114] A dynamic link library (DLL) initialization routine failed.
Error loading "...\torch\lib\c10.dll" or one of its dependencies.
```

## 🔍 Root Cause

The error occurs because:
1. `sentence-transformers` requires PyTorch
2. Default PyTorch includes CUDA (GPU) dependencies
3. CUDA DLLs fail to load on systems without proper GPU setup
4. Solution: Install PyTorch **CPU-only** version

## ✅ Fix Applied

Updated `requirements.txt` to install PyTorch CPU version:

```txt
# PyTorch CPU (required for sentence-transformers on Windows)
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.5.1+cpu
torchvision==0.20.1+cpu
```

## 🚀 How to Apply Fix

### Option 1: Reinstall Everything (Recommended)

```bash
# 1. Remove old torch if exists
pip uninstall torch torchvision torchaudio -y

# 2. Install from updated requirements
pip install -r requirements.txt
```

### Option 2: Install Just PyTorch CPU

```bash
# Uninstall old torch
pip uninstall torch torchvision torchaudio -y

# Install CPU version
pip install torch==2.5.1+cpu torchvision==0.20.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

### Option 3: One-liner

```bash
pip uninstall torch torchvision torchaudio -y && pip install torch==2.5.1+cpu torchvision==0.20.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

## 🧪 Verify Fix

After installation, test:

```python
# Test PyTorch
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CPU available: {torch.cpu.is_available()}")

# Test sentence-transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Sentence-transformers working!")
```

## 📊 Download Size

- **Before** (CUDA): ~2.5 GB
- **After** (CPU-only): ~150 MB

**Much smaller and faster to install!**

## 🎯 What This Fixes

✅ Local embeddings now work on Windows
✅ No GPU/CUDA required
✅ Smaller download size
✅ Faster installation
✅ Same functionality for CPU-based embedding

## 🔄 After Fix

Once installed, the RAG system will:
1. Try Gemini embeddings first
2. If quota exceeded → automatically fallback to local embeddings
3. Local embeddings will now work without DLL errors

## ⚠️ Important Notes

1. **CPU-only**: This is CPU version, no GPU acceleration
   - For embeddings, CPU is fast enough (5-10 seconds)
   - No GPU needed for this use case

2. **Windows-specific**: This fix is primarily for Windows
   - Linux/Mac usually don't have this issue
   - But CPU version works fine on all platforms

3. **Version compatibility**: torch 2.5.1+cpu is compatible with:
   - sentence-transformers 3.3.1
   - Python 3.8+
   - Windows 10/11

## 🎉 Expected Result

After applying fix and running app:

```
Creating RAG index with local embeddings...
Initializing local embeddings (all-MiniLM-L6-v2, 384d)...
This will download model on first use (~80MB)
Downloading model... [100%]
✓ Local embeddings initialized successfully
Creating vectorstore from 268 documents...
Using local embeddings...
✓ Vectorstore created successfully with local embeddings!
```

**No more DLL errors!** 🎊
