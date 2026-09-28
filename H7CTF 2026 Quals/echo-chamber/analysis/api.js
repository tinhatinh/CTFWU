export async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `Request failed (${response.status})`);
  return body;
}

export function message(node, text, state = "") {
  node.textContent = text;
  node.classList.toggle("is-error", state === "error");
  node.classList.toggle("is-success", state === "success");
}

export function dateLabel(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

export function setBusy(button, busy, label = "Working…") {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = label;
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
    delete button.dataset.label;
  }
  button.disabled = busy;
  button.setAttribute("aria-busy", String(busy));
}
