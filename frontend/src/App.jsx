import React, { useState, useEffect, useCallback } from "react";
import {
  Send,
  Cpu,
  BookOpen,
  GitBranch,
  Terminal,
  MoreVertical,
  Sparkles,
  LayoutGrid,
} from "lucide-react";
import "./App.css"; // Import the plain CSS file

// Pointing to Localhost Backend
const API_URL = "http://127.0.0.1:8000/query";

// --- Helpers ---
const formatJson = (jsonString) => {
  try {
    const obj =
      typeof jsonString === "string" ? JSON.parse(jsonString) : jsonString;
    return JSON.stringify(obj, null, 2);
  } catch (e) {
    return String(jsonString);
  }
};

const getToolIcon = (toolName) => {
  if (toolName.includes("filesystem")) return <BookOpen size={16} />;
  if (toolName.includes("browser")) return <Terminal size={16} />;
  if (toolName.includes("github")) return <GitBranch size={16} />;
  return <Cpu size={16} />;
};

const App = () => {
  const [messages, setMessages] = useState([
    {
      sender: "system",
      text: 'Welcome to the B.Tech MCP Agent Host. Enter a query (e.g., "list files in my directory" or "browse https://www.google.com").',
      toolCalls: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState(false);

  // --- Backend Health Check ---
  const checkBackendStatus = useCallback(async () => {
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: "status check",
          session_id: "health-check",
        }),
      });
      setIsBackendOnline(response.ok);
    } catch (error) {
      setIsBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    checkBackendStatus();
    const interval = setInterval(checkBackendStatus, 5000);
    return () => clearInterval(interval);
  }, [checkBackendStatus]);

  // --- Send Message ---
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    // Optimistic UI update
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: userQuery, toolCalls: [] },
    ]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: userQuery,
          session_id: "session-1",
        }),
      });

      if (!response.ok) throw new Error("Backend Error");

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: data.final_answer,
          toolCalls: data.tool_calls_executed || [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "agent", text: `Error: ${error.message}`, toolCalls: [] },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="brand">
          <Cpu className="brand-icon" size={28} />
          <span className="brand-text">MCP Host Agent</span>
        </div>
        <div
          className={`status-pill ${
            isBackendOnline ? "status-online" : "status-offline"
          }`}
        >
          Backend Status: {isBackendOnline ? "Online" : "Offline"}
        </div>
      </header>

      {/* Chat Scroll Area */}
      <div className="chat-area">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message-card ${
              msg.sender === "user" ? "user-msg" : ""
            }`}
          >
            <div className="message-header">
              <span>{msg.sender === "user" ? "You" : "Agent Host"}</span>
              {msg.sender === "agent" && <Cpu size={14} />}
            </div>
            <div className="message-content">{msg.text}</div>

            {/* Tool Execution Visualization */}
            {msg.toolCalls && msg.toolCalls.length > 0 && (
              <div className="tool-trace-container">
                <div className="tool-trace-header">
                  <Cpu size={14} /> Tool Execution Trace
                </div>
                {msg.toolCalls.map((call, i) => (
                  <div key={i} className="tool-item">
                    <div className="tool-name">
                      {getToolIcon(call.tool)} {call.tool}
                    </div>
                    <pre className="json-block">{formatJson(call.result)}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="message-card" style={{ opacity: 0.7 }}>
            <div className="message-content">Thinking...</div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-wrapper">
        <form onSubmit={handleSend} className="input-bar">
          <input
            type="text"
            className="text-input"
            placeholder="Ask the AI to read a file, browse the web, or check GitHub..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!isBackendOnline}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!isBackendOnline || isLoading}
          >
            <Send size={16} /> Send Query
          </button>
        </form>
      </div>

      {/* Footer Text */}
      <div className="footer">
        Project Architecture: Host (React UI) connects to Orchestrator
        (FastAPI/Gemini) which calls specialized MCP Servers.
      </div>

      {/* Visual only: Floating Menu from screenshot */}
      <div className="fab-menu">
        <MoreVertical size={20} />
        <Sparkles size={20} />
        <LayoutGrid size={20} />
      </div>
    </div>
  );
};

export default App;
