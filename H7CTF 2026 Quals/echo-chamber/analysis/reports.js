import { api, dateLabel, message } from "./api.js";

const list = document.querySelector("#report-list");
const detail = document.querySelector("#report-detail");

async function openReport(id) {
  const report = await api(`/api/reports/${encodeURIComponent(id)}`);
  detail.replaceChildren();
  const heading = document.createElement("h3");
  heading.textContent = `${report.report_id} · ${report.diagnostic_depth} assessment`;
  const date = document.createElement("p");
  date.className = "result-meta";
  date.textContent = dateLabel(report.created_at);
  const artifacts = document.createElement("pre");
  artifacts.textContent = JSON.stringify(report.artifacts, null, 2);
  detail.append(heading, date, artifacts);
}

export async function loadReports() {
  list.replaceChildren();
  const reports = await api("/api/incidents/INC-7421/reports");
  if (!reports.length) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "No reports have been filed for this case.";
    list.append(empty);
    return reports;
  }
  reports.forEach(report => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "report-link";
    button.textContent = `${report.report_id} · ${report.diagnostic_depth}`;
    button.addEventListener("click", () => openReport(report.report_id).catch(error => message(detail, error.message, "error")));
    list.append(button);
  });
  await openReport(reports[0].report_id);
  return reports;
}

const refresh = document.querySelector("#refresh-reports");
if (refresh) refresh.addEventListener("click", () => loadReports().catch(error => message(list, error.message, "error")));
