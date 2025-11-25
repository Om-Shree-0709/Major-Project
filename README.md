# Major Project: Unified MCP Framework for Context-Aware AI Agents in Software Development

This project implements a full-stack AI Agent system inspired by the core principles of the **Model Context Protocol (MCP)**. It provides a unified architectural framework in which an AI Orchestrator can interpret natural language instructions, identify the appropriate tool to execute (Filesystem, Browser, GitHub), invoke that tool safely, and return structured results to a frontend chat interface. The project demonstrates a practical application of context-aware AI agents through a modern client–server architecture.

## Project Overview

**Architecture:**
The system follows a client–server model consisting of:

1. A **React frontend** responsible for user interaction, request submission, state display, and visualization of tool call traces.
2. A **FastAPI backend** acting as the AI Orchestrator, responsible for routing requests, determining tool usage, executing operations, and generating natural-language responses.

**AI Engine:**
The backend uses **Google Gemini** via the `google-generativeai` SDK for prompt interpretation, intent analysis, tool routing, and summarization.

**Objective:**
To build an extensible agent framework capable of handling developer-centric tasks such as file manipulation, web research, and repository inspection, while maintaining security, transparency, and modularity.

---

## Technology Stack

### Frontend

* **Framework:** React 19 with Vite for fast development and build performance
* **Styling:** Custom CSS using the Inter font family
* **Icons:** Lucide React
* **Networking:** REST API communication via `fetch`

### Backend

* **Framework:** FastAPI
* **Server Runner:** Uvicorn
* **AI Integration:** Google Generative AI SDK
* **Browser Automation:** Playwright (asynchronous)
* **GitHub Integration:** PyGithub
* **Security:** Filesystem sandboxing to restrict access to predefined directories

---

## Project Structure

```text
major-project/
├── backend/
│   ├── mcp_host_server.py       # Main FastAPI application; AI Orchestrator logic
│   ├── mcp_core.py              # Base interfaces for tools and tool execution
│   ├── filesystem_server.py     # Restricted file operations inside a sandbox
│   ├── browser_server.py        # Live web search and page extraction using Playwright
│   ├── github_server.py         # GitHub repository access and file inspection
│   ├── mcp_sandbox/             # Secure directory for all file operations
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main chat and UI logic
│   │   └── App.css              # Styling definitions
│   └── package.json             # Node.js dependencies
└── README.md
```

---

## Setup and Installation

### 1. Prerequisites

* Python 3.8 or higher
* Node.js and npm
* Google Gemini API key
* GitHub Personal Access Token (optional, required for GitHub tool)

### 2. Backend Setup

Navigate to the backend directory and configure the Python environment:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browser binaries:

```bash
playwright install chromium
```

#### Environment Configuration

Create a `.env` file inside the `backend/` directory:

```ini
GEMINI_API_KEY=your_google_gemini_api_key_here
GITHUB_PAT=your_github_personal_access_token_here
```

### 3. Frontend Setup

Navigate to the frontend directory and install required packages:

```bash
cd frontend
npm install
```

---

## Running the Application

The frontend and backend must be started separately.

### Start the Backend

```bash
uvicorn mcp_host_server:app --reload
```

The backend will run at:

```
http://127.0.0.1:8000
```

### Start the Frontend

```bash
npm run dev
```

The frontend interface will be available at:

```
http://localhost:5173
```

---

## Features and Capabilities

### 1. Intelligent Tool Selection

The backend Orchestrator uses Gemini to interpret natural language requests, determine whether a tool invocation is required, and decide which tool is best suited for the task.
Examples:

* “Summarize this GitHub repository.” → GitHub tool
* “Search for the latest cloud security news.” → Browser tool
* “Create a file named report.txt and write content inside it.” → Filesystem tool

### 2. Secure Filesystem Operations

The Filesystem Tool provides:

* Reading files
* Writing files
* Listing directories

All operations are strictly restricted to the `mcp_sandbox/` directory to prevent unauthorized system access. This approach is consistent with MCP’s emphasis on capability-limited tool execution.

### 3. Web Browsing and Search

The Browser Tool uses Playwright to:

* Perform Google-style search queries
* Visit live websites
* Extract visible text content from pages
* Return structured responses to the Orchestrator

This enables tasks such as real-time research, information gathering, or summarizing website content.

### 4. GitHub Repository Integration

Using PyGithub, the GitHub Tool can:

* List user repositories
* Fetch file contents
* Inspect repository metadata

This supports developer workflows such as reviewing documentation, checking code, or retrieving project details.

### 5. Tool Trace Visualization

The frontend displays:

* Tool invoked
* Raw JSON payload returned by the backend
* AI-generated explanation

This transparency helps users understand how the agent operates internally. It also mirrors the tool-call tracing behavior of MCP-compliant systems.

---

## Troubleshooting Guide

### Backend Not Responding

If the frontend displays “Backend Status: Offline,” ensure:

* The FastAPI server is running
* There are no runtime errors in the terminal
* Environment variables are correctly configured

### Playwright Browser Errors

If the Browser Tool fails:

* Verify that `playwright install chromium` was executed
* Ensure your system supports Playwright’s required dependencies
* On Windows, confirm the event loop policy fix in `mcp_host_server.py` is active

### Environment Issues on Windows

The project includes a Windows-specific event loop configuration to ensure Playwright’s asynchronous operations function correctly on the platform.
