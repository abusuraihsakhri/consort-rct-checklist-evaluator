# CONSORT RCT Checklist Evaluator

> **Domain:** Clinical Decision Support & Biomedical Computing / Trial Methodologies  
> **Reference Standards:** CONSORT 2010 Statement (Consolidated Standards of Reporting Trials), ICMJE Clinical Trial Registration, and Cochrane Risk of Bias 2.0 (RoB 2.0)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Build](https://img.shields.io/badge/Tests-27%20Passed-brightgreen.svg)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library-brightgreen.svg)

</div>

---

## 📖 What It Does

The **CONSORT RCT Checklist Evaluator** is a clinical-grade methodological auditor designed for randomized controlled trials (RCTs). It evaluates manuscript drafts, protocols, and published study reports against the authoritative **CONSORT 2010 25-item checklist (37 sub-items)**.

In addition to checklist scoring, the engine provides:
1. **Section-by-Section Compliance Scoring** across Title/Abstract, Introduction, Methods, Results, Discussion, and Other Information.
2. **Participant Flow Diagram Arithmetic & Conservation Validation** verifying mathematical consistency across the four stages of a trial (Enrollment, Allocation, Follow-Up, and Analysis).
3. **Cochrane Risk of Bias 2.0 (RoB 2.0) Domain Mapping** translating reporting adherence into bias risk categories (`LOW_RISK`, `SOME_CONCERNS`, `HIGH_RISK`).
4. **Actionable Remediation Diagnostics** pointing out missing or partially reported items with specific protocol guidance.
5. **Batch Evaluation CLI** allowing high-throughput screening of trials via CSV inputs with summary CSV or JSON export.

---

## 📋 CONSORT 2010 25-Item Checklist Structure

The evaluator audits 37 distinct sub-items mapped across standard clinical reporting sections:

```
+----------------------------------------------------------------------------------------------------+
|                               CONSORT 2010 REPORTING TAXONOMY                                      |
+-------------------+---------+---------------------------------------------------+------------------+
| Section           | Item    | Description / Methodological Focus                | RoB 2.0 Domain   |
+-------------------+---------+---------------------------------------------------+------------------+
| TITLE & ABSTRACT  | 1a      | Identification as a randomised trial in title     | None             |
|                   | 1b      | Structured summary of trial design, methods, res. | None             |
+-------------------+---------+---------------------------------------------------+------------------+
| INTRODUCTION      | 2a      | Scientific background and rationale               | None             |
|                   | 2b      | Specific objectives or hypotheses                 | None             |
+-------------------+---------+---------------------------------------------------+------------------+
| METHODS           | 3a      | Description of trial design (parallel/factorial)  | D1 Randomisation |
|                   | 3b      | Changes to methods after trial commencement       | D2 Deviations    |
|                   | 4a      | Eligibility criteria for participants             | None             |
|                   | 4b      | Settings and locations of data collection         | None             |
|                   | 5       | Interventions for each group with replication det.| D2 Deviations    |
|                   | 6a      | Pre-specified primary and secondary outcomes      | D4 Measurement   |
|                   | 6b      | Any changes to trial outcomes with reasons        | D5 Reported Res. |
|                   | 7a      | Sample size determination and power calculation   | None             |
|                   | 7b      | Interim analyses explanation & stopping guidelines| D2 Deviations    |
|                   | 8a      | Method used to generate random sequence           | D1 Randomisation |
|                   | 8b      | Type of randomisation (blocking, stratification)  | D1 Randomisation |
|                   | 9       | Allocation concealment mechanism                  | D1 Randomisation |
|                   | 10      | Implementation (generation, enrollment, assignment| D1 Randomisation |
|                   | 11a     | Blinding procedure (participants, providers, obs.)| D2 Deviations    |
|                   | 11b     | Similarity of interventions (placebo matching)    | D2 Deviations    |
|                   | 12a     | Statistical methods comparing groups for outcomes | D5 Reported Res. |
|                   | 12b     | Additional statistical analyses (subgroup, adj.)  | D5 Reported Res. |
+-------------------+---------+---------------------------------------------------+------------------+
| RESULTS           | 13a     | Participant flow numbers (assigned, received, ana)| D3 Missing Data  |
|                   | 13b     | Losses and exclusions after randomisation         | D3 Missing Data  |
|                   | 14a     | Dates defining periods of recruitment & follow-up | None             |
|                   | 14b     | Why the trial ended or was stopped early          | D2 Deviations    |
|                   | 15      | Baseline demographic and clinical characteristics | D1 Randomisation |
|                   | 16      | Number of participants analysed & ITT adherence   | D3 Missing Data  |
|                   | 17a     | Effect size and precision (95% CI) for outcomes   | D4 Measurement   |
|                   | 17b     | Binary outcome effect sizes (relative & absolute) | D4 Measurement   |
|                   | 18      | Ancillary and exploratory analyses results        | D5 Reported Res. |
|                   | 19      | All important harms or unintended adverse events  | D2 Deviations    |
+-------------------+---------+---------------------------------------------------+------------------+
| DISCUSSION        | 20      | Trial limitations (sources of bias & imprecision) | D3 Missing Data  |
|                   | 21      | Generalisability (external validity)              | None             |
|                   | 22      | Interpretation balancing benefits and harms       | None             |
+-------------------+---------+---------------------------------------------------+------------------+
| OTHER INFORMATION | 23      | Trial registration number and registry name       | D5 Reported Res. |
|                   | 24      | Full protocol access location                     | D5 Reported Res. |
|                   | 25      | Sources of funding and role of funders            | None             |
+-------------------+---------+---------------------------------------------------+------------------+
```

---

## 📐 Mathematical Formulation & Invariants

### 1. Scoring & Compliance Percentage

Each evaluated item $i$ receives a status and associated points:
* **Fully Reported (`FULL` / `2`):** $P_i = 2$ points, $M_i = 2$ max points.
* **Partially Reported (`PARTIAL` / `1`):** $P_i = 1$ point, $M_i = 2$ max points.
* **Not Reported (`NO` / `0`):** $P_i = 0$ points, $M_i = 2$ max points.
* **Not Applicable (`NA`):** $P_i = 0$ points, $M_i = 0$ max points (excluded from denominator).

Overall compliance score across $N$ evaluated items:
$$\text{Compliance } (\%) = \left( \frac{\sum_{i=1}^N P_i}{\sum_{i=1}^N M_i} \right) \times 100\%$$

Quality tiers are categorized as:
* **`HIGH_QUALITY`:** Compliance $\ge 85.0\%$
* **`ACCEPTABLE_MODERATE`:** $65.0\% \le \text{Compliance} < 85.0\%$
* **`SUBSTANDARD_LOW`:** Compliance $< 65.0\%$

### 2. Participant Flow Conservation Arithmetic

The CONSORT flow diagram monitors participant accounting across four essential trial phases:

```
                  +-------------------------------+
                  |    Assessed for Eligibility   |
                  +---------------+---------------+
                                  |
               +------------------+------------------+
               |                                     |
               v                                     v
      +-----------------+                   +-----------------+
      |    Excluded     |                   |   Randomised    |
      | - Not eligible  |                   +--------+--------+
      | - Declined      |                            |
      | - Other reasons |                            |
      +-----------------+              +-------------+-------------+
                                       |                           |
                                       v                           v
                             +-------------------+       +-------------------+
                             | Allocated Arm 1   |       | Allocated Arm 2   |
                             | - Received        |       | - Received        |
                             | - Did not receive |       | - Did not receive |
                             +---------+---------+       +---------+---------+
                                       |                           |
                                       v                           v
                             +-------------------+       +-------------------+
                             | Follow-Up Arm 1   |       | Follow-Up Arm 2   |
                             | - Lost            |       | - Lost            |
                             | - Discontinued    |       | - Discontinued    |
                             +---------+---------+       +---------+---------+
                                       |                           |
                                       v                           v
                             +-------------------+       +-------------------+
                             | Analysed Arm 1    |       | Analysed Arm 2    |
                             | - Primary outcome |       | - Primary outcome |
                             | - Excluded        |       | - Excluded        |
                             +-------------------+       +-------------------+
```

Conservation invariants:
1. **Enrollment Conservation:**
   $$\Delta_{\text{enroll}} = N_{\text{assessed}} - (N_{\text{randomised}} + N_{\text{excluded}}) = 0$$
   $$N_{\text{excluded}} = N_{\text{not eligible}} + N_{\text{declined}} + N_{\text{other}}$$
2. **Allocation Conservation:**
   $$\Delta_{\text{alloc}} = N_{\text{randomised}} - \sum_{k=1}^K N_{\text{allocated}, k} = 0$$
3. **Arm Intervention Conservation:**
   $$N_{\text{allocated}, k} = N_{\text{received}, k} + N_{\text{did not receive}, k}$$
4. **Intention-to-Treat (ITT) Ratio:**
   $$\text{ITT Ratio} = \frac{\sum_{k=1}^K N_{\text{analysed}, k}}{\sum_{k=1}^K N_{\text{allocated}, k}}$$
   * An ITT ratio $< 0.90$ generates an **Attrition Bias Warning**.

### 3. Cochrane Risk of Bias 2.0 Mapping

Reporting adherence directly informs bias assessment across 5 core Cochrane domains:
* **D1 (Randomisation Process):** Items 3a, 8a, 8b, 9, 10, 15
* **D2 (Deviations from Intended Interventions):** Items 3b, 5, 7b, 11a, 11b, 14b, 19
* **D3 (Missing Outcome Data):** Items 13a, 13b, 16, 20
* **D4 (Measurement of the Outcome):** Items 6a, 17a, 17b
* **D5 (Selection of Reported Results):** Items 6b, 12a, 12b, 18, 23, 24

Domain score percentage:
* **`LOW_RISK`:** Score $\ge 80.0\%$
* **`SOME_CONCERNS`:** $50.0\% \le \text{Score} < 80.0\%$
* **`HIGH_RISK`:** Score $< 50.0\%$

---

## 💻 CLI Quickstart & Usage

### 1. Batch Audit from CSV (`batch` Subcommand)

Audit multiple clinical trials listed in a CSV file and output results to CSV or JSON:

```bash
# Evaluate sample CSV and save tabular summary to out.csv
python cli.py batch -i sample.csv -o out_smoke.csv

# Evaluate sample CSV with structured JSON output
python cli.py batch -i sample.csv -o out_smoke.json --json

# Run evaluation directly to terminal stdout
python cli.py batch -i sample.csv
```

### 2. Single-Trial Direct Audit

Evaluate a single trial using command-line arguments:

```bash
# Perfect compliance benchmark trial
python cli.py --trial-id TRIAL-CARDIO-01 --title "Empagliflozin RCT" --full-compliance

# Output trial audit as JSON
python cli.py --trial-id TRIAL-002 --json
```

### 3. Interactive Clinical Audit Mode

Step through CONSORT checklist items interactively in the terminal:

```bash
python cli.py --interactive
```

---

## 📊 CSV Input Format Specification

The CSV header requires `trial_id`, `trial_title`, and item identifiers (`1a` through `25`). Accepted values for checklist responses are `FULL`, `PARTIAL`, `NO`, or `NA` (case-insensitive).

| Field | Description | Requirement | Example |
|:------|:------------|:------------|:--------|
| `trial_id` | Unique study identifier | Required | `TRIAL-P3-CARDIO` |
| `trial_title` | Official manuscript title | Required | `Efficacy of Novel SGLT2 Inhibitor in Heart Failure` |
| `1a` - `25` | CONSORT checklist item reporting status | Optional (defaults to NO) | `FULL`, `PARTIAL`, `NO`, `NA` |

### Sample CSV Excerpt:
```csv
trial_id,trial_title,1a,1b,2a,2b,3a,3b,4a,4b,5,6a,6b,7a,7b,8a,8b,9,10,11a,11b,12a,12b,13a,13b,14a,14b,15,16,17a,17b,18,19,20,21,22,23,24,25
TRIAL-P3-CARDIO,Efficacy of Novel SGLT2 Inhibitor in Heart Failure,FULL,FULL,FULL,FULL,FULL,NA,FULL,FULL,FULL,FULL,NA,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,NA,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL,FULL
TRIAL-PILOT-ONCO,Phase 2 Open-Label Checkpoint Inhibitor Trial,FULL,FULL,FULL,FULL,FULL,NA,FULL,FULL,FULL,FULL,NA,PARTIAL,NA,FULL,PARTIAL,PARTIAL,NO,NO,NO,FULL,PARTIAL,FULL,FULL,FULL,NA,FULL,PARTIAL,FULL,FULL,PARTIAL,FULL,FULL,PARTIAL,FULL,FULL,NO,FULL
TRIAL-SUBSTANDARD,Unblinded Herbal Extract Trial,NO,PARTIAL,FULL,PARTIAL,PARTIAL,NO,PARTIAL,NO,PARTIAL,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,PARTIAL,NO,NO,NO,PARTIAL,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO,NO
```

---

## 🧪 Testing & Verification

Run the full test suite with pytest:

```bash
python -m pytest -p no:zarr -v
```

Execute a CLI batch smoke test:

```bash
python cli.py batch -i sample.csv -o out_smoke.csv
```

---

## 📄 License

This software is released under the **MIT License**.

