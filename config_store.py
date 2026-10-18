# -*- coding: utf-8 -*-
"""Luu va doc cau hinh AI (chua API key) trong file rieng tai may nguoi choi.

File: config/ai_config.json - tu dong tao khi luu lan dau.
File nay khong duoc dua len kho ma nguon (da loc trong .gitignore).
API key chi backend doc, khong bao gio tra ve frontend.
"""
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "ai_config.json")

DEFAULTS = {
    "provider_name": "",
    "base_url": "",
    "api_key": "",
    "model_id": "",
    "temperature": 0.9,
    "max_tokens": 700,
}


def load():
    """Doc cau hinh, hop nhat voi gia tri mac dinh."""
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return cfg


def is_configured(cfg=None):
    cfg = cfg or load()
    return bool(cfg.get("base_url")) and bool(cfg.get("api_key")) and bool(cfg.get("model_id"))


def save(cfg):
    """Kiem tra kieu du lieu va ghi cau hinh ra file rieng."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    clean = dict(DEFAULTS)
    for k in DEFAULTS:
        if k in cfg:
            clean[k] = cfg[k]
    for k in ("provider_name", "base_url", "api_key", "model_id"):
        clean[k] = str(clean[k] or "").strip()
    try:
        clean["temperature"] = max(0.0, min(2.0, float(clean["temperature"])))
    except (TypeError, ValueError):
        clean["temperature"] = 0.9
    try:
        clean["max_tokens"] = int(max(120, min(4000, int(clean["max_tokens"]))))
    except (TypeError, ValueError):
        clean["max_tokens"] = 700
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_PATH)
    return clean


def masked():
    """Tra ve trang thai cau hinh de hien thi, khong tra ve API key."""
    cfg = load()
    key = cfg.get("api_key") or ""
    hint = ("****" + key[-4:]) if len(key) >= 8 else ("****" if key else "")
    return {
        "provider_name": cfg.get("provider_name", ""),
        "base_url": cfg.get("base_url", ""),
        "model_id": cfg.get("model_id", ""),
        "temperature": cfg.get("temperature", 0.9),
        "max_tokens": cfg.get("max_tokens", 700),
        "api_key_set": bool(key),
        "api_key_hint": hint,
        "configured": is_configured(cfg),
    }
