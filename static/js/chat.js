const toggle = document.getElementById("chat-toggle");
const panel = document.getElementById("chat-panel");
const form = document.getElementById("chat-form");
const log = document.getElementById("chat-log");
const input = document.getElementById("chat-input");

function addMessage(role, text) {
  const p = document.createElement("p");
  p.className = `chat-msg chat-${role}`;
  p.textContent = text;
  log.appendChild(p);
  log.scrollTop = log.scrollHeight;
}

if (toggle && panel) {
  toggle.addEventListener("click", () => {
    const open = !panel.hasAttribute("hidden");
    if (open) {
      panel.setAttribute("hidden", "");
      toggle.setAttribute("aria-expanded", "false");
    } else {
      panel.removeAttribute("hidden");
      toggle.setAttribute("aria-expanded", "true");
      input.focus();
    }
  });
}

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addMessage("user", message);
    input.value = "";
    addMessage("bot", "…");
    const pending = log.lastElementChild;
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      pending.textContent = data.reply || "I could not answer just then.";
    } catch (_err) {
      pending.textContent = "The assistant is unavailable. Try again in a moment.";
    }
  });
}
