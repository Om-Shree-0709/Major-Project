// src/components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from "react";
import "./ChatInterface.css";

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: "system-1",
      sender: "system",
      text: "👋 Hey! I'm your MCP Orchestrator. Ask me to fetch Bollywood news or any other query. I can access web, files, and GitHub.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, showComparison]);

  // Fetch Bollywood News
  const handleFetchNews = async () => {
    const query = "Fetch the latest Bollywood and pop culture news";
    await sendQuery(query);
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

      // Add agent response
      let answerText = data.final_answer || "No answer generated";

      // If answer mentions file creation, add helpful note
      if (
        answerText.toLowerCase().includes("file") ||
        answerText.toLowerCase().includes("created") ||
        answerText.toLowerCase().includes("saved")
      ) {
        answerText += "\n\n📁 Files are saved to: `backend/mcp_sandbox/`";
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
        text: `❌ Error: ${error.message}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  // Handle form submit
  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery();
  };

  // Run Comparison
  const handleRunComparison = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/multi-agent/compare",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query:
              "fetch latest technology and bollywood news and create a formatted file",
          }),
        },
      );

      if (!response.ok) throw new Error("Comparison failed");

      const data = await response.json();
      setComparison(data.comparison);
      setShowComparison(true);
    } catch (error) {
      const errorMsg = {
        id: `msg-${Date.now()}`,
        sender: "agent",
        text: `❌ Comparison Error: ${error.message}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-layout">
      {/* Left Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-icon">⚙️</span>
          <h2>Tools</h2>
        </div>

        <div className="sidebar-actions">
          <button
            className="action-btn action-btn-primary"
            onClick={handleFetchNews}
            disabled={loading}
          >
            <span className="btn-icon">📰</span>
            <span className="btn-text">Fetch Bollywood News</span>
          </button>

          <button
            className="action-btn action-btn-secondary"
            onClick={handleRunComparison}
            disabled={loading}
          >
            <span className="btn-icon">⚡</span>
            <span className="btn-text">Run Comparison</span>
          </button>
        </div>

        <div className="sidebar-info">
          <h3>About</h3>
          <p>This is a Multi-Agent MCP Orchestrator that can:</p>
          <ul>
            <li>🌐 Browse the web</li>
            <li>📁 Access files</li>
            <li>🔗 Interact with GitHub</li>
            <li>⚡ Compare execution strategies</li>
          </ul>

          <h3 style={{ marginTop: "1rem" }}>📂 File Storage</h3>
          <p style={{ fontSize: "0.8rem", color: "#64748b" }}>
            All files created by the orchestrator are saved in:
          </p>
          <code
            style={{
              display: "block",
              background: "#0f172a",
              padding: "0.5rem",
              borderRadius: "0.375rem",
              fontSize: "0.75rem",
              marginTop: "0.5rem",
              color: "#a5f3fc",
              wordBreak: "break-all",
            }}
          >
            backend/mcp_sandbox/
          </code>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-container">
        {showComparison && comparison ? (
          <ComparisonView
            comparison={comparison}
            onBack={() => setShowComparison(false)}
          />
        ) : (
          <>
            {/* Messages */}
            <div className="messages-area">
              {messages.map((msg) => (
                <div key={msg.id} className={`message message-${msg.sender}`}>
                  <div className="message-avatar">
                    {msg.sender === "user"
                      ? "👤"
                      : msg.sender === "system"
                        ? "🤖"
                        : "🔧"}
                  </div>
                  <div className="message-content">
                    <div className="message-text">{msg.text}</div>

                    {/* Tool Calls */}
                    {msg.toolCalls && msg.toolCalls.length > 0 && (
                      <div className="tool-calls">
                        <div className="tool-label">Tool Calls:</div>
                        {msg.toolCalls.map((call, idx) => (
                          <div key={idx} className="tool-item">
                            <code>{call.tool}</code>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message message-system">
                  <div className="message-avatar">🔄</div>
                  <div className="message-content">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="input-form">
              <input
                type="text"
                className="input-field"
                placeholder="Ask me anything... or use the buttons"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={loading || !input.trim()}
              >
                {loading ? "..." : "→"}
              </button>
            </form>
          </>
        )}
      </main>
    </div>
  );
};

/**
 * Comparison View Component
 */
const ComparisonView = ({ comparison, onBack }) => {
  const linear = comparison.linear;
  const hierarchical = comparison.hierarchical;

  const linearTime = linear?.metrics?.total_time_ms || 0;
  const hierarchicalTime = hierarchical?.metrics?.total_time_ms || 0;
  const timeDiff = Math.abs(linearTime - hierarchicalTime);
  const faster = hierarchicalTime < linearTime ? "HIERARCHICAL" : "LINEAR";

  return (
    <div className="comparison-view">
      <button className="back-btn" onClick={onBack}>
        ← Back to Chat
      </button>

      <h1>⚡ Execution Strategy Comparison</h1>

      {/* Metrics Comparison */}
      <section className="comparison-section">
        <h2>📊 Performance Metrics</h2>

        <div className="metrics-grid">
          <div className="metric-card metric-linear">
            <h3>📊 LINEAR</h3>
            <div className="metric-row">
              <span>Time:</span>
              <strong>{linearTime}ms</strong>
            </div>
            <div className="metric-row">
              <span>Tasks:</span>
              <strong>
                {linear?.metrics?.completed_tasks}/
                {linear?.metrics?.total_tasks}
              </strong>
            </div>
            <div className="metric-row">
              <span>Agents:</span>
              <strong>{linear?.agents?.length || 0}</strong>
            </div>
          </div>

          <div className="metric-card metric-hierarchical">
            <h3>⚡ HIERARCHICAL</h3>
            <div className="metric-row">
              <span>Time:</span>
              <strong>{hierarchicalTime}ms</strong>
            </div>
            <div className="metric-row">
              <span>Tasks:</span>
              <strong>
                {hierarchical?.metrics?.completed_tasks}/
                {hierarchical?.metrics?.total_tasks}
              </strong>
            </div>
            <div className="metric-row">
              <span>Agents:</span>
              <strong>{hierarchical?.agents?.length || 0}</strong>
            </div>
          </div>
        </div>

        <div className="winner-box">
          <strong>🏆 Winner: {faster}</strong> (Faster by {timeDiff}ms)
        </div>
      </section>

      {/* Tool Calls Diagram */}
      <section className="comparison-section">
        <h2>🔧 Tool Calls (LINEAR)</h2>
        <div className="diagram">
          <ToolCallDiagram toolCalls={linear?.metrics?.tool_invocations} />
        </div>
      </section>

      <section className="comparison-section">
        <h2>🔧 Tool Calls (HIERARCHICAL)</h2>
        <div className="diagram">
          <ToolCallDiagram
            toolCalls={hierarchical?.metrics?.tool_invocations}
          />
        </div>
      </section>

      {/* Data Flow */}
      <section className="comparison-section">
        <h2>🔄 Data Flow (LINEAR)</h2>
        <div className="data-flow">
          <DataFlowDiagram flows={linear?.data_flow?.data_flows} />
        </div>
      </section>

      <section className="comparison-section">
        <h2>🔄 Data Flow (HIERARCHICAL)</h2>
        <div className="data-flow">
          <DataFlowDiagram flows={hierarchical?.data_flow?.data_flows} />
        </div>
      </section>
    </div>
  );
};

/**
 * Tool Call Diagram Component
 */
const ToolCallDiagram = ({ toolCalls }) => {
  if (!toolCalls || Object.keys(toolCalls).length === 0) {
    return <div className="empty-diagram">No tool calls recorded</div>;
  }

  return (
    <div className="tool-diagram">
      {Object.entries(toolCalls).map(([tool, count], idx) => (
        <div key={tool} className="tool-flow-item">
          <div className="tool-name">{tool}</div>
          <div className="tool-arrow">→</div>
          <div className="tool-count">{count}x</div>
        </div>
      ))}
    </div>
  );
};

/**
 * Data Flow Diagram Component - Arrow format like markdown
 */
const DataFlowDiagram = ({ flows }) => {
  if (!flows || flows.length === 0) {
    return <div className="empty-diagram">No data flows recorded</div>;
  }

  return (
    <div className="data-flow-diagram">
      {flows.slice(0, 5).map((flow, idx) => (
        <div key={idx} className="flow-line">
          <code className="flow-source">{flow.source?.substring(0, 8)}</code>
          <span className="flow-arrow">→</span>
          <code className="flow-target">{flow.target}</code>
          <span className="flow-tool">({flow.tool})</span>
        </div>
      ))}
      {flows.length > 5 && (
        <div className="flow-more">... and {flows.length - 5} more flows</div>
      )}
    </div>
  );
};

export default ChatInterface;
