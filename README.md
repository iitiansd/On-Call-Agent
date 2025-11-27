# 🧠 OnCallBuddy – AI-Powered On-Call Assistant

### Autonomous ReAct-Driven Incident Resolution • JIRA • PagerDuty • Datadog • Slack • VectorDB • GitHub • MongoDB

OnCallBuddy is an **AI-powered on-call assistant** designed to automate ticket triage, log analysis, runbook retrieval, and troubleshooting using the **ReAct (Reasoning + Acting) Framework**.
This proof-of-concept demonstrates how an LLM combined with domain-specific tools can dramatically reduce MTTR and operational load during incidents.

---

## 🚀 What Is OnCallBuddy?

OnCallBuddy acts as an **autonomous incident-handling agent** that activates whenever a **PagerDuty** or **Jira** ticket is created.
It uses a modern LLM as its **brain**, and a collection of custom-built tools as its **hands**, to perform tasks such as:

* Fetching ticket details
* Retrieving runbook knowledge
* Analyzing logs & failure patterns
* Checking recent deployments
* Performing operations/debugging actions

All of this follows the **ReAct Thought → Action → Observation loop**, allowing the agent to make decisions dynamically.

---

## 🧩 Architecture Overview

<img width="1600" height="856" alt="image" src="https://github.com/user-attachments/assets/01c93ec0-63ee-4441-bb88-3a91e2c8272f" />

OnCallBuddy is powered by:

* **LLM Brain (OpenAI/Gemini/etc)** — replaceable backend

* **Custom ReAct Executor** — built from scratch

* **Tooling Layer**

  * Datadog (logs & metrics)
  * GitHub (deployments / PR history)
  * Slack (deployment notifications)
  * MongoDB (state/doc store)
  * VectorDB (runbooks & knowledge base)
  * JIRA / PagerDuty integrations

* **Service Layer**

  * Preprocessing
  * Log summarization (TF-IDF, Cosine Similarity)
  * Clustering (DBSCAN)
  * Anomaly detection

---

## 🔁 Ticket Resolution Flow

<img width="1599" height="869" alt="image" src="https://github.com/user-attachments/assets/38d84317-3bf5-4b11-9c44-a91a5360c8a4" />


### 1️⃣ Receive Ticket

A new issue arrives from **PagerDuty or Jira**, triggering the AI agent.

### 2️⃣ Trigger AI Agent

The agent is activated to begin the ReAct loop.

### 3️⃣ Evaluate Context

The LLM analyzes ticket priority, description, history, and patterns.

### 4️⃣ Fetch Knowledge (VectorDB)

Search runbooks, historical incidents, RCA notes.

### 5️⃣ Use Tools

The agent autonomously interacts with Datadog, Observe, GitHub, Slack, MongoDB, etc.

### 6️⃣ Perform Actions

The AI executes the required operational steps to resolve or escalate.

---

## 🧠 ReAct Framework in Action

OnCallBuddy follows this cycle:

```
Thought → “What do I need next?”
Action → Call a tool (API, search, logs)
Observation → Read the tool’s output
Repeat until done
```

Examples:

### 🔍 Step 1: Understand the ticket

**Thought:** I need to know the issue.
**Action:** Query JIRA tool for ticket details + similar issues.
**Observation:** Summarized description, priority, past 10 related incidents.

### 📚 Step 2: Search knowledge base

**Thought:** Is this already known?
**Action:** Query VectorDB for matching runbooks.
**Observation:** Fetch RCA steps or fallback to log analysis.

### 📊 Step 3: Log analysis

**Thought:** Need to check logs for anomalies.
**Action:** Query Datadog/Observe with prebuilt filters.
**Observation:** Retrieve errors, timestamps, patterns.

### 🚢 Step 4: Deployment correlation

**Thought:** Did a recent deploy cause this?
**Action:** Query Slack or GitHub deployment history.
**Observation:** Identify time-based correlation.

---

## 🌟 Key Features

### ✔️ Autonomous RCA (Root Cause Analysis)

Automatically identifies patterns, anomalies, and likely causes.

### ✔️ Integrated Tooling

Works with Datadog, GitHub, Slack, Jira, PagerDuty, MongoDB, VectorDB.

### ✔️ ReAct & Non-ReAct Modes

Framework supports both controlled & autonomous workflows.

### ✔️ VectorDB-Powered Memory

Stores runbooks, historical issues, and domain knowledge.

### ✔️ ML-Enhanced Log Processing

* TF-IDF + Cosine Similarity
* DBSCAN clustering
* Anomaly detection models
* Hybrid log classification (future-ready)

### ✔️ Designed for Modularity

Add/replace tools and LLMs easily.
A foundation for fully autonomous agents.

---

## 📈 Why This Matters

* **25–40% faster MTTR**
* **Proactive RCA** with historical matching
* **Zero missed SLAs** (automated alerts + triage)
* **Reduced cognitive load** on on-call engineers
* **Free engineers from “firefighting” to focus on innovation**

---

## 🏗️ Tech Stack

| Layer         | Tools / Technologies                       |
| ------------- | ------------------------------------------ |
| LLM Brain     | OpenAI, Gemini, Custom replaceable backend |
| Framework     | Custom-built ReAct runtime                 |
| Integrations  | JIRA, PagerDuty, Slack, GitHub             |
| Observability | Datadog, Observe                           |
| Data Stores   | MongoDB, VectorDB                          |
| ML/Logs       | TF-IDF, DBSCAN, Anomaly Models             |
| Infra         | Containerized microservice                 |

---

## 📝 Future Enhancements

* Autonomous tool chaining (multi-agent collaboration)
* Live patching & remediation actions
* Hybrid log classification (LLM + clustering)
* Improved memory retrieval via RAG-Fusion
* End-to-end deployment rollback automation

---

## 🧩 For Developers

This POC serves as a **plug-and-play base** for anyone who wants to build:

* Production-ready autonomous agents
* Custom internal AI ops copilots
* ReAct-based automation frameworks

If you want to extend or build your own AI agent, the architecture and tooling foundation here will accelerate development significantly.

---

## 📖 Reference

Inspired by concepts discussed in:
**“Unveiling the Magic Behind Autonomous AI Agents”**
(Article by apssouza22)

---
