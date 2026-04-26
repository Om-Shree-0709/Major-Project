// src/components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from "react";
import { 
  LuBot, LuUser, LuGlobe, LuFolder, LuGitBranch,
  LuArrowRight, LuLoader, LuChevronDown, 
  LuChevronRight, LuAlignLeft, LuCloud, LuTerminal, LuMonitor, LuSettings
} from "react-icons/lu";
import "./ChatInterface.css";
import Settings from "./Settings";

const TraceBlock = ({ call }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="tool-trace-block">
      <div className="tool-trace-header" onClick={() => setExpanded(!expanded)}>
        <div className="tool-trace-header-left">
          <span className="tool-server-badge">{call.tool ? call.tool.split('.')[0] : "tool"}</span>
          <span className="tool-name-text">{call.tool || "unknown_tool"}</span>
        </div>
        <div className="tool-chevron">
          {expanded ? <LuChevronDown size={14} /> : <LuChevronRight size={14} />}
        </div>
      </div>
      {expanded && (
        <div className="tool-trace-body">
          {JSON.stringify(call.args || call, null, 2)}
        </div>
      )}
    </div>
  );
};

const ChatInterface = () => {
  const [showSettings, setShowSettings] = useState(false);
  const [activeProvider, setActiveProvider] = useState("Groq · llama-3.3-70b");
  
  const [showSandboxToast, setShowSandboxToast] = useState(false);
  const [sandboxPathInput, setSandboxPathInput] = useState("");
  const [fullSettings, setFullSettings] = useState({});

  useEffect(() => {
    console.log("[ChatInterface] Fetching /settings...")
    fetch("http://127.0.0.1:8000/settings")
      .then(r => r.json())
      .then(data => {
        console.log("[ChatInterface] Settings received:", data)
        setFullSettings(data);
      })
      .catch(err => console.error("[ChatInterface] Failed to load settings:", err.message));

    console.log("[ChatInterface] Fetching /health...")
    fetch("http://127.0.0.1:8000/health")
      .then(r => r.json())
      .then(data => {
        console.log("[ChatInterface] Health data received:", data)
        if (data?.llm?.providers?.length > 0) {
          setActiveProvider(data.llm.providers[0]);
        }
      })
      .catch(err => console.error("[ChatInterface] Failed to load health:", err.message));
  }, []);

  const handleSaveSandbox = async () => {
    if (!sandboxPathInput.trim()) return;
    const newSettings = { ...fullSettings, sandbox_path: sandboxPathInput.trim() };
    try {
      const resp = await fetch("http://127.0.0.1:8000/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newSettings)
      });
      if (resp.ok) {
        setShowSandboxToast(false);
        setFullSettings(newSettings);
      }
    } catch (e) {
      console.error("[ChatInterface] Failed to save sandbox path:", e.message);
    }
  };

  const [messages, setMessages] = useState([
    {
      id: "system-1",
      sender: "system",
      text: "Hello. I'm your MCP Agent. I can access the web, filesystem, and GitHub to assist you with tasks.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle clear chat
  const handleClearChat = () => {
    setMessages([{
      id: "system-1",
      sender: "system",
      text: "Hello. I'm your MCP Agent. I can access the web, filesystem, and GitHub to assist you with tasks.",
    }]);
  };

  // Send Query
  const sendQuery = async (queryText) => {
    const text = queryText || input;
    if (!text.trim()) return;

    // Add user message
    const userMsg = {
      id: `msg-${Date.now()}`,
      sender: "user",
      text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        user_query: text,
        session_id: "session-" + Date.now(),
      }
      console.log("[ChatInterface] Sending query:", text.slice(0, 50))
      
      // Call backend /query endpoint
      const response = await fetch("http://127.0.0.1:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        console.error("[ChatInterface] Query request failed with status:", response.status)
        throw new Error("Backend error");
      }

      const data = await response.json();
      console.log("[ChatInterface] Query response received. Tool calls:", data.tool_calls_executed?.length || 0)

      let answerText = data.final_answer || "No answer generated";
      if (
        answerText.toLowerCase().includes("file") ||
        answerText.toLowerCase().includes("created") ||
        answerText.toLowerCase().includes("saved")
      ) {
        answerText += "\n\nFiles are saved to: `backend/mcp_sandbox/`";
      }

      const agentMsg = {
        id: `msg-${Date.now()}`,
        sender: "agent",
        text: answerText,
        toolCalls: data.tool_calls_executed || [],
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (error) {
      console.error("[ChatInterface] Query request error:", error.message)
      const errorMsg = {
        id: `msg-${Date.now()}`,
        sender: "agent",
        text: `Error: ${error.message}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery();
  };

  return (
    <div className="chat-layout">
      {showSandboxToast && (
        <div className="sandbox-toast">
          <div className="toast-content">
            <LuFolder size={20} color="var(--accent-blue)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>Workspace Location Required</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.4' }}>
                The agent tried to access the file system, but no sandbox location is set. Where should files be stored?
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
            <input 
              type="text" 
              value={sandboxPathInput} 
              onChange={e => setSandboxPathInput(e.target.value)} 
              placeholder="e.g. C:\MyProjects\Workspace"
              className="field-input"
              style={{ flex: 1 }}
            />
            <button className="save-btn" onClick={handleSaveSandbox} style={{ padding: '0 16px' }}>
              Save
            </button>
            <button className="icon-btn" onClick={() => setShowSandboxToast(false)}>
              <LuX size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="header-left">
            <div className="header-logo"><LuAlignLeft size={16} /></div>
            <div className="header-title">MCP Agent</div>
          </div>
          <div className="header-right">
            <div className="status-dot"></div>
            <div className="status-text">Connected</div>
          </div>
        </div>

        <div className="sidebar-content">
          <div>
            <div className="sidebar-section-title">TOOLS</div>
            <div className="sidebar-tools-list">
              {fullSettings.browser_enabled !== false && (
                <div className="tool-list-item" onClick={() => setInput("Search for the latest news about AI and machine learning")} title="Click to test">
                  <span className="tool-list-icon"><LuGlobe size={16} /></span>
                  <span>Browser Search</span>
                </div>
              )}
              {fullSettings.filesystem_enabled !== false && (
                <div className="tool-list-item" onClick={() => setInput("Create a file called hello.txt with the content: Hello from MCP Agent!")} title="Click to test">
                  <span className="tool-list-icon"><LuFolder size={16} /></span>
                  <span>File System</span>
                </div>
              )}
              {fullSettings.github_enabled !== false && (
                <div className="tool-list-item" onClick={() => setInput("List all my GitHub repositories")} title="Click to test">
                  <span className="tool-list-icon"><LuGitBranch size={16} /></span>
                  <span>GitHub</span>
                </div>
              )}
              {fullSettings.weather_enabled !== false && (
                <div className="tool-list-item" onClick={() => setInput("What is the current weather in Mumbai?")} title="Click to test">
                  <span className="tool-list-icon"><LuCloud size={16} /></span>
                  <span>Weather</span>
                </div>
              )}
              {fullSettings.code_runner_enabled !== false && (
                <div className="tool-list-item" onClick={() => setInput("Run this Python code: print('Hello from Code Runner!'); print(2 + 2)")} title="Click to test">
                  <span className="tool-list-icon"><LuTerminal size={16} /></span>
                  <span>Code Runner</span>
                </div>
              )}
              {fullSettings.system_info_enabled !== false && (
                <div className="tool-list-item" onClick={() => setInput("What files are in my sandbox and what is the system info?")} title="Click to test">
                  <span className="tool-list-icon"><LuMonitor size={16} /></span>
                  <span>System Info</span>
                </div>
              )}
            </div>
          </div>
          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
            <button
              onClick={() => setShowSettings(true)}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)' }}
            >
              <LuSettings size={14} />
              Settings
            </button>

            <button
              onClick={handleClearChat}
              disabled={loading}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)' }}
            >
              Clear Chat
            </button>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="model-info">{activeProvider}</div>
        </div>
      </aside>

      {showSettings ? (
        <Settings onBack={() => {
          setShowSettings(false);
          fetch("http://127.0.0.1:8000/settings")
            .then(r => r.json())
            .then(data => setFullSettings(data))
            .catch(err => console.error("Failed to refresh settings:", err));
        }} />
      ) : (
        /* Main Chat Area */
        <main className="chat-container">
          {/* Messages */}
          <div className="messages-area">
            {messages.map((msg) => (
              <div key={msg.id} className={`message message-${msg.sender}`}>
                <div className="message-avatar-circle">
                  {msg.sender === "user" ? <LuUser size={16} /> : <LuBot size={16} />}
                </div>
                <div className="message-body">
                  <div className="message-label">
                    {msg.sender === "user" ? "You" : "MCP Agent"}
                  </div>
                  <div className="message-text">{msg.text}</div>

                  {/* Tool Calls */}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="tool-traces-container">
                      {msg.toolCalls.map((call, idx) => (
                        <TraceBlock key={idx} call={call} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message message-system">
                <div className="message-avatar-circle">
                  <LuBot size={16} />
                </div>
                <div className="message-body">
                  <div className="message-label">MCP Agent</div>
                  <div className="loading-row">
                    <LuLoader size={14} className="spin" />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="input-form">
            <form className="input-container" onSubmit={handleSubmit}>
              <input
                type="text"
                className="input-field"
                placeholder="Ask me anything..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className={`send-btn ${input.trim() && !loading ? 'active' : ''}`}
                disabled={loading || !input.trim()}
              >
                <LuArrowRight size={16} />
              </button>
            </form>
          </div>
        </main>
      )}
    </div>
  );
};

export default ChatInterface;
