import React, { useState, useEffect } from "react";
import "./MultiAgentComparison.css";

/**
 * MultiAgentComparison Component
 *
 * Visualizes:
 * 1. Linear vs Hierarchical execution comparison
 * 2. Data flow between agents and MCP servers
 * 3. Task dependencies and execution timing
 * 4. Agent spawning and tool invocations
 */
const MultiAgentComparison = () => {
  const [query, setQuery] = useState(
    "find all latest AI related news and create a file called news.md",
  );
  const [loading, setLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [newsResult, setNewsResult] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedExecution, setSelectedExecution] = useState("linear");

  const handleCompare = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/multi-agent/compare",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        },
      );
      const data = await response.json();
      setComparison(data.comparison);
    } catch (error) {
      console.error("Error:", error);
    }
    setLoading(false);
  };

  const handleFetchNews = async () => {
    setNewsLoading(true);
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/multi-agent/fetch-news",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      );
      const data = await response.json();
      setNewsResult(data);
      setActiveTab("news-results");
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to fetch news");
    }
    setNewsLoading(false);
  };

  const getStrategy = (strategyName) => {
    if (!comparison) return null;
    // server returns comparison with 'linear' and 'hierarchical' keys
    if (strategyName.toLowerCase() === "linear") return comparison.linear;
    if (strategyName.toLowerCase() === "hierarchical")
      return comparison.hierarchical;
    return null;
  };

  const linearData = getStrategy("LINEAR");
  const hierarchicalData = getStrategy("HIERARCHICAL");

  return (
    <div className="multi-agent-comparison">
      <div className="comparison-header">
        <h1>Multi-Agent Execution Comparison</h1>
        <p>
          Compare LINEAR vs HIERARCHICAL execution strategies for MCP server
          orchestration
        </p>
      </div>

      {/* Query Input & Action Buttons */}
      <div className="query-section">
        <div className="query-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a task query (e.g., search for AI news and create a file)..."
            className="query-input"
          />
          <button
            onClick={handleCompare}
            disabled={loading || !query}
            className="compare-btn"
            title="Compare LINEAR vs HIERARCHICAL execution strategies"
          >
            {loading ? "⏳ Comparing..." : "⚡ Run Comparison"}
          </button>
        </div>

        {/* Special Action Buttons */}
        <div className="action-buttons">
          <button
            onClick={handleFetchNews}
            disabled={newsLoading}
            className="fetch-news-btn"
            title="Fetch latest Bollywood & Pop Culture news and create file"
          >
            {newsLoading ? "📰 Fetching..." : "📰 Fetch Latest News"}
          </button>
        </div>
      </div>

      {comparison && (
        <>
          {/* Tabs */}
          <div className="tabs">
            <button
              className={`tab ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              📊 Overview
            </button>
            <button
              className={`tab ${activeTab === "linear" ? "active" : ""}`}
              onClick={() => setActiveTab("linear")}
            >
              📈 Linear Execution
            </button>
            <button
              className={`tab ${activeTab === "hierarchical" ? "active" : ""}`}
              onClick={() => setActiveTab("hierarchical")}
            >
              ⚡ Hierarchical Execution
            </button>
            <button
              className={`tab ${activeTab === "dataflow" ? "active" : ""}`}
              onClick={() => setActiveTab("dataflow")}
            >
              🔄 Data Flow
            </button>
          </div>

          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="tab-content overview">
              <div className="comparison-cards">
                <div className="card linear-card">
                  <h3>📊 Linear Execution</h3>
                  <div className="metric">
                    <span className="label">Total Time:</span>
                    <span className="value">
                      {linearData?.metrics.total_time_ms}ms
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Completed Tasks:</span>
                    <span className="value">
                      {linearData?.metrics.completed_tasks}/
                      {linearData?.metrics.total_tasks}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Tool Invocations:</span>
                    <span className="value">
                      {linearData?.metrics.tool_invocations}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Agents Spawned:</span>
                    <span className="value">
                      {linearData?.agents?.length || 0}
                    </span>
                  </div>
                </div>

                <div className="card hierarchical-card">
                  <h3>⚡ Hierarchical Execution</h3>
                  <div className="metric">
                    <span className="label">Total Time:</span>
                    <span className="value">
                      {hierarchicalData?.metrics.total_time_ms}ms
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Completed Tasks:</span>
                    <span className="value">
                      {hierarchicalData?.metrics.completed_tasks}/
                      {hierarchicalData?.metrics.total_tasks}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Tool Invocations:</span>
                    <span className="value">
                      {hierarchicalData?.metrics.tool_invocations}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Agents Spawned:</span>
                    <span className="value">
                      {hierarchicalData?.agents?.length || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Comparison Analysis */}
              <div className="comparison-analysis">
                <h3>Comparative Analysis</h3>
                <div className="analysis-row">
                  <div className="analysis-item">
                    <span className="label">Faster Strategy:</span>
                    <span className="value highlight">
                      {(() => {
                        if (!comparison) return "-";
                        const lt = linearData?.metrics?.total_time_ms || 0;
                        const ht =
                          hierarchicalData?.metrics?.total_time_ms || 0;
                        return lt <= ht ? "📊 Linear" : "⚡ Hierarchical";
                      })()}
                    </span>
                  </div>
                  <div className="analysis-item">
                    <span className="label">Time Savings:</span>
                    <span className="value">
                      {(() => {
                        const lt = linearData?.metrics?.total_time_ms || 0;
                        const ht =
                          hierarchicalData?.metrics?.total_time_ms || 0;
                        const diff = lt - ht;
                        const pct = lt ? (diff / lt) * 100 : 0;
                        return `${Math.abs(Math.round(diff))}ms (${Math.abs(pct).toFixed(2)}%)`;
                      })()}
                    </span>
                  </div>
                </div>
                <div className="recommendation">
                  <p>
                    <strong>Recommendation:</strong>{" "}
                    {(() => {
                      // Simple recommendation based on time
                      const lt = linearData?.metrics?.total_time_ms || 0;
                      const ht = hierarchicalData?.metrics?.total_time_ms || 0;
                      if (ht < lt)
                        return "Use Hierarchical for complex, dependent tasks.";
                      if (lt < ht)
                        return "Use Linear for simple sequential tasks.";
                      return "Both strategies perform similarly; choose based on task characteristics.";
                    })()}
                  </p>
                </div>
              </div>

              {/* Timeline Visualization */}
              <div className="timeline-section">
                <h3>Execution Timeline Comparison</h3>
                <div className="timeline">
                  <div className="timeline-item">
                    <div className="timeline-label">Linear</div>
                    <div className="timeline-bar">
                      <div
                        className="timeline-fill linear"
                        style={{
                          width: `${(linearData?.metrics.total_time_ms / 500) * 100}%`,
                        }}
                      >
                        {linearData?.metrics.total_time_ms}ms
                      </div>
                    </div>
                  </div>
                  <div className="timeline-item">
                    <div className="timeline-label">Hierarchical</div>
                    <div className="timeline-bar">
                      <div
                        className="timeline-fill hierarchical"
                        style={{
                          width: `${(hierarchicalData?.metrics.total_time_ms / 500) * 100}%`,
                        }}
                      >
                        {hierarchicalData?.metrics.total_time_ms}ms
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Linear Execution Tab */}
          {activeTab === "linear" && linearData && (
            <div className="tab-content execution-details">
              <ExecutionDetails execution={linearData} mode="linear" />
            </div>
          )}

          {/* Hierarchical Execution Tab */}
          {activeTab === "hierarchical" && hierarchicalData && (
            <div className="tab-content execution-details">
              <ExecutionDetails
                execution={hierarchicalData}
                mode="hierarchical"
              />
            </div>
          )}

          {/* Data Flow Tab */}
          {activeTab === "dataflow" && (
            <div className="tab-content dataflow">
              <h3>Data Flow Visualization</h3>
              <div className="dataflow-columns">
                <div className="dataflow-column">
                  <h4>Linear - Data Flows</h4>
                  <pre>{JSON.stringify(linearData?.data_flow, null, 2)}</pre>
                </div>
                <div className="dataflow-column">
                  <h4>Hierarchical - Data Flows</h4>
                  <pre>
                    {JSON.stringify(hierarchicalData?.data_flow, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* News Results Section */}
      {newsResult && (
        <div className="news-results-section">
          <div className="results-header">
            <h2>📰 News Fetch Results</h2>
            <button
              onClick={() => setNewsResult(null)}
              className="close-btn"
              title="Close"
            >
              ✕
            </button>
          </div>

          {newsResult.success ? (
            <>
              {/* Execution Timeline */}
              <div className="execution-timeline">
                <h3>⏱️ Execution Flow & Timeline</h3>
                <div className="timeline-steps">
                  {newsResult.execution_logs?.map((log, idx) => {
                    const match = log.match(/\[(.*?)\]\s*\[(.*?)\]\s*(.*)/);
                    const timestamp = match?.[1] || "";
                    const component = match?.[2] || "";
                    const message = match?.[3] || "";

                    return (
                      <div
                        key={idx}
                        className={`timeline-step ${
                          component === "COMPLETE" ? "complete" : ""
                        } ${message.includes("✅") ? "success" : ""} ${
                          message.includes("❌") ? "error" : ""
                        }`}
                      >
                        <div className="step-time">
                          {timestamp.split(" ")[1]}
                        </div>
                        <div className="step-component">
                          <span className="component-tag">{component}</span>
                        </div>
                        <div className="step-message">{message}</div>
                      </div>
                    );
                  })}
                </div>

                <div className="execution-summary">
                  <div className="summary-stat">
                    <span className="stat-label">Total Execution Time:</span>
                    <span className="stat-value">
                      {newsResult.total_time_ms?.toFixed(2)}ms
                    </span>
                  </div>
                  <div className="summary-stat">
                    <span className="stat-label">News Items Fetched:</span>
                    <span className="stat-value">{newsResult.news_count}</span>
                  </div>
                  <div className="summary-stat">
                    <span className="stat-label">Agents Spawned:</span>
                    <span className="stat-value">
                      {newsResult.agents?.length}
                    </span>
                  </div>
                  <div className="summary-stat">
                    <span className="stat-label">File Path:</span>
                    <span className="stat-value" title={newsResult.file_path}>
                      {newsResult.file_path?.split("\\").pop()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Formatted News Content */}
              <div className="news-content">
                <h3>📄 Formatted News Content</h3>
                <div className="markdown-preview">
                  <pre>{newsResult.formatted_content}</pre>
                </div>
              </div>

              {/* Agents & Data Flow */}
              <div className="agents-dataflow">
                <h3>🤖 Agents & Data Flow</h3>
                <div className="agents-summary">
                  {newsResult.agents?.map((agent, idx) => (
                    <div key={idx} className="agent-summary-card">
                      <h5>{agent.name}</h5>
                      <div className="agent-detail">
                        <span className="label">Role:</span>
                        <span className="badge">{agent.role}</span>
                      </div>
                      <div className="agent-detail">
                        <span className="label">Tools:</span>
                        <span className="count">
                          {agent.available_tools?.length || 0}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {newsResult.data_flow && (
                  <div className="dataflow-summary">
                    <h4>Data Flows</h4>
                    <div className="dataflow-items">
                      {newsResult.data_flow.data_flows
                        ?.slice(0, 5)
                        .map((flow, idx) => (
                          <div key={idx} className="dataflow-item">
                            <span className="flow-source">
                              {flow.source?.slice(0, 8)}
                            </span>
                            <span className="flow-arrow">→</span>
                            <span className="flow-target">{flow.target}</span>
                            <span className="flow-tool">{flow.tool}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="error-message">
              <p>❌ Error: {newsResult.error}</p>
              {newsResult.execution_logs &&
                newsResult.execution_logs.length > 0 && (
                  <div className="error-logs">
                    <h4>Execution Logs:</h4>
                    <ul>
                      {newsResult.execution_logs.map((log, idx) => (
                        <li key={idx}>{log}</li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          )}
        </div>
      )}

      {!comparison && !loading && !newsResult && (
        <div className="empty-state">
          <p>👋 Welcome! Choose an action:</p>
          <ul style={{ marginTop: "15px" }}>
            <li>
              📊 Enter a query and click "Run Comparison" to see LINEAR vs
              HIERARCHICAL execution
            </li>
            <li>
              📰 Click "Fetch Latest News" to fetch and create a formatted news
              file
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

/**
 * ExecutionDetails Component
 * Shows detailed information about an execution strategy
 */
const ExecutionDetails = ({ execution, mode }) => {
  return (
    <div className="execution-details-container">
      {/* Agents Spawned */}
      <section className="agents-section">
        <h3>🤖 Agents Spawned ({execution.agents?.length || 0})</h3>
        <div className="agents-grid">
          {execution.agents?.map((agent, idx) => (
            <div key={idx} className="agent-card">
              <h4>{agent.name}</h4>
              <div className="agent-info">
                <div className="info-row">
                  <span className="label">Role:</span>
                  <span
                    className="badge"
                    style={{ backgroundColor: getRoleColor(agent.role) }}
                  >
                    {agent.role}
                  </span>
                </div>
                <div className="info-row">
                  <span className="label">ID:</span>
                  <span className="value">{agent.id?.slice(0, 8)}</span>
                </div>
                <div className="info-row">
                  <span className="label">Tasks:</span>
                  <span className="value">{agent.tasks_assigned || 0}</span>
                </div>
              </div>
              {agent.tools && agent.tools.length > 0 && (
                <div className="tools-list">
                  <span className="tools-label">Tools:</span>
                  {agent.tools.slice(0, 3).map((tool, i) => (
                    <span key={i} className="tool-badge">
                      {tool.split(".")[1]}
                    </span>
                  ))}
                  {agent.tools.length > 3 && (
                    <span className="tool-badge">
                      +{agent.tools.length - 3}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Tasks Created */}
      <section className="tasks-section">
        <h3>📋 Tasks Created ({execution.tasks?.length || 0})</h3>
        <div className="tasks-list">
          {execution.tasks?.map((task, idx) => (
            <div key={idx} className="task-item">
              <div className="task-header">
                <span className="task-num">Step {idx + 1}</span>
                <span className="task-desc">{task.description}</span>
                <span className={`task-status ${task.status?.toLowerCase()}`}>
                  {task.status || "pending"}
                </span>
              </div>
              {task.execution_time && (
                <div className="task-time">⏱️ {task.execution_time}ms</div>
              )}
              {task.dependencies && task.dependencies.length > 0 && (
                <div className="task-deps">
                  Dependencies: {task.dependencies.join(" → ")}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Metrics */}
      <section className="metrics-section">
        <h3>📊 Metrics</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">
              {execution.metrics?.total_time_ms}ms
            </div>
            <div className="metric-label">Total Time</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">
              {execution.metrics?.average_task_time_ms}ms
            </div>
            <div className="metric-label">Avg Task Time</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">
              {execution.metrics?.completed_tasks}/
              {execution.metrics?.total_tasks}
            </div>
            <div className="metric-label">Success Rate</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">
              {execution.metrics?.tool_invocations}
            </div>
            <div className="metric-label">Tool Calls</div>
          </div>
        </div>
      </section>

      {/* Execution Plan */}
      {execution.execution_plan && (
        <section className="plan-section">
          <h3>📍 Execution Plan</h3>
          <div className="execution-flow">
            {execution.execution_plan.map((step, idx) => (
              <React.Fragment key={idx}>
                <div className="flow-step">{step}</div>
                {idx < execution.execution_plan.length - 1 && (
                  <div className="flow-arrow">↓</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

/**
 * DataFlowVisualization Component
 * Shows how data flows between agents and MCP servers
 */
const DataFlowVisualization = ({
  linearFlow,
  hierarchicalFlow,
  comparison,
}) => {
  const [selectedFlow, setSelectedFlow] = useState("linear");

  const currentFlow = selectedFlow === "linear" ? linearFlow : hierarchicalFlow;

  return (
    <div className="dataflow-container">
      <div className="dataflow-selector">
        <button
          className={`flow-btn ${selectedFlow === "linear" ? "active" : ""}`}
          onClick={() => setSelectedFlow("linear")}
        >
          Linear Data Flow
        </button>
        <button
          className={`flow-btn ${selectedFlow === "hierarchical" ? "active" : ""}`}
          onClick={() => setSelectedFlow("hierarchical")}
        >
          Hierarchical Data Flow
        </button>
      </div>

      {currentFlow && (
        <>
          {/* Agent Flows */}
          <section className="flow-section">
            <h3>🔄 Agent Data Flows</h3>
            <div className="flows-grid">
              {(currentFlow.data_flows || []).map((flow, idx) => (
                <div key={idx} className="flow-item">
                  <div className="flow-source">{flow.source}</div>
                  <div className="flow-arrow">→</div>
                  <div className="flow-target">{flow.target}</div>
                  <div className="flow-data">
                    {flow.type} ({flow.tool})
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Server Interactions */}
          <section className="flow-section">
            <h3>🖥️ MCP Server Interactions</h3>
            <div className="server-interactions">
              {(
                (currentFlow.data_flows || []).map((f) => ({
                  agent: f.source,
                  server: f.target === "mcp_server" ? "MCP Server" : f.target,
                  tool: f.tool,
                  status: "ok",
                })) || []
              ).map((interaction, idx) => (
                <div key={idx} className="interaction-item">
                  <div className="interaction-agent">{interaction.agent}</div>
                  <div className="interaction-server">{interaction.server}</div>
                  <div className="interaction-tool">{interaction.tool}</div>
                  <div className="interaction-status">{interaction.status}</div>
                </div>
              ))}
            </div>
          </section>

          {/* Task Dependencies */}
          {currentFlow.task_dependencies &&
            currentFlow.task_dependencies.length > 0 && (
              <section className="flow-section">
                <h3>📊 Task Dependency Graph</h3>
                <div className="dependency-graph">
                  {currentFlow.task_dependencies.map((dep, idx) => (
                    <div key={idx} className="dependency-item">
                      <span className="task-id">{dep.task_id}</span>
                      <span className="dependency-arrow">→</span>
                      <span className="task-id">
                        {dep.dependencies?.join(", ") || "-"}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}
        </>
      )}
    </div>
  );
};

/**
 * Helper function to get role badge color
 */
function getRoleColor(role) {
  const colors = {
    RESEARCHER: "#4A90E2",
    DEVELOPER: "#7B68EE",
    ANALYST: "#50C878",
    EXECUTOR: "#FF6B6B",
    ORCHESTRATOR: "#FFD700",
  };
  return colors[role] || "#808080";
}

export default MultiAgentComparison;
