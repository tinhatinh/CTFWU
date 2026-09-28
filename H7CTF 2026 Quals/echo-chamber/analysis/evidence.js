import { api, dateLabel, message } from "./api.js";

function renderEvidence(record, target) {
  const template = document.querySelector("#evidence-record-template");
  const fragment = template.content.cloneNode(true);
  const values = {
    representation: record.representation_type.replaceAll("_", " "),
    title: record.title,
    "evidence-id": record.evidence_id,
    processor: record.processor,
    "created-at": dateLabel(record.created_at),
    content: record.content,
  };
  for (const [field, value] of Object.entries(values)) {
    fragment.querySelector(`[data-field="${field}"]`).textContent = value ?? "—";
  }
  target.replaceChildren(fragment);
}

export async function openEvidence(evidenceId, target = document.querySelector("#evidence-detail")) {
  const record = await api(`/api/evidence/${encodeURIComponent(evidenceId)}`);
  renderEvidence(record, target);
  return record;
}

const form = document.querySelector("#evidence-form");
if (form) form.addEventListener("submit", async event => {
  event.preventDefault();
  const id = form.elements.evidence_id.value.trim();
  const status = document.querySelector("#evidence-message");
  try {
    await openEvidence(id);
    message(status, `Opened ${id}.`);
  } catch (error) {
    document.querySelector("#evidence-detail").replaceChildren();
    message(status, error.message, "error");
  }
});

export { renderEvidence };
