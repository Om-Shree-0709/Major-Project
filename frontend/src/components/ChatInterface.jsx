// src/components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from "react";
import { 
  LuBot, LuUser, LuGlobe, LuFolder, LuGitBranch,
  LuArrowRight, LuLoader, LuChevronDown, 
  LuChevronRight, LuAlignLeft 
} from "react-icons/lu";
import "./ChatInterface.css";

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
      // Call backend /query endpoint
      const response = await fetch("http://127.0.0.1:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: text,
          session_id: "session-" + Date.now(),
        }),
      });

      if (!response.ok) throw new Error("Backend error");

      const data = await response.json();

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
              <div className="tool-list-item">
                <span className="tool-list-icon"><LuGlobe size={16} /></span>
                <span>Browser Search</span>
              </div>
              <div className="tool-list-item">
                <span className="tool-list-icon"><LuFolder size={16} /></span>
                <span>File System</span>
              </div>
              <div className="tool-list-item">
                <span className="tool-list-icon"><LuGitBranch size={16} /></span>
                <span>GitHub</span>
              </div>
            </div>
          </div>
          <div style={{ marginTop: 'auto', marginBottom: '16px' }}>
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
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              Clear Chat
            </button>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="model-info">Groq · llama-3.3-70b</div>
        </div>
      </aside>

      {/* Main Chat Area */}
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
    </div>
  );
};

export default ChatInterface;
