# 🚀 Quick Reference Card

## Start Backend

```bash
cd backend
python server.py
# Server runs on http://127.0.0.1:8000
```

## Test Everything

```bash
# Test all MCP servers
python test_mcp_servers.py

# Check API keys and rate limits
python check_rate_limits.py

# Full API test
python test_all_apis.py

# Run interactive demo
python demo_usage.py
```

## Check Status

```bash
# Health check
curl http://127.0.0.1:8000/health

# Swarm framework status
curl http://127.0.0.1:8000/swarm/status
```

## Make a Query

```bash
# Simple HTTP request
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Your query here"}'

# Python
import requests
r = requests.post(
    "http://127.0.0.1:8000/query",
    json={"user_query": "Your query here"}
)
print(r.json())
```

## Query Examples

### Research

```
"Search for the latest Python security vulnerabilities in 2025"
"Find information about async programming best practices"
```

### Code

```
"Create a Python script that calculates fibonacci numbers"
"Write a class that implements a binary search tree"
```

### Complex (Multi-Persona)

```
"Research async bugs, fix them in code, and push to GitHub"
"Find security vulnerabilities, implement patch, create PR"
```

## Available Personas

| Persona        | Role              | Tools                    |
| -------------- | ----------------- | ------------------------ |
| **Manager**    | Orchestrator      | All (coordinates others) |
| **Researcher** | Search & Analysis | Browser MCP Server       |
| **Coder**      | Software Engineer | Filesystem & GitHub MCP  |

## MCP Servers & Tools

### Filesystem MCP (11 tools)

- `filesystem.read_file`
- `filesystem.write_file`
- `filesystem.list_dir`
- `filesystem.delete`
- And 7 more...

### Browser MCP (2 tools)

- `browser.search_web`
- `browser.browse_website`

### GitHub MCP (12 tools)

- `github.list_repos`
- `github.get_repo`
- `github.read_file`
- `github.create_pull_request`
- And 8 more...

## Environment Variables

```
GROQ_API_KEY              # Groq API
GITHUB_TOKEN              # GitHub PAT
GITHUB_PAT                # Alternative GitHub PAT
```

## Endpoints

| Endpoint        | Method | Purpose                     |
| --------------- | ------ | --------------------------- |
| `/`             | GET    | Basic health check          |
| `/health`       | GET    | Detailed health info        |
| `/swarm/status` | GET    | Framework & personas status |
| `/query`        | POST   | Submit a query              |

## File Structure

```
backend/
├── server.py              # Main FastAPI server
├── swarm_manager.py       # Multi-persona coordination
├── mcp_core.py           # MCP base classes
├── filesystem_server.py   # Filesystem MCP
├── browser_server.py      # Browser MCP
├── github_server.py       # GitHub MCP
├── test_mcp_servers.py    # Test suite
├── demo_usage.py          # Interactive demo
├── BACKEND_STARTUP.md     # Setup guide
├── REFACTORING_SUMMARY.md # What was done
└── mcp_sandbox/           # Sandboxed file operations
```

## Troubleshooting

### Backend won't start

```bash
# Check Python version (needs 3.8+)
python --version

# Install dependencies
pip install -r requirements.txt

# Check port 8000 is free
netstat -ano | findstr :8000
```

### API key errors

```bash
# Create .env file
echo GROQ_API_KEY=your_key > .env
echo GITHUB_TOKEN=your_token >> .env

# Test keys
python check_rate_limits.py
```

### MCP server errors

```bash
# Test individual servers
python test_mcp_servers.py

# Check sandbox exists
ls -la mcp_sandbox/
```

## Common Queries

```
"What is Python?"
→ Simple reasoning (no tools)

"Search for FastAPI tutorials"
→ Research query (Browser MCP)

"Create a Python file with class X"
→ Code query (Filesystem MCP)

"Research Python bugs, fix code, push to GitHub"
→ Complex query (All 3 servers + all personas)
```

## Performance Tips

1. Use shorter max_iterations for faster responses
2. GitHub Models (GPT-4o-mini) is faster than Groq
3. Keep queries focused and specific
4. Batch related operations together
5. Reuse session IDs to maintain context

## Key Files to Edit

| File               | Purpose                    |
| ------------------ | -------------------------- |
| `server.py`        | Query handling & endpoints |
| `swarm_manager.py` | Personas & task management |
| `.env`             | API keys                   |
| `requirements.txt` | Dependencies               |

## Logs

Backend logs to stdout with timestamps:

```
17:12:37 [INFO] 🚀 UNIFIED MCP FRAMEWORK
17:12:37 [INFO] ✅ Groq (Llama 3.3 70B)
17:12:37 [INFO] ✅ GitHub (GPT-4o-mini)
...
```

## Resources

- **Setup Guide:** See BACKEND_STARTUP.md
- **What Changed:** See REFACTORING_SUMMARY.md
- **Examples:** Run python demo_usage.py
- **Tests:** Run python test_mcp_servers.py

---

**Last Updated:** January 20, 2026  
**Status:** ✅ Production Ready
