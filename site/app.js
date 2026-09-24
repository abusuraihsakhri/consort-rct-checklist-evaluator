"use strict";

const checklistItems = [
  { key: "1a", section: "TITLE_ABSTRACT", title: "Identify the study as a randomised trial in the title" },
  { key: "1b", section: "TITLE_ABSTRACT", title: "Provide a structured summary of trial design, methods, results, and conclusions" },
  { key: "2", section: "OPEN_SCIENCE", title: "Report trial registry name, registration identifier or URL, and registration date" },
  { key: "3", section: "OPEN_SCIENCE", title: "State where the trial protocol and statistical analysis plan can be accessed" },
  { key: "4", section: "OPEN_SCIENCE", title: "State where and how de-identified participant data, code, and other materials can be accessed" },
  { key: "5a", section: "OPEN_SCIENCE", title: "Report sources of financial and other support and the role of funders or sponsors" },
  { key: "5b", section: "OPEN_SCIENCE", title: "Report financial and other conflicts of interest of manuscript authors" },
  { key: "6", section: "INTRODUCTION", title: "Describe the scientific background and rationale" },
  { key: "7", section: "INTRODUCTION", title: "State specific objectives or hypotheses relating to benefits and harms" },
  { key: "8", section: "METHODS", title: "Describe patient and/or public involvement in trial design, conduct, or reporting" },
  { key: "9", section: "METHODS", title: "Describe trial design, allocation ratio, and framework" },
  { key: "10", section: "METHODS", title: "Report important changes after trial commencement, including non-prespecified outcomes or analyses, with reasons" },
  { key: "11", section: "METHODS", title: "Describe settings and locations where the trial was conducted" },
  { key: "12a", section: "METHODS", title: "Report eligibility criteria for participants" },
  { key: "12b", section: "METHODS", title: "If applicable, report eligibility criteria for sites and individuals delivering interventions" },
  { key: "13", section: "METHODS", title: "Describe intervention and comparator in enough detail for replication and link additional materials if relevant" },
  { key: "14", section: "METHODS", title: "Define prespecified outcomes, including measurement, analysis metric, aggregation, and time point" },
  { key: "15", section: "METHODS", title: "Describe how harms and other unintended effects were defined and assessed" },
  { key: "16a", section: "METHODS", title: "Explain sample-size determination and all supporting assumptions" },
  { key: "16b", section: "METHODS", title: "Explain interim analyses and stopping guidelines, if applicable" },
  { key: "17a", section: "METHODS", title: "State who generated the random allocation sequence and how it was generated" },
  { key: "17b", section: "METHODS", title: "Describe randomisation type and restrictions such as stratification or blocking" },
  { key: "18", section: "METHODS", title: "Describe the mechanism used to conceal allocation until assignment" },
  { key: "19", section: "METHODS", title: "Describe implementation of randomisation and who had access to the allocation sequence" },
  { key: "20a", section: "METHODS", title: "State who was blinded after assignment to interventions" },
  { key: "20b", section: "METHODS", title: "If blinding was used, describe how it was achieved and intervention similarity" },
  { key: "21a", section: "METHODS", title: "Describe statistical methods for primary and secondary outcomes, including harms" },
  { key: "21b", section: "METHODS", title: "Define who was included in each analysis and in which randomised group" },
  { key: "21c", section: "METHODS", title: "Describe how missing data were handled in the analysis" },
  { key: "21d", section: "METHODS", title: "Describe additional analyses and distinguish prespecified from post-hoc analyses" },
  { key: "22a", section: "RESULTS", title: "For each group, report numbers randomised, receiving intended intervention, and analysed" },
  { key: "22b", section: "RESULTS", title: "For each group, report losses and exclusions after randomisation with reasons" },
  { key: "23a", section: "RESULTS", title: "Report dates defining recruitment and follow-up periods" },
  { key: "23b", section: "RESULTS", title: "Explain why the trial ended or was stopped, if applicable" },
  { key: "24a", section: "RESULTS", title: "Describe how intervention and comparator were actually administered, including adherence and fidelity where relevant" },
  { key: "24b", section: "RESULTS", title: "Report concomitant care received during the trial for each group" },
  { key: "25", section: "RESULTS", title: "Provide baseline demographic and clinical characteristics for each group" },
  { key: "26", section: "RESULTS", title: "For each primary and secondary outcome, report analysed and available-data counts, group results, effect estimates, and precision" },
  { key: "27", section: "RESULTS", title: "Report all important harms or unintended effects in each group" },
  { key: "28", section: "RESULTS", title: "Report ancillary analyses and distinguish prespecified from post-hoc analyses" },
  { key: "29", section: "DISCUSSION", title: "Interpret results consistently with the evidence, balancing benefits and harms and considering other evidence" },
  { key: "30", section: "DISCUSSION", title: "Discuss limitations, including potential bias, imprecision, generalisability, and multiplicity where relevant" },
];

const sections = [
  ["TITLE_ABSTRACT", "Title & abstract"],
  ["OPEN_SCIENCE", "Open science"],
  ["INTRODUCTION", "Introduction"],
  ["METHODS", "Methods"],
  ["RESULTS", "Results"],
  ["DISCUSSION", "Discussion"],
];

const choices = [
  ["FULL", "Full", 2, 2],
  ["PARTIAL", "Partial", 1, 2],
  ["NO", "No", 0, 2],
  ["NA", "N/A", 0, 0],
];

const state = {
  activeSection: "TITLE_ABSTRACT",
  responses: Object.fromEntries(checklistItems.map((item) => [item.key, "NO"])),
  lastReport: null,
};

const sectionTabs = document.getElementById("sectionTabs");
const checklistPane = document.getElementById("checklistPane");
const themeToggle = document.getElementById("themeToggle");
const themeIcon = themeToggle.querySelector(".theme-icon");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderTabs() {
  sectionTabs.replaceChildren();
  for (const [sectionKey, label] of sections) {
    const count = checklistItems.filter((item) => item.section === sectionKey).length;
    const button = element("button", "tab-button", `${label} · ${count}`);
    button.type = "button";
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", String(state.activeSection === sectionKey));
    button.addEventListener("click", () => {
      state.activeSection = sectionKey;
      renderTabs();
      renderChecklist();
    });
    sectionTabs.append(button);
  }
}

function renderChecklist() {
  checklistPane.replaceChildren();
  const visible = checklistItems.filter((item) => item.section === state.activeSection);
  for (const item of visible) {
    const row = element("div", "item-row");
    const copy = element("div", "item-copy");
    copy.append(element("span", "item-key", item.key), element("span", "item-title", item.title));

    const group = element("div", "choice-group");
    group.setAttribute("role", "radiogroup");
    group.setAttribute("aria-label", `CONSORT item ${item.key}`);
    for (const [value, labelText] of choices) {
      const label = element("label", "choice");
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `item-${item.key}`;
      input.value = value;
      input.checked = state.responses[item.key] === value;
      input.addEventListener("change", () => {
        if (input.checked) state.responses[item.key] = value;
      });
      label.append(input, element("span", "", labelText));
      group.append(label);
    }
    row.append(copy, group);
    checklistPane.append(row);
  }
  checklistPane.scrollTop = 0;
}

function scoreReport() {
  const sectionScores = {};
  let awarded = 0;
  let maximum = 0;
  const counts = { FULL: 0, PARTIAL: 0, NO: 0, NA: 0 };
  const gaps = [];

  for (const item of checklistItems) {
    const response = state.responses[item.key];
    const choice = choices.find(([value]) => value === response) || choices[2];
    const points = choice[2];
    const maxPoints = choice[3];
    counts[response] += 1;
    awarded += points;
    maximum += maxPoints;
    if (!sectionScores[item.section]) sectionScores[item.section] = { awarded: 0, maximum: 0 };
    sectionScores[item.section].awarded += points;
    sectionScores[item.section].maximum += maxPoints;
    if (response === "PARTIAL" || response === "NO") {
      gaps.push({ key: item.key, title: item.title, status: response, section: item.section });
    }
  }

  const percentage = maximum > 0 ? Math.round((awarded / maximum) * 1000) / 10 : 0;
  let band = "Low completeness";
  if (percentage >= 85) band = "High completeness";
  else if (percentage >= 65) band = "Moderate completeness";

  const flow = document.getElementById("includeFlow").checked ? validateFlow() : null;
  return {
    trial_id: document.getElementById("trialId").value.trim() || "TRIAL-001",
    trial_title: document.getElementById("trialTitle").value.trim(),
    standard_version: "CONSORT 2025",
    scored_entries: 42,
    overall_completion_percentage: percentage,
    reporting_completeness_band: band.toUpperCase().replaceAll(" ", "_"),
    total_points_awarded: awarded,
    total_points_max: maximum,
    response_counts: counts,
    responses: { ...state.responses },
    section_scores: Object.fromEntries(
      Object.entries(sectionScores).map(([key, value]) => [
        key,
        value.maximum > 0 ? Math.round((value.awarded / value.maximum) * 1000) / 10 : 100,
      ]),
    ),
    reporting_gaps: gaps,
    participant_flow: flow,
    methodological_note: "Repository-defined reporting aid; not an official CONSORT score, trial-quality rating, or Cochrane RoB 2 judgement.",
  };
}

function integerValue(id) {
  const raw = document.getElementById(id).value;
  if (raw.trim() === "") return null;
  const number = Number(raw);
  return Number.isInteger(number) && number >= 0 ? number : null;
}

function validateFlow() {
  const ids = [
    "assessed", "excludedTotal", "excludedCriteria", "excludedDeclined", "excludedOther", "randomised",
    "aAllocated", "aReceived", "aNotReceived", "aAnalysed", "aExcludedAnalysis",
    "bAllocated", "bReceived", "bNotReceived", "bAnalysed", "bExcludedAnalysis",
  ];
  const values = Object.fromEntries(ids.map((id) => [id, integerValue(id)]));
  const flags = [];
  for (const [id, value] of Object.entries(values)) {
    if (value === null) flags.push(`${id}: enter a non-negative whole number.`);
  }
  if (flags.length > 0) return { consistent: false, analysis_coverage_ratio: null, flags };

  const exclusionSum = values.excludedCriteria + values.excludedDeclined + values.excludedOther;
  if (exclusionSum !== values.excludedTotal) {
    flags.push(`Exclusion subcategories total ${exclusionSum}, not ${values.excludedTotal}.`);
  }
  if (values.assessed !== values.randomised + values.excludedTotal) {
    flags.push(`Assessed (${values.assessed}) does not equal randomized + excluded (${values.randomised + values.excludedTotal}).`);
  }
  const allocated = values.aAllocated + values.bAllocated;
  if (values.randomised !== allocated) {
    flags.push(`Randomized (${values.randomised}) does not equal total allocated (${allocated}).`);
  }
  for (const prefix of ["a", "b"]) {
    const label = prefix === "a" ? "Intervention" : "Comparator";
    const allocation = values[`${prefix}Allocated`];
    const received = values[`${prefix}Received`];
    const notReceived = values[`${prefix}NotReceived`];
    const analysed = values[`${prefix}Analysed`];
    const excluded = values[`${prefix}ExcludedAnalysis`];
    if (allocation !== received + notReceived) {
      flags.push(`${label}: allocated does not equal received + did not receive.`);
    }
    if (analysed > allocation) flags.push(`${label}: analysed exceeds allocated.`);
    if (excluded > allocation) flags.push(`${label}: excluded from analysis exceeds allocated.`);
    if (analysed + excluded > allocation) flags.push(`${label}: analysed + excluded from analysis exceeds allocated.`);
  }

  const totalAnalysed = values.aAnalysed + values.bAnalysed;
  const coverage = allocated > 0 ? Math.round((totalAnalysed / allocated) * 10000) / 10000 : 0;
  return { consistent: flags.length === 0, analysis_coverage_ratio: coverage, flags };
}

function renderReport(report) {
  document.getElementById("resultStatus").textContent = "Analysed";
  document.getElementById("resultStatus").classList.add("ready");
  document.getElementById("scoreValue").textContent = `${report.overall_completion_percentage.toFixed(1)}%`;
  document.getElementById("scoreRing").style.setProperty("--score", String(report.overall_completion_percentage));
  document.getElementById("bandValue").textContent = report.reporting_completeness_band.replaceAll("_", " ").toLowerCase().replace(/^./, (char) => char.toUpperCase());
  document.getElementById("pointsValue").textContent = `${report.total_points_awarded} / ${report.total_points_max} reporting points`;
  document.getElementById("fullCount").textContent = String(report.response_counts.FULL);
  document.getElementById("partialCount").textContent = String(report.response_counts.PARTIAL);
  document.getElementById("noCount").textContent = String(report.response_counts.NO);
  document.getElementById("naCount").textContent = String(report.response_counts.NA);

  const sectionResults = document.getElementById("sectionResults");
  sectionResults.replaceChildren();
  for (const [sectionKey, label] of sections) {
    const percentage = report.section_scores[sectionKey];
    const row = element("div", "section-result");
    const progress = element("div", "progress");
    const fill = document.createElement("span");
    fill.style.width = `${percentage}%`;
    progress.append(fill);
    row.append(element("span", "", label), progress, element("strong", "", `${percentage.toFixed(1)}%`));
    sectionResults.append(row);
  }

  const gapList = document.getElementById("gapList");
  gapList.replaceChildren();
  gapList.classList.remove("muted-message");
  document.getElementById("gapCount").textContent = String(report.reporting_gaps.length);
  if (report.reporting_gaps.length === 0) {
    gapList.classList.add("muted-message");
    gapList.append(element("span", "", "No partial or unreported checklist entries."));
  } else {
    for (const gap of report.reporting_gaps.slice(0, 12)) {
      const item = element("div", "gap-item");
      item.append(element("strong", "", gap.key), element("span", "", gap.title));
      gapList.append(item);
    }
    if (report.reporting_gaps.length > 12) {
      gapList.append(element("div", "muted-message", `+ ${report.reporting_gaps.length - 12} additional gaps`));
    }
  }

  const flowSection = document.getElementById("flowResultSection");
  const flowResults = document.getElementById("flowResults");
  flowResults.replaceChildren();
  if (report.participant_flow) {
    flowSection.hidden = false;
    const flow = report.participant_flow;
    if (flow.consistent) {
      flowResults.append(element("div", "flow-ok", "Reported counts are arithmetically consistent."));
    } else {
      for (const flag of flow.flags) flowResults.append(element("div", "flow-flag", flag));
    }
    if (flow.analysis_coverage_ratio !== null) {
      flowResults.append(element("div", "muted-message", `Analysis coverage: ${(flow.analysis_coverage_ratio * 100).toFixed(1)}% (analysed / allocated; descriptive only).`));
    }
  } else {
    flowSection.hidden = true;
  }

  document.getElementById("exportJson").disabled = false;
  document.getElementById("exportCsv").disabled = false;
}

function analyse() {
  state.lastReport = scoreReport();
  renderReport(state.lastReport);
}

function reset() {
  state.responses = Object.fromEntries(checklistItems.map((item) => [item.key, "NO"]));
  state.lastReport = null;
  document.getElementById("trialId").value = "TRIAL-001";
  document.getElementById("trialTitle").value = "";
  document.getElementById("includeFlow").checked = false;
  renderChecklist();
  document.getElementById("resultStatus").textContent = "Not analysed";
  document.getElementById("resultStatus").classList.remove("ready");
  document.getElementById("scoreValue").textContent = "—";
  document.getElementById("scoreRing").style.setProperty("--score", "0");
  document.getElementById("bandValue").textContent = "Ready for review";
  document.getElementById("pointsValue").textContent = "Set each checklist item, then analyse.";
  document.getElementById("fullCount").textContent = "0";
  document.getElementById("partialCount").textContent = "0";
  document.getElementById("noCount").textContent = "42";
  document.getElementById("naCount").textContent = "0";
  document.getElementById("sectionResults").replaceChildren();
  const gaps = document.getElementById("gapList");
  gaps.replaceChildren(element("span", "", "Run an analysis to list incomplete items."));
  gaps.classList.add("muted-message");
  document.getElementById("gapCount").textContent = "0";
  document.getElementById("flowResultSection").hidden = true;
  document.getElementById("exportJson").disabled = true;
  document.getElementById("exportCsv").disabled = true;
}

function loadExample() {
  checklistItems.forEach((item, index) => {
    if (["12b", "16b", "20b", "23b"].includes(item.key)) state.responses[item.key] = "NA";
    else if (index % 7 === 5) state.responses[item.key] = "PARTIAL";
    else if (index % 11 === 8) state.responses[item.key] = "NO";
    else state.responses[item.key] = "FULL";
  });
  document.getElementById("trialId").value = "EXAMPLE-RCT";
  document.getElementById("trialTitle").value = "Example randomized trial report";
  renderChecklist();
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function exportJson() {
  if (!state.lastReport) return;
  downloadFile("consort-2025-evaluation.json", JSON.stringify(state.lastReport, null, 2), "application/json");
}

function csvCell(value) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function exportCsv() {
  if (!state.lastReport) return;
  const headers = ["trial_id", "trial_title", ...checklistItems.map((item) => item.key)];
  const row = [state.lastReport.trial_id, state.lastReport.trial_title, ...checklistItems.map((item) => state.lastReport.responses[item.key])];
  const content = `${headers.map(csvCell).join(",")}\n${row.map(csvCell).join(",")}\n`;
  downloadFile("consort-2025-checklist.csv", content, "text/csv;charset=utf-8");
}

function applyTheme(theme) {
  const selected = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = selected;
  themeIcon.textContent = selected === "dark" ? "☀" : "☾";
  themeToggle.setAttribute("aria-label", selected === "dark" ? "Switch to light theme" : "Switch to dark theme");
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("consort-theme", next); } catch (_) { /* storage may be disabled */ }
}

function initializeTheme() {
  let saved = "light";
  try { saved = localStorage.getItem("consort-theme") || "light"; } catch (_) { saved = "light"; }
  applyTheme(saved);
}

initializeTheme();
renderTabs();
renderChecklist();

themeToggle.addEventListener("click", toggleTheme);
document.getElementById("analyseButton").addEventListener("click", analyse);
document.getElementById("resetButton").addEventListener("click", reset);
document.getElementById("exampleButton").addEventListener("click", loadExample);
document.getElementById("exportJson").addEventListener("click", exportJson);
document.getElementById("exportCsv").addEventListener("click", exportCsv);
