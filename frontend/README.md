# Unified MCP Framework for Context-Aware AI Agents in Software Development – Frontend

This directory contains the user interface for the **Model Context Protocol (MCP) AI Agent Host**. It is a modern, component-driven chat application developed using React and Vite. The frontend acts as the user-facing layer of the AI Agent system and communicates directly with the Python-based Orchestrator backend to display responses, tool traces, and system status information.

## Overview

Within the MCP-inspired architecture, the frontend serves as the **Host** responsible for mediating all interactions between the user and the backend Orchestrator. Its design focuses on clarity, responsiveness, and transparency, ensuring that users can understand not only the agent’s responses but also the underlying tool executions triggered by those responses.

The frontend allows users to:

* Submit natural language instructions such as “Search for today’s cybersecurity news” or “Check my GitHub repositories.”
* Receive real-time AI-generated responses returned by the backend.
* View detailed tool execution traces, including the exact tool invoked and the JSON payload generated.
* Monitor backend availability through a continuously updated health indicator.

The application replicates the workflow of an MCP-compliant host by exposing system state, tool traces, and user–agent interactions in a structured, developer-friendly interface.

---

## Technology Stack

* **Core Framework:** React 19
* **Build Tool:** Vite, enabling fast refresh and optimized bundling
* **Styling:** Native CSS3 with custom variables, Flexbox, and CSS Grid; Inter font family
* **Icons:** `lucide-react`
* **Linting:** ESLint for code-quality enforcement

This combination prioritizes fast development cycles, clean component architecture, and predictable build output.

---

## Directory Structure

```text
frontend/
├── public/              # Static assets (icons, images)
├── src/
│   ├── assets/          # Internal images and SVG files
│   ├── App.css          # Styles for main components
│   ├── App.jsx          # Core chat interface and logic
│   ├── index.css        # Global styles, variables, and layout definitions
│   └── main.jsx         # React entry point and root mounting logic
├── eslint.config.js     # Linting rules and code standards
├── index.html           # HTML entry point for the SPA
├── package.json         # Scripts and dependency list
└── vite.config.js       # Vite project configuration
```

The overall structure is minimal but modular, ensuring maintainability and ease of extension for future features such as authentication, session history, or advanced tool trace visualizations.

---

## Setup and Installation

### 1. Prerequisites

Ensure that the following are installed on your system:

* Node.js (version 18 or newer is recommended)
* npm (bundled with Node.js)

### 2. Installation

After navigating to the `frontend` directory, install project dependencies:

```bash
npm install
```

This will download all required libraries, including React, ReactDOM, and icon packages.

---

## Running the Application

### Development Mode

To start the development server with full Hot Module Replacement (HMR) support:

```bash
npm run dev
```

The application will be available at:

```
http://localhost:5173
```

### Production Build

To create an optimized production-ready build:

```bash
npm run build
```

To preview the production build locally:

```bash
npm run preview
```

---

## Backend Connection

The frontend communicates with the backend MCP Orchestrator through REST API endpoints. By default, it expects the backend to be running at:

```
http://127.0.0.1:8000
```

To modify the API route (for deployment or remote hosting), update the `API_URL` constant in `src/App.jsx`:

```javascript
// src/App.jsx
const API_URL = "http://127.0.0.1:8000/query";
```

Ensure that CORS settings on the backend are configured appropriately if deploying across different domains.

---

## Features

### Real-Time Chat Interface

User messages are rendered immediately to maintain a responsive interaction flow, while backend responses are appended once processed by the Orchestrator.

### Auto-Scrolling

The interface automatically scrolls to the latest message to support long conversations without manual navigation.

### Tool Execution Tracing

When the backend includes `tool_calls_executed` in its response, the frontend renders:

* The tool name
* Input parameters
* Raw JSON response
* Any errors or warnings

This gives users full visibility into internal agent reasoning and mirrors MCP tool-call transparency standards.

### Backend Health Monitoring

A lightweight polling mechanism checks backend availability every five seconds and updates the on-screen status indicator. This assists users in quickly identifying connectivity issues.

---

## Dependencies

Primary libraries used within the frontend include:

* **react:** Core library for UI development
* **react-dom:** DOM renderer for React
* **lucide-react:** Icon set used within the UI

These dependencies collectively support efficient component rendering, clean UI structure, and visual clarity through scalable vector icons.

