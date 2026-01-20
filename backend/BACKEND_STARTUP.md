# Backend Startup Guide

## Quick Start

### 1. Setup Environment

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# or source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the backend directory with:

```
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_pat_token
GITHUB_PAT=your_github_pat_token
```

### 3. Start the Backend Server

```bash
python server.py
```

The server will start on `http://127.0.0.1:8000` with automatic reload enabled.

## Testing

### Run All MCP Server Tests

```bash
python test_mcp_servers.py
```

This tests:

- **Filesystem MCP Server**: File read/write/management
- **Browser MCP Server**: Web search and website browsing
- **GitHub MCP Server**: Repository operations and code management

### Check API Key Status

```bash
python check_rate_limits.py
```

### Test All Available APIs

```bash
python test_all_apis.py
```

## Endpoints

### Health & Status

- `GET /` - Basic health check
- `GET /health` - Detailed health check
- `GET /swarm/status` - Swarm framework status and available personas

### Main Query Endpoint

- `POST /query` - Submit a query for the swarm to process

**Request Body:**

```json
{
  "user_query": "Your query here",
  "session_id": "optional_session_id"
}
```

**Response:**

```json
{
  "final_answer": "The processed answer",
  "tool_calls_executed": [
    {
      "server": "filesystem",
      "tool": "read_file",
      "result": {...}
    }
  ]
}
```

## Supported Query Types

The system automatically detects and handles:

1. **Simple Queries**: Single-step operations
   - "What is the weather?"
   - "Write a Python script for X"

2. **Research Queries**: Multi-step information gathering
   - "Search for the latest Python best practices"
   - "Find information about async programming"

3. **Code Implementation**: File system operations
   - "Create a new Python file with X functionality"
   - "Fix the bug in my code"

4. **Complex Queries**: Multi-persona coordination
   - "Research about async/await bugs, fix them in my code, and push to GitHub"
   - "Find the latest security vulnerability, implement a patch, and create a PR"

## Personas

The system uses three personas that work together:

### Manager (Orchestrator)

- Analyzes queries and breaks them into subtasks
- Coordinates between Researcher and Coder
- Ensures consistency and completeness

### Researcher (Search & Analysis)

- Uses Browser MCP Server for web searches
- Gathers and analyzes information
- Reports findings to the team

### Coder (Software Engineer)

- Uses Filesystem MCP Server for code operations
- Uses GitHub MCP Server for repository management
- Implements solutions and handles deployments

## Architecture

```
┌─────────────────────────────────────────┐
│        Frontend (React + Vite)          │
│       Displays chat & tool traces       │
└──────────────────┬──────────────────────┘
                   │ HTTP
                   ↓
┌──────────────────────────────────────────┐
│      Backend (FastAPI + Swarm Manager)   │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   Swarm Context & Multi-Persona    │ │
│  │   - Manager (Orchestrator)         │ │
│  │   - Researcher (Browser tools)     │ │
│  │   - Coder (File + GitHub tools)    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │    LLM Manager (Groq/GitHub/etc)   │ │
│  │    With automatic fallback         │ │
│  └────────────────────────────────────┘ │
└──────┬──────────────────────────────────┘
       │
       ├─────────────────┬──────────────────┬─────────────────┐
       ↓                 ↓                  ↓                 ↓
┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ Filesystem  │  │   Browser   │  │    GitHub    │  │ Rate Limits  │
│ MCP Server  │  │ MCP Server  │  │ MCP Server   │  │   Monitor    │
└─────────────┘  └─────────────┘  └──────────────┘  └──────────────┘
```

## Environment Variables

```
GROQ_API_KEY           # Groq API key (30 req/min free)
GITHUB_TOKEN           # GitHub Personal Access Token
GITHUB_PAT             # Alternative GitHub PAT name
GEMINI_API_KEY         # (Optional) Google Gemini API key
GOOGLE_API_KEY         # (Optional) Alternative Gemini key
```

## Troubleshooting

### Backend won't start

1. Check Python version (3.8+)
2. Verify all dependencies: `pip install -r requirements.txt`
3. Check for port 8000 already in use: `netstat -ano | findstr :8000`

### API key errors

1. Verify `.env` file exists and is readable
2. Check API key format and validity
3. Run `python check_rate_limits.py` to diagnose

### MCP server failures

1. Run `python test_mcp_servers.py` to test individual servers
2. Check sandbox directory exists: `mcp_sandbox/`
3. For GitHub: Verify PAT has required scopes (repo, read:user)

## Performance Tips

1. **Reduce iterations** for faster responses (edit `max_iterations` in server.py)
2. **Use cheaper models** - GitHub Models (GPT-4o-mini) is faster than Groq
3. **Cache results** - The swarm context remembers previous findings
4. **Batch operations** - Group related tasks together

## Development

### Adding a New Tool

1. Create a new MCP server class in a new file
2. Inherit from `IMCPExternalServer` (in mcp_core.py)
3. Implement `list_tools()` and `execute_tool()`
4. Register in `server.py`'s `load_servers()` function

### Extending Personas

Edit `PERSONAS` in `swarm_manager.py` to add new roles or modify prompts.

### Customizing the Workflow

Modify the `/query` endpoint in `server.py` to change:

- Task decomposition strategy
- Persona assignment logic
- Tool execution flow
