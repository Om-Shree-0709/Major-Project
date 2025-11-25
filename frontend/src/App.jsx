import React, { useState, useEffect, useCallback } from "react";
import { Send, Cpu, BookOpen, GitBranch, Terminal } from "lucide-react";

// --- Configuration ---
// IMPORTANT: The backend host is typically at http://127.0.0.1:8000
// The API endpoint used by the UI is /query (and the docs are available at /docs).
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/query";

// --- Utility Functions ---

// Simple syntax highlighting for tool execution logs
const formatJson = (jsonString) => {
  try {
    const obj = JSON.parse(jsonString);
    return JSON.stringify(obj, null, 2);
  } catch (e) {
    return jsonString;
  }
};

// Map tool names to icons
const getToolIcon = (toolName) => {
  if (toolName.startsWith("filesystem"))
    return <BookOpen size={16} className="text-green-500" />;
  if (toolName.startsWith("browser"))
    return <Terminal size={16} className="text-blue-500" />;
  if (toolName.startsWith("github"))
    return <GitBranch size={16} className="text-purple-500" />;
  return <Cpu size={16} className="text-yellow-500" />;
};

const ChatMessage = ({ message }) => (
  <div className={`message ${message.sender === "user" ? "user" : ""}`}>
    <div className="meta">
      {message.sender === "user" ? "You" : "Agent Host"}
    </div>
    <p>{message.text}</p>

    {message.toolCalls && message.toolCalls.length > 0 && (
      <div
        style={{
          marginTop: 12,
          borderTop: "1px solid #eef2f6",
          paddingTop: 12,
        }}
      >
        <h3
          style={{
            fontSize: 13,
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Cpu size={18} style={{ color: "#ef4444" }} />
          Tool Execution Trace:
        </h3>
        {message.toolCalls.map((call, index) => (
          <div
            key={index}
            style={{
              background: "#fafafa",
              padding: 10,
              borderRadius: 8,
              border: "1px solid #eceff4",
              marginTop: 8,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                fontSize: 13,
                color: "#4f46e5",
                fontWeight: 600,
              }}
            >
              {getToolIcon(call.tool)}
              <span style={{ marginLeft: 8 }}>{call.tool}</span>
            </div>
            <pre
              style={{
                fontSize: 12,
                color: "#0f172a",
                background: "#ffffff",
                padding: 8,
                borderRadius: 6,
                overflowX: "auto",
                marginTop: 8,
              }}
            >
              {formatJson(JSON.stringify(call.result, null, 2))}
            </pre>
          </div>
        ))}
      </div>
    )}
  </div>
);

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
  const [isBackendOnline, setIsBackendOnline] = useState(true);

  // Function to ping the backend to check if it's running
  const checkBackendStatus = useCallback(async () => {
    try {
      // Using a non-existent session ID for a quick status check
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: "host status check",
          session_id: "status",
        }),
      });
      // We just need the status code 200 (OK) to confirm the API is up
      if (response.ok) {
        setIsBackendOnline(true);
      } else {
        setIsBackendOnline(false);
      }
    } catch (error) {
      setIsBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    checkBackendStatus();
    // Set up an interval to check status every 5 seconds
    const interval = setInterval(checkBackendStatus, 5000);
    return () => clearInterval(interval); // Cleanup on component unmount
  }, [checkBackendStatus]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    const sessionId = "session-" + Date.now();

    // 1. Add user message to chat
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: userQuery, toolCalls: [] },
    ]);
    setInput("");
    setIsLoading(true);

    try {
      // 2. Send query to the FastAPI Host
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_query: userQuery, session_id: sessionId }),
      });

      if (!response.ok) {
        // Read error message from the backend if available
        const errorText = await response.text();
        throw new Error(
          `HTTP error! Status: ${
            response.status
          }. Detail: ${errorText.substring(0, 100)}...`
        );
      }

      const data = await response.json();

      // 3. Add Agent Host response
      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: data.final_answer,
          toolCalls: data.tool_calls_executed,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: `ERROR: Failed to connect to backend or process query. Is the Python Host Server running at ${API_URL}? Details: ${error.message}`,
          toolCalls: [],
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      {/* Header and Status */}
      <header className="top-bar">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="logo-ic">
            <Cpu size={20} />
          </div>
          <div className="brand">MCP Host Agent</div>
        </div>
        <div
          className={
            "status-pill " +
            (isBackendOnline ? "status-online" : "status-offline")
          }
        >
          Backend Status: {isBackendOnline ? "Online" : "Offline"}
        </div>
      </header>

      {/* Chat Area */}
      <div className="chat-wrap">
        <div className="messages">
          {messages.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))}
          {isLoading && (
            <div className="self-start">
              <div className="p-3 bg-white rounded-xl shadow-md text-gray-500 flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-500"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Agent is thinking/executing tool...
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="input-area">
        <form onSubmit={handleSend} style={{ width: "100%" }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI to read a file, browse the web, or check GitHub..."
            className="text-input"
            disabled={isLoading}
          />

          <button
            type="submit"
            className={
              isLoading || !isBackendOnline
                ? "btn btn-disabled"
                : "btn btn-primary"
            }
            disabled={isLoading || !isBackendOnline}
          >
            <Send size={18} />
            <span style={{ marginLeft: 6 }}>Send Query</span>
          </button>
        </form>
      </div>

      {/* Footer / Notes */}
      <footer className="footer">
        Project Architecture: Host (React UI) connects to Orchestrator
        (FastAPI/Gemini) which calls specialized MCP Servers.
        <div style={{ marginTop: 6 }}>
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            Open server /docs
          </a>
        </div>
      </footer>
    </div>
  );
};

export default App;
