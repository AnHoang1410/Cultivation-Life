# -*- coding: utf-8 -*-
"""Luu tru du lieu SQLite: nhan vat, NPC, the luc, tui do, nhat ky cuoc doi."""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "tiendovankiep.db")


def get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gender TEXT DEFAULT 'Nam',
    origin_key TEXT DEFAULT 'nguoi_pham',
    origin_label TEXT DEFAULT 'Người Phàm',
    root_key TEXT DEFAULT 'tap',
    root_name TEXT DEFAULT 'Tạp Linh Căn',
    root_mult REAL DEFAULT 1.0,
    aptitude INTEGER DEFAULT 40,
    comprehension INTEGER DEFAULT 40,
    bone INTEGER DEFAULT 40,
    luck INTEGER DEFAULT 50,
    charm INTEGER DEFAULT 40,
    spirit_sense INTEGER DEFAULT 14,
    health REAL DEFAULT 100,
    mind REAL DEFAULT 75,
    reputation REAL DEFAULT 0,
    technique_name TEXT DEFAULT 'Vô Danh Khẩu Quyết',
    technique_quality INTEGER DEFAULT 1,
    faction_id INTEGER,
    spirit_stones INTEGER DEFAULT 20,
    age INTEGER DEFAULT 16,
    base_lifespan INTEGER DEFAULT 80,
    extra_lifespan INTEGER DEFAULT 0,
    realm_index INTEGER DEFAULT 0,
    progress REAL DEFAULT 1.0,
    statuses TEXT DEFAULT '[]',
    alive INTEGER DEFAULT 1,
    death_cause TEXT,
    death_age INTEGER,
    pending_event TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    identity TEXT DEFAULT 'Tán tu',
    realm_index INTEGER DEFAULT 0,
    progress REAL DEFAULT 1,
    personality TEXT DEFAULT '',
    goal TEXT DEFAULT '',
    relationship_value REAL DEFAULT 0,
    role TEXT DEFAULT '',
    alive INTEGER DEFAULT 1,
    notes TEXT DEFAULT '',
    created_age INTEGER DEFAULT 16
);
CREATE TABLE IF NOT EXISTS factions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'Tông môn',
    leader TEXT DEFAULT '',
    resources TEXT DEFAULT '',
    reputation REAL DEFAULT 0,
    power_realm INTEGER DEFAULT 0,
    territory TEXT DEFAULT '',
    description TEXT DEFAULT '',
    is_player_founded INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    item_type TEXT DEFAULT 'tạp vật',
    quality INTEGER DEFAULT 1,
    quantity INTEGER DEFAULT 1,
    description TEXT DEFAULT '',
    usable_key TEXT,
    equipped INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS log_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    age INTEGER NOT NULL,
    event_type TEXT DEFAULT 'he_thong',
    content TEXT NOT NULL,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_log_char ON log_entries(character_id, id);
CREATE INDEX IF NOT EXISTS idx_npc_char ON npcs(character_id);
CREATE INDEX IF NOT EXISTS idx_inv_char ON inventory(character_id);
CREATE INDEX IF NOT EXISTS idx_fac_char ON factions(character_id);
"""


def init_db():
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def query(conn, sql, params=()):
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def query_one(conn, sql, params=()):
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    return dict(row) if row is not None else None


def execute(conn, sql, params=()):
    cur = conn.execute(sql, params)
    return cur.lastrowid
