import React, { useState, useEffect } from "react"
import {
  LuSettings, LuCheck, LuX, LuToggleLeft,
  LuToggleRight, LuEye, LuEyeOff, LuRefreshCw,
  LuTrash2, LuSave, LuChevronDown, LuChevronRight,
  LuServer, LuBrain, LuGlobe, LuFolder,
  LuGitBranch, LuCloud, LuTerminal, LuMonitor, LuInfo, LuArrowLeft
} from "react-icons/lu"
import "./Settings.css"

const API = "http://127.0.0.1:8000"

const PROVIDERS = [
  { id: "groq", label: "Groq", keyField: "groq_api_key", modelField: "groq_model", models: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"] },
  { id: "openai", label: "OpenAI", keyField: "openai_api_key", modelField: "openai_model", models: ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"] },
  { id: "anthropic", label: "Anthropic", keyField: "anthropic_api_key", modelField: "anthropic_model", models: ["claude-opus-4-5", "claude-sonnet-4-5", "claude-3-5-haiku-20241022"] },
  { id: "gemini", label: "Google Gemini", keyField: "gemini_api_key", modelField: "gemini_model", models: ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"] },
  { id: "github", label: "GitHub Models", keyField: "github_token", modelField: "github_model", models: ["gpt-4o-mini", "gpt-4o", "mistral-small"] },
  { id: "ollama", label: "Ollama (Local)", keyField: null, modelField: "ollama_model", models: ["llama3", "mistral", "phi3", "gemma2"] },
]

const MCP_SERVERS = [
  { key: "browser_enabled", label: "Browser Search", desc: "DuckDuckGo web search and page browsing", icon: LuGlobe },
  { key: "filesystem_enabled", label: "File System", desc: "Read and write files in sandbox", icon: LuFolder },
  { key: "github_enabled", label: "GitHub", desc: "Repository and code management", icon: LuGitBranch },
  { key: "weather_enabled", label: "Weather", desc: "Current weather and forecasts", icon: LuCloud },
  { key: "code_runner_enabled", label: "Code Runner", desc: "Execute Python code snippets", icon: LuTerminal },
  { key: "system_info_enabled", label: "System Info", desc: "Disk usage and environment info", icon: LuMonitor },
]

const DEFAULT_SETTINGS = {
  primary_provider: "groq",
  fallback_provider: "github",
  groq_api_key: "",
  groq_model: "llama-3.3-70b-versatile",
  openai_api_key: "",
  openai_model: "gpt-4o-mini",
  anthropic_api_key: "",
  anthropic_model: "claude-3-5-haiku-20241022",
  gemini_api_key: "",
  gemini_model: "gemini-1.5-flash",
  github_token: "",
  github_model: "gpt-4o-mini",
  ollama_host: "http://localhost:11434",
  ollama_model: "llama3",
  browser_enabled: true,
  filesystem_enabled: true,
  github_enabled: true,
  weather_enabled: true,
  code_runner_enabled: true,
  system_info_enabled: true,
  agent_temperature: 0.3,
  agent_max_tokens: 2048,
  agent_max_iterations: 5,
  sandbox_path: "",
  github_path: "",
}

const Settings = ({ onBack }) => {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [saving, setSaving] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState(null)
  const [showKeys, setShowKeys] = useState({})
  const [expanded, setExpanded] = useState({})
  const [testResults, setTestResults] = useState({})
  const [testing, setTesting] = useState({})
  const [healthData, setHealthData] = useState(null)
  const [clearFeedback, setClearFeedback] = useState(null)

  useEffect(() => {
    console.log("[Settings] Fetching /settings...")
    fetch(`${API}/settings`)
      .then(r => r.json())
      .then(data => {
        console.log("[Settings] Settings loaded:", data)
        setSettings(prev => ({ ...prev, ...data }))
      })
      .catch(err => console.error("[Settings] Failed to load settings:", err.message))

    console.log("[Settings] Fetching /health...")
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(data => {
        console.log("[Settings] Health data received:", data)
        setHealthData(data)
      })
      .catch(err => console.error("[Settings] Failed to load health:", err.message))
  }, [])

  const update = (key, val) => {
    setSettings(prev => ({ ...prev, [key]: val }))
  }

  const toggleKey = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const toggleExpand = (id) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }))
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveFeedback(null)
    try {
      console.log("[Settings] Sending /settings save request...")
      const resp = await fetch(`${API}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      })
      const data = await resp.json()
      if (resp.ok) {
        console.log("[Settings] Save success:", data)
        setSaveFeedback({ type: "success", msg: `Saved. Active: ${data.active_providers?.join(", ")}` })
      } else {
        console.error("[Settings] Save failed with response:", data)
        setSaveFeedback({ type: "error", msg: data.detail || "Save failed" })
      }
    } catch (err) {
      console.error("[Settings] Save fetch failed:", err.message)
      setSaveFeedback({ type: "error", msg: "Backend unreachable" })
    } finally {
      setSaving(false)
      setTimeout(() => setSaveFeedback(null), 4000)
    }
  }

  const handleTest = async (provider) => {
    const p = PROVIDERS.find(x => x.id === provider)
    if (!p) return
    const apiKey = p.keyField ? settings[p.keyField] : null
    if (p.id !== "ollama" && !apiKey) {
      setTestResults(prev => ({ ...prev, [provider]: { ok: false, msg: "No API key entered" } }))
      return
    }
    setTesting(prev => ({ ...prev, [provider]: true }))
    setTestResults(prev => ({ ...prev, [provider]: null }))
    try {
      console.log(`[Settings] Testing provider ${provider}...`)
      const resp = await fetch(`${API}/settings/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          api_key: apiKey || "",
          model: settings[p.modelField],
          ollama_host: settings.ollama_host
        })
      })
      const data = await resp.json()
      if (resp.ok) {
        console.log(`[Settings] Test result for ${provider}:`, data)
        setTestResults(prev => ({ ...prev, [provider]: { ok: true, msg: "Connected" } }))
      } else {
        console.error(`[Settings] Test failed for ${provider}:`, data)
        setTestResults(prev => ({ ...prev, [provider]: { ok: false, msg: data.detail || "Failed" } }))
      }
    } catch (err) {
      console.error(`[Settings] Test fetch failed for ${provider}:`, err.message)
      setTestResults(prev => ({ ...prev, [provider]: { ok: false, msg: "Unreachable" } }))
    } finally {
      setTesting(prev => ({ ...prev, [provider]: false }))
    }
  }

  const handleClearSandbox = async () => {
    try {
      console.log("[Settings] Clearing sandbox...")
      const resp = await fetch(`${API}/sandbox`, { method: "DELETE" })
      const data = await resp.json()
      console.log("[Settings] Sandbox cleared:", data)
      setClearFeedback({ type: "success", msg: `Cleared ${data.files_removed?.length || 0} items` })
    } catch (err) {
      console.error("[Settings] Failed to clear sandbox:", err.message)
      setClearFeedback({ type: "error", msg: "Failed to clear sandbox" })
    } finally {
      setTimeout(() => setClearFeedback(null), 3000)
    }
  }

  const getProviderBadge = (providerId) => {
    if (settings.primary_provider === providerId) return "primary"
    if (settings.fallback_provider === providerId) return "fallback"
    return null
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <div className="settings-header-left">
          <button className="icon-btn" onClick={onBack} style={{ marginRight: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <LuArrowLeft size={18} />
          </button>
          <LuSettings size={16} color="var(--text-muted)" />
          <div>
            <div className="settings-title">Settings</div>
            <div className="settings-subtitle">Configure providers, tools, and agent behavior</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {saveFeedback && (
            <div className={`save-feedback ${saveFeedback.type}`}>
              {saveFeedback.type === "success"
                ? <LuCheck size={13} />
                : <LuX size={13} />}
              {saveFeedback.msg}
            </div>
          )}
          <button
            className={`save-btn ${saving ? "saving" : ""}`}
            onClick={handleSave}
            disabled={saving}
          >
            {saving
              ? <LuRefreshCw size={14} className="spin" />
              : <LuSave size={14} />}
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      <div className="settings-body">

        {/* PRIMARY + FALLBACK */}
        <div className="settings-section">
          <div className="section-header">
            <span className="section-icon"><LuBrain size={15} /></span>
            <span className="section-title">Provider Priority</span>
          </div>
          <div className="section-body">
            <div className="primary-fallback-row">
              <div className="field-row">
                <label className="field-label">Primary Provider</label>
                <select
                  className="field-select"
                  value={settings.primary_provider}
                  onChange={e => update("primary_provider", e.target.value)}
                >
                  {PROVIDERS.map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div className="field-row">
                <label className="field-label">Fallback Provider</label>
                <select
                  className="field-select"
                  value={settings.fallback_provider}
                  onChange={e => update("fallback_provider", e.target.value)}
                >
                  {PROVIDERS.map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* LLM PROVIDERS */}
        <div className="settings-section">
          <div className="section-header">
            <span className="section-icon"><LuServer size={15} /></span>
            <span className="section-title">LLM Providers</span>
          </div>
          <div className="section-body">
            {PROVIDERS.map(provider => {
              const badge = getProviderBadge(provider.id)
              const isOpen = expanded[provider.id]
              const testResult = testResults[provider.id]
              const isTesting = testing[provider.id]

              return (
                <div key={provider.id} className="provider-block">
                  <div
                    className="provider-header"
                    onClick={() => toggleExpand(provider.id)}
                  >
                    <div className="provider-name">
                      {provider.label}
                      {badge && (
                        <span className={`provider-badge ${badge}`}>
                          {badge}
                        </span>
                      )}
                    </div>
                    {isOpen
                      ? <LuChevronDown size={14} color="var(--text-muted)" />
                      : <LuChevronRight size={14} color="var(--text-muted)" />}
                  </div>

                  {isOpen && (
                    <div className="provider-body">
                      {provider.keyField && (
                        <div className="field-row">
                          <label className="field-label">API Key</label>
                          <div className="key-input-row">
                            <input
                              className="field-input"
                              type={showKeys[provider.keyField] ? "text" : "password"}
                              placeholder={`Enter ${provider.label} API key`}
                              value={settings[provider.keyField] || ""}
                              onChange={e => update(provider.keyField, e.target.value)}
                            />
                            <button
                              className="icon-btn"
                              onClick={() => toggleKey(provider.keyField)}
                            >
                              {showKeys[provider.keyField]
                                ? <LuEyeOff size={14} />
                                : <LuEye size={14} />}
                            </button>
                          </div>
                        </div>
                      )}

                      {provider.id === "ollama" && (
                        <div className="field-row">
                          <label className="field-label">Ollama Host</label>
                          <input
                            className="field-input"
                            type="text"
                            placeholder="http://localhost:11434"
                            value={settings.ollama_host || ""}
                            onChange={e => update("ollama_host", e.target.value)}
                          />
                        </div>
                      )}

                      <div className="field-row">
                        <label className="field-label">Model</label>
                        <select
                          className="field-select"
                          value={settings[provider.modelField] || provider.models[0]}
                          onChange={e => update(provider.modelField, e.target.value)}
                        >
                          {provider.models.map(m => (
                            <option key={m} value={m}>{m}</option>
                          ))}
                        </select>
                      </div>

                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <button
                          className={`test-btn ${isTesting ? "testing" : ""}`}
                          onClick={() => handleTest(provider.id)}
                          disabled={isTesting}
                        >
                          {isTesting
                            ? <LuRefreshCw size={12} className="spin" />
                            : <LuCheck size={12} />}
                          {isTesting ? "Testing..." : "Test Connection"}
                        </button>
                        {testResult && (
                          <div className={`test-result ${testResult.ok ? "ok" : "fail"}`}>
                            {testResult.ok
                              ? <LuCheck size={12} />
                              : <LuX size={12} />}
                            {testResult.msg}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* MCP SERVERS */}
        <div className="settings-section">
          <div className="section-header">
            <span className="section-icon"><LuServer size={15} /></span>
            <span className="section-title">MCP Servers</span>
          </div>
          <div className="section-body">
            {MCP_SERVERS.map(server => {
              const Icon = server.icon
              const enabled = settings[server.key]
              return (
                <div key={server.key} className="toggle-row">
                  <div className="toggle-label">
                    <span className="toggle-label-icon">
                      <Icon size={15} />
                    </span>
                    <div>
                      <div>{server.label}</div>
                      <div className="toggle-desc">{server.desc}</div>
                    </div>
                  </div>
                  <button
                    className={`toggle-switch ${enabled ? "on" : ""}`}
                    onClick={() => update(server.key, !enabled)}
                  >
                    {enabled
                      ? <LuToggleRight size={26} />
                      : <LuToggleLeft size={26} />}
                  </button>
                </div>
              )
            })}
          </div>
        </div>

        {/* AGENT BEHAVIOR */}
        <div className="settings-section">
          <div className="section-header">
            <span className="section-icon"><LuBrain size={15} /></span>
            <span className="section-title">Agent Behavior</span>
          </div>
          <div className="section-body">
            <div className="slider-row">
              <div className="slider-label-row">
                <label className="field-label">Temperature</label>
                <span className="slider-value">{settings.agent_temperature}</span>
              </div>
              <div className="field-hint" style={{ marginBottom: '8px' }}>
                Controls response creativity. Lower values (0.0) make the agent more focused and deterministic. Higher values (1.0) make it more creative but less predictable. Recommended: 0.3 for coding tasks, 0.7 for creative tasks.
              </div>
              <input
                type="range"
                className="field-slider"
                min="0" max="1" step="0.1"
                value={settings.agent_temperature}
                onChange={e => update("agent_temperature", parseFloat(e.target.value))}
              />
            </div>

            <div className="slider-row">
              <div className="slider-label-row">
                <label className="field-label">Max Iterations</label>
                <span className="slider-value">{settings.agent_max_iterations}</span>
              </div>
              <div className="field-hint" style={{ marginBottom: '8px' }}>
                How many reasoning steps the agent takes before giving a final answer. Higher values allow more complex multi-step tasks but take longer. Recommended: 5 for most tasks, 10+ for complex research or multi-file operations.
              </div>
              <input
                type="range"
                className="field-slider"
                min="1" max="20" step="1"
                value={settings.agent_max_iterations}
                onChange={e => update("agent_max_iterations", parseInt(e.target.value))}
              />
            </div>

            <div className="field-row">
              <label className="field-label">Max Tokens</label>
              <div className="field-hint" style={{ marginBottom: '8px' }}>
                Maximum length of each LLM response in tokens. 1 token is roughly 4 characters. 2048 is suitable for most tasks. Increase to 4096 for longer code generation or detailed reports.
              </div>
              <input
                type="number"
                className="field-input"
                min="256"
                max="8192"
                value={settings.agent_max_tokens}
                onChange={e => update("agent_max_tokens", parseInt(e.target.value))}
              />
            </div>
          </div>
        </div>

        {/* SANDBOX */}
        <div className="settings-section">
          <div className="section-header">
            <span className="section-icon"><LuFolder size={15} /></span>
            <span className="section-title">Sandbox</span>
          </div>
          <div className="section-body">
            <div className="field-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
              <label className="field-label">MCP Sandbox Location</label>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Where all files created will be stored</div>
              <input
                className="field-input"
                type="text"
                value={settings.sandbox_path || ""}
                onChange={e => update("sandbox_path", e.target.value)}
                placeholder="e.g. C:\sandbox or /tmp/sandbox"
              />
            </div>
            
            <div className="field-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
              <label className="field-label">GitHub Path</label>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Default GitHub repository or local path</div>
              <input
                className="field-input"
                type="text"
                value={settings.github_path || ""}
                onChange={e => update("github_path", e.target.value)}
                placeholder="e.g. owner/repo"
              />
            </div>
            <div className="field-row">
              <button 
                className="danger-btn" 
                onClick={handleClearSandbox}
                style={{ width: 'fit-content', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <LuTrash2 size={14} />
                Clear Sandbox
              </button>
              {clearFeedback && (
                <div className={`test-result ${clearFeedback.type === "success" ? "ok" : "fail"}`}>
                  {clearFeedback.type === "success"
                    ? <LuCheck size={14} />
                    : <LuX size={14} />}
                  {clearFeedback.msg}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ABOUT */}
        <div className="settings-section">
          <div className="section-header">
            <span className="section-icon"><LuInfo size={15} /></span>
            <span className="section-title">About</span>
          </div>
          <div className="section-body">
            <div className="about-grid">
              <div className="about-item">
                <span className="about-key">Version</span>
                <span className="about-val">1.1.3</span>
              </div>
              <div className="about-item">
                <span className="about-key">Backend Status</span>
                <span className="about-val" style={{ color: healthData ? "var(--success)" : "var(--error)" }}>
                  {healthData ? "Online" : "Offline"}
                </span>
              </div>
              <div className="about-item">
                <span className="about-key">Package</span>
                <span className="about-val">unified-mcp</span>
              </div>
              <div className="about-item">
                <span className="about-key">Framework</span>
                <span className="about-val">FastAPI + React</span>
              </div>
            </div>
            {healthData?.llm?.providers?.length > 0 && (
              <div className="field-row" style={{ marginTop: "8px" }}>
                <label className="field-label">Active Providers</label>
                <div className="active-providers-list">
                  {healthData.llm.providers.map(p => (
                    <div key={p} className="active-provider-item">
                      <span className="dot-active" />
                      {p}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}

export default Settings
