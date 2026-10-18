# -*- coding: utf-8 -*-
"""Backend Flask: API cua game. Backend la nguon du lieu dang tin cay duy nhat.

Frontend chi hien thi; moi thay doi du lieu deu duoc xac thuc tai day.
Moi request dung mot ket noi SQLite rieng va commit mot giao dich nguyen ven:
neu AI that bai giua chung, khong thay doi nao duoc ghi lai.
"""
import os
import sys
import traceback

from flask import Flask, jsonify, render_template, request

import database as db
import game_engine as engine
import ai_service as aisvc
from config_store import load as load_config, save as save_config, masked

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
db.init_db()

_locks = {}


class BusyError(Exception):
    pass


def _acquire(cid):
    if _locks.get(cid):
        raise BusyError("Thao tác trước đó chưa hoàn tất, vui lòng đợi thêm một chút.")
    _locks[cid] = True


def _release(cid):
    _locks[cid] = False


def _run_engine(fn, *args, **kwargs):
    """Chay mot ham engine trong mot giao dich: thanh cong thi commit, loi thi rollback."""
    conn = db.get_conn()
    try:
        result = fn(conn, *args, **kwargs)
        conn.commit()
        return result
    finally:
        conn.close()


def _body():
    return request.get_json(silent=True) or {}


# ==================== TRANG ====================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


# ==================== API CO BAN ====================
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "app": "tiendovankiep"})


@app.route("/api/meta")
def meta():
    return jsonify({
        "origins": [{"key": k, "label": v["label"], "desc": v["desc"]}
                    for k, v in engine.ORIGINS.items()],
        "genders": ["Nam", "Nữ", "Khác"],
        "realms": engine.REALMS,
    })


@app.route("/api/actions")
def actions_list():
    out = []
    for k, v in engine.ACTIONS.items():
        out.append({"key": k, "label": v["label"], "category": v["category"],
                    "kind": v["kind"], "hint": v.get("hint", "")})
    return jsonify(out)


@app.route("/api/characters", methods=["GET"])
def list_characters():
    conn = db.get_conn()
    try:
        rows = db.query(conn, "SELECT id, name, age, realm_index, alive, death_age, updated_at "
                              "FROM characters ORDER BY updated_at DESC")
        for r in rows:
            r["realm"] = engine.REALMS[r["realm_index"]]
            r["alive"] = bool(r["alive"])
        return jsonify(rows)
    finally:
        conn.close()


@app.route("/api/characters", methods=["POST"])
def create_character():
    data = _body()
    cid = _run_engine(engine.create_character, data)
    return jsonify({"character_id": cid}), 201


@app.route("/api/state/<int:cid>")
def state(cid):
    return jsonify(_run_engine(engine.load_full_state, cid))


@app.route("/api/log/<int:cid>")
def log(cid):
    conn = db.get_conn()
    try:
        rows = db.query(conn, "SELECT age, event_type, content FROM log_entries "
                              "WHERE character_id=? ORDER BY id DESC LIMIT 500", (cid,))
        rows.reverse()
        return jsonify(rows)
    finally:
        conn.close()


# ==================== TIEN THOI GIAN / BIEN CO ====================
@app.route("/api/time/advance", methods=["POST"])
def time_advance():
    data = _body()
    cid = int(data.get("character_id") or 0)
    mode = data.get("mode", "normal")
    if mode not in ("normal", "cultivate", "seclude"):
        mode = "normal"
    _acquire(cid)
    try:
        return jsonify(_run_engine(engine.advance_time, cid, mode))
    finally:
        _release(cid)


@app.route("/api/event/resolve", methods=["POST"])
def event_resolve():
    data = _body()
    cid = int(data.get("character_id") or 0)
    choice = data.get("choice_id")
    _acquire(cid)
    try:
        return jsonify(_run_engine(engine.resolve_event, cid, choice))
    finally:
        _release(cid)


@app.route("/api/action", methods=["POST"])
def do_action():
    data = _body()
    cid = int(data.get("character_id") or 0)
    key = str(data.get("action_key") or "")
    action = engine.ACTIONS.get(key)
    if not action:
        raise engine.GameError("Hành động không tồn tại.")
    _acquire(cid)
    try:
        if action["kind"] == "engine":
            if key == "breakthrough":
                return jsonify(_run_engine(engine.attempt_breakthrough, cid))
            if key == "rest":
                return jsonify(_run_engine(engine.rest_action, cid))
            if key == "calm_mind":
                return jsonify(_run_engine(engine.calm_mind_action, cid))
            raise engine.GameError("Hành động chưa được hỗ trợ.")
        if action["kind"] == "time":
            return jsonify(_run_engine(engine.advance_time, cid, action["mode"]))
        return jsonify(_run_engine(engine.generate_action_event, cid, key))
    finally:
        _release(cid)


@app.route("/api/action/free", methods=["POST"])
def free_action():
    data = _body()
    cid = int(data.get("character_id") or 0)
    text = str(data.get("text") or "").strip()
    if not text:
        raise engine.GameError("Hãy mô tả hành động ngươi muốn thực hiện.")
    _acquire(cid)
    try:
        return jsonify(_run_engine(engine.generate_action_event, cid, "free", text))
    finally:
        _release(cid)


# ==================== TUI DO ====================
@app.route("/api/item/use", methods=["POST"])
def item_use():
    data = _body()
    cid = int(data.get("character_id") or 0)
    item_id = int(data.get("item_id") or 0)
    _acquire(cid)
    try:
        return jsonify(_run_engine(engine.use_item, cid, item_id))
    finally:
        _release(cid)


@app.route("/api/item/equip", methods=["POST"])
def item_equip():
    data = _body()
    cid = int(data.get("character_id") or 0)
    item_id = int(data.get("item_id") or 0)
    _acquire(cid)
    try:
        return jsonify(_run_engine(engine.equip_item, cid, item_id))
    finally:
        _release(cid)


# ==================== CAU HINH AI ====================
@app.route("/api/ai/config", methods=["GET"])
def ai_config_get():
    return jsonify(masked())


@app.route("/api/ai/config", methods=["POST"])
def ai_config_save():
    data = _body()
    cfg = load_config()
    for k in ("provider_name", "base_url", "model_id"):
        if isinstance(data.get(k), str):
            cfg[k] = data[k].strip()
    if isinstance(data.get("api_key"), str) and data["api_key"].strip():
        cfg["api_key"] = data["api_key"].strip()
    if "temperature" in data:
        try:
            cfg["temperature"] = float(data["temperature"])
        except (TypeError, ValueError):
            pass
    if "max_tokens" in data:
        try:
            cfg["max_tokens"] = int(data["max_tokens"])
        except (TypeError, ValueError):
            pass
    save_config(cfg)
    return jsonify(masked())


@app.route("/api/ai/test", methods=["POST"])
def ai_test():
    data = _body()
    cfg = load_config()
    for k in ("base_url", "model_id", "api_key"):
        if isinstance(data.get(k), str) and data[k].strip():
            cfg[k] = data[k].strip()
    try:
        message = aisvc.test_connection(cfg)
        return jsonify({"ok": True, "message": message})
    except aisvc.AIServiceError as e:
        return jsonify({"ok": False, "message": e.message})


# ==================== XU LY LOI ====================
@app.errorhandler(engine.GameError)
def handle_game_error(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(BusyError)
def handle_busy(e):
    return jsonify({"error": str(e)}), 409


@app.errorhandler(aisvc.AIServiceError)
def handle_ai_error(e):
    return jsonify({"error": e.message, "detail": e.detail or ""}), 502


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Không tìm thấy endpoint."}), 404


@app.errorhandler(Exception)
def handle_exc(e):
    traceback.print_exc()
    return jsonify({"error": "Lỗi hệ thống: " + str(e)}), 500


if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            port = 5000
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    with open(os.path.join(BASE_DIR, "data", "server_port.txt"), "w") as f:
        f.write(str(port))
    print("Tien Do Van Kiep server: http://127.0.0.1:%d/" % port)
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)
