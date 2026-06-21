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


def _add_column_if_not_exists(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row["name"] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '新玩家',
                gold INTEGER NOT NULL DEFAULT 5000,
                enhance_stones INTEGER NOT NULL DEFAULT 30,
                protect_scrolls INTEGER NOT NULL DEFAULT 0,
                lucky_charms INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        _add_column_if_not_exists(cursor, "player", "protect_scrolls", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_not_exists(cursor, "player", "lucky_charms", "INTEGER NOT NULL DEFAULT 0")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 0,
                base_name TEXT NOT NULL,
                quality TEXT NOT NULL DEFAULT 'white',
                affix_key TEXT,
                affix_value REAL,
                affix_name TEXT,
                FOREIGN KEY (player_id) REFERENCES player (id)
            )
        """)

        _add_column_if_not_exists(cursor, "equipment", "quality", "TEXT NOT NULL DEFAULT 'white'")
        _add_column_if_not_exists(cursor, "equipment", "affix_key", "TEXT")
        _add_column_if_not_exists(cursor, "equipment", "affix_value", "REAL")
        _add_column_if_not_exists(cursor, "equipment", "affix_name", "TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 0,
                base_name TEXT NOT NULL,
                quality TEXT NOT NULL DEFAULT 'white',
                affix_key TEXT,
                affix_value REAL,
                affix_name TEXT,
                is_equipped INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES player (id)
            )
        """)

        _add_column_if_not_exists(cursor, "inventory", "quality", "TEXT NOT NULL DEFAULT 'white'")
        _add_column_if_not_exists(cursor, "inventory", "affix_key", "TEXT")
        _add_column_if_not_exists(cursor, "inventory", "affix_value", "REAL")
        _add_column_if_not_exists(cursor, "inventory", "affix_name", "TEXT")

        cursor.execute("SELECT COUNT(*) as cnt FROM player")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            cursor.execute(
                "INSERT INTO player (name, gold, enhance_stones, protect_scrolls, lucky_charms) VALUES (?, ?, ?, ?, ?)",
                ("新玩家", 50000, 30, 0, 0)
            )
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
            cursor.executemany(
                "INSERT INTO inventory (player_id, slot, name, level, base_name, is_equipped) VALUES (?, ?, ?, ?, ?, 1)",
                default_equips
            )

        cursor.execute("SELECT id FROM player")
        all_players = cursor.fetchall()
        for p in all_players:
            pid = p["id"]
            cursor.execute("SELECT * FROM equipment WHERE player_id = ?", (pid,))
            equips = cursor.fetchall()
            for e in equips:
                cursor.execute(
                    "SELECT COUNT(*) as cnt FROM inventory WHERE player_id = ? AND slot = ? AND level = ? AND base_name = ?",
                    (pid, e["slot"], e["level"], e["base_name"])
                )
                if cursor.fetchone()["cnt"] == 0:
                    cursor.execute(
                        "INSERT INTO inventory (player_id, slot, name, level, base_name, is_equipped) VALUES (?, ?, ?, ?, ?, 1)",
                        (pid, e["slot"], e["name"], e["level"], e["base_name"])
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
    if level < 6:
        return 1
    return level - 4


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


QUALITY_CONFIG = {
    "white": {
        "name": "普通",
        "color": "white",
        "multiplier": 1.0,
        "weight": 50,
        "affix_chance": 0.0,
    },
    "green": {
        "name": "优秀",
        "color": "green",
        "multiplier": 1.5,
        "weight": 30,
        "affix_chance": 0.0,
    },
    "purple": {
        "name": "稀有",
        "color": "purple",
        "multiplier": 2.0,
        "weight": 15,
        "affix_chance": 0.0,
    },
    "orange": {
        "name": "传说",
        "color": "orange",
        "multiplier": 3.0,
        "weight": 5,
        "affix_chance": 0.0,
    },
}

QUALITY_ORDER = ["white", "green", "purple", "orange"]


AFFIX_POOL = [
    {"key": "attack_pct", "name": "攻击", "value": 0.10, "is_percent": True, "slot": "weapon", "icon": "⚔"},
    {"key": "crit_pct", "name": "暴击率", "value": 0.05, "is_percent": True, "slot": "weapon", "icon": "💥"},
    {"key": "hp_pct", "name": "血量", "value": 0.10, "is_percent": True, "slot": "helmet", "icon": "❤"},
    {"key": "defense_pct", "name": "防御", "value": 0.10, "is_percent": True, "slot": "armor", "icon": "🛡"},
    {"key": "crit_dmg_pct", "name": "暴击伤害", "value": 0.15, "is_percent": True, "slot": "necklace", "icon": "💫"},
    {"key": "attack_pct", "name": "攻击", "value": 0.08, "is_percent": True, "slot": "necklace", "icon": "⚔"},
]


def roll_random_quality() -> str:
    import random
    total_weight = sum(cfg["weight"] for cfg in QUALITY_CONFIG.values())
    roll = random.randint(1, total_weight)
    cum = 0
    for q_key in QUALITY_ORDER:
        cum += QUALITY_CONFIG[q_key]["weight"]
        if roll <= cum:
            return q_key
    return "white"


def get_quality_info(quality: str) -> dict:
    return QUALITY_CONFIG.get(quality, QUALITY_CONFIG["white"])


def get_quality_name(quality: str) -> str:
    return get_quality_info(quality)["name"]


def get_quality_color(quality: str) -> str:
    return get_quality_info(quality)["color"]


def get_quality_multiplier(quality: str) -> float:
    return get_quality_info(quality)["multiplier"]


def roll_random_affix(slot: str, quality: str) -> dict | None:
    import random
    if quality not in QUALITY_CONFIG:
        return None
    quality_idx = QUALITY_ORDER.index(quality)
    if quality_idx < 1:
        return None

    pool = [a for a in AFFIX_POOL if a["slot"] == slot]
    if not pool:
        pool = AFFIX_POOL

    affix = random.choice(pool)
    value_multiplier = 1.0 + quality_idx * 0.3
    return {
        "key": affix["key"],
        "name": affix["name"],
        "value": round(affix["value"] * value_multiplier, 4),
        "is_percent": affix["is_percent"],
        "icon": affix["icon"],
    }


def get_slot_attribute(slot: str, level: int, quality: str = "white"):
    info = SLOT_ATTRIBUTE_INFO.get(slot)
    if not info:
        return None
    multiplier = get_quality_multiplier(quality)
    base_value = info["per_level"] * level
    value = int(base_value * multiplier) if not info.get("is_percent") else round(base_value * multiplier, 2)
    return {
        "key": info["attr_key"],
        "name": info["attr_name"],
        "icon": info["icon"],
        "value": value,
        "per_level": info["per_level"],
        "is_percent": info.get("is_percent", False),
        "multiplier": multiplier,
    }


EQUIPMENT_BASE_NAMES = {
    "weapon": {
        0: "铁剑", 5: "钢剑", 10: "精钢剑", 15: "秘银剑", 18: "龙牙剑"
    },
    "helmet": {
        0: "布帽", 5: "皮帽", 10: "铁盔", 15: "钢盔", 18: "龙骨盔"
    },
    "armor": {
        0: "布衣", 5: "皮甲", 10: "铁甲", 15: "钢甲", 18: "龙鳞甲"
    },
    "necklace": {
        0: "铜项链", 5: "银项链", 10: "金项链", 15: "宝石项链", 18: "龙心项链"
    },
}


def get_equipment_base_name(slot: str, level: int) -> str:
    names = EQUIPMENT_BASE_NAMES.get(slot, {})
    result = "未知"
    for min_level, name in sorted(names.items()):
        if level >= min_level:
            result = name
    return result


def get_equipment_quality(level: int, quality: str = "white") -> str:
    return get_quality_name(quality)


def get_equipment_quality_color(level: int, quality: str = "white") -> str:
    return get_quality_color(quality)


MONSTER_TIERS = [
    {"tier": "weak", "power_range": (20, 80), "hp_range": (50, 150),
     "names": ["史莱姆", "哥布林", "野狼", "毒蜘蛛", "蝙蝠", "骷髅兵"]},
    {"tier": "normal", "power_range": (80, 200), "hp_range": (150, 400),
     "names": ["兽人战士", "石像鬼", "狼人", "巨型蝎子", "暗影刺客", "食人魔"]},
    {"tier": "strong", "power_range": (200, 500), "hp_range": (400, 1000),
     "names": ["巨魔", "独眼巨人", "龙人", "黑暗骑士", "火焰元素", "冰霜巨人"]},
    {"tier": "elite", "power_range": (500, 1200), "hp_range": (1000, 2500),
     "names": ["远古巨龙", "恶魔领主", "死灵法师", "深渊领主", "泰坦守卫", "凤凰"]},
    {"tier": "boss", "power_range": (1200, 3000), "hp_range": (2500, 6000),
     "names": ["毁灭之王", "虚空之主", "时光守护者", "混沌邪神", "世界树化身", "星海巨兽"]},
]


def calculate_player_power(player_id: int) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment WHERE player_id = ?", (player_id,))
        rows = cursor.fetchall()
        equips = [dict(row) for row in rows]

    total_power = 50

    base_attrs = {"attack": 0, "hp": 0, "defense": 0, "crit": 0}

    for equip in equips:
        slot = equip["slot"]
        level = equip["level"] or 0
        quality = equip.get("quality", "white")
        attr = get_slot_attribute(slot, level, quality)
        if attr:
            base_attrs[attr["key"]] += attr["value"]

        affix_key = equip.get("affix_key")
        affix_value = equip.get("affix_value")
        if affix_key and affix_value and level >= 10:
            if affix_key == "attack_pct":
                base_attrs["attack"] = int(base_attrs["attack"] * (1 + affix_value))
            elif affix_key == "hp_pct":
                base_attrs["hp"] = int(base_attrs["hp"] * (1 + affix_value))
            elif affix_key == "defense_pct":
                base_attrs["defense"] = int(base_attrs["defense"] * (1 + affix_value))
            elif affix_key == "crit_pct":
                base_attrs["crit"] += affix_value * 100

    total_power += base_attrs["attack"] * 3
    total_power += base_attrs["hp"] // 5
    total_power += base_attrs["defense"] * 4
    total_power += base_attrs["crit"] * 20

    return int(total_power)
