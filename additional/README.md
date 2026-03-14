# MCP vs Baseline LLM  
### A Small Empirical Attempt to Observe Hallucination Behaviour

## Overview

This repository contains a small experimental evaluation comparing:

- **Baseline LLM inference** (model answers using internal training knowledge only)
- **MCP / Tool-augmented inference** (model answers with access to external tools such as web search)

The goal of this experiment was to observe how **tool access affects hallucination rates and factual accuracy**, particularly for **version-sensitive technical questions** in the Flask / Python web framework ecosystem.

This project is **not a formal or peer-reviewed research study**.  
It is simply an **independent attempt to explore how MCP-style tool usage impacts LLM responses**.

---

## Motivation

Large language models are known to sometimes produce **hallucinations**, meaning:

- Invented APIs  
- Incorrect framework behaviour  
- Outdated version information  
- Confident but factually wrong explanations  

These issues are particularly problematic for **software developers**, where small inaccuracies can lead to:

- Runtime errors
- Security misconceptions
- Debugging time

This experiment attempts to observe whether **external documentation retrieval (MCP-style tool use)** reduces these problems.

---

## Experiment Setup

The experiment compares two response modes:

| Mode | Description |
|-----|-------------|
| **Baseline (No MCP)** | Model answers using internal knowledge only |
| **MCP Enabled** | Model answers with access to web search and documentation |

All queries were executed manually through a live model interface.

---

## Query Design

A set of **20 queries** was designed specifically to trigger common LLM failure modes.

These include:

1. **Non-existent APIs**
2. **Deprecated or removed framework features**
3. **Renamed parameters across versions**
4. **Incorrect internal framework behaviour**
5. **Subtle semantic misunderstandings**

The queries are grouped into categories:

| Category | Description |
|--------|-------------|
| Hallucination Trap | Questions about APIs that do not exist |
| Version / API Change | Version-specific framework changes |
| Internals / Mechanism | Framework lifecycle and internal behaviour |
| Code Generation | Writing code that must match current APIs |
| Cross-Version Semantic | Subtle but important behaviour differences |

The full query list is included in the repository as a **PDF document**.

---

## Key Observations

In this experiment:

- Baseline responses frequently produced **confident but incorrect answers**
- Many errors involved **invented APIs or outdated parameters**
- Access to documentation via tool usage **resolved these issues**

The observed pattern was:

- **Tool access improved accuracy**
- **Hallucinations were greatly reduced**

However, these observations should be interpreted carefully.

---

## Important Disclaimer

This repository **does NOT present verified scientific results**.

Limitations include:

- Small sample size (20 queries)
- Manual execution
- Single domain (Flask)
- Single model environment
- No statistical validation

Therefore this work should be considered:

> **An exploratory experiment rather than formal research.**

---

## Repository Contents

```
/queries
    flask_query_set.pdf
README.md
```

---

## Purpose of This Repository

The purpose of this project is simply to:

- Explore hallucination behaviour in LLMs
- Observe how tool-augmented inference affects responses
- Share the query set used in the experiment

This may help others perform **more rigorous evaluations in the future**.

---

## License

This repository is shared for educational and experimental purposes.