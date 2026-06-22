from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from game_service import GameService

SLOT_NAMES = {
    "weapon": "武器",
    "helmet": "头盔",
    "armor": "铠甲",
    "necklace": "项链"
}

SLOT_ICONS = {
    "weapon": "⚔",
    "helmet": "⛑",
    "armor": "🛡",
    "necklace": "📿"
}

QUALITY_COLORS = {
    "white": "#dddddd",
    "green": "#66ff66",
    "blue": "#66aaff",
    "purple": "#cc66ff",
    "orange": "#ffaa33",
}

MONSTER_TIER_NAMES = {
    "weak": "弱小",
    "normal": "普通",
    "strong": "强力",
    "elite": "精英",
    "boss": "Boss",
}

MONSTER_TIER_COLORS = {
    "weak": "#88ff88",
    "normal": "#88ddff",
    "strong": "#ffaa66",
    "elite": "#cc88ff",
    "boss": "#ff6666",
}


class WildPage(QWidget):
    gold_updated = Signal(int)
    stones_updated = Signal(int)
    scrolls_updated = Signal(int)
    charms_updated = Signal(int)
    equipment_changed = Signal()

    def __init__(self, game_service: GameService, parent=None):
        super().__init__(parent)
        self.game = game_service
        self.player_power = 0
        self._current_monster = None

        self._init_ui()
        self.refresh_power()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        power_frame = QFrame()
        power_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
        """)
        power_layout = QHBoxLayout(power_frame)
        power_layout.setContentsMargins(20, 15, 20, 15)

        power_title = QLabel("⚔ 总战力")
        power_title_font = QFont()
        power_title_font.setPointSize(14)
        power_title_font.setBold(True)
        power_title.setFont(power_title_font)
        power_title.setStyleSheet("color: #eee;")

        self.power_label = QLabel("加载中...")
        power_label_font = QFont()
        power_label_font.setPointSize(20)
        power_label_font.setBold(True)
        self.power_label.setFont(power_label_font)
        self.power_label.setStyleSheet("color: #ffcc44;")

        self.refresh_power_btn = QPushButton("🔄 刷新")
        self.refresh_power_btn.setFixedHeight(36)
        self.refresh_power_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_power_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a5a;
                color: #ddd;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #4a4a6a;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #2a2a4a;
            }
        """)
        self.refresh_power_btn.clicked.connect(self.refresh_power)

        power_layout.addWidget(power_title)
        power_layout.addSpacing(15)
        power_layout.addWidget(self.power_label)
        power_layout.addStretch()
        power_layout.addWidget(self.refresh_power_btn)

        main_layout.addWidget(power_frame)

        battle_frame = QFrame()
        battle_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
        """)
        battle_layout = QVBoxLayout(battle_frame)
        battle_layout.setContentsMargins(25, 20, 25, 20)
        battle_layout.setSpacing(15)

        battle_title = QLabel("🌲 野外狩猎")
        battle_title_font = QFont()
        battle_title_font.setPointSize(18)
        battle_title_font.setBold(True)
        battle_title.setFont(battle_title_font)
        battle_title.setStyleSheet("color: #eee;")
        battle_title.setAlignment(Qt.AlignCenter)
        battle_layout.addWidget(battle_title)

        self.monster_frame = QFrame()
        self.monster_frame.setMinimumHeight(200)
        self.monster_frame.setStyleSheet("""
            QFrame {
                background-color: #252538;
                border-radius: 8px;
                border: 2px dashed #555;
            }
        """)
        monster_layout = QVBoxLayout(self.monster_frame)
        monster_layout.setContentsMargins(20, 15, 20, 15)
        monster_layout.setSpacing(8)

        self.monster_icon_label = QLabel("❓")
        self.monster_icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(48)
        self.monster_icon_label.setFont(icon_font)

        self.monster_name_label = QLabel("点击下方按钮搜索怪物")
        self.monster_name_label.setAlignment(Qt.AlignCenter)
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self.monster_name_label.setFont(name_font)
        self.monster_name_label.setStyleSheet("color: #aaa;")

        self.monster_tier_label = QLabel("")
        self.monster_tier_label.setAlignment(Qt.AlignCenter)
        tier_font = QFont()
        tier_font.setPointSize(12)
        self.monster_tier_label.setFont(tier_font)

        monster_stats_layout = QHBoxLayout()
        monster_stats_layout.setSpacing(20)

        self.monster_power_label = QLabel("")
        self.monster_power_label.setAlignment(Qt.AlignCenter)
        power_font = QFont()
        power_font.setPointSize(13)
        power_font.setBold(True)
        self.monster_power_label.setFont(power_font)

        self.monster_hp_label = QLabel("")
        self.monster_hp_label.setAlignment(Qt.AlignCenter)
        hp_font = QFont()
        hp_font.setPointSize(13)
        hp_font.setBold(True)
        self.monster_hp_label.setFont(hp_font)

        monster_stats_layout.addWidget(self.monster_power_label)
        monster_stats_layout.addWidget(self.monster_hp_label)

        monster_layout.addWidget(self.monster_icon_label)
        monster_layout.addWidget(self.monster_name_label)
        monster_layout.addWidget(self.monster_tier_label)
        monster_layout.addLayout(monster_stats_layout)
        monster_layout.addStretch()

        battle_layout.addWidget(self.monster_frame)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        result_font = QFont()
        result_font.setPointSize(14)
        result_font.setBold(True)
        self.result_label.setFont(result_font)
        battle_layout.addWidget(self.result_label)

        self.gold_reward_label = QLabel("")
        self.gold_reward_label.setAlignment(Qt.AlignCenter)
        gold_reward_font = QFont()
        gold_reward_font.setPointSize(13)
        self.gold_reward_label.setFont(gold_reward_font)
        self.gold_reward_label.setStyleSheet("color: #ffcc44;")
        battle_layout.addWidget(self.gold_reward_label)

        self.drop_frame = QFrame()
        self.drop_frame.setVisible(False)
        self.drop_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a4a;
                border-radius: 8px;
                border: 1px solid #666;
            }
        """)
        drop_layout = QVBoxLayout(self.drop_frame)
        drop_layout.setContentsMargins(15, 12, 15, 12)
        drop_layout.setSpacing(6)

        self.drop_title_label = QLabel("✨ 装备掉落")
        self.drop_title_label.setAlignment(Qt.AlignCenter)
        drop_title_font = QFont()
        drop_title_font.setPointSize(13)
        drop_title_font.setBold(True)
        self.drop_title_label.setFont(drop_title_font)

        self.drop_name_label = QLabel("")
        self.drop_name_label.setAlignment(Qt.AlignCenter)
        drop_name_font = QFont()
        drop_name_font.setPointSize(14)
        drop_name_font.setBold(True)
        self.drop_name_label.setFont(drop_name_font)

        self.drop_slot_label = QLabel("")
        self.drop_slot_label.setAlignment(Qt.AlignCenter)
        drop_slot_font = QFont()
        drop_slot_font.setPointSize(12)
        self.drop_slot_label.setFont(drop_slot_font)
        self.drop_slot_label.setStyleSheet("color: #aaa;")

        self.drop_attr_label = QLabel("")
        self.drop_attr_label.setAlignment(Qt.AlignCenter)
        drop_attr_font = QFont()
        drop_attr_font.setPointSize(12)
        self.drop_attr_label.setFont(drop_attr_font)
        self.drop_attr_label.setStyleSheet("color: #88ddff;")

        self.drop_status_label = QLabel("")
        self.drop_status_label.setAlignment(Qt.AlignCenter)
        drop_status_font = QFont()
        drop_status_font.setPointSize(11)
        self.drop_status_label.setFont(drop_status_font)

        drop_layout.addWidget(self.drop_title_label)
        drop_layout.addWidget(self.drop_name_label)
        drop_layout.addWidget(self.drop_slot_label)
        drop_layout.addWidget(self.drop_attr_label)
        drop_layout.addWidget(self.drop_status_label)

        battle_layout.addWidget(self.drop_frame)

        self.hunt_button = QPushButton("🔍 搜索怪物")
        self.hunt_button.setFixedHeight(55)
        btn_font = QFont()
        btn_font.setPointSize(15)
        btn_font.setBold(True)
        self.hunt_button.setFont(btn_font)
        self.hunt_button.setCursor(Qt.PointingHandCursor)
        self.hunt_button.setStyleSheet("""
            QPushButton {
                background-color: #4a7acc;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover:enabled {
                background-color: #5a8adc;
            }
            QPushButton:pressed:enabled {
                background-color: #3a6abc;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.hunt_button.clicked.connect(self._on_hunt_clicked)
        battle_layout.addWidget(self.hunt_button)

        battle_layout.addStretch()

        main_layout.addWidget(battle_frame, 1)

        self.tip_label = QLabel("💡 提示：战力越高，遇到的怪物越强，掉落的装备品质越好")
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setStyleSheet("color: #888; font-size: 12px;")
        main_layout.addWidget(self.tip_label)

    def refresh_power(self):
        data = self.game.get_player_power()
        if data and data.get("player_power") is not None:
            self.player_power = data["player_power"]
            self.power_label.setText(f"{self.player_power:,}")

    def _on_hunt_clicked(self):
        self.hunt_button.setEnabled(False)
        self.hunt_button.setText("搜索中...")
        self.result_label.setText("")
        self.gold_reward_label.setText("")
        self.drop_frame.setVisible(False)

        self.monster_icon_label.setText("❓")
        self.monster_name_label.setText("正在搜索怪物...")
        self.monster_name_label.setStyleSheet("color: #aaa;")
        self.monster_tier_label.setText("")
        self.monster_power_label.setText("")
        self.monster_hp_label.setText("")
        self.monster_frame.setStyleSheet("""
            QFrame {
                background-color: #252538;
                border-radius: 8px;
                border: 2px dashed #777;
            }
        """)

        result = self.game.hunt_monster()
        self._apply_hunt_result(result)

        self.hunt_button.setEnabled(True)

    def _apply_hunt_result(self, result):
        if not result:
            self.result_label.setText("错误：操作失败")
            self.result_label.setStyleSheet("color: #ff6666;")
            self.hunt_button.setText("🔍 搜索怪物")
            return

        monster = result.get("monster")
        if monster:
            self._current_monster = monster
            tier = monster.get("tier", "normal")
            tier_name = MONSTER_TIER_NAMES.get(tier, "普通")
            tier_color = MONSTER_TIER_COLORS.get(tier, "#88ddff")

            monster_icon = "👹"
            if tier == "weak":
                monster_icon = "🐺"
            elif tier == "normal":
                monster_icon = "👹"
            elif tier == "strong":
                monster_icon = "👺"
            elif tier == "elite":
                monster_icon = "🐉"
            elif tier == "boss":
                monster_icon = "💀"

            self.monster_icon_label.setText(monster_icon)
            self.monster_name_label.setText(monster["name"])
            self.monster_name_label.setStyleSheet(f"color: {tier_color};")
            self.monster_tier_label.setText(f"【{tier_name}】")
            self.monster_tier_label.setStyleSheet(f"color: {tier_color};")
            self.monster_power_label.setText(f"⚔ 战力：{monster['power']:,}")
            self.monster_power_label.setStyleSheet("color: #ffaa66;")
            self.monster_hp_label.setText(f"❤ 血量：{monster['hp']:,}")
            self.monster_hp_label.setStyleSheet("color: #ff6666;")
            self.monster_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: #252538;
                    border-radius: 8px;
                    border: 2px solid {tier_color};
                }}
            """)

        victory = result.get("victory", False)
        if victory:
            self.result_label.setText("🎉 战斗胜利！")
            self.result_label.setStyleSheet("color: #66ff66;")

            gold_reward = result.get("gold_reward", 0)
            if gold_reward > 0:
                self.gold_reward_label.setText(f"💰 获得 {gold_reward:,} 金币")

            equip_drop = result.get("equipment_drop")
            if equip_drop:
                self._show_equipment_drop(equip_drop)
            else:
                self.drop_frame.setVisible(False)

            self.hunt_button.setText("➡️ 继续狩猎")
        else:
            self.result_label.setText("💔 战斗失败...")
            self.result_label.setStyleSheet("color: #ff6666;")
            self.gold_reward_label.setText("（未获得任何奖励）")
            self.gold_reward_label.setStyleSheet("color: #888;")
            self.drop_frame.setVisible(False)
            self.hunt_button.setText("🔍 搜索怪物")

        if result.get("player_power") is not None:
            self.player_power = result["player_power"]
            self.power_label.setText(f"{self.player_power:,}")

        if result.get("gold") is not None:
            self.gold_updated.emit(result["gold"])

        if result.get("enhance_stones") is not None:
            self.stones_updated.emit(result["enhance_stones"])

        if result.get("protect_scrolls") is not None:
            self.scrolls_updated.emit(result["protect_scrolls"])

        if result.get("lucky_charms") is not None:
            self.charms_updated.emit(result["lucky_charms"])

        if result.get("equipment_drop"):
            self.equipment_changed.emit()

    def _show_equipment_drop(self, equip):
        slot = equip.get("slot", "")
        level = equip.get("level", 0)
        quality = equip.get("quality", "普通")
        quality_color = equip.get("quality_color", "white")
        is_better = equip.get("is_better", False)
        color = QUALITY_COLORS.get(quality_color, "#dddddd")

        self.drop_title_label.setText(f"✨ {quality}装备掉落！")
        self.drop_title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")

        display_name = equip.get("display_name", "")
        self.drop_name_label.setText(display_name)
        self.drop_name_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 15px;")

        slot_name = SLOT_NAMES.get(slot, slot)
        slot_icon = SLOT_ICONS.get(slot, "❓")
        self.drop_slot_label.setText(f"{slot_icon} {slot_name}")
        self.drop_slot_label.setStyleSheet("color: #aaa; font-size: 12px;")

        attr = equip.get("attribute")
        if attr:
            attr_name = attr.get("name", "")
            attr_value = attr.get("value", 0)
            attr_icon = attr.get("icon", "")
            multiplier = attr.get("multiplier", 1.0)
            if attr.get("is_percent"):
                attr_text = f"{attr_icon} {attr_name} +{attr_value}%"
            else:
                attr_text = f"{attr_icon} {attr_name} +{attr_value}"
            if multiplier != 1.0:
                attr_text += f" (x{multiplier})"
            self.drop_attr_label.setText(attr_text)
        else:
            self.drop_attr_label.setText("")

        has_affix = equip.get("has_affix", False)
        affix = equip.get("affix")
        if has_affix and affix:
            affix_name = affix.get("name", "")
            affix_value = affix.get("value", 0)
            self.drop_status_label.setText(f"✨ 特殊词条：{affix_name} +{int(affix_value * 100)}%")
            self.drop_status_label.setStyleSheet("color: #ffaa33; font-size: 11px; font-weight: bold;")
        elif is_better:
            self.drop_status_label.setText("✅ 已自动装备，并放入背包")
            self.drop_status_label.setStyleSheet("color: #66ff66; font-size: 11px;")
        else:
            self.drop_status_label.setText("📦 已放入背包")
            self.drop_status_label.setStyleSheet("color: #ffaa66; font-size: 11px;")

        self.drop_frame.setVisible(True)

    def refresh_data(self):
        self.refresh_power()
