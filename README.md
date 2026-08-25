# CONSORT 2010 RCT Reporting Checklist & Flow Diagram Evaluator

An evidence-based clinical methodology audit engine that operationalizes the **CONSORT 2010 Statement (Consolidated Standards of Reporting Trials)** for parallel group, factorial, and multi-arm randomized controlled trials. The system evaluates trial manuscripts against the official 25-item checklist (37 sub-items), computes section-by-section compliance scores, performs mathematical conservation checks on 4-stage participant flow diagrams, and maps reporting deficits to the **Cochrane Risk of Bias (RoB 2.0)** 5-domain matrix.

---

## 1. Domain Background & Regulatory Importance

The CONSORT (Consolidated Standards of Reporting Trials) 2010 Statement provides an evidence-based minimum set of recommendations for reporting randomized trials. Incomplete or ambiguous trial reporting conceals methodological flaws, prevents replication, and introduces systematic bias into meta-analyses. 
This engine automates compliance auditing for:
- **Journal Editors & Peer Reviewers:** Pre-review screening of submitted trial manuscripts.
- **Trial Authors & Investigators:** Pre-submission gap analysis to ensure all mandatory methodological items are documented.
- **Systematic Reviewers:** Methodological quality appraisal and Cochrane RoB 2.0 cross-mapping.

---

## 2. Taxonomy & Scoring Methodology

### A. 25-Item Checklist Structure
The evaluator tracks all 37 sub-items across 6 core sections:
1. **Title & Abstract (Items 1a–1b):** Explicit identification as randomized trial; structured abstract.
2. **Introduction (Items 2a–2b):** Scientific background, rationale, specific objectives/hypotheses.
3. **Methods (Items 3a–12b):** Trial design, allocation ratio, eligibility criteria, study settings, intervention replication details, primary/secondary outcomes, sample size power calculations, sequence generation, allocation concealment, blinding procedures, and statistical methods.
4. **Results (Items 13a–19):** Participant flow counts, recruitment/follow-up dates, early termination reasons, baseline demographic table, Intention-to-Treat (ITT) denominators, effect sizes with precision (95% CI), absolute/relative risk metrics, and harms/adverse events.
5. **Discussion (Items 20–22):** Limitations/bias sources, generalisability (external validity), and balanced interpretation.
6. **Other Information (Items 23–25):** Registry identifier (e.g. ClinicalTrials.gov), full protocol access, and funding source role.

### B. Scoring System & Adherence Tiers
- **Fully Reported (`FULL` / `2`):** $+2$ points.
- **Partially Reported (`PARTIAL` / `1`):** $+1$ point (triggers actionable remediation notice).
- **Not Reported (`NO` / `0`):** $0$ points (triggers high-priority remediation notice).
- **Not Applicable (`NA`):** Excluded from the denominator.

$$\text{Composite Adherence (\%)} = \frac{\sum \text{Awarded Points}}{\sum \text{Applicable Maximum Points}} \times 100\%$$

| Compliance Score | Quality Tier | Interpretation |
| :---: | :---: | :--- |
| $\ge 85.0\%$ | **HIGH_QUALITY** | Robust reporting adhering to CONSORT 2010 standard |
| $65.0\% \le \text{Score} < 85.0\%$ | **ACCEPTABLE_MODERATE** | Acceptable reporting; minor methodological clarifications required |
| $< 65.0\%$ | **SUBSTANDARD_LOW** | Substandard reporting; critical items missing |

---

## 3. Participant Flow Diagram Conservation Arithmetic

The evaluator enforces mathematical invariants across all 4 stages of participant flow:
1. **Enrollment Stage:** $\text{Assessed} = \text{Randomised} + \text{Excluded (Not Met Criteria + Declined + Other)}$
2. **Allocation Stage:** $\text{Randomised} = \sum_{\text{arms}} \text{Allocated}$
3. **Follow-Up Stage:** For each arm: $\text{Allocated} = \text{Received} + \text{Did Not Receive}$
   $\text{Completed Follow-up} = \text{Received} - (\text{Lost to Follow-up} + \text{Discontinued})$
4. **Analysis Stage:** $\text{Analysed} = \text{Completed} - \text{Excluded from Analysis}$
   - **Intention-to-Treat Ratio:** $\text{ITT} = \frac{\sum \text{Analysed}}{\sum \text{Allocated}}$. Ratios below $90\%$ trigger attrition bias alerts.

---

## 4. Cochrane Risk of Bias (RoB 2.0) Cross-Mapping

The engine automatically synthesizes CONSORT item responses into the 5 Cochrane RoB 2.0 domains:
- **Domain 1 (Randomisation Process):** Evaluates sequence generation (8a), allocation concealment (9), implementation (10), and baseline comparability (15).
- **Domain 2 (Deviations from Intended Interventions):** Evaluates protocol changes (3b), intervention fidelity (5), blinding (11a, 11b), and early stopping (14b).
- **Domain 3 (Missing Outcome Data):** Evaluates participant flow (13a), dropouts/losses (13b), ITT analysis denominator (16), and limitation discussion (20).
- **Domain 4 (Measurement of the Outcome):** Evaluates outcome definitions (6a), assessor blinding (11a), and effect size precision (17a, 17b).
- **Domain 5 (Selection of the Reported Result):** Evaluates pre-specified outcome consistency (6b), statistical methods (12a, 12b), trial registration (23), and protocol transparency (24).

---

## 5. Installation & Quick Start

Requires Python 3.9+ (Pure Python standard library; zero third-party dependencies).

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/consort-rct-checklist-evaluator.git
cd consort-rct-checklist-evaluator

# Run unit tests
python -m unittest test_consort_evaluator.py
```

---

## 6. Command-Line Interface (CLI)

### Quick Benchmark Evaluation (100% Full Compliance)
```bash
python cli.py --full-compliance --trial-id TRIAL-BENCHMARK
```

### Interactive Manuscript Checklist Audit
```bash
python cli.py -i
```

### Batch CSV Audit & JSON Output
```bash
python cli.py --csv sample.csv --json
```

---

## 7. Test Suite & Validation

The test suite in [`test_consort_evaluator.py`](file:///C:/Users/abusu/Desktop/Apps-Developed/507-Projects_25Aug/consort-rct-checklist-evaluator/test_consort_evaluator.py) contains 24 tests verifying:
- Full, partial, zero, and Not Applicable compliance scoring.
- Section-by-section breakdown across all 6 CONSORT divisions.
- Cochrane RoB 2.0 domain score calculations and risk classifications.
- Participant flow diagram conservation checking and discrepancy alerts.
- Attrition Intention-to-Treat ratio calculations.
- Batch CSV parsing and JSON roundtrips.

```bash
python -m unittest test_consort_evaluator.py
# Ran 24 tests in 0.007s -> OK
```

---

## 8. License

MIT License. Authored by Dr. Abu Suraih Sakhri.
