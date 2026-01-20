import React, { useState } from "react";
import "./NewsComparison.css";

/**
 * NewsComparison Component
 * Main interface for fetching news and comparing execution strategies
 */
const NewsComparison = () => {
  const [loading, setLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsResult, setNewsResult] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [activeSection, setActiveSection] = useState("home");
  const [error, setError] = useState(null);

  const handleFetchNews = async () => {
    setNewsLoading(true);
    setError(null);
    try {
      console.log("Fetching news...");
      const response = await fetch(
        "http://127.0.0.1:8000/multi-agent/fetch-news",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log("News result:", data);
      setNewsResult(data);
      setActiveSection("news");
    } catch (error) {
      console.error("Error fetching news:", error);
      setError(`Failed to fetch news: ${error.message}`);
    } finally {
      setNewsLoading(false);
    }
  };

  const handleRunComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("Running comparison...");
      const response = await fetch(
        "http://127.0.0.1:8000/multi-agent/compare",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: "find latest technology news and create a formatted file",
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log("Comparison result:", data);
      setComparisonResult(data.comparison);
      setActiveSection("comparison");
    } catch (error) {
      console.error("Error running comparison:", error);
      setError(`Failed to run comparison: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="news-comparison-container">
      {/* Header */}
      <header className="nc-header">
        <div className="nc-header-content">
          <div className="nc-logo">
            <span className="nc-logo-icon">🚀</span>
            <h1>Multi-Agent Execution Platform</h1>
          </div>
          <p className="nc-subtitle">
            Compare LINEAR vs HIERARCHICAL MCP execution
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="nc-main">
        {/* Home / Action Buttons */}
        {activeSection === "home" && (
          <div className="nc-home">
            <div className="nc-welcome">
              <h2>Welcome to the Multi-Agent Orchestrator</h2>
              <p>
                This platform demonstrates how agents can fetch news and compare
                execution strategies
              </p>
            </div>

            {error && (
              <div className="nc-error-box">
                <span className="nc-error-icon">❌</span>
                <p>{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="nc-error-close"
                >
                  ✕
                </button>
              </div>
            )}

            <div className="nc-action-buttons">
              {/* Fetch News Button */}
              <button
                onClick={handleFetchNews}
                disabled={newsLoading}
                className="nc-btn nc-btn-primary nc-btn-large nc-btn-fetch"
              >
                <span className="nc-btn-icon">📰</span>
                <span className="nc-btn-text">
                  {newsLoading ? "Fetching News..." : "Fetch Latest News"}
                </span>
                <span className="nc-btn-desc">
                  Get Bollywood & Pop Culture news with execution flow
                </span>
              </button>

              {/* Run Comparison Button */}
              <button
                onClick={handleRunComparison}
                disabled={loading}
                className="nc-btn nc-btn-secondary nc-btn-large nc-btn-compare"
              >
                <span className="nc-btn-icon">⚡</span>
                <span className="nc-btn-text">
                  {loading ? "Running Comparison..." : "Run Comparison"}
                </span>
                <span className="nc-btn-desc">
                  Compare LINEAR vs HIERARCHICAL execution strategies
                </span>
              </button>
            </div>

            {/* Info Cards */}
            <div className="nc-info-grid">
              <div className="nc-info-card">
                <h3>📰 Fetch News</h3>
                <p>
                  Spawns MCP-capable agents that fetch latest news from multiple
                  sources, format it beautifully, and save to a file. Watch the
                  execution timeline in real-time.
                </p>
              </div>

              <div className="nc-info-card">
                <h3>⚡ Compare Execution</h3>
                <p>
                  Runs the same task using LINEAR (sequential) and HIERARCHICAL
                  (optimized) execution strategies. See which is faster and how
                  agents communicate with MCP servers.
                </p>
              </div>

              <div className="nc-info-card">
                <h3>🤖 Agent Spawning</h3>
                <p>
                  LLM-powered agents are dynamically created based on task
                  requirements. Each agent has access to Browser, Filesystem,
                  and GitHub MCP servers.
                </p>
              </div>

              <div className="nc-info-card">
                <h3>📊 Metrics & Visualization</h3>
                <p>
                  See detailed execution logs, agent spawning, task
                  dependencies, data flows, and performance metrics for both
                  execution strategies.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* News Results */}
        {activeSection === "news" && newsResult && (
          <NewsResultsView result={newsResult} />
        )}

        {/* Comparison Results */}
        {activeSection === "comparison" && comparisonResult && (
          <ComparisonView result={comparisonResult} />
        )}
      </main>

      {/* Navigation Footer */}
      <footer className="nc-footer">
        <button
          onClick={() => setActiveSection("home")}
          className={`nc-nav-btn ${activeSection === "home" ? "active" : ""}`}
        >
          🏠 Home
        </button>
        {newsResult && (
          <button
            onClick={() => setActiveSection("news")}
            className={`nc-nav-btn ${activeSection === "news" ? "active" : ""}`}
          >
            📰 News Results
          </button>
        )}
        {comparisonResult && (
          <button
            onClick={() => setActiveSection("comparison")}
            className={`nc-nav-btn ${activeSection === "comparison" ? "active" : ""}`}
          >
            ⚡ Comparison Results
          </button>
        )}
      </footer>
    </div>
  );
};

/**
 * News Results View Component
 */
const NewsResultsView = ({ result }) => {
  const [expandedLog, setExpandedLog] = useState(true);

  if (!result.success) {
    return (
      <div className="nc-results-container">
        <div className="nc-error-section">
          <h2>❌ Error Fetching News</h2>
          <p>{result.error}</p>
          {result.execution_logs && (
            <div className="nc-logs-container">
              <h3>Execution Logs:</h3>
              <div className="nc-logs">
                {result.execution_logs.map((log, idx) => (
                  <div key={idx} className="nc-log-line">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="nc-results-container">
      <div className="nc-results-header">
        <h2>✅ News Fetch Complete</h2>
        <p>Fetched and formatted {result.news_count} news items</p>
      </div>

      {/* Execution Timeline */}
      <section className="nc-section nc-timeline-section">
        <h3>
          <span className="nc-section-icon">⏱️</span> Execution Flow Timeline
        </h3>

        <div className="nc-execution-timeline">
          {result.execution_logs?.map((log, idx) => {
            const match = log.match(/\[(.*?)\]\s*\[(.*?)\]\s*(.*)/);
            const timestamp = match?.[1] || "";
            const component = match?.[2] || "";
            const message = match?.[3] || "";

            const isSuccess = message.includes("✅");
            const isError = message.includes("❌");
            const isWarning = message.includes("⚠️");

            return (
              <div
                key={idx}
                className={`nc-timeline-item ${isSuccess ? "success" : isError ? "error" : isWarning ? "warning" : ""}`}
              >
                <div className="nc-timeline-time">
                  {timestamp.split(" ")[1]}
                </div>
                <div className="nc-timeline-component">{component}</div>
                <div className="nc-timeline-message">{message}</div>
              </div>
            );
          })}
        </div>

        <div className="nc-metrics-summary">
          <div className="nc-metric">
            <div className="nc-metric-label">Total Time</div>
            <div className="nc-metric-value">
              {result.total_time_ms?.toFixed(2)}ms
            </div>
          </div>
          <div className="nc-metric">
            <div className="nc-metric-label">News Items</div>
            <div className="nc-metric-value">{result.news_count}</div>
          </div>
          <div className="nc-metric">
            <div className="nc-metric-label">Agents</div>
            <div className="nc-metric-value">{result.agents?.length}</div>
          </div>
          <div className="nc-metric">
            <div className="nc-metric-label">File</div>
            <div className="nc-metric-value">
              {result.file_path?.split("\\").pop()}
            </div>
          </div>
        </div>
      </section>

      {/* Agents */}
      <section className="nc-section">
        <h3>
          <span className="nc-section-icon">🤖</span> Spawned Agents
        </h3>
        <div className="nc-agents-grid">
          {result.agents?.map((agent, idx) => (
            <div key={idx} className="nc-agent-card">
              <h4>{agent.name}</h4>
              <div className="nc-agent-detail">
                <span className="nc-label">Role:</span>
                <span className="nc-badge">{agent.role}</span>
              </div>
              <div className="nc-agent-detail">
                <span className="nc-label">Tools:</span>
                <span className="nc-badge">
                  {agent.available_tools?.length || 0}
                </span>
              </div>
              <div className="nc-agent-detail">
                <span className="nc-label">Completed Tasks:</span>
                <span className="nc-badge">{agent.completed_tasks || 0}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* News Content */}
      <section className="nc-section">
        <h3>
          <span className="nc-section-icon">📄</span> Formatted News Content
        </h3>
        <div className="nc-news-content">
          <pre>{result.formatted_content}</pre>
        </div>
      </section>

      {/* Data Flow */}
      {result.data_flow && (
        <section className="nc-section">
          <h3>
            <span className="nc-section-icon">🔄</span> Data Flow
          </h3>
          <div className="nc-dataflow-grid">
            {result.data_flow.data_flows?.slice(0, 6).map((flow, idx) => (
              <div key={idx} className="nc-dataflow-item">
                <div className="nc-flow-source">
                  {flow.source?.slice(0, 12)}
                </div>
                <div className="nc-flow-arrow">→</div>
                <div className="nc-flow-target">{flow.target}</div>
                <div className="nc-flow-tool">{flow.tool}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

/**
 * Comparison View Component
 */
const ComparisonView = ({ result }) => {
  const linear = result.linear;
  const hierarchical = result.hierarchical;

  const linearTime = linear?.metrics?.total_time_ms || 0;
  const hierarchicalTime = hierarchical?.metrics?.total_time_ms || 0;
  const isFaster = hierarchicalTime < linearTime;
  const timeSaved = Math.abs(linearTime - hierarchicalTime);
  const percentSaved = linearTime
    ? ((timeSaved / linearTime) * 100).toFixed(2)
    : 0;

  return (
    <div className="nc-results-container">
      <div className="nc-results-header">
        <h2>⚡ Execution Comparison</h2>
        <p>LINEAR vs HIERARCHICAL Strategy Analysis</p>
      </div>

      {/* Comparison Cards */}
      <section className="nc-section nc-comparison-cards">
        <div className="nc-strategy-card nc-strategy-linear">
          <h3>📊 LINEAR Execution</h3>
          <div className="nc-card-metric">
            <span className="nc-label">Total Time:</span>
            <span className="nc-value">{linearTime}ms</span>
          </div>
          <div className="nc-card-metric">
            <span className="nc-label">Completed Tasks:</span>
            <span className="nc-value">
              {linear?.metrics?.completed_tasks}/{linear?.metrics?.total_tasks}
            </span>
          </div>
          <div className="nc-card-metric">
            <span className="nc-label">Agents Spawned:</span>
            <span className="nc-value">{linear?.agents?.length}</span>
          </div>
          <div className="nc-card-metric">
            <span className="nc-label">Tool Invocations:</span>
            <span className="nc-value">
              {Object.keys(linear?.metrics?.tool_invocations || {}).length}
            </span>
          </div>
        </div>

        <div className="nc-strategy-card nc-strategy-hierarchical">
          <h3>⚡ HIERARCHICAL Execution</h3>
          <div className="nc-card-metric">
            <span className="nc-label">Total Time:</span>
            <span className="nc-value">{hierarchicalTime}ms</span>
          </div>
          <div className="nc-card-metric">
            <span className="nc-label">Completed Tasks:</span>
            <span className="nc-value">
              {hierarchical?.metrics?.completed_tasks}/
              {hierarchical?.metrics?.total_tasks}
            </span>
          </div>
          <div className="nc-card-metric">
            <span className="nc-label">Agents Spawned:</span>
            <span className="nc-value">{hierarchical?.agents?.length}</span>
          </div>
          <div className="nc-card-metric">
            <span className="nc-label">Tool Invocations:</span>
            <span className="nc-value">
              {
                Object.keys(hierarchical?.metrics?.tool_invocations || {})
                  .length
              }
            </span>
          </div>
        </div>
      </section>

      {/* Analysis */}
      <section className="nc-section nc-analysis-section">
        <h3>📈 Comparative Analysis</h3>
        <div className="nc-analysis-card">
          <div className="nc-analysis-item">
            <span className="nc-label">Faster Strategy:</span>
            <span className="nc-value highlight">
              {isFaster ? "⚡ HIERARCHICAL" : "📊 LINEAR"}
            </span>
          </div>
          <div className="nc-analysis-item">
            <span className="nc-label">Time Saved:</span>
            <span className="nc-value">
              {timeSaved}ms ({percentSaved}%)
            </span>
          </div>
          <div className="nc-recommendation">
            <p>
              <strong>Recommendation:</strong>{" "}
              {isFaster
                ? "Use HIERARCHICAL execution for better performance on complex, dependent tasks."
                : "Use LINEAR execution for simpler, independent tasks."}
            </p>
          </div>
        </div>
      </section>

      {/* Timeline Bars */}
      <section className="nc-section">
        <h3>📊 Execution Timeline</h3>
        <div className="nc-timeline-bars">
          <div className="nc-bar-item">
            <div className="nc-bar-label">LINEAR</div>
            <div className="nc-bar-container">
              <div
                className="nc-bar nc-bar-linear"
                style={{
                  width: `${(linearTime / Math.max(linearTime, hierarchicalTime)) * 100}%`,
                }}
              >
                {linearTime}ms
              </div>
            </div>
          </div>
          <div className="nc-bar-item">
            <div className="nc-bar-label">HIERARCHICAL</div>
            <div className="nc-bar-container">
              <div
                className="nc-bar nc-bar-hierarchical"
                style={{
                  width: `${(hierarchicalTime / Math.max(linearTime, hierarchicalTime)) * 100}%`,
                }}
              >
                {hierarchicalTime}ms
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Agents */}
      <section className="nc-section">
        <h3>🤖 Agents Comparison</h3>
        <div className="nc-agents-comparison">
          <div className="nc-agents-column">
            <h4>LINEAR Agents</h4>
            <div className="nc-agents-list">
              {linear?.agents?.map((agent, idx) => (
                <div key={idx} className="nc-agent-item">
                  <span>{agent.name}</span>
                  <span className="nc-role">{agent.role}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="nc-agents-column">
            <h4>HIERARCHICAL Agents</h4>
            <div className="nc-agents-list">
              {hierarchical?.agents?.map((agent, idx) => (
                <div key={idx} className="nc-agent-item">
                  <span>{agent.name}</span>
                  <span className="nc-role">{agent.role}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Data Flow Comparison */}
      <section className="nc-section">
        <h3>🔄 Data Flow Comparison</h3>
        <div className="nc-dataflow-comparison">
          <div className="nc-flow-column">
            <h4>LINEAR Data Flow</h4>
            <div className="nc-dataflow-items">
              {linear?.data_flow?.data_flows?.slice(0, 4).map((flow, idx) => (
                <div key={idx} className="nc-dataflow-item-small">
                  {flow.source?.slice(0, 8)} → {flow.target}
                </div>
              ))}
            </div>
          </div>
          <div className="nc-flow-column">
            <h4>HIERARCHICAL Data Flow</h4>
            <div className="nc-dataflow-items">
              {hierarchical?.data_flow?.data_flows
                ?.slice(0, 4)
                .map((flow, idx) => (
                  <div key={idx} className="nc-dataflow-item-small">
                    {flow.source?.slice(0, 8)} → {flow.target}
                  </div>
                ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default NewsComparison;
