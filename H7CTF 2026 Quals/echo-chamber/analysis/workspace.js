import { api, dateLabel, message, setBusy } from "./api.js";
import { openEvidence, renderEvidence } from "./evidence.js";
import { loadReports } from "./reports.js";
import "./research.js";

const views = ["incident", "knowledge", "research", "evidence", "reports"];
const nodes = Object.fromEntries(views.map(name => [name, document.querySelector(`#view-${name}`)]));

function showView(name, { focus = false } = {}) {
  const view = views.includes(name) ? name : "incident";
  views.forEach(key => { nodes[key].hidden = key !== view; });
  document.querySelectorAll(".index-link").forEach(button => {
    if (button.dataset.view === view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (focus) nodes[view].querySelector("h1")?.focus({ preventScroll: true });
  if (view === "reports") loadReports().catch(error => message(document.querySelector("#report-list"), error.message, "error"));
}

document.querySelectorAll(".index-link").forEach(button => button.addEventListener("click", () => {
  const view = button.dataset.view;
  history.replaceState(null, "", `#${view}`);
  showView(view);
  nodes[view].scrollIntoView({ block: "start" });
}));
window.addEventListener("hashchange", () => showView(location.hash.slice(1)));
document.addEventListener("echo:open-view", event => {
  showView(event.detail);
  history.replaceState(null, "", `#${event.detail}`);
});
showView(location.hash.slice(1));

async function loadIncident() {
  const incident = await api("/api/incidents/INC-7421");
  const values = {
    "incident-id": incident.incident_id,
    "incident-title": `${incident.product} ${incident.version} · ${incident.component}`,
    "incident-summary": incident.summary,
    "incident-hypothesis": incident.working_hypothesis,
    "incident-state-label": incident.status,
    "incident-product": incident.product,
    "incident-version": incident.version,
    "incident-component": incident.component,
    "incident-state": incident.status,
    "incident-corroboration": incident.corroboration_status,
    "incident-depth": incident.diagnostic_depth,
    "incident-root": incident.corroborated_root_cause || "Not established",
  };
  Object.entries(values).forEach(([id, value]) => { document.getElementById(id).textContent = value; });
  const [analyses, reports] = await Promise.all([
    api("/api/incidents/INC-7421/analyses"),
    api("/api/incidents/INC-7421/reports"),
  ]);
  renderAnalyses(analyses);
  renderLatestReport(reports[0]);
}

function renderAnalyses(analyses) {
  const target = document.querySelector("#analysis-list");
  target.replaceChildren();
  if (!analyses.length) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "No analysis entries have been filed.";
    target.append(empty);
    return;
  }
  analyses.forEach(entry => {
    const fragment = document.querySelector("#analysis-entry-template").content.cloneNode(true);
    fragment.querySelector('[data-field="date"]').textContent = dateLabel(entry.created_at);
    fragment.querySelector('[data-field="status"]').textContent = `${entry.status} · ${entry.relation}`;
    fragment.querySelector('[data-field="hypothesis"]').textContent = entry.hypothesis;
    fragment.querySelector('[data-field="measure"]').textContent = `${entry.supporting_count} supporting record(s) · ${entry.retrieved_count} retrieved · confidence ${Math.round(entry.confidence * 100)}%`;
    const citations = fragment.querySelector('[data-field="citations"]');
    entry.citations.forEach(citation => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "citation-link";
      button.textContent = `${citation.evidence_id} · ${citation.relation}`;
      button.addEventListener("click", () => {
        document.dispatchEvent(new CustomEvent("echo:open-view", { detail: "evidence" }));
        document.querySelector("#evidence-id").value = citation.evidence_id;
        openEvidence(citation.evidence_id).catch(error => message(document.querySelector("#evidence-message"), error.message, "error"));
      });
      citations.append(button);
    });
    target.append(fragment);
  });
}

function renderLatestReport(report) {
  const target = document.querySelector("#latest-report");
  target.replaceChildren();
  if (!report) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "No reports have been generated.";
    target.append(empty);
    return;
  }
  const button = document.createElement("button");
  button.type = "button";
  button.className = "report-link";
  button.textContent = `${report.report_id} · ${report.diagnostic_depth}`;
  button.addEventListener("click", () => document.dispatchEvent(new CustomEvent("echo:open-view", { detail: "reports" })));
  target.append(button);
}

async function searchArchive(query, limit = 15) {
  const status = document.querySelector("#knowledge-status");
  const target = document.querySelector("#search-results");
  message(status, "Searching the collection…");
  try {
    const rows = await api(`/api/knowledge/search?limit=${limit}`, { method: "POST", body: JSON.stringify({ query }) });
    target.replaceChildren();
    if (!rows.length) {
      const empty = document.createElement("p");
      empty.className = "empty-note";
      empty.textContent = "No records matched this search.";
      target.append(empty);
    }
    rows.forEach(row => {
      const article = document.createElement("article");
      article.className = "record-result";
      const copy = document.createElement("div");
      const type = document.createElement("p");
      type.className = "record-kicker";
      type.textContent = row.representation_type.replaceAll("_", " ");
      const title = document.createElement("h2");
      title.textContent = row.title;
      const snippet = document.createElement("p");
      snippet.textContent = row.content.slice(0, 220) + (row.content.length > 220 ? "…" : "");
      const meta = document.createElement("p");
      meta.className = "result-meta";
      meta.textContent = row.evidence_id;
      copy.append(type, title, snippet, meta);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "record-link";
      button.textContent = "Inspect";
      button.addEventListener("click", () => {
        document.querySelector("#evidence-prompt").hidden = true;
        openEvidence(row.evidence_id, document.querySelector("#knowledge-evidence-detail"))
          .catch(error => message(status, error.message, "error"));
      });
      article.append(copy, button);
      target.append(article);
    });
    message(status, `${rows.length} record(s) found.`);
  } catch (error) { message(status, error.message, "error"); }
}

document.querySelector("#search-form").addEventListener("submit", event => {
  event.preventDefault();
  history.replaceState(null, "", "#knowledge");
  showView("knowledge");
  searchArchive(document.querySelector("#search-query").value.trim());
});
document.querySelector("#browse-archive").addEventListener("click", async () => {
  const target = document.querySelector("#search-results");
  const status = document.querySelector("#knowledge-status");
  message(status, "Loading the collection…");
  try {
    const rows = await api("/api/knowledge?limit=100");
    target.replaceChildren();
    rows.forEach(row => {
      const article = document.createElement("article");
      article.className = "record-result";
      const copy = document.createElement("div");
      const type = document.createElement("p");
      type.className = "record-kicker";
      type.textContent = row.representation_type.replaceAll("_", " ");
      const title = document.createElement("h2");
      title.textContent = row.title;
      const meta = document.createElement("p");
      meta.className = "result-meta";
      meta.textContent = row.evidence_id;
      copy.append(type, title, meta);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "record-link";
      button.textContent = "Inspect";
      button.addEventListener("click", () => {
        document.querySelector("#evidence-prompt").hidden = true;
        renderEvidence(row, document.querySelector("#knowledge-evidence-detail"));
      });
      article.append(copy, button);
      target.append(article);
    });
    message(status, `${rows.length} record(s) in this register.`);
  } catch (error) { message(status, error.message, "error"); }
});

document.querySelector("#analyze").addEventListener("click", async event => {
  const button = event.currentTarget;
  const status = document.querySelector("#analysis-message");
  setBusy(button, true, "Preparing analysis…");
  message(status, "Analysis is in progress.");
  try {
    await api("/api/incidents/INC-7421/analyze", { method: "POST" });
    await loadIncident();
    message(status, "Analysis filed.", "success");
  } catch (error) { message(status, error.message, "error"); }
  finally { setBusy(button, false); }
});

loadIncident().catch(error => message(document.querySelector("#analysis-message"), error.message, "error"));
