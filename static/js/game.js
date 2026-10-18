/* game.js - hien thi du lieu game len giao diện. Khong tu quyet dinh gia tri quan trong. */
"use strict";

const GameUI = (() => {
  const REALMS = ["Luyện Khí", "Trúc Cơ", "Kết Đan", "Nguyên Anh", "Hóa Thần",
                  "Luyện Hư", "Hợp Thể", "Đại Thừa"];
  const STAGES = ["Sơ Kỳ", "Trung Kỳ", "Hậu Kỳ", "Đại Viên Mãn"];
  const LOG_ICONS = {
    tu_luyen: "☯", bien_co: "✦", chien_dau: "⚔", giao_dich: "◈", xa_giao: "❖",
    vat_pham: "▣", dot_pha: "⚡", the_luc: "⚑", sinh_tu: "☠", he_thong: "•"
  };
  const LOG_TYPES = {
    tu_luyen: "Tu luyện", bien_co: "Biến cố", chien_dau: "Chiến đấu", giao_dich: "Giao dịch",
    xa_giao: "Xã giao", vat_pham: "Vật phẩm", dot_pha: "Đột phá", the_luc: "Thế lực",
    sinh_tu: "Sinh tử", he_thong: "Hệ thống"
  };
  const CATS = [
    ["tu_luyen", "Tu Luyện"], ["bi_canh", "Bí Cảnh"], ["nghe_nghiep", "Nghề Nghiệp"],
    ["the_luc", "Thế Lực"], ["xa_giao", "Xã Giao"], ["kinh_te", "Kinh Tế"]
  ];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[m]));
  }
  function $(id) { return document.getElementById(id); }
  function bacOf(p) { return Math.max(1, Math.min(10, Math.floor(p))); }
  function stageOf(bac) { return STAGES[Math.min(3, Math.floor((bac - 1) / 3))]; }

  function bar(fraction, cls) {
    const pct = Math.max(0, Math.min(100, Math.round(fraction * 100)));
    return '<div class="bar ' + (cls || "") + '"><div class="bar-fill" style="width:' +
           pct + '%"></div></div>';
  }

  function renderState(state) {
    const c = state.character;
    const cv = state.cultivation;
    $("tb-name").textContent = c.name;
    $("tb-age").textContent = "Tuổi " + c.age;
    $("tb-realm").textContent = cv.full;
    $("tb-life").textContent = "Thọ nguyên còn " + Math.max(0, state.lifespan.remaining) +
      " năm (" + c.age + "/" + state.lifespan.lifespan + ")";
    $("btn-advance").textContent = "Bế quan / Tiến thời gian (+" + state.time_step_years + " năm)";
    $("tb-save").textContent = "Đã lưu " + (state.saved_at || "");
    const aiChip = $("tb-ai");
    if (aiChip) aiChip.classList.toggle("hidden", state.ai_configured !== false);

    $("pf-name").textContent = c.name;
    $("pf-origin").textContent = c.origin_label + " • " + c.gender;
    $("pf-stats").innerHTML = [
      ["Linh căn", c.root_name], ["Tư chất", c.aptitude], ["Ngộ tính", c.comprehension],
      ["Căn cốt", c.bone], ["Khí vận", c.luck], ["Mị lực", c.charm],
      ["Thần thức", c.spirit_sense], ["Danh tiếng", Math.round(c.reputation)],
      ["Công pháp", c.technique_name + " (phẩm " + c.technique_quality + ")"]
    ].map((r) => "<div><dt>" + esc(r[0]) + "</dt><dd>" + esc(r[1]) + "</dd></div>").join("");

    let cul = "<h3>Tu vi</h3><p class='realm-line'>" + esc(cv.full) + "</p>" +
              bar(cv.progress_fraction, "jade");
    if (cv.dvm) {
      cul += "<p class='hint'>Đại Viên Mãn — tiến độ nội bộ " + cv.dvm.current + "/3</p>" +
             bar(cv.dvm.fraction, "gold");
    }
    if (cv.at_cap) cul += "<p class='gold-text'>Đại Thừa Đại Viên Mãn — đỉnh cao của thế giới này.</p>";
    else if (cv.can_breakthrough) cul += "<p class='gold-text'>Tu vi đã đầy, có thể thử đột phá!</p>";
    $("pf-cultivation").innerHTML = cul;

    $("pf-bars").innerHTML =
      "<h3>Sức khỏe</h3>" + bar(c.health / 100, "red") +
      "<h3>Tâm cảnh</h3>" + bar(c.mind / 100, "violet") +
      (c.statuses && c.statuses.length
        ? "<p class='warn'>Trạng thái: " + c.statuses.map(esc).join(", ") + "</p>" : "");

    $("pf-faction").innerHTML = "<h3>Thế lực</h3><p>" +
      (state.member_faction
        ? esc(state.member_faction.name) + " — " + esc(state.member_faction.type)
        : "Tán tu, chưa gia nhập thế lực nào") + "</p>";

    $("currency-box").innerHTML = "<div class='stones'>◈ " + state.currency.linh_thach + " linh thạch</div>";
    renderInventory(state.inventory);
    renderNPCs(state.npcs);
    renderFactions(state.factions, state.member_faction);
    renderLog(state.log);
    if (state.pending_event && state.pending_event.event) {
      renderEvent(state.pending_event.event);
    }
  }

  function renderInventory(items) {
    if (!items || !items.length) {
      $("inventory-box").innerHTML = "<p class='hint'>Túi đồ trống rỗng.</p>";
      return;
    }
    $("inventory-box").innerHTML = items.map((it) => {
      let btns = "";
      if (it.usable_key) btns += "<button class='btn mini jade' data-use='" + it.id + "'>Dùng</button>";
      if (it.item_type === "pháp bảo") {
        btns += "<button class='btn mini ghost' data-equip='" + it.id + "'>" +
                (it.equipped ? "Tháo" : "Trang bị") + "</button>";
      }
      return "<div class='item" + (it.equipped ? " equipped" : "") + "'>" +
        "<div class='item-name'>" + (it.equipped ? "✦ " : "") + esc(it.name) +
        " <span class='qty'>x" + it.quantity + "</span></div>" +
        "<div class='hint'>" + esc(it.item_type) + " • phẩm " + it.quality +
        (it.description ? " — " + esc(it.description) : "") + "</div>" +
        (btns ? "<div class='item-btns'>" + btns + "</div>" : "") + "</div>";
    }).join("");
  }

  function renderNPCs(npcs) {
    const alive = (npcs || []).filter((n) => n.alive);
    if (!alive.length) {
      $("npc-box").innerHTML = "<p class='hint'>Chưa quen biết ai.</p>";
      return;
    }
    $("npc-box").innerHTML = alive.map((n) =>
      "<div class='item'><div class='item-name'>" + esc(n.name) + "</div>" +
      "<div class='hint'>" + esc(n.identity) + "</div>" +
      "<div class='hint'>" + esc(REALMS[n.realm_index]) + " • " + esc(n.relationship_label) +
      (n.role ? " • " + esc(n.role) : "") + "</div></div>"
    ).join("") + (npcs.some((n) => !n.alive)
      ? "<p class='hint warn'>Có người đã vĩnh viễn ra đi (xem nhật ký).</p>" : "");
  }

  function renderFactions(factions, member) {
    if (!factions || !factions.length) {
      $("faction-box").innerHTML = "<p class='hint'>Chưa có thế lực nào trong thế giới.</p>";
      return;
    }
    $("faction-box").innerHTML = factions.map((f) =>
      "<div class='item" + (member && member.id === f.id ? " equipped" : "") + "'>" +
      "<div class='item-name'>" + (member && member.id === f.id ? "✦ " : "") + esc(f.name) + "</div>" +
      "<div class='hint'>" + esc(f.type) + " • thủ lĩnh: " + esc(f.leader) +
      " • lực lượng: " + esc(REALMS[f.power_realm]) + "</div>" +
      "<div class='hint'>" + esc(f.description) + "</div></div>"
    ).join("");
  }

  function renderEvent(ev) {
    $("story-content").innerHTML =
      "<div class='event'><div class='event-head'>✦ Biến cố</div>" +
      "<p class='narrative'>" + esc(ev.narrative) + "</p>" +
      "<div class='choices'>" + ev.choices.map((ch) =>
        "<button class='choice' data-choice='" + esc(ch.id) + "'>" +
        "<b>" + esc(ch.id) + ". " + esc(ch.label) + "</b>" +
        (ch.description ? "<span>" + esc(ch.description) + "</span>" : "") +
        "</button>").join("") + "</div></div>";
  }

  function renderOutcome(text, summary, notes) {
    let html = "<div class='event'><div class='event-head gold'>Kết quả</div>" +
               "<p class='narrative'>" + esc(text) + "</p>";
    if (summary && summary.length) {
      html += "<div class='chips'>" + summary.map((s) =>
        "<span class='chip gold'>" + esc(s) + "</span>").join("") + "</div>";
    }
    if (notes && notes.length) {
      html += "<div class='chips'>" + notes.map((s) =>
        "<span class='chip warn-chip'>" + esc(s) + "</span>").join("") + "</div>";
    }
    $("story-content").innerHTML = html + "</div>";
  }

  function renderLog(entries) {
    $("log-box").innerHTML = (entries || []).map((e) =>
      "<div class='log-line'><span class='log-age'>Tuổi " + e.age + "</span>" +
      "<span class='log-icon'>" + (LOG_ICONS[e.event_type] || "•") + "</span>" +
      "<span class='log-type'>" + (LOG_TYPES[e.event_type] || esc(e.event_type)) + "</span>" +
      "<span class='log-content'>" + esc(e.content) + "</span></div>"
    ).join("");
    const box = $("log-box");
    box.scrollTop = box.scrollHeight;
  }

  function renderSaves(list) {
    if (!list.length) {
      $("saves-list").innerHTML =
        "<p class='hint'>Chưa có nhân vật nào. Hãy tạo nhân vật đầu tiên phía dưới.</p>";
      return;
    }
    $("saves-list").innerHTML = list.map((s) =>
      "<div class='save-row'><div><b>" + esc(s.name) + "</b> — " + esc(s.realm) +
      ", tuổi " + s.age + (s.alive ? "" : " (đã qua đời)") + "</div>" +
      "<div class='hint'>Lưu lần cuối: " + esc(s.updated_at || "") + "</div>" +
      "<button class='btn jade small' data-play='" + s.id + "'>Chơi tiếp</button></div>"
    ).join("");
  }

  function renderActions(actions) {
    const tabs = $("action-tabs");
    if (!tabs) return;
    tabs.innerHTML = CATS.map((c, i) =>
      "<button class='tab" + (i === 0 ? " active" : "") + "' data-cat='" + c[0] + "'>" +
      c[1] + "</button>").join("");
    const render = (cat) => {
      const items = actions.filter((a) => a.category === cat);
      $("action-buttons").innerHTML = items.map((a) =>
        "<button class='action' data-action='" + esc(a.key) + "' title='" + esc(a.hint) + "'>" +
        esc(a.label) + "</button>").join("");
    };
    render(CATS[0][0]);
    tabs.querySelectorAll(".tab").forEach((t) => {
      t.addEventListener("click", () => {
        tabs.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
        t.classList.add("active");
        render(t.dataset.cat);
      });
    });
  }

  function toast(msg, kind) {
    const t = $("toast");
    t.textContent = msg;
    t.className = "show " + (kind || "info");
    clearTimeout(t._tm);
    t._tm = setTimeout(() => { t.className = "hidden"; }, 4200);
  }

  return { esc, $, REALMS, renderState, renderEvent, renderOutcome, renderLog,
           renderSaves, renderActions, toast };
})();
