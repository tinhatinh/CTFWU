import { api, dateLabel, message, setBusy } from "./api.js";

const form = document.querySelector("#research-form");
const historyNode = document.querySelector("#recent-submission");
const detailNode = document.querySelector("#submission-detail");
const idsKey = "echo-chamber.recent-submissions";

function recentIds() {
  try { return JSON.parse(localStorage.getItem(idsKey) || "[]").filter(id => typeof id === "string").slice(0, 8); }
  catch { return []; }
}

async function showSubmission(id) {
  const [submission, artifacts] = await Promise.all([
    api(`/api/research/submissions/${encodeURIComponent(id)}`),
    api(`/api/research/submissions/${encodeURIComponent(id)}/artifacts`),
  ]);
  detailNode.replaceChildren();
  detailNode.hidden = false;
  const title = document.createElement("h2");
  title.textContent = submission.title;
  const summary = document.createElement("p");
  summary.textContent = `${submission.product} ${submission.version} · filed ${dateLabel(submission.created_at)}`;
  const source = document.createElement("details");
  const sourceTitle = document.createElement("summary");
  sourceTitle.textContent = "Submitted source text";
  const sourceText = document.createElement("pre");
  sourceText.className = "evidence-content";
  sourceText.textContent = submission.content;
  source.append(sourceTitle, sourceText);
  const heading = document.createElement("h3");
  heading.textContent = "Associated records";
  const list = document.createElement("div");
  list.className = "submission-artifacts";
  artifacts.forEach(record => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "submission-link";
    const label = document.createElement("span");
    label.textContent = record.title;
    const meta = document.createElement("span");
    meta.className = "index-code";
    meta.textContent = `${record.representation_type.replaceAll("_", " ")} · ${record.evidence_id}`;
    button.append(label, meta);
    button.addEventListener("click", () => renderEvidence(record, list));
    list.append(button);
  });
  detailNode.append(title, summary, source, heading, list);
}

async function loadHistory() {
  const ids = recentIds();
  if (!ids.length) return;
  historyNode.replaceChildren();
  await Promise.all(ids.map(async id => {
    try {
      const submission = await api(`/api/research/submissions/${encodeURIComponent(id)}`);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "submission-link";
      button.textContent = submission.title;
      button.addEventListener("click", () => showSubmission(id).catch(error => message(document.querySelector("#research-message"), error.message, "error")));
      historyNode.append(button);
    } catch { /* Old browser history can outlive server data. */ }
  }));
  if (!historyNode.children.length) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "No recent submissions.";
    historyNode.append(empty);
  }
}

if (form) {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const button = form.querySelector("button[type=submit]");
    const status = document.querySelector("#research-message");
    const payload = Object.fromEntries(new FormData(form));
    setBusy(button, true, "Processing source…");
    message(status, "The source is being processed into research records.");
    try {
      const result = await api("/api/research/submissions", { method: "POST", body: JSON.stringify(payload) });
      const ids = [result.submission_id];
      localStorage.setItem(idsKey, JSON.stringify(ids));
      await Promise.all([loadHistory(), showSubmission(result.submission_id)]);
      message(status, "Research filed and ready to inspect.", "success");
    } catch (error) {
      message(status, error.message, "error");
    } finally { setBusy(button, false); }
  });
  loadHistory();
}
