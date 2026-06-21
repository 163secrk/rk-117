import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    init_db, get_db, get_upgrade_cost, get_enhance_stone_cost, get_success_rate,
    get_slot_attribute, MONSTER_TIERS, calculate_player_power,
    get_equipment_base_name, get_equipment_quality, get_equipment_quality_color
)

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


class MonsterInfo(BaseModel):
    name: str
    power: int
    hp: int
    tier: str


class EquipmentDrop(BaseModel):
    id: int
    slot: str
    name: str
    base_name: str
    level: int
    quality: str
    quality_color: str
    display_name: str
    is_better: bool
    attribute: dict


class HuntResponse(BaseModel):
    success: bool
    message: str
    monster: MonsterInfo | None = None
    victory: bool = False
    gold_reward: int = 0
    equipment_drop: EquipmentDrop | None = None
    player_power: int = 0
    gold: int | None = None
    enhance_stones: int | None = None
    protect_scrolls: int | None = None
    lucky_charms: int | None = None


def _generate_monster(player_power: int) -> dict:
    if player_power < 100:
        tier_idx = 0
    elif player_power < 250:
        tier_idx = random.choice([0, 1])
    elif player_power < 600:
        tier_idx = random.choice([1, 2])
    elif player_power < 1500:
        tier_idx = random.choice([2, 3])
    else:
        tier_idx = random.choice([3, 4])

    tier = MONSTER_TIERS[tier_idx]
    name = random.choice(tier["names"])
    min_p, max_p = tier["power_range"]
    min_h, max_h = tier["hp_range"]

    variance = 0.2
    power_base = min(max(player_power, min_p), max_p)
    power_min = int(power_base * (1 - variance))
    power_max = int(power_base * (1 + variance))
    power = max(min_p, min(max_p, random.randint(power_min, power_max)))

    hp_min = int(min_h + (power - min_p) / max(1, max_p - min_p) * (max_h - min_h))
    hp_max = int(hp_min * 1.3)
    hp = random.randint(max(min_h, hp_min), min(max_h, hp_max))

    return {
        "name": name,
        "power": power,
        "hp": hp,
        "tier": tier["tier"]
    }


def _roll_equipment_drop(monster_power: int, player_id: int) -> dict | None:
    drop_chance = 0.35 + min(0.3, monster_power / 3000)
    if random.random() > drop_chance:
        return None

    slots = ["weapon", "helmet", "armor", "necklace"]
    slot = random.choice(slots)

    max_level_from_power = min(20, int(monster_power / 80) + 1)

    level_weights = []
    for lv in range(0, max_level_from_power + 1):
        weight = max(1, max_level_from_power - lv + 1)
        level_weights.append((lv, weight))

    total_weight = sum(w for _, w in level_weights)
    roll = random.randint(1, total_weight)
    cum = 0
    level = 0
    for lv, w in level_weights:
        cum += w
        if roll <= cum:
            level = lv
            break

    level = min(20, max(0, level))

    base_name = get_equipment_base_name(slot, level)
    quality = get_equipment_quality(level)
    quality_color = get_equipment_quality_color(level)
    display_name = f"+{level} {base_name}" if level > 0 else base_name
    attr = get_slot_attribute(slot, level)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM equipment WHERE player_id = ? AND slot = ?",
            (player_id, slot)
        )
        current = cursor.fetchone()
        is_better = True
        if current and current["level"] >= level:
            is_better = False

        if is_better:
            if current:
                cursor.execute(
                    "UPDATE equipment SET name = ?, level = ?, base_name = ? WHERE id = ?",
                    (base_name, level, base_name, current["id"])
                )
                equip_id = current["id"]
            else:
                cursor.execute(
                    "INSERT INTO equipment (player_id, slot, name, level, base_name) VALUES (?, ?, ?, ?, ?)",
                    (player_id, slot, base_name, level, base_name)
                )
                equip_id = cursor.lastrowid
        else:
            equip_id = current["id"] if current else None

    return {
        "id": equip_id,
        "slot": slot,
        "name": display_name,
        "base_name": base_name,
        "level": level,
        "quality": quality,
        "quality_color": quality_color,
        "display_name": display_name,
        "is_better": is_better,
        "attribute": attr
    }


@app.get("/api/wild/player_power")
def get_player_power():
    player = get_default_player()
    power = calculate_player_power(player["id"])
    return {"player_power": power}


@app.post("/api/wild/hunt")
def hunt_monster():
    player = get_default_player()
    player_id = player["id"]
    player_power = calculate_player_power(player_id)

    monster = _generate_monster(player_power)

    victory = player_power > monster["power"]

    gold_reward = 0
    equip_drop = None

    if victory:
        base_gold = monster["power"] // 3
        gold_reward = random.randint(max(10, int(base_gold * 0.7)), int(base_gold * 1.3))

        equip_drop = _roll_equipment_drop(monster["power"], player_id)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE player SET gold = gold + ? WHERE id = ?",
                (gold_reward, player_id)
            )
            cursor.execute(
                "SELECT gold, enhance_stones, protect_scrolls, lucky_charms FROM player WHERE id = ?",
                (player_id,)
            )
            player_data = cursor.fetchone()

        msg = f"战斗胜利！击败了 {monster['name']}"
        return HuntResponse(
            success=True,
            message=msg,
            monster=MonsterInfo(**monster),
            victory=True,
            gold_reward=gold_reward,
            equipment_drop=EquipmentDrop(**equip_drop) if equip_drop else None,
            player_power=player_power,
            gold=player_data["gold"],
            enhance_stones=player_data["enhance_stones"],
            protect_scrolls=player_data["protect_scrolls"],
            lucky_charms=player_data["lucky_charms"],
        )
    else:
        msg = f"战斗失败！{monster['name']} 太强了，快提升战力再来挑战吧"
        return HuntResponse(
            success=True,
            message=msg,
            monster=MonsterInfo(**monster),
            victory=False,
            gold_reward=0,
            equipment_drop=None,
            player_power=player_power,
            gold=player["gold"],
            enhance_stones=player["enhance_stones"],
            protect_scrolls=player["protect_scrolls"],
            lucky_charms=player["lucky_charms"],
        )
