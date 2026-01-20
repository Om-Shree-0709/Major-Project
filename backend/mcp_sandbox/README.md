# MCP Sandbox Directory

This directory (`backend/mcp_sandbox/`) is where all files created by the Multi-Agent MCP Orchestrator are stored.

## ✅ What Gets Stored Here

When you use the chatbot to:

- **Fetch news** → Creates files like `news.txt`, `news.md`
- **Create files** → All custom files created via `/query` endpoint
- **Use filesystem tools** → Any file write operations through the MCP filesystem server

## 📂 File Structure

```
backend/mcp_sandbox/
├── news.txt                 (Bollywood/pop culture news)
├── tech_news.txt           (Technology news)
├── use_cases.txt           (Use case documentation)
└── [other user files]      (Any files created through MCP)
```

## 🔍 How It Works

1. **Hardcoded Sandbox Path**: The filesystem server is configured to use this exact directory
2. **Relative Path Resolution**: All file paths are resolved relative to this sandbox
3. **Security**: Path traversal is blocked - files can only be created within this sandbox
4. **Automatic Creation**: The sandbox directory is created automatically if it doesn't exist

## 🛠️ Configuration

**File**: `backend/filesystem_server.py` (Line 18-20)

```python
BACKEND_DIR = Path(__file__).parent.resolve()
SANDBOX_DIR = (BACKEND_DIR / "mcp_sandbox").resolve()
```

This ensures that regardless of where the Python process is executed from, files are always saved to `backend/mcp_sandbox/`.

## ✨ Recent Fix

**Date**: January 20, 2026

**Issue**: Files were being created in unpredictable locations

**Solution**: Updated `filesystem_server.py` to use `Path(__file__).parent.resolve()` instead of relative paths

**Result**: All files now reliably save to `E:\Major Project\backend\mcp_sandbox\`

## 📝 Testing

To verify file creation is working:

```bash
cd backend
python test_sandbox_path.py
```

This will:

1. Create a test file in the sandbox
2. Read it back
3. Confirm the correct path

---

**All created files are safe and secure within this isolated sandbox directory!** 🔒
