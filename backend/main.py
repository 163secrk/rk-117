import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db, get_db, get_upgrade_cost, get_enhance_stone_cost, get_success_rate

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
    enhance_stones: int | None = None


class ShopResponse(BaseModel):
    success: bool
    message: str
    gold: int | None = None
    enhance_stones: int | None = None


def get_default_player():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM player ORDER BY id ASC LIMIT 1")
        player = cursor.fetchone()
        if not player:
            cursor.execute("INSERT INTO player (name, gold, enhance_stones) VALUES (?, ?, ?)", ("新玩家", 5000, 30))
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
        stone_cost = get_enhance_stone_cost(current_level)

        if player["gold"] < cost:
            return UpgradeResponse(success=False, message=f"金币不足，需要 {cost} 金币")

        if player["enhance_stones"] < stone_cost:
            return UpgradeResponse(success=False, message=f"强化石不足，需要 {stone_cost} 颗强化石")

        cursor.execute("UPDATE player SET gold = gold - ?, enhance_stones = enhance_stones - ? WHERE id = ?", (cost, stone_cost, player["id"]))

        rate = get_success_rate(current_level)
        roll = random.random()

        cursor.execute("SELECT gold, enhance_stones FROM player WHERE id = ?", (player["id"],))
        player_data = cursor.fetchone()
        new_gold = player_data["gold"]
        new_stones = player_data["enhance_stones"]

        if roll < rate:
            new_level = current_level + 1
            cursor.execute("UPDATE equipment SET level = ? WHERE id = ?", (new_level, equipment_id))
            return UpgradeResponse(
                success=True,
                message=f"强化成功！+{current_level} → +{new_level}",
                new_level=new_level,
                gold=new_gold,
                enhance_stones=new_stones
            )
        else:
            return UpgradeResponse(
                success=False,
                message=f"强化失败！+{current_level} 保持不变",
                new_level=current_level,
                gold=new_gold,
                enhance_stones=new_stones
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
                "stone_cost": 0,
                "success_rate": 0.0,
                "is_max": True
            }
        return {
            "current_level": current_level,
            "next_level": current_level + 1,
            "max_level": 20,
            "cost": get_upgrade_cost(current_level),
            "stone_cost": get_enhance_stone_cost(current_level),
            "success_rate": get_success_rate(current_level),
            "is_max": False
        }


@app.post("/api/shop/buy_stones/{amount}")
def buy_stones(amount: int):
    player = get_default_player()

    if amount <= 0:
        return ShopResponse(success=False, message="购买数量必须大于0")

    price_per_stone = 10
    total_cost = amount * price_per_stone

    with get_db() as conn:
        cursor = conn.cursor()

        if player["gold"] < total_cost:
            return ShopResponse(success=False, message=f"金币不足，需要 {total_cost} 金币")

        cursor.execute("UPDATE player SET gold = gold - ?, enhance_stones = enhance_stones + ? WHERE id = ?", (total_cost, amount, player["id"]))

        cursor.execute("SELECT gold, enhance_stones FROM player WHERE id = ?", (player["id"],))
        player_data = cursor.fetchone()
        new_gold = player_data["gold"]
        new_stones = player_data["enhance_stones"]

        return ShopResponse(
            success=True,
            message=f"成功购买 {amount} 颗强化石",
            gold=new_gold,
            enhance_stones=new_stones
        )
