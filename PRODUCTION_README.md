# 🚀 Unified MCP Framework - Production Setup

## ⚡ Quick Start (Windows)

### Backend Setup:
```bash
cd backend
setup.bat          # One-time setup
start.bat          # Start server
```

### Frontend Setup:
```bash
cd frontend
npm install        # One-time setup
npm run dev        # Start frontend
```

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** installed  
3. **API Keys** (FREE):
   - Groq API: https://console.groq.com/keys
   - GitHub Token: https://github.com/settings/tokens

## 🔑 Environment Setup

Create `backend/.env`:
```env
# Required - At least ONE
GROQ_API_KEY=gsk_your_key_here
GITHUB_TOKEN=ghp_your_token_here

# Optional
GITHUB_PAT=ghp_your_token_here
```

## 🎯 Usage

1. Start backend: `cd backend && start.bat`
2. Start frontend: `cd frontend && npm run dev`
3. Open: http://localhost:5173

## ✅ Verification

Test queries:
- "Create a file test.txt with Hello World"
- "Search for Python tutorials"
- "List my GitHub repos"

## 🛠️ Troubleshooting

### Backend won't start:
```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

### Frontend issues:
```bash
cd frontend
npm install
npm run dev
```

### Rate Limits:
- Groq: 30 requests/min (resets every 60s)
- GitHub: 15 requests/min (resets every 60s)
- Wait 1 minute if rate limited

## 📁 Project Structure

```
Major Project/
├── backend/
│   ├── server.py           ← MAIN SERVER
│   ├── mcp_core.py
│   ├── filesystem_server.py
│   ├── browser_server.py
│   ├── github_server.py
│   ├── swarm_manager.py
│   ├── requirements.txt
│   ├── .env
│   ├── start.bat
│   └── setup.bat
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

## 🎓 Features

✅ Multi-provider LLM (Groq + GitHub Models)
✅ Automatic fallback on rate limits
✅ File system operations (sandboxed)
✅ Web search capabilities
✅ GitHub repository access
✅ Tool execution transparency
✅ Clean, modern UI

## 📊 Performance

- Backend startup: ~2 seconds
- Query response: 2-5 seconds
- Tool execution: 1-3 seconds
- No continuous API calls

## 🆘 Support

Check logs in terminal for errors.
Common issues are usually:
1. Missing .env file
2. Wrong API keys
3. Virtual environment not activated
