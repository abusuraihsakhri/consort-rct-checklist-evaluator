# Consort RCT Checklist Evaluator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

CONSORT 2010 Statement RCT Reporting Checklist Evaluator & Flow Diagram Auditor
--------------------------------------------------------------------------------
Comprehensive clinical trial reporting evaluation engine implementing the CONSORT 2010
25-item checklist (37 sub-items), section-by-section compliance scoring, participant
flow diagram conservation arithmetic, and Cochrane Risk of Bias (RoB 2.0) domain mapping.

Domain: Clinical Research / Evidence-Based Medicine / Trial Methodologies
Pure Python Standard Library (no external dependencies required).

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`FlowDiagramArm`**: Participant counts for a single trial arm.
- **`FlowDiagramCounts`**: Consolidated participant flow metrics across all stages.
- **`FlowValidationResult`**: Conservation arithmetic and consistency check results for flow diagram.
- **`SectionScore`**: Compliance breakdown for a single CONSORT section.
- **`RiskOfBiasDomainEvaluation`**: Cochrane RoB 2.0 domain score derived from CONSORT reporting items.
- **`ConsortAuditReport`**: Unified comprehensive CONSORT evaluation report.

---

## 📐 Mathematical Formulation & Logic

```text
  risk = "LOW_RISK"
  risk = "SOME_CONCERNS"
  risk = "HIGH_RISK"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --- <value> --interactive <value> --json <value> --csv <value>
```

### Parameter Reference
- `---`: Specifies input measurement or parameter value.
- `--interactive`: Specifies input measurement or parameter value.
- `--json`: Specifies input measurement or parameter value.
- `--csv`: Specifies input measurement or parameter value.
- `--trial-id`: Specifies input measurement or parameter value.
- `--title`: Specifies input measurement or parameter value.
- `--responses-json`: Specifies input measurement or parameter value.
- `--full-compliance`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `trial_id` | Parameter / observation metric | Required |
| `trial_title` | Parameter / observation metric | Required |
| `1a` | Parameter / observation metric | Required |
| `1b` | Parameter / observation metric | Required |
| `2a` | Parameter / observation metric | Required |
| `2b` | Parameter / observation metric | Required |
| `3a` | Parameter / observation metric | Required |
| `3b` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t consort-rct-checklist-evaluator .
docker run -p 8000:8000 consort-rct-checklist-evaluator
```
