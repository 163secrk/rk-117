import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db, get_db, get_upgrade_cost, get_enhance_stone_cost, get_success_rate, get_slot_attribute

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
    protect_scrolls: int | None = None
    lucky_charms: int | None = None


class ShopResponse(BaseModel):
    success: bool
    message: str
    gold: int | None = None
    enhance_stones: int | None = None
    protect_scrolls: int | None = None
    lucky_charms: int | None = None


class UpgradeRequest(BaseModel):
    use_protect_scroll: bool = False
    use_lucky_charm: bool = False


def get_default_player():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM player ORDER BY id ASC LIMIT 1")
        player = cursor.fetchone()
        if not player:
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
            cursor.execute("SELECT * FROM player WHERE id = ?", (player_id,))
            player = cursor.fetchone()
        player_id = player["id"]
        cursor.execute("SELECT * FROM equipment WHERE player_id = ?", (player_id,))
        equips = cursor.fetchall()
        if len(equips) < 4:
            existing_slots = {e["slot"] for e in equips}
            all_slots = {
                "weapon": ("铁剑", "铁剑"),
                "helmet": ("布帽", "布帽"),
                "armor": ("布衣", "布衣"),
                "necklace": ("铜项链", "铜项链"),
            }
            for slot, (name, base_name) in all_slots.items():
                if slot not in existing_slots:
                    cursor.execute(
                        "INSERT INTO equipment (player_id, slot, name, level, base_name) VALUES (?, ?, ?, ?, ?)",
                        (player_id, slot, name, 0, base_name)
                    )
        result = dict(player)
        result.setdefault("protect_scrolls", 0)
        result.setdefault("lucky_charms", 0)
        return result


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
                level = equip["level"] or 0
                display_name = equip["base_name"] if level == 0 else f"+{level} {equip['base_name']}"
                equip["display_name"] = display_name
                attr = get_slot_attribute(slot, level)
                next_attr = get_slot_attribute(slot, level + 1)
                equip["attribute"] = attr
                equip["next_attribute"] = next_attr
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
                    "empty": True,
                    "attribute": None,
                    "next_attribute": None
                })
        return result


@app.post("/api/upgrade/{equipment_id}")
def upgrade_equipment(equipment_id: int, request: UpgradeRequest = UpgradeRequest()):
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

        use_protect = request.use_protect_scroll
        use_lucky = request.use_lucky_charm

        if use_protect and player.get("protect_scrolls", 0) < 1:
            return UpgradeResponse(success=False, message="保护卷不足")

        if use_lucky and player.get("lucky_charms", 0) < 1:
            return UpgradeResponse(success=False, message="幸运符不足")

        cursor.execute("UPDATE player SET gold = gold - ?, enhance_stones = enhance_stones - ? WHERE id = ?", (cost, stone_cost, player["id"]))

        if use_protect:
            cursor.execute("UPDATE player SET protect_scrolls = protect_scrolls - 1 WHERE id = ?", (player["id"],))

        if use_lucky:
            cursor.execute("UPDATE player SET lucky_charms = lucky_charms - 1 WHERE id = ?", (player["id"],))

        base_rate = get_success_rate(current_level)
        rate = min(base_rate + 0.15 if use_lucky else base_rate, 1.0)
        roll = random.random()

        cursor.execute("SELECT gold, enhance_stones, protect_scrolls, lucky_charms FROM player WHERE id = ?", (player["id"],))
        player_data = cursor.fetchone()
        new_gold = player_data["gold"]
        new_stones = player_data["enhance_stones"]
        new_scrolls = player_data["protect_scrolls"]
        new_charms = player_data["lucky_charms"]

        if roll < rate:
            new_level = current_level + 1
            cursor.execute("UPDATE equipment SET level = ? WHERE id = ?", (new_level, equipment_id))
            msg = f"强化成功！+{current_level} → +{new_level}"
            if use_lucky:
                msg += "（幸运符生效）"
            return UpgradeResponse(
                success=True,
                message=msg,
                new_level=new_level,
                gold=new_gold,
                enhance_stones=new_stones,
                protect_scrolls=new_scrolls,
                lucky_charms=new_charms
            )
        else:
            if use_protect:
                cursor.execute("UPDATE player SET enhance_stones = enhance_stones + ? WHERE id = ?", (stone_cost, player["id"]))
                cursor.execute("SELECT enhance_stones FROM player WHERE id = ?", (player["id"],))
                new_stones = cursor.fetchone()["enhance_stones"]
                msg = f"强化失败！保护卷生效，已返还 {stone_cost} 颗强化石"
            else:
                msg = f"强化失败！+{current_level} 保持不变"
            return UpgradeResponse(
                success=False,
                message=msg,
                new_level=current_level,
                gold=new_gold,
                enhance_stones=new_stones,
                protect_scrolls=new_scrolls,
                lucky_charms=new_charms
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

        cursor.execute("SELECT gold, enhance_stones, protect_scrolls, lucky_charms FROM player WHERE id = ?", (player["id"],))
        player_data = cursor.fetchone()
        new_gold = player_data["gold"]
        new_stones = player_data["enhance_stones"]
        new_scrolls = player_data["protect_scrolls"]
        new_charms = player_data["lucky_charms"]

        return ShopResponse(
            success=True,
            message=f"成功购买 {amount} 颗强化石",
            gold=new_gold,
            enhance_stones=new_stones,
            protect_scrolls=new_scrolls,
            lucky_charms=new_charms
        )


@app.post("/api/shop/buy_protect_scrolls/{amount}")
def buy_protect_scrolls(amount: int):
    player = get_default_player()

    if amount <= 0:
        return ShopResponse(success=False, message="购买数量必须大于0")

    price_per_scroll = 500
    total_cost = amount * price_per_scroll

    with get_db() as conn:
        cursor = conn.cursor()

        if player["gold"] < total_cost:
            return ShopResponse(success=False, message=f"金币不足，需要 {total_cost} 金币")

        cursor.execute("UPDATE player SET gold = gold - ?, protect_scrolls = protect_scrolls + ? WHERE id = ?", (total_cost, amount, player["id"]))

        cursor.execute("SELECT gold, enhance_stones, protect_scrolls, lucky_charms FROM player WHERE id = ?", (player["id"],))
        player_data = cursor.fetchone()
        new_gold = player_data["gold"]
        new_stones = player_data["enhance_stones"]
        new_scrolls = player_data["protect_scrolls"]
        new_charms = player_data["lucky_charms"]

        return ShopResponse(
            success=True,
            message=f"成功购买 {amount} 张保护卷",
            gold=new_gold,
            enhance_stones=new_stones,
            protect_scrolls=new_scrolls,
            lucky_charms=new_charms
        )


@app.post("/api/shop/buy_lucky_charms/{amount}")
def buy_lucky_charms(amount: int):
    player = get_default_player()

    if amount <= 0:
        return ShopResponse(success=False, message="购买数量必须大于0")

    price_per_charm = 800
    total_cost = amount * price_per_charm

    with get_db() as conn:
        cursor = conn.cursor()

        if player["gold"] < total_cost:
            return ShopResponse(success=False, message=f"金币不足，需要 {total_cost} 金币")

        cursor.execute("UPDATE player SET gold = gold - ?, lucky_charms = lucky_charms + ? WHERE id = ?", (total_cost, amount, player["id"]))

        cursor.execute("SELECT gold, enhance_stones, protect_scrolls, lucky_charms FROM player WHERE id = ?", (player["id"],))
        player_data = cursor.fetchone()
        new_gold = player_data["gold"]
        new_stones = player_data["enhance_stones"]
        new_scrolls = player_data["protect_scrolls"]
        new_charms = player_data["lucky_charms"]

        return ShopResponse(
            success=True,
            message=f"成功购买 {amount} 张幸运符",
            gold=new_gold,
            enhance_stones=new_stones,
            protect_scrolls=new_scrolls,
            lucky_charms=new_charms
        )
