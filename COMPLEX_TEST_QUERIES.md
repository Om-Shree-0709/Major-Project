# 🧪 Complex Test Queries for Multi-Agent MCP Orchestrator

## Testing Guide

Use these queries to thoroughly test your Multi-Agent MCP system. They range from **simple** to **extremely complex**, exercising different MCP servers and features.

---

## 📊 Difficulty Levels

### 🟢 BEGINNER (Tests Basic File & Web Operations)

1. **Simple News Fetch + File Creation**

   ```
   Fetch the latest AI news and create a file called ai_news.txt with the results
   ```

   - Tests: Browser search, file write
   - Expected: File appears in `backend/mcp_sandbox/ai_news.txt`

2. **Weather & Tech News**

   ```
   Find the top 5 trending tech articles from the past week and save them to trending.md
   ```

   - Tests: Web search, markdown formatting, file creation
   - Expected: File with formatted markdown content

3. **Create Multiple Files**
   ```
   Create three files: headlines.txt with news headlines, sources.txt with URLs, and stats.txt with story counts
   ```

   - Tests: Multiple file writes, data organization
   - Expected: 3 files in sandbox with organized content

---

### 🟡 INTERMEDIATE (Tests Multi-Step Processes & Data Processing)

4. **Fetch & Compare News from Different Domains**

   ```
   Search for "machine learning news", "blockchain updates", and "cloud computing trends". Create a comprehensive summary file that compares how many articles mention each topic, and list the top sources for each
   ```

   - Tests: Multiple searches, data analysis, file writing
   - Expected: Detailed comparison file with statistics

5. **Create a Structured Report**

   ```
   Find the latest cybersecurity vulnerabilities, create a structured JSON file with fields: vulnerability_id, severity_level, affected_software, patch_available, date_discovered. Format it nicely and save as security_report.json
   ```

   - Tests: Web search, complex data structuring, JSON formatting
   - Expected: Well-formatted JSON file in sandbox

6. **Fetch News by Category and Create Index**
   ```
   Search for news in these categories: "Artificial Intelligence", "Cybersecurity", "Web3", "Quantum Computing". Create an index file that lists all categories with a brief summary of each, then create individual files for each category with detailed articles
   ```

   - Tests: Multiple searches, file organization, categorization
   - Expected: Index file + 4 category files

---

### 🔴 ADVANCED (Tests GitHub Integration & Complex Processing)

7. **GitHub Repository Analysis**

   ```
   Find information about the trending Python repositories on GitHub focused on machine learning. Create a file that lists: repository name, number of stars, description, primary use case, and top 3 files. Organize it in a markdown table format
   ```

   - Tests: GitHub API, data aggregation, markdown tables
   - Expected: Well-formatted markdown with GitHub data

8. **Multi-Source Tech Digest**

   ```
   Fetch latest news from: tech news websites, GitHub trending repos (Python category), and security advisories. Create a comprehensive digest file that combines all three sources, with sections for each, and includes publication dates and relevance scores
   ```

   - Tests: Multiple APIs, data merging, complex file structure
   - Expected: Rich digest file with multiple data sources

9. **Create a Developer Handbook**
   ```
   Search for "best practices" in JavaScript, Python, and Go. Find common patterns. Create a handbook file with sections for each language, best practices for each, and create a summary file that lists language-agnostic principles. Use proper markdown formatting with code examples if possible
   ```

   - Tests: Web search, knowledge synthesis, markdown formatting
   - Expected: Handbook files with cross-language patterns

---

### 🔥 EXPERT (Tests Strategy Comparison & Optimization)

10. **Execute with Comparison - News Processing**

    ```
    Fetch news from 5 different tech domains, create a master index file, categorize each article by sentiment (positive/negative/neutral), create category files, and generate a statistics file. Then run the comparison to see if HIERARCHICAL execution is faster than LINEAR for this complex multi-step task.
    ```

    - Tests: Complex multi-step task, LINEAR vs HIERARCHICAL comparison
    - Expected: Execution comparison showing which strategy is faster

11. **Advanced Data Pipeline with Comparison**

    ```
    Search for "web development frameworks" trends, "database technologies" trends, and "DevOps tools" trends. Create: (1) a trends.md file with all trends, (2) a comparison.md file comparing frameworks vs databases vs tools, (3) a recommendations.md with pros/cons. Compare LINEAR (sequential) vs HIERARCHICAL (parallel) execution for this entire pipeline.
    ```

    - Tests: Multi-stage pipeline, data comparison, execution strategy comparison
    - Expected: Multiple files + detailed execution comparison

12. **Security & Performance Audit**
    ```
    Search for: "latest security breaches 2026", "performance optimization techniques", and "cloud security best practices". Create: (1) threats.txt with security info, (2) solutions.md with fixes, (3) audit_checklist.txt with verification steps. Use the comparison feature to determine if processing these three searches in parallel (HIERARCHICAL) vs sequentially (LINEAR) makes a significant difference
    ```

    - Tests: Critical information gathering, complex output, strategy optimization
    - Expected: Risk mitigation files + performance analysis

---

### ⚡ EXTREME (Stress Tests - Maximum Complexity)

13. **Massive Knowledge Base Creation**

    ```
    Compile comprehensive information on: "React.js", "Vue.js", "Angular", "Svelte" frameworks. For EACH framework, search for: latest version features, best practices, common pitfalls, and use cases. Create individual framework files with all details, a comparison matrix file, and a recommendation guide. Then run COMPARISON to see execution time differences between LINEAR (process one framework at a time) vs HIERARCHICAL (parallel processing).
    ```

    - Tests: Massive data gathering, complex organization, parallel processing
    - Expected: 4 framework files + comparison + matrix, execution comparison

14. **Full Technology Stack Research**

    ```
    Research complete tech stacks for: "modern web app", "mobile app", "data science project", "DevOps infrastructure". For each stack, find: recommended tools, integration patterns, pros/cons, cost analysis, and learning resources. Create: individual stack guides, a side-by-side comparison matrix, and a decision framework. Compare LINEAR vs HIERARCHICAL execution performance.
    ```

    - Tests: Comprehensive research, complex analysis, optimization
    - Expected: 4 stack guides + comparison matrix + decision framework, execution metrics

15. **Real-Time Market Intelligence Report**
    ```
    Search for: "AI companies funding rounds 2026", "open source trending projects", "technology acquisition news", "startup ecosystem trends". Create: (1) companies.md - investor profiles, (2) projects.md - trending tools, (3) deals.md - acquisition analysis, (4) trends.md - market overview, (5) summary.txt - executive summary. Execute with COMPARISON to determine optimal processing strategy and provide timing analysis for each approach.
    ```

    - Tests: Real-time data, complex reports, deep analysis, strategy optimization
    - Expected: 5 detailed reports + comprehensive execution comparison

---

## 📋 Testing Checklist

For **each query**, verify:

- [ ] **Web Search Works**: Results retrieved from internet
- [ ] **File Creation**: File appears in `backend/mcp_sandbox/`
- [ ] **File Content**: Expected data is in the file
- [ ] **Formatting**: Markdown/JSON/text is properly formatted
- [ ] **File Naming**: Correct filenames as requested
- [ ] **Data Accuracy**: Information matches expectations
- [ ] **Completion**: Task completed within reasonable time
- [ ] **No Errors**: Chat shows success message

---

## 🎯 Suggested Testing Path

1. **Start Simple**: Test queries 1-3 (basic operations)
2. **Progress Medium**: Test queries 4-6 (multi-step)
3. **Go Advanced**: Test queries 7-9 (GitHub integration)
4. **Test Comparison**: Test queries 10-12 (strategy comparison)
5. **Stress Test**: Test queries 13-15 (maximum complexity)

---

## 💡 Tips for Testing

### Monitor These Metrics:

- ⏱️ **Execution Time**: How long queries take
- 📁 **File Creation**: Check `backend/mcp_sandbox/` after each query
- 🔍 **Web Search**: Verify results are relevant
- 📊 **Data Quality**: Check if formatting is correct
- ⚡ **Comparison Results**: Note LINEAR vs HIERARCHICAL timing

### For Comparison Queries:

- Look for timing differences
- Check agent spawning
- Review tool invocations
- Analyze data flow patterns
- Compare execution strategies

### Expected Behaviors:

- ✅ Files always appear in `backend/mcp_sandbox/`
- ✅ Web searches return current information
- ✅ File formatting matches request
- ✅ Complex tasks complete successfully
- ✅ Comparison shows performance metrics

---

## 🚀 Quick Start Examples

**Copy-paste these into the chat:**

**Simple (30 seconds):**

```
Fetch the latest Bollywood and pop culture news and create a bollywood_news.txt file
```

**Medium (1-2 minutes):**

```
Search for "AI breakthroughs", "quantum computing news", and "robotics advances". Create a tech_digest.md file that combines all three categories with summaries
```

**Complex (2-5 minutes):**

```
Find information about React, Vue, and Angular frameworks. Create individual files for each with features, pros/cons, and use cases. Then create a comparison file. Run comparison to see LINEAR vs HIERARCHICAL timing
```

---

## 📝 Recording Results

Keep track of:

```
Query: [Your query]
Time Taken: [X seconds]
Files Created: [List]
Status: [Success/Failed]
Notes: [Any observations]
Comparison Result: [If applicable]
```

---

## ✅ Success Indicators

You'll know the system is working well when:

1. ✅ All files appear in correct location
2. ✅ Content matches the request
3. ✅ Formatting is proper (markdown, JSON, etc.)
4. ✅ Complex queries complete successfully
5. ✅ Comparison shows meaningful execution metrics
6. ✅ No errors in the chat
7. ✅ Web searches return relevant results
8. ✅ File organization is logical
9. ✅ Timestamps and metadata are accurate
10. ✅ Parallel execution (HIERARCHICAL) shows time savings

---

**Happy Testing!** 🎉

Choose a query from above and give it a try. Start with beginner level and work your way up!
