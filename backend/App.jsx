import React, { useState, useEffect, useCallback } from "react";
import { Send, Cpu, BookOpen, GitBranch, Terminal } from "lucide-react";

// --- Configuration ---
// IMPORTANT: This URL must match your FastAPI server host and port.
const API_URL = "http://127.0.0.1:8000/query";

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
  <div
    className={`p-4 rounded-xl shadow-lg mb-4 max-w-4xl mx-auto ${
      message.sender === "user"
        ? "bg-indigo-50/50 self-end"
        : "bg-white self-start"
    }`}
  >
    <div className="font-semibold text-gray-800">
      {message.sender === "user" ? "You" : "Agent Host"}
    </div>
    <p className="text-gray-600 whitespace-pre-wrap">{message.text}</p>

    {message.toolCalls && message.toolCalls.length > 0 && (
      <div className="mt-4 border-t pt-3 space-y-3">
        <h3 className="text-sm font-bold text-gray-700 flex items-center">
          <Cpu size={18} className="mr-2 text-red-500" />
          Tool Execution Trace:
        </h3>
        {message.toolCalls.map((call, index) => (
          <div
            key={index}
            className="bg-gray-50 p-3 rounded-lg border border-gray-200"
          >
            <div className="flex items-center text-sm font-medium mb-2 text-indigo-700">
              {getToolIcon(call.tool)}
              <span className="ml-2">{call.tool}</span>
            </div>
            <pre className="text-xs text-gray-800 bg-gray-100 p-2 rounded-md overflow-x-auto">
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
      await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: "host status check",
          session_id: "status",
        }),
      });
      setIsBackendOnline(true);
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
        throw new Error(`HTTP error! status: ${response.status}`);
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
    <div className="min-h-screen bg-gray-100 font-sans p-4 flex flex-col">
      {/* Header and Status */}
      <header className="py-4 px-6 bg-white shadow-md rounded-xl mb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center">
          <Cpu size={28} className="mr-2 text-indigo-600" />
          MCP Host Agent
        </h1>
        <div
          className={`px-3 py-1 text-sm font-medium rounded-full ${
            isBackendOnline
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          Backend Status: {isBackendOnline ? "Online" : "Offline"}
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-grow overflow-y-auto mb-4 p-4 space-y-4 flex flex-col max-w-5xl mx-auto w-full bg-gray-50/80 rounded-xl shadow-inner">
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

      {/* Input Area */}
      <div className="max-w-5xl mx-auto w-full bg-white p-4 rounded-xl shadow-2xl">
        <form onSubmit={handleSend} className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI to read a file, browse the web, or check GitHub..."
            className="flex-grow p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150"
            disabled={isLoading}
          />
          <button
            type="submit"
            className={`px-6 py-3 rounded-lg text-white font-semibold flex items-center transition duration-150 ${
              isLoading || !isBackendOnline
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-700 shadow-md hover:shadow-lg"
            }`}
            disabled={isLoading || !isBackendOnline}
          >
            <Send size={20} className="mr-2" />
            Send Query
          </button>
        </form>
      </div>

      {/* Footer / Notes */}
      <footer className="mt-4 text-center text-xs text-gray-500">
        Project Architecture: Host (React UI) connects to Orchestrator
        (FastAPI/Gemini) which calls specialized MCP Servers.
      </footer>
    </div>
  );
};

export default App;
