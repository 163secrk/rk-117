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
                FOREIGN KEY (player_id) REFERENCES player (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 0,
                base_name TEXT NOT NULL,
                is_equipped INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES player (id)
            )
        """)

        cursor.execute("SELECT COUNT(*) as cnt FROM player")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            cursor.execute(
                "INSERT INTO player (name, gold, enhance_stones, protect_scrolls, lucky_charms) VALUES (?, ?, ?, ?, ?)",
                ("新玩家", 5000, 30, 0, 0)
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


EQUIPMENT_TIERS = [
    {"min_level": 0, "max_level": 3, "quality": "普通", "color": "white",
     "names": {"weapon": "铁剑", "helmet": "布帽", "armor": "布衣", "necklace": "铜项链"}},
    {"min_level": 4, "max_level": 7, "quality": "优秀", "color": "green",
     "names": {"weapon": "钢剑", "helmet": "皮帽", "armor": "皮甲", "necklace": "银项链"}},
    {"min_level": 8, "max_level": 11, "quality": "稀有", "color": "blue",
     "names": {"weapon": "精钢剑", "helmet": "铁盔", "armor": "铁甲", "necklace": "金项链"}},
    {"min_level": 12, "max_level": 15, "quality": "史诗", "color": "purple",
     "names": {"weapon": "秘银剑", "helmet": "钢盔", "armor": "钢甲", "necklace": "宝石项链"}},
    {"min_level": 16, "max_level": 20, "quality": "传说", "color": "orange",
     "names": {"weapon": "龙牙剑", "helmet": "龙骨盔", "armor": "龙鳞甲", "necklace": "龙心项链"}},
]


def get_equipment_tier(level: int):
    for tier in reversed(EQUIPMENT_TIERS):
        if level >= tier["min_level"]:
            return tier
    return EQUIPMENT_TIERS[0]


def get_equipment_base_name(slot: str, level: int) -> str:
    tier = get_equipment_tier(level)
    return tier["names"].get(slot, "未知")


def get_equipment_quality(level: int) -> str:
    tier = get_equipment_tier(level)
    return tier["quality"]


def get_equipment_quality_color(level: int) -> str:
    tier = get_equipment_tier(level)
    return tier["color"]


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
        equips = cursor.fetchall()

    total_power = 50

    for equip in equips:
        slot = equip["slot"]
        level = equip["level"] or 0
        attr = get_slot_attribute(slot, level)
        if attr:
            value = attr["value"]
            if attr.get("is_percent"):
                total_power += value * 20
            else:
                if attr["key"] == "attack":
                    total_power += value * 3
                elif attr["key"] == "hp":
                    total_power += value // 5
                elif attr["key"] == "defense":
                    total_power += value * 4
                else:
                    total_power += value

    return total_power
