const state = {
  status: null,
  context: null,
  history: [],
};

const els = {
  userId: document.getElementById("userId"),
  modeBadge: document.getElementById("modeBadge"),
  modelBadge: document.getElementById("modelBadge"),
  skillLevel: document.getElementById("skillLevel"),
  learningStyle: document.getElementById("learningStyle"),
  turnCount: document.getElementById("turnCount"),
  practiceCount: document.getElementById("practiceCount"),
  lastRoute: document.getElementById("lastRoute"),
  sourceLine: document.getElementById("sourceLine"),
  topicList: document.getElementById("topicList"),
  chatLog: document.getElementById("chatLog"),
  typing: document.getElementById("typing"),
  composer: document.getElementById("composer"),
  message: document.getElementById("message"),
  sendBtn: document.getElementById("sendBtn"),
  resetBtn: document.getElementById("resetBtn"),
  clearLocalBtn: document.getElementById("clearLocalBtn"),
  banner: document.getElementById("banner"),
};

// Human-readable explanations for why the coach is serving local content.
const DEGRADED_REASONS = {
  quota_exhausted:
    "Gemini free-tier quota for this model is used up. Answers come from the built-in lesson library until it resets.",
  rate_limit:
    "Gemini is rate-limiting requests. Answers come from the built-in lesson library for now.",
  auth_error:
    "Gemini rejected the credentials. Check GEMINI_API_KEY or the Vertex AI permissions.",
  model_not_found:
    "The configured model is not available to this project. Check GEMINI_MODEL.",
};

function showBanner(text) {
  if (!els.banner) {
    return;
  }
  els.banner.textContent = text;
  els.banner.classList.toggle("hidden", !text);
}

const storageKey = () => `plc_history_${currentUserId()}`;

function currentUserId() {
  return els.userId.value.trim() || "demo";
}

function loadHistory() {
  try {
    state.history = JSON.parse(localStorage.getItem(storageKey()) || "[]");
  } catch {
    state.history = [];
  }
}

function saveHistory() {
  localStorage.setItem(storageKey(), JSON.stringify(state.history.slice(-100)));
}

function setBusy(isBusy) {
  els.typing.classList.toggle("hidden", !isBusy);
  els.message.disabled = isBusy;
  els.sendBtn.disabled = isBusy;
}

function addMessage(role, text, meta = "") {
  state.history.push({ role, text, meta });
  saveHistory();
  renderMessages();
}

function renderMessages() {
  els.chatLog.innerHTML = "";
  if (!state.history.length) {
    const row = document.createElement("div");
    row.className = "empty-state";
    row.textContent = "Start with an assessment, roadmap, explanation, or practice request.";
    els.chatLog.appendChild(row);
    return;
  }

  for (const item of state.history) {
    const row = document.createElement("div");
    row.className = `message-row ${item.role}`;

    const bubble = document.createElement("div");
    bubble.className = "message";
    bubble.textContent = item.text;

    if (item.meta) {
      const meta = document.createElement("div");
      meta.className = "message-meta";
      meta.textContent = item.meta;
      bubble.appendChild(meta);
    }

    row.appendChild(bubble);
    els.chatLog.appendChild(row);
  }
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function renderContext(context) {
  const safe = context || {};
  const progress = safe.progress || {};
  const topics = Array.isArray(progress.topics_learned) ? progress.topics_learned : [];

  els.skillLevel.textContent = safe.skill_level || "unknown";
  els.learningStyle.textContent = safe.learning_style || "adaptive";
  els.turnCount.textContent = progress.interactions || 0;
  // Completed out of delivered: the old single number counted exercises handed
  // out, which read as progress the learner had not actually made.
  els.practiceCount.textContent = `${progress.exercises_completed || 0}/${
    progress.exercises_delivered || 0
  }`;
  els.lastRoute.textContent = safe.last_agent
    ? `Last route: ${safe.last_agent}`
    : "No route yet";
  els.sourceLine.textContent = safe.last_response_source
    ? `Last source: ${safe.last_response_source}`
    : "Waiting for first response";

  els.topicList.innerHTML = "";
  if (!topics.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No topics tracked yet.";
    els.topicList.appendChild(empty);
    return;
  }

  for (const topic of topics) {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = topic;
    els.topicList.appendChild(tag);
  }
}

async function loadStatus() {
  const res = await fetch("/status");
  state.status = await res.json();
  els.modeBadge.textContent = state.status.mode || "unknown";
  els.modelBadge.textContent = state.status.model || "model unknown";

  const kind = state.status.last_error && state.status.last_error.kind;
  if (state.status.degraded && kind) {
    showBanner(DEGRADED_REASONS[kind] || `Gemini is unavailable (${kind}).`);
  }
}

async function loadContext() {
  const res = await fetch(`/context/${encodeURIComponent(currentUserId())}`);
  const data = await res.json();
  state.context = data.context;
  renderContext(state.context);
}

async function sendMessage(message) {
  const text = message.trim();
  if (!text) {
    return;
  }

  addMessage("user", text, "You");
  els.message.value = "";
  setBusy(true);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, user_id: currentUserId() }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }

    const modelPart = data.model ? ` - ${data.model}` : "";
    const meta = `${data.agent_used || "coach"} - ${data.source || "unknown"}${modelPart}`;
    addMessage("coach", data.response || "", meta);
    state.context = data.context;
    renderContext(state.context);

    if (data.degraded) {
      showBanner(
        DEGRADED_REASONS[data.degraded_reason] ||
          `Gemini is unavailable (${data.degraded_reason || "unknown"}).`
      );
    } else if (data.source === "gemini") {
      showBanner("");
    }
  } catch (error) {
    addMessage("error", String(error), "Request failed");
  } finally {
    setBusy(false);
  }
}

async function resetSession() {
  await fetch("/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: currentUserId() }),
  });
  state.history = [];
  saveHistory();
  renderMessages();
  await loadContext();
}

function bindPromptButtons() {
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      els.message.value = button.dataset.prompt || "";
      els.message.focus();
    });
  });
}

els.composer.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(els.message.value);
});

els.resetBtn.addEventListener("click", resetSession);

els.clearLocalBtn.addEventListener("click", () => {
  state.history = [];
  saveHistory();
  renderMessages();
});

els.userId.addEventListener("change", async () => {
  loadHistory();
  renderMessages();
  await loadContext();
});

bindPromptButtons();
loadHistory();
renderMessages();
loadStatus().catch(() => {
  els.modeBadge.textContent = "offline";
  els.modelBadge.textContent = "unavailable";
});
loadContext().catch(() => renderContext(null));
