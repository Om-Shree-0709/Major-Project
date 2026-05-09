# Major Project Report Draft: Unified MCP Framework

**Note to Student:** This is a comprehensive outline and initial draft based on your project's codebase (`Unified MCP Framework for Context-Aware AI Agents in Software Development`). It follows the exact guidelines provided in your images. You will need to copy this into MS Word and apply the specified formatting (Times New Roman, 1.5 spacing, specific font sizes, etc.).

---

## Preliminary Pages (To be added later)
* Cover Page (Use provided template)
* Certificate
* Declaration (Use provided template)
* Acknowledgement
* Table of Contents
* List of Tables
* List of Figures
* List of Abbreviations, Symbols or Nomenclature

---

## Abstract

As software development grows increasingly complex, developers often need to switch contexts between coding, web research, running terminal commands, and inspecting version control systems. Existing AI assistants typically lack dynamic, secure, and extensible integrations to handle these diverse tasks within a single ecosystem. This project presents a "Unified MCP Framework for Context-Aware AI Agents in Software Development," built upon the principles of the Model Context Protocol (MCP). The proposed system employs a client-server architecture, utilizing a React-based frontend for intuitive user interaction and tool trace visualization, and a FastAPI backend acting as the AI Orchestrator powered by the Google Gemini model. 

The framework is designed to securely route and execute natural language instructions across various integrated tools, including a restricted Filesystem Sandbox, a Playwright-powered Browser tool for real-time web search and extraction, and a GitHub tool for repository inspection. By constraining execution within a predefined sandbox and providing complete transparency of tool invocations on the frontend, the system addresses critical security and usability concerns. The result is a highly extensible, modular AI agent workspace that significantly reduces context switching and enhances developer productivity, laying the groundwork for more advanced autonomous software engineering tools.

---

## Chapter 1: Introduction

### 1.1 Introduction
The integration of Artificial Intelligence (AI) into software development has transitioned from simple code autocomplete features to complex agentic systems capable of reasoning and executing tasks. However, many current AI implementations remain isolated from the developer's broader workspace, unable to securely interact with the local filesystem or fetch real-time information from the web or version control systems. The Model Context Protocol (MCP) has emerged as a standardization effort to seamlessly connect AI models with external data sources and tools. This project, the "Unified MCP Framework," implements an orchestrator that leverages these principles to create a context-aware AI agent. By combining a robust backend (FastAPI) with a responsive frontend (React) and powerful AI capabilities (Google Gemini), the system can interpret complex user intents and execute them using specialized, sandboxed tools.

### 1.2 Problem Statement
Modern software engineering involves a high degree of context switching between Integrated Development Environments (IDEs), web browsers for documentation, and version control platforms like GitHub. Current Large Language Models (LLMs) operate in isolated environments and lack direct, secure access to these essential developer tools. When access is granted, it is often without strict security boundaries or execution transparency, leading to potential security risks (e.g., unauthorized file modifications) and a lack of user trust. Therefore, there is a critical need for a unified, secure framework that allows an AI agent to dynamically access filesystem operations, web search, and repository data while maintaining strict execution boundaries and providing transparent operational traces to the user.

### 1.3 Objectives
The primary objectives of this project are to:
1. Develop a robust AI Orchestrator using FastAPI and Google Gemini capable of interpreting natural language to dynamically select and invoke appropriate tools.
2. Implement a secure, sandboxed Filesystem Tool that restricts AI file operations (read/write/list) to a designated directory, preventing unauthorized system access.
3. Integrate a Browser Automation Tool using Playwright to enable real-time web research and content extraction for the AI agent.
4. Develop a GitHub Tool using PyGithub to allow the agent to inspect repositories, fetch file contents, and analyze project metadata.
5. Create a dynamic React frontend that provides a seamless chat interface and visualizes real-time tool traces (invocations, payloads, and AI explanations) to ensure transparency and user trust.

### 1.4 Significance and Motivation of the Project Work
The significance of this project lies in its potential to streamline the software development workflow. By bridging the gap between natural language reasoning and concrete tool execution, developers can delegate tedious tasks—such as boilerplate generation, documentation lookups, or repository analysis—directly to the AI agent. The motivation stems from the rapid advancement of agentic AI; creating a secure, standardized framework (inspired by MCP) ensures that as AI models become more capable, they have a safe and transparent environment in which to operate. The emphasis on sandboxing and trace visualization directly addresses industry concerns regarding AI safety and alignment.

### 1.5 Organization of Project Report
The remainder of this report is organized as follows: Chapter 2 reviews the existing literature and identifies key gaps in current AI agent frameworks. Chapter 3 details the system development, including requirements, architecture, and implementation specifics. Chapter 4 discusses the testing strategy and presents the test cases and outcomes. Chapter 5 evaluates the results and compares the framework with existing solutions. Finally, Chapter 6 concludes the project and outlines potential future scope.

---

## Chapter 2: Literature Survey

### 2.1 Overview of Relevant Literature
*(You will need to expand this section with actual research papers from IEEE, ACM, etc., focusing on the last 5 years. Look for papers on: Large Language Models in Software Engineering, AI Agents, Tool-augmented LLMs, Sandboxing for AI, and the Model Context Protocol.)*
Recent advancements in Natural Language Processing (NLP) have led to the development of tool-augmented LLMs. Models like GPT-4 and Gemini have demonstrated the ability to use external APIs to overcome limitations in their training data. Frameworks such as LangChain and AutoGPT have explored the concept of autonomous agents capable of breaking down complex tasks. Furthermore, research into AI safety emphasizes the necessity of isolated execution environments (sandboxes) to prevent malicious or accidental system damage by AI agents. The recent introduction of the Model Context Protocol (MCP) by Anthropic represents a significant step toward standardizing how AI models connect to data sources, providing a relevant architectural blueprint for this project.

### 2.2 Key Gaps in the Literature
While tool-augmented LLMs are heavily researched, there is a lack of cohesive frameworks that combine secure local filesystem access, web browsing, and version control integration into a single, transparent client-server architecture designed specifically for developer workflows. Many existing solutions either compromise on security by granting unrestricted system access or fail to provide adequate visibility into the agent's decision-making process (tool trace visualization). This project bridges that gap by enforcing strict sandboxing and prioritizing user transparency.

---

## Chapter 3: System Development

### 3.1 Requirements and Analysis
* **Functional Requirements:**
  * The system must accept natural language queries from the user.
  * The AI Orchestrator must select the correct tool (Filesystem, Browser, GitHub) based on the user's prompt.
  * The Filesystem tool must only operate within `mcp_sandbox/`.
  * The frontend must display the AI's response and the corresponding tool invocation payload.
* **Non-Functional Requirements:**
  * **Security:** Strict path validation to prevent directory traversal attacks.
  * **Performance:** Asynchronous execution of tools (especially Playwright) to prevent blocking the main server thread.
  * **Modularity:** Easy addition of new tools in the future.

### 3.2 Project Design and Architecture
The system employs a decoupled Client-Server architecture:
* **Frontend (Client):** Developed using React 19 and Vite. It manages the chat state, renders markdown responses, and visualizes tool traces.
* **Backend (Server):** Built with FastAPI. It handles API endpoints, orchestrates communication with the Google Gemini model, and manages tool execution.
* **AI Engine:** Google Generative AI is used for intent parsing and response generation.
* **Tools:**
  * *Filesystem Server:* Python `os` and `pathlib` for sandboxed I/O.
  * *Browser Server:* Playwright for headless browsing.
  * *GitHub Server:* PyGithub for API interactions.

*(Add an architecture diagram here in your final report)*

### 3.3 Data Preparation
*(As this is primarily a tool-integration project rather than a machine learning model training project, data preparation involves configuring environment variables, setting up the `mcp_sandbox` directory structure, and ensuring access tokens (GEMINI_API_KEY, GITHUB_PAT) are correctly injected into the environment.)*

### 3.4 Implementation
The implementation was carried out iteratively. 
**Key Technologies Used:** Python 3.8+, Node.js, React, FastAPI, Google Generative AI SDK, Playwright, PyGithub.

**Code Snippet: Filesystem Sandboxing Logic**
*(Include a snippet from `filesystem_server.py` showing how you prevent directory traversal using `os.path.abspath` and `startswith`)*

**Code Snippet: Tool Routing**
*(Include a snippet from `mcp_host_server.py` showing how the Gemini model is provided with tool schemas and how the response is parsed to trigger the correct Python function)*

### 3.5 Key Challenges
1. **Asynchronous Execution:** Managing Playwright's asynchronous browser operations within FastAPI, especially handling Windows event loop policy issues. This was resolved by configuring the specific event loop policy in `mcp_host_server.py`.
2. **Security Sandboxing:** Ensuring the AI could not access arbitrary files on the host machine required implementing strict path resolution and validation logic.
3. **State Management:** Maintaining conversation history and mapping tool executions to their respective chat turns on the React frontend.

---

## Chapter 4: Testing

### 4.1 Testing Strategy
The testing strategy involved Unit Testing for individual tools and Integration Testing for the full conversational flow. 
* **Manual Testing:** Used to verify the UI/UX, responsiveness of the React frontend, and accuracy of tool traces.
* **Security Testing:** Specifically targeting the Filesystem tool by attempting directory traversal attacks (e.g., trying to read `../.env`) to ensure the sandbox restrictions hold.

### 4.2 Test Cases and Outcomes
| Test Case ID | Description | Expected Outcome | Actual Outcome | Status |
|---|---|---|---|---|
| TC01 | System identifies web search intent | Browser Tool is invoked with correct query | Browser Tool invoked successfully | Pass |
| TC02 | Write file outside sandbox | Filesystem Tool rejects request | Access Denied error returned | Pass |
| TC03 | Write file inside sandbox | File is created with correct content | File created successfully | Pass |
| TC04 | Fetch GitHub Repo | GitHub Tool returns repo metadata | Metadata returned and parsed | Pass |

---

## Chapter 5: Results and Evaluation

### 5.1 Results
The developed Unified MCP Framework successfully processes natural language prompts, selects the appropriate tool, and returns accurate results. The frontend accurately reflects the agent's thought process and the raw JSON payloads of the tools used. The sandboxing mechanism effectively blocked all tested unauthorized access attempts.

### 5.2 Comparison with Existing Solutions
Compared to generalized AI assistants (like ChatGPT without plugins), this framework provides direct, local system interaction. Compared to raw auto-coding tools (like AutoGPT), this system provides much stronger security guarantees through its strict sandboxing and offers better user transparency through the visible tool trace UI.

---

## Chapter 6: Conclusions and Future Scope

### 6.1 Conclusion
This project successfully demonstrates the feasibility and utility of a context-aware AI agent framework tailored for software development. By integrating the Gemini model with a FastAPI orchestrator and a React frontend, the system bridges the gap between natural language understanding and practical tool execution. The successful implementation of sandboxed filesystem access, headless browsing, and GitHub integration proves that AI agents can be given powerful capabilities without compromising host system security.

### 6.2 Future Scope
1. **Additional Tools:** Integrating database access tools (SQL execution), Docker container management, and continuous integration (CI/CD) pipelines.
2. **Multi-Agent Orchestration:** Upgrading the backend to support multiple specialized agents communicating with each other to solve more complex software engineering tasks.
3. **Advanced UI:** Implementing a more IDE-like frontend with syntax highlighting, inline file editing, and direct terminal access.

---

## References
*(You will need to add at least 25 references in IEEE format. Include links to the FastAPI documentation, React documentation, Playwright docs, PyGithub docs, Google Gemini API docs, the Model Context Protocol specification, and relevant academic papers.)*

---

## Appendix
* **Appendix A:** Project Code Snippets (Full files or critical sections)
* **Appendix B:** User Manual (How to run the backend and frontend)
* **Appendix C:** Plagiarism Certificate (To be added later)
