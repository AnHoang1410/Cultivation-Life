/* app.js - dieu phoi API, trang thai va tuong tac cua nguoi choi. */
"use strict";

let currentChar = null;
let actions = [];
let busy = false;

async function api(path, method, body) {
  const opts = { method: method || "GET", headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    throw new Error((data && data.error) ? data.error : "Lỗi kết nối server (mã " + res.status + ").");
  }
  return data;
}

function setBusy(b) {
  busy = b;
  document.querySelectorAll("button").forEach((btn) => { btn.disabled = b; });
}

function showScreen(id) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.add("hidden"));
  GameUI.$(id).classList.remove("hidden");
}

function showDeath(d) {
  const ov = GameUI.$("death-overlay");
  ov.classList.remove("hidden");
  GameUI.$("death-text").textContent =
    "Người từng sống một đời tu tiên nay đã hóa về cát bụi" +
    (d && d.cause ? ": " + d.cause : ".") +
    (d && d.age ? " (tại tuổi " + d.age + ")" : "");
}

async function loadState() {
  const state = await api("/api/state/" + currentChar);
  GameUI.renderState(state);
  GameUI.$("btn-advance").disabled = !state.alive || !!state.pending_event;
  if (!state.alive) showDeath(state.death);
}

async function refresh() {
  if (!currentChar) return;
  try { await loadState(); } catch (e) { GameUI.toast(e.message, "error"); }
}

async function advanceTime() {
  if (busy || !currentChar) return;
  setBusy(true);
  const btn = GameUI.$("btn-advance");
  btn.textContent = "Đang tính toán thời gian...";
  try {
    const r = await api("/api/time/advance", "POST", { character_id: currentChar });
    if (r.died) GameUI.toast("Đại hạn đã đến... nhân vật qua đời.", "error");
    else if (r.event) GameUI.toast("Một biến cố xuất hiện!", "info");
    else GameUI.toast("Trôi qua " + r.years + " năm.", "info");
    await loadState();
  } catch (e) {
    GameUI.toast(e.message, "error");
    await refresh();
  } finally {
    setBusy(false);
  }
}

async function resolveChoice(id) {
  if (busy) return;
  setBusy(true);
  try {
    const r = await api("/api/event/resolve", "POST", { character_id: currentChar, choice_id: id });
    GameUI.renderOutcome(r.outcome, r.summary, r.notes);
    if (r.died) GameUI.toast("Nhân vật đã tử vong...", "error");
    await loadState();
  } catch (e) {
    GameUI.toast(e.message, "error");
  } finally {
    setBusy(false);
  }
}

async function doAction(key) {
  if (busy || !currentChar) return;
  setBusy(true);
  try {
    const r = await api("/api/action", "POST", { character_id: currentChar, action_key: key });
    if (r.choices) GameUI.renderEvent(r);
    if (r.success !== undefined) {
      GameUI.toast(r.note || (r.success ? "Đột phá thành công!" : "Đột phá thất bại."),
                   r.success ? "success" : "error");
    } else if (r.note) {
      GameUI.toast(r.note, "info");
    }
    if (r.years) GameUI.toast("Trôi qua " + r.years + " năm.", "info");
    if (r.died) GameUI.toast("Nhân vật đã qua đời.", "error");
    await loadState();
  } catch (e) {
    GameUI.toast(e.message, "error");
    await refresh();
  } finally {
    setBusy(false);
  }
}

async function freeAction(text) {
  if (busy || !currentChar) return;
  setBusy(true);
  try {
    const r = await api("/api/action/free", "POST", { character_id: currentChar, text: text });
    if (r.choices) GameUI.renderEvent(r);
    await loadState();
  } catch (e) {
    GameUI.toast(e.message, "error");
  } finally {
    setBusy(false);
  }
}

async function useItem(id) {
  if (busy) return;
  setBusy(true);
  try {
    const r = await api("/api/item/use", "POST", { character_id: currentChar, item_id: id });
    GameUI.toast(r.note || "Đã sử dụng.", "success");
    await loadState();
  } catch (e) {
    GameUI.toast(e.message, "error");
  } finally {
    setBusy(false);
  }
}

async function equipItem(id) {
  if (busy) return;
  setBusy(true);
  try {
    const r = await api("/api/item/equip", "POST", { character_id: currentChar, item_id: id });
    GameUI.toast(r.note || "Đã cập nhật.", "success");
    await loadState();
  } catch (e) {
    GameUI.toast(e.message, "error");
  } finally {
    setBusy(false);
  }
}

async function loadSaves(auto) {
  const list = await api("/api/characters");
  GameUI.renderSaves(list);
  const stored = parseInt(localStorage.getItem("tdvk_char") || "0", 10);
  if (auto && stored) {
    const found = list.find((s) => s.id === stored);
    if (found) { playCharacter(stored); return; }
  }
  showScreen("screen-saves");
}

async function playCharacter(id) {
  currentChar = id;
  localStorage.setItem("tdvk_char", String(id));
  showScreen("screen-game");
  await refresh();
}

async function onCreate(e) {
  e.preventDefault();
  const name = GameUI.$("in-name").value.trim();
  if (!name) { GameUI.toast("Hãy đặt tên cho nhân vật.", "error"); return; }
  try {
    const r = await api("/api/characters", "POST", {
      name: name,
      gender: GameUI.$("in-gender").value,
      origin_key: GameUI.$("in-origin").value
    });
    await playCharacter(r.character_id);
  } catch (err) {
    GameUI.toast(err.message, "error");
  }
}

async function initSettings() {
  const cfg = await api("/api/ai/config");
  GameUI.$("cfg-provider").value = cfg.provider_name || "";
  GameUI.$("cfg-base").value = cfg.base_url || "";
  GameUI.$("cfg-model").value = cfg.model_id || "";
  GameUI.$("cfg-temp").value = cfg.temperature;
  GameUI.$("cfg-tokens").value = cfg.max_tokens;
  GameUI.$("key-hint").textContent = cfg.api_key_set
    ? "Key đã được lưu trên máy (gợi ý: " + cfg.api_key_hint +
      "). Để giữ nguyên key cũ, hãy bỏ trống ô API Key."
    : "Key được lưu trong file riêng trên máy của ngươi, chỉ backend sử dụng.";
  GameUI.$("cfg-status").textContent = cfg.configured ? "AI đã sẵn sàng." : "Chưa cấu hình.";

  GameUI.$("ai-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/ai/config", "POST", {
        provider_name: GameUI.$("cfg-provider").value,
        base_url: GameUI.$("cfg-base").value,
        model_id: GameUI.$("cfg-model").value,
        api_key: GameUI.$("cfg-key").value,
        temperature: parseFloat(GameUI.$("cfg-temp").value || "0.9"),
        max_tokens: parseInt(GameUI.$("cfg-tokens").value || "700", 10)
      });
      GameUI.toast("Đã lưu cài đặt AI.", "success");
      GameUI.$("cfg-key").value = "";
      initSettings();
    } catch (err) {
      GameUI.toast(err.message, "error");
    }
  });

  GameUI.$("btn-test").addEventListener("click", async () => {
    const out = GameUI.$("test-result");
    out.textContent = "Đang kiểm tra kết nối thật...";
    out.className = "";
    try {
      const r = await api("/api/ai/test", "POST", {
        base_url: GameUI.$("cfg-base").value,
        model_id: GameUI.$("cfg-model").value,
        api_key: GameUI.$("cfg-key").value
      });
      out.textContent = r.message;
      out.className = r.ok ? "ok" : "err";
    } catch (err) {
      out.textContent = err.message;
      out.className = "err";
    }
  });
}

async function init() {
  if (GameUI.$("ai-form")) { initSettings(); return; }

  const meta = await api("/api/meta");
  const sel = GameUI.$("in-origin");
  sel.innerHTML = meta.origins.map((o) =>
    "<option value='" + GameUI.esc(o.key) + "'>" + GameUI.esc(o.label) + "</option>").join("");
  const desc = () => {
    const o = meta.origins.find((x) => x.key === sel.value);
    GameUI.$("origin-desc").textContent = o ? o.desc : "";
  };
  sel.addEventListener("change", desc);
  desc();

  actions = await api("/api/actions");
  GameUI.renderActions(actions);

  GameUI.$("create-form").addEventListener("submit", onCreate);
  GameUI.$("btn-advance").addEventListener("click", advanceTime);
  GameUI.$("btn-menu").addEventListener("click", () => { loadSaves(false); });
  GameUI.$("free-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const t = GameUI.$("free-input").value.trim();
    if (t) { freeAction(t); GameUI.$("free-input").value = ""; }
  });
  GameUI.$("btn-death-log").addEventListener("click", () => {
    GameUI.$("death-overlay").classList.add("hidden");
  });
  GameUI.$("btn-death-menu").addEventListener("click", () => {
    GameUI.$("death-overlay").classList.add("hidden");
    currentChar = null;
    localStorage.removeItem("tdvk_char");
    loadSaves(false);
  });

  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-choice],[data-action],[data-use],[data-equip],[data-play]");
    if (!t || busy) return;
    if (t.dataset.choice) resolveChoice(t.dataset.choice);
    else if (t.dataset.action) doAction(t.dataset.action);
    else if (t.dataset.use) useItem(parseInt(t.dataset.use, 10));
    else if (t.dataset.equip) equipItem(parseInt(t.dataset.equip, 10));
    else if (t.dataset.play) playCharacter(parseInt(t.dataset.play, 10));
  });

  await loadSaves(true);
}

document.addEventListener("DOMContentLoaded", () => {
  init().catch((err) => GameUI.toast("Không khởi động được game: " + err.message, "error"));
});
