# AI-Native Data Drift & Quality Monitoring Framework

## Overview

This project is an **AI-native Python framework** designed to automatically detect and explain **schema drift**, **statistical data drift**, and **semantic drift** between a reference dataset and a new incoming dataset.

The framework was built as part of a case study to simulate real-world data ingestion scenarios where client data formats, schemas, and business behavior evolve unpredictably across monthly batches.

---

## Initial Approach & Design Evolution

Initially, I approached the problem using traditional techniques:

* Statistical tests for numerical drift
* Regex-based pattern matching for structured strings
* Fixed schema comparisons

However, these approaches break down quickly when:

* Client schemas are unknown or loosely defined
* Business behavior shifts semantically (e.g., B2C → B2B)
* String identifiers evolve in structure rather than exact format

To address these limitations, the framework was redesigned to be **AI-native**, where:

* Statistical and structural signals are first extracted
* A Large Language Model (LLM) reasons holistically over these signals
* Drift is explained in plain English with **document-level citations**

This enables detection of **semantic drift**, which would otherwise be extremely tedious or impossible to implement using traditional tooling alone.

---

## Key Capabilities

### 1. Schema Drift Detection

* Column additions and removals
* Column type changes
* Schema inferred dynamically (no predefined contracts required)

### 2. Data Drift Detection

* Numerical distribution drift
* Categorical distribution drift
* Null value drift
* Structured string / pattern drift (e.g., ID formats)

### 3. AI-Native Drift Reasoning

* LLM synthesizes all detected signals
* Explains why the drift matters
* Assigns severity levels
* Identifies affected columns
* Produces human-readable explanations

### 4. Transparent Reporting with Citations

* Structured JSON output
* Each insight includes its data source (`reference` or `new`)
* Enables traceability and trust in AI outputs

---

## Project Architecture

```text
LLM_DRIFT_FRAMEWORK/
│
├── core/                 # Profiling, AI reasoning, prompts
├── ingestion/            # CSV / Excel ingestion
├── report/               # Drift report generation
├── ui/                   # Streamlit UI (optional visualization)
├── data/                 # Sample datasets
├── cli.py                # Command-line entrypoint
├── requirements.txt
└── README.md
```

Each module is intentionally decoupled so new drift detectors can be added without modifying existing logic.

---

## AI System Prompt (Core of the Framework)

The system prompt defines the LLM’s role as a **data quality analyst**.
It instructs the model to reason over schema changes, distributions, and patterns, and to return structured outputs including:

SYSTEM_PROMPT = """
You are an AI data reliability engineer working on enterprise client ingestion pipelines.

Your job is to:
- Understand unknown datasets with no predefined schema
- Infer semantic meaning, structure, and intent of columns
- Detect meaningful drift between datasets
- Explain why the drift matters for downstream analytics or ML
- Be conservative: only flag drift when it is meaningful

Always:
- Reason step by step
- Produce structured JSON output
- Cite the data source identifiers provided
- Avoid hallucinating domain assumptions
"""

This prompt is intentionally treated as **first-class logic**, not an afterthought.

---

## Running the Project Locally

### 1. Setup Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure LLM Access

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

> The framework currently uses OpenAI via LangChain, but can be adapted to any other LLM provider by updating `core/llm_client.py`.

---

### 3. Run Drift Analysis (CLI)

```bash
python cli.py \
  --reference data/reference_data.csv \
  --new data/new_data_with_drift.csv
```

This generates a structured `drift_report.json`.

---

### 4. (Optional) Launch the UI

```bash
streamlit run ui/app.py
```

The UI visualizes:

* Detected drifts
* AI explanations
* Document-level citations

---

## Adding a New Drift Detection Rule

1. Create a new profiler in `core/` (e.g., `temporal_profiler.py`)
2. Extract relevant signals
3. Pass results into `drift_reasoner.py`
4. Update the system prompt if needed

No existing logic needs to be rewritten.

---

## Summary

This framework does not just detect drift — it explains **why it matters**, enabling faster and more informed decisions in real-world data pipelines.

