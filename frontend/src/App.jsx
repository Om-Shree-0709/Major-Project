// src/App.jsx
import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Send,
  Cpu,
  Terminal,
  FolderOpen,
  GitBranch,
  ChevronDown,
  ChevronRight,
  User,
  Activity,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/query";
const HEALTH_URL = "http://127.0.0.1:8000/health";

// --- Components ---

const ToolTrace = ({ tool, result }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getIcon = (name) => {
    if (name.includes("filesystem"))
      return <FolderOpen size={14} className="text-amber-500" />;
    if (name.includes("browser"))
      return <Terminal size={14} className="text-blue-500" />;
    if (name.includes("github"))
      return <GitBranch size={14} className="text-slate-800" />;
    return <Activity size={14} />;
  };

  const formatJson = (data) => {
    try {
      const obj = typeof data === "string" ? JSON.parse(data) : data;
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(data);
    }
  };

  return (
    <div className="tool-trace">
      <div className="tool-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="tool-info">
          {getIcon(tool)}
          <span>
            Used: <span style={{ fontFamily: "monospace" }}>{tool}</span>
          </span>
        </div>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </div>

      {isOpen && (
        <div className="tool-body">
          <pre className="code-block">{formatJson(result)}</pre>
        </div>
      )}
    </div>
  );
};

const Message = ({ msg }) => {
  const isUser = msg.sender === "user";

  return (
    <div className={`message-wrapper ${isUser ? "user" : "agent"}`}>
      <div className={`avatar ${isUser ? "user" : "agent"}`}>
        {isUser ? <User size={18} /> : <Cpu size={18} />}
      </div>

      <div className="message-content">
        <div className="message-sender">
          {isUser ? "You" : "Swarm Orchestrator"}
        </div>

        {msg.toolCalls?.length > 0 && (
          <div className="swarm-chain">
            <div className="swarm-label">Swarm Thought Process:</div>
            {msg.toolCalls.map((call, idx) => (
              <ToolTrace key={idx} tool={call.tool} result={call.result} />
            ))}
          </div>
        )}

        {msg.text && (
          <div className={`bubble ${isUser ? "user" : "agent"}`}>
            {msg.text}
          </div>
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [messages, setMessages] = useState([
    {
      sender: "system",
      text: "Hello! I am your Host MCP Server. I can access files, browse the web, and inspect GitHub repositories. How can I help you today?",
      toolCalls: [],
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const scrollRef = useRef(null);

  // --- HEALTH CHECK (ONE TIME) ---
  const checkBackendStatus = useCallback(async () => {
    try {
      const res = await fetch(HEALTH_URL);
      setIsBackendOnline(res.ok);
    } catch {
      setIsBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    checkBackendStatus();
  }, [checkBackendStatus]);

  // Auto scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();

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

      if (!response.ok) throw new Error("Backend connection failed");

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: data.final_answer,
          toolCalls: data.tool_calls_executed || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "agent", text: err.message, toolCalls: [] },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <header className="header">
        <div className="brand">
          <div className="brand-icon-wrapper">
            <Cpu size={24} />
          </div>
          <h1>Unified MCP Framework</h1>
        </div>

        <div
          className={`status-badge ${isBackendOnline ? "online" : "offline"}`}
        >
          <div className="status-dot"></div>
          {isBackendOnline ? "Systems Online" : "Connecting..."}
        </div>
      </header>

      <div className="chat-container" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <Message key={idx} msg={msg} />
        ))}

        {isLoading && (
          <div className="message-wrapper agent">
            <div className="avatar agent">
              <Cpu size={18} />
            </div>
            <div className="thinking">Processing Request...</div>
          </div>
        )}
      </div>

      <div className="input-area">
        <form onSubmit={handleSend} className="input-form">
          <input
            className="input-field"
            placeholder={
              isBackendOnline ? "Ask me anything..." : "Waiting for backend..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!isBackendOnline || isLoading}
          />

          <button
            type="submit"
            className="send-button"
            disabled={!isBackendOnline || isLoading || !input.trim()}
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;
