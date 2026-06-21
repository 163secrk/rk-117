import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db, get_db, get_upgrade_cost, get_success_rate

app = FastAPI(title="装备强化游戏API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


class UpgradeResponse(BaseModel):
    success: bool
    message: str
    new_level: int | None = None
    gold: int | None = None


def get_default_player():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM player ORDER BY id ASC LIMIT 1")
        player = cursor.fetchone()
        if not player:
            cursor.execute("INSERT INTO player (name, gold) VALUES (?, ?)", ("新玩家", 5000))
            player_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO equipment (player_id, slot, name, level, base_name) VALUES (?, ?, ?, ?, ?)",
                (player_id, "weapon", "铁剑", 0, "铁剑")
            )
            cursor.execute("SELECT * FROM player WHERE id = ?", (player_id,))
            player = cursor.fetchone()
        return dict(player)


@app.get("/api/player")
def get_player():
    return get_default_player()


@app.get("/api/equipment")
def get_equipment():
    player = get_default_player()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment WHERE player_id = ?", (player["id"],))
        rows = cursor.fetchall()
        equips = [dict(row) for row in rows]

        slots = ["weapon", "helmet", "armor", "necklace"]
        result = []
        for slot in slots:
            equip = next((e for e in equips if e["slot"] == slot), None)
            if equip:
                display_name = equip["base_name"] if equip["level"] == 0 else f"+{equip['level']} {equip['base_name']}"
                equip["display_name"] = display_name
                result.append(equip)
            else:
                result.append({
                    "id": None,
                    "player_id": player["id"],
                    "slot": slot,
                    "name": None,
                    "level": None,
                    "base_name": None,
                    "display_name": "（空）",
                    "empty": True
                })
        return result


@app.post("/api/upgrade/{equipment_id}")
def upgrade_equipment(equipment_id: int):
    player = get_default_player()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment WHERE id = ? AND player_id = ?", (equipment_id, player["id"]))
        equip = cursor.fetchone()
        if not equip:
            raise HTTPException(status_code=404, detail="装备不存在")

        equip = dict(equip)
        current_level = equip["level"]

        if current_level >= 20:
            return UpgradeResponse(success=False, message="已达到最高等级+20")

        cost = get_upgrade_cost(current_level)
        if player["gold"] < cost:
            return UpgradeResponse(success=False, message=f"金币不足，需要 {cost} 金币")

        cursor.execute("UPDATE player SET gold = gold - ? WHERE id = ?", (cost, player["id"]))

        rate = get_success_rate(current_level)
        roll = random.random()

        if roll < rate:
            new_level = current_level + 1
            cursor.execute("UPDATE equipment SET level = ? WHERE id = ?", (new_level, equipment_id))
            cursor.execute("SELECT gold FROM player WHERE id = ?", (player["id"],))
            new_gold = cursor.fetchone()["gold"]
            return UpgradeResponse(
                success=True,
                message=f"强化成功！+{current_level} → +{new_level}",
                new_level=new_level,
                gold=new_gold
            )
        else:
            cursor.execute("SELECT gold FROM player WHERE id = ?", (player["id"],))
            new_gold = cursor.fetchone()["gold"]
            return UpgradeResponse(
                success=False,
                message=f"强化失败！+{current_level} 保持不变",
                new_level=current_level,
                gold=new_gold
            )


@app.get("/api/upgrade/info/{equipment_id}")
def get_upgrade_info(equipment_id: int):
    player = get_default_player()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment WHERE id = ? AND player_id = ?", (equipment_id, player["id"]))
        equip = cursor.fetchone()
        if not equip:
            raise HTTPException(status_code=404, detail="装备不存在")
        equip = dict(equip)
        current_level = equip["level"]
        if current_level >= 20:
            return {
                "current_level": current_level,
                "max_level": 20,
                "cost": 0,
                "success_rate": 0.0,
                "is_max": True
            }
        return {
            "current_level": current_level,
            "next_level": current_level + 1,
            "max_level": 20,
            "cost": get_upgrade_cost(current_level),
            "success_rate": get_success_rate(current_level),
            "is_max": False
        }
