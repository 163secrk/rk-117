import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '新玩家',
                gold INTEGER NOT NULL DEFAULT 5000,
                enhance_stones INTEGER NOT NULL DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 0,
                base_name TEXT NOT NULL,
                FOREIGN KEY (player_id) REFERENCES player (id)
            )
        """)

        cursor.execute("SELECT COUNT(*) as cnt FROM player")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            cursor.execute("INSERT INTO player (name, gold, enhance_stones) VALUES (?, ?, ?)", ("新玩家", 5000, 30))
            player_id = cursor.lastrowid
            default_equips = [
                (player_id, "weapon", "铁剑", 0, "铁剑"),
                (player_id, "helmet", "布帽", 0, "布帽"),
                (player_id, "armor", "布衣", 0, "布衣"),
                (player_id, "necklace", "铜项链", 0, "铜项链"),
            ]
            cursor.executemany(
                "INSERT INTO equipment (player_id, slot, name, level, base_name) VALUES (?, ?, ?, ?, ?)",
                default_equips
            )


SLOT_ATTRIBUTE_INFO = {
    "weapon": {"attr_key": "attack", "attr_name": "攻击", "icon": "⚔", "per_level": 5},
    "helmet": {"attr_key": "hp", "attr_name": "血量", "icon": "❤", "per_level": 20},
    "armor": {"attr_key": "defense", "attr_name": "防御", "icon": "🛡", "per_level": 3},
    "necklace": {"attr_key": "crit", "attr_name": "暴击率", "icon": "💥", "per_level": 1, "is_percent": True},
}


def get_slot_attribute(slot: str, level: int):
    info = SLOT_ATTRIBUTE_INFO.get(slot)
    if not info:
        return None
    value = info["per_level"] * level
    return {
        "key": info["attr_key"],
        "name": info["attr_name"],
        "icon": info["icon"],
        "value": value,
        "per_level": info["per_level"],
        "is_percent": info.get("is_percent", False),
    }


def get_upgrade_cost(level: int) -> int:
    base_cost = 100
    return int(base_cost * (1.5 ** level))


def get_enhance_stone_cost(level: int) -> int:
    if level < 5:
        return 1
    return level - 3


def get_success_rate(level: int) -> float:
    rates = {
        0: 1.0,
        1: 0.95,
        2: 0.90,
        3: 0.85,
        4: 0.80,
        5: 0.70,
        6: 0.60,
        7: 0.50,
        8: 0.40,
        9: 0.30,
        10: 0.25,
        11: 0.20,
        12: 0.15,
        13: 0.12,
        14: 0.10,
        15: 0.08,
        16: 0.06,
        17: 0.04,
        18: 0.03,
        19: 0.02,
    }
    return rates.get(level, 0.01)
