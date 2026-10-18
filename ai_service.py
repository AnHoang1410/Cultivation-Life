# -*- coding: utf-8 -*-
"""Go API AI tuong thich OpenAI Chat Completions va kiem tra phan hoi JSON.

- Khong hardcode Base URL, API key hay Model ID.
- API key chi o backend, doc tu config_store.
- Moi loi (key sai, model sai, het quota, timeout, JSON hong) deu duoc bien
  thanh thong bao ro rang cho nguoi choi, khong gia vong thanh cong.
"""
import json
import re
import requests

from config_store import load as load_config, is_configured

REQUEST_TIMEOUT = 90


class AIServiceError(Exception):
    """Loi khi go AI, message tieng Viet hien thi truc tiep cho nguoi choi."""

    def __init__(self, message, detail=""):
        super().__init__(message)
        self.message = message
        self.detail = detail


SYSTEM_PROMPT = (
    "Bạn là người dẫn truyện của game mô phỏng cuộc đời tu tiên \"Tiên Đồ Vạn Kiếp\".\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Chỉ trả về MỘT khối JSON hợp lệ. Không dùng markdown, không giải thích thêm.\n"
    "2. Viết tiếng Việt, giọng cổ phong huyền huyễn, gọi nhân vật chính là \"ngươi\".\n"
    "3. narrative và outcome chỉ dài 1-2 câu.\n"
    "4. Tuyệt đối không mâu thuẫn dữ liệu game: không hồi sinh người đã chết, không đổi tên NPC, "
    "không tự nâng cảnh giới nhân vật, không tạo vật phẩm hoặc sự kiện trái với ngữ cảnh.\n"
    "5. Hiệu ứng phải khiêm tốn và phù hợp cảnh giới hiện tại của nhân vật.\n"
    "6. Tránh lặp lại các biến cố gần đây được liệt kê trong ngữ cảnh.\n"
    "7. Đối thủ trong biến cố có cảnh giới tối đa chỉ cao hơn nhân vật MỘT đại cảnh giới.\n"
)

EVENT_SCHEMA = (
    '{"narrative": "1-2 câu mở đầu biến cố", '
    '"event_type": "exploration|cultivation|combat|social|trade|faction|misc", '
    '"opponents": [{"name": "tên đối thủ (chỉ khi liên quan chiến đấu)", "realm_index": 0, "progress": 1}], '
    '"choices": [{"id": "A", "label": "tên ngắn lựa chọn", "description": "một câu mô tả", "combat": false}]}'
)

EFFECTS_SCHEMA = (
    '{"outcome": "1-2 câu kết quả", "effects": {'
    '"health_delta": 0, "mind_delta": 0, "cultivation_progress_delta": 0, '
    '"spirit_stones_delta": 0, "reputation_delta": 0, "lifespan_delta": 0, '
    '"add_items": [{"name": "", "item_type": "đan dược|pháp bảo|linh thảo|nguyên liệu|công pháp giản|tạp vật", '
    '"quality": 1, "quantity": 1, "description": ""}], '
    '"remove_items": [{"name": "", "quantity": 1}], '
    '"new_npcs": [{"name": "", "identity": "", "realm_index": 0, "progress": 1, "personality": "", '
    '"goal": "", "relationship": "xa lạ|quen biết|bạn bè|đồng minh|thân thiết|đối địch|kẻ thù"}], '
    '"relationship_changes": [{"name": "tên NPC đã biết", "delta": 0}], '
    '"npc_deaths": ["tên NPC"], '
    '"status_add": ["trọng thương|trung độc|tâm ma|kiệt sức|bị truy sát"], '
    '"status_remove": ["trạng thái hiện có"], '
    '"set_technique": {"name": "", "quality": 1}, '
    '"join_faction": "tên thế lực đã có", "leave_faction": false, '
    '"found_faction": {"name": "", "type": ""}, '
    '"player_death": false}}'
)


def normalize_endpoint(base_url):
    """Quy tac xu ly Base URL, khong lam hong endpoint nguoi dung nhap:
    - Ket thuc bang /chat/completions -> dung nguyen ven.
    - Ket thuc bang /v1, /v2, /v3... -> noi them /chat/completions.
    - Con lai -> noi them /v1/chat/completions.
    """
    b = (base_url or "").strip().rstrip("/")
    if not b:
        raise AIServiceError("Base URL đang trống. Hãy điền địa chỉ API do nhà cung cấp cung cấp.")
    if b.lower().endswith("/chat/completions"):
        return b
    if re.search(r"/v\d+$", b, re.IGNORECASE):
        return b + "/chat/completions"
    return b + "/v1/chat/completions"


def _chat(cfg, messages, max_tokens, temperature):
    """Mot lan goi Chat Completions, tra ve chuoi noi dung. Moi loi deu raise AIServiceError."""
    url = normalize_endpoint(cfg.get("base_url"))
    headers = {
        "Authorization": "Bearer " + str(cfg.get("api_key", "")),
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.get("model_id"),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        raise AIServiceError("Hết thời gian chờ khi gọi AI (trên %d giây)." % REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise AIServiceError("Không kết nối được tới máy chủ AI. Kiểm tra kết nối mạng và Base URL.")
    if resp.status_code in (401, 403):
        raise AIServiceError("API key bị từ chối (mã %d). Kiểm tra lại API key." % resp.status_code)
    if resp.status_code == 404:
        raise AIServiceError("Không tìm thấy endpoint hoặc model (404). Kiểm tra Base URL và Model ID.")
    if resp.status_code == 429:
        raise AIServiceError("Vượt hạn mức hoặc gửi quá nhiều yêu cầu (429). Thử lại sau ít phút.")
    if resp.status_code >= 500:
        raise AIServiceError("Máy chủ AI đang gặp lỗi (mã %d)." % resp.status_code)
    if resp.status_code != 200:
        raise AIServiceError("AI trả về mã trạng thái %d." % resp.status_code, resp.text[:300])
    try:
        data = resp.json()
    except ValueError:
        raise AIServiceError("Phản hồi của AI không phải JSON.", resp.text[:300])
    choices = data.get("choices") or []
    if not choices or not isinstance(choices, list):
        raise AIServiceError("Phản hồi AI thiếu nội dung (không có choices).", json.dumps(data)[:300])
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        content = "".join(x.get("text", "") for x in content if isinstance(x, dict))
    if not content or not str(content).strip():
        raise AIServiceError("AI trả về nội dung rỗng.")
    return str(content).strip()


def _extract_json(text):
    """Trich khối JSON tu phan hoi, loai bo markdown fence neu co."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(t[start:end + 1])
    except (json.JSONDecodeError, ValueError):
        return None


def _chat_json(cfg, messages, max_tokens, temperature):
    """Go AI va lay JSON. Neu JSON hong, thu lai mot lan voi nhac nho dinh dang."""
    content = _chat(cfg, messages, max_tokens, temperature)
    data = _extract_json(content)
    if data is None:
        retry = messages + [
            {"role": "assistant", "content": content[:2000]},
            {"role": "user", "content": "Phản hồi trên không phải JSON hợp lệ. "
             "Chỉ trả về MỘT khối JSON đúng cấu trúc đã yêu cầu, không thêm gì khác."},
        ]
        content2 = _chat(cfg, retry, max_tokens, temperature)
        data = _extract_json(content2)
        if data is None:
            raise AIServiceError("AI trả về JSON không hợp lệ sau hai lần thử.", content[:300])
    return data


def _validate_event(data):
    """Kiem tra cau truc bien co. Tra ve (event, loi). event None neu khong hop le."""
    if not isinstance(data, dict):
        return None, "phải là một object JSON"
    narrative = str(data.get("narrative", "")).strip()
    if len(narrative) < 5 or len(narrative) > 600:
        return None, "narrative phải dài 1-2 câu (5-600 ký tự)"
    etype = str(data.get("event_type", "misc")).strip().lower() or "misc"
    choices_raw = data.get("choices")
    if not isinstance(choices_raw, list):
        return None, "phải có danh sách choices"
    if len(choices_raw) > 4:
        choices_raw = choices_raw[:4]
    if not (3 <= len(choices_raw) <= 4):
        return None, "phải có đúng 3 hoặc 4 lựa chọn"
    choices = []
    for i, c in enumerate(choices_raw):
        if not isinstance(c, dict):
            return None, "mỗi lựa chọn phải là object"
        cid = str(c.get("id", "")).strip().upper() or "ABCD"[i]
        label = str(c.get("label", "")).strip()
        if not (1 <= len(label) <= 80):
            return None, "label lựa chọn phải từ 1-80 ký tự"
        desc = str(c.get("description", "")).strip()[:200]
        combat = bool(c.get("combat"))
        choices.append({"id": cid, "label": label, "description": desc, "combat": combat})
    ids = [c["id"] for c in choices]
    if len(set(ids)) != len(ids):
        for i, c in enumerate(choices):
            c["id"] = "ABCD"[i]
    opponents = []
    ops = data.get("opponents")
    if isinstance(ops, list):
        for o in ops[:3]:
            if not isinstance(o, dict):
                continue
            name = str(o.get("name", "")).strip()[:60]
            if not name:
                continue
            try:
                ri = int(max(0, min(7, int(o.get("realm_index", 0)))))
            except (TypeError, ValueError):
                ri = 0
            try:
                pr = float(max(1.0, min(12.0, float(o.get("progress", 1)))))
            except (TypeError, ValueError):
                pr = 1.0
            opponents.append({"name": name, "realm_index": ri, "progress": pr})
    return {"narrative": narrative, "event_type": etype, "choices": choices,
            "opponents": opponents}, None


def _validate_outcome(data):
    if not isinstance(data, dict):
        return None, "phải là object JSON"
    outcome = str(data.get("outcome", "")).strip()
    if len(outcome) < 5 or len(outcome) > 800:
        return None, "outcome phải dài 5-800 ký tự"
    effects = data.get("effects")
    if effects is None:
        effects = {}
    if not isinstance(effects, dict):
        return None, "effects phải là object"
    return {"outcome": outcome, "effects": effects}, None


def generate_event(context, instruction):
    """Tao bien co moi tu ngu canh game. Raise AIServiceError neu that bai."""
    cfg = load_config()
    if not is_configured(cfg):
        raise AIServiceError("Chưa cấu hình AI. Mở trang Cài đặt AI, điền Base URL, "
                             "API key và Model ID rồi lưu lại.")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            "NGỮ CẢNH GAME (JSON):\n" + json.dumps(context, ensure_ascii=False, indent=1) +
            "\n\nNHIỆM VỤ: " + instruction +
            "\n\nTRẢ VỀ ĐÚNG CẤU TRÚC JSON SAU:\n" + EVENT_SCHEMA +
            "\nYÊU CẦU: đúng 3 hoặc 4 lựa chọn, id lần lượt là A, B, C, D; label tối đa 6 từ; "
            "description là một câu ngắn. Chỉ đặt \"combat\": true khi lựa chọn đó là giao tranh "
            "trực diện công bằng. Chỉ thêm \"opponents\" khi biến cố liên quan một kẻ địch cụ thể."
        )},
    ]
    max_tokens = int(cfg.get("max_tokens", 700))
    temperature = float(cfg.get("temperature", 0.9))
    last_err = None
    for _ in range(2):
        data = _chat_json(cfg, messages, max_tokens, temperature)
        event, err = _validate_event(data)
        if event is not None:
            return event
        last_err = err
        messages = messages + [
            {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)[:1500]},
            {"role": "user", "content": "Biến cố vừa rồi không hợp lệ: " + err +
             " Hãy trả lại JSON đúng cấu trúc, đúng 3-4 lựa chọn, không thêm gì khác."},
        ]
    raise AIServiceError("AI trả về biến cố không hợp lệ: " + (last_err or "không rõ"))


def resolve_choice(context):
    """Phan giai mot lua chon cua nguoi choi thanh ket qua + hieu ung."""
    cfg = load_config()
    if not is_configured(cfg):
        raise AIServiceError("Chưa cấu hình AI. Mở trang Cài đặt AI để hoàn tất trước khi tiếp tục.")
    combat_note = ""
    v = context.get("combat_verdict")
    if v:
        combat_note = (
            "\n\nKẾT QUẢ CHIẾN ĐẤU DO HỆ THỐNG TÍNH TOÁN — BẮT BUỘC TUÂN THEO ĐÚNG: "
            "kết quả " + v["result"] + " (" + v["text"] + ") với " + str(v.get("opponent", "")) + ". "
            "Hệ quả bắt buộc: sức khỏe thay đổi " + str(v["health_delta"]) +
            ", linh thạch thay đổi " + str(v.get("stones_delta", 0)) +
            ", trạng thái thêm: " + (", ".join(v.get("status_add") or []) or "không") + ". " +
            ("Nhân vật TỬ VONG. " if v.get("result") == "death" else "Nhân vật sống sót. ") +
            "Hãy viết outcome khớp với kết quả này, KHÔNG đảo ngược thắng thua."
        )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            "NGỮ CẢNH GAME (JSON):\n" + json.dumps(context, ensure_ascii=False, indent=1) +
            combat_note +
            "\n\nTRẢ VỀ ĐÚNG CẤU TRÚC JSON SAU:\n" + EFFECTS_SCHEMA +
            "\nYÊU CẦU: outcome 1-2 câu. Chỉ dùng những trường effects cần thiết, bỏ qua số 0 và "
            "mảng rỗng. Không tiêu linh thạch nhiều hơn số nhân vật đang có. Không tự ý giết nhân vật. "
            "Nếu hành động thất bại thì thể hiện qua health_delta âm hoặc mất vật phẩm, không tặng thưởng."
        )},
    ]
    max_tokens = int(cfg.get("max_tokens", 700))
    data = _chat_json(cfg, messages, max_tokens, min(0.9, float(cfg.get("temperature", 0.9))))
    out, err = _validate_outcome(data)
    if out is None:
        data2 = _chat_json(cfg, messages + [
            {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)[:1500]},
            {"role": "user", "content": "Phản hồi không hợp lệ: " + err +
             " Trả lại JSON đúng cấu trúc đã yêu cầu."},
        ], max_tokens, 0.7)
        out, err = _validate_outcome(data2)
        if out is None:
            raise AIServiceError("AI trả về kết quả không hợp lệ: " + err)
    return out


def test_connection(cfg):
    """Kiem tra ket noi bang mot yeu cau that su. Tra ve chuoi thong bao thanh cong."""
    if not (cfg.get("base_url") and cfg.get("api_key") and cfg.get("model_id")):
        raise AIServiceError("Chưa điền đủ Base URL, API key và Model ID.")
    _chat(cfg, [{"role": "user", "content": "Trả lời đúng một chữ: OK"}], 16, 0.0)
    return "Kết nối thành công! Model \"" + str(cfg.get("model_id")) + "\" đã phản hồi."
