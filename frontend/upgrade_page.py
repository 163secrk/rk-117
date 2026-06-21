from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from api_client import ApiClient

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
    "purple": "#cc66ff",
    "orange": "#ffaa33",
}


class EquipmentSlot(QFrame):
    clicked = Signal(str)

    def __init__(self, slot_key, parent=None):
        super().__init__(parent)
        self.slot_key = slot_key
        self.equipment_id = None
        self.is_empty = True
        self.selected = False
        self.level = 0
        self.attribute = None
        self.quality = "white"

        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(170, 230)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._get_style(False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(3)

        self.icon_label = QLabel(SLOT_ICONS.get(slot_key, "?"))
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(32)
        self.icon_label.setFont(icon_font)

        self.slot_name_label = QLabel(SLOT_NAMES.get(slot_key, slot_key))
        self.slot_name_label.setAlignment(Qt.AlignCenter)
        slot_font = QFont()
        slot_font.setPointSize(11)
        slot_font.setBold(True)
        self.slot_name_label.setFont(slot_font)

        self.equip_name_label = QLabel("（空）")
        self.equip_name_label.setAlignment(Qt.AlignCenter)
        self.equip_name_label.setWordWrap(True)
        name_font = QFont()
        name_font.setPointSize(10)
        self.equip_name_label.setFont(name_font)

        self.quality_label = QLabel("")
        self.quality_label.setAlignment(Qt.AlignCenter)
        quality_font = QFont()
        quality_font.setPointSize(9)
        quality_font.setBold(True)
        self.quality_label.setFont(quality_font)

        self.level_label = QLabel("")
        self.level_label.setAlignment(Qt.AlignCenter)
        level_font = QFont()
        level_font.setPointSize(12)
        level_font.setBold(True)
        self.level_label.setFont(level_font)

        self.attr_label = QLabel("")
        self.attr_label.setAlignment(Qt.AlignCenter)
        attr_font = QFont()
        attr_font.setPointSize(9)
        self.attr_label.setFont(attr_font)

        self.affix_label = QLabel("")
        self.affix_label.setAlignment(Qt.AlignCenter)
        self.affix_label.setWordWrap(True)
        affix_font = QFont()
        affix_font.setPointSize(8)
        self.affix_label.setFont(affix_font)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.slot_name_label)
        layout.addWidget(self.equip_name_label)
        layout.addWidget(self.quality_label)
        layout.addWidget(self.level_label)
        layout.addWidget(self.attr_label)
        layout.addWidget(self.affix_label)
        layout.addStretch()

    def _get_style(self, selected):
        if selected:
            return """
                QFrame {
                    background-color: #3a5a8a;
                    border: 2px solid #5a9aff;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: #4a6a9a;
                }
            """
        else:
            return """
                QFrame {
                    background-color: #2a2a3a;
                    border: 1px solid #555;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: #3a3a4a;
                    border: 1px solid #777;
                }
            """

    def set_selected(self, selected):
        self.selected = selected
        self.setStyleSheet(self._get_style(selected))

    def update_data(self, equip_data):
        if equip_data and not equip_data.get("empty"):
            self.is_empty = False
            self.equipment_id = equip_data["id"]
            self.level = equip_data["level"] or 0
            self.quality = equip_data.get("quality", "white")
            quality_name = equip_data.get("quality_name", "普通")
            quality_color = QUALITY_COLORS.get(self.quality, "#dddddd")

            self.equip_name_label.setText(equip_data["base_name"])
            self.equip_name_label.setStyleSheet(f"color: {quality_color};")

            self.quality_label.setText(f"【{quality_name}】")
            self.quality_label.setStyleSheet(f"color: {quality_color};")

            if self.level > 0:
                self.level_label.setText(f"+{self.level}")
                self.level_label.setStyleSheet("color: #ffcc44;")
            else:
                self.level_label.setText("")
            self.attribute = equip_data.get("attribute")
            if self.attribute:
                val = self.attribute["value"]
                name = self.attribute["name"]
                multiplier = self.attribute.get("multiplier", 1.0)
                if self.attribute.get("is_percent"):
                    text = f'{self.attribute["icon"]} {name} +{val}%'
                else:
                    text = f'{self.attribute["icon"]} {name} +{val}'
                if multiplier != 1.0:
                    text += f" (x{multiplier})"
                self.attr_label.setText(text)
                self.attr_label.setStyleSheet("color: #88ddff;")
            else:
                self.attr_label.setText("")

            has_affix = equip_data.get("has_affix", False)
            affix = equip_data.get("affix")
            if has_affix and affix:
                affix_name = affix.get("name", "")
                affix_value = affix.get("value", 0)
                self.affix_label.setText(f"✨ {affix_name} +{int(affix_value * 100)}%")
                self.affix_label.setStyleSheet("color: #ffaa33; font-weight: bold;")
            elif self.level < 10:
                self.affix_label.setText(f"🔒 +10解锁词条")
                self.affix_label.setStyleSheet("color: #666;")
            else:
                self.affix_label.setText("")
        else:
            self.is_empty = True
            self.equipment_id = None
            self.level = 0
            self.quality = "white"
            self.attribute = None
            self.equip_name_label.setText("（空）")
            self.equip_name_label.setStyleSheet("color: #888;")
            self.quality_label.setText("")
            self.level_label.setText("")
            self.attr_label.setText("")
            self.affix_label.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.slot_key)
        super().mousePressEvent(event)


class UpgradePage(QWidget):
    gold_updated = Signal(int)
    stones_updated = Signal(int)
    scrolls_updated = Signal(int)
    charms_updated = Signal(int)

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.selected_slot = None
        self.slots = {}
        self.equipment_list = []
        self._upgrade_pending = False
        self._reforge_pending = False
        self._current_info = None
        self.player_scrolls = 0
        self.player_charms = 0

        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        title_label = QLabel("装备栏")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #eee;")
        left_layout.addWidget(title_label)

        slots_grid = QGridLayout()
        slots_grid.setSpacing(10)

        slot_order = ["weapon", "helmet", "armor", "necklace"]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for i, slot_key in enumerate(slot_order):
            slot = EquipmentSlot(slot_key)
            slot.clicked.connect(self._on_slot_clicked)
            self.slots[slot_key] = slot
            row, col = positions[i]
            slots_grid.addWidget(slot, row, col)

        left_layout.addLayout(slots_grid)
        left_layout.addStretch()

        main_layout.addWidget(left_panel, 1)

        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(25, 25, 25, 25)
        right_layout.setSpacing(15)

        upgrade_title = QLabel("强化")
        upgrade_title_font = QFont()
        upgrade_title_font.setPointSize(18)
        upgrade_title_font.setBold(True)
        upgrade_title.setFont(upgrade_title_font)
        upgrade_title.setStyleSheet("color: #eee;")
        right_layout.addWidget(upgrade_title)

        self.current_equip_label = QLabel("加载中...")
        self.current_equip_label.setAlignment(Qt.AlignCenter)
        equip_font = QFont()
        equip_font.setPointSize(14)
        equip_font.setBold(True)
        self.current_equip_label.setFont(equip_font)
        self.current_equip_label.setStyleSheet("color: #aaa; padding: 10px;")
        right_layout.addWidget(self.current_equip_label)

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #252538;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(10)

        self.quality_info_label = QLabel("品质：-")
        self.quality_info_label.setStyleSheet("color: #dddddd; font-size: 13px; font-weight: bold;")

        self.attr_current_label = QLabel("当前属性：-")
        self.attr_current_label.setStyleSheet("color: #88ddff; font-size: 13px;")

        self.attr_next_label = QLabel("")
        self.attr_next_label.setStyleSheet("color: #88ff88; font-size: 13px;")

        self.level_info_label = QLabel("等级：-")
        self.level_info_label.setStyleSheet("color: #ddd; font-size: 13px;")

        self.affix_info_label = QLabel("")
        self.affix_info_label.setStyleSheet("color: #ffaa33; font-size: 12px;")
        self.affix_info_label.setWordWrap(True)

        self.cost_label = QLabel("消耗金币：-")
        self.cost_label.setStyleSheet("color: #ffcc44; font-size: 13px;")

        self.stone_cost_label = QLabel("消耗强化石：-")
        self.stone_cost_label.setStyleSheet("color: #88ddff; font-size: 13px;")

        self.rate_label = QLabel("成功率：-")
        self.rate_label.setStyleSheet("color: #88ff88; font-size: 13px;")

        info_layout.addWidget(self.quality_info_label)
        info_layout.addWidget(self.attr_current_label)
        info_layout.addWidget(self.attr_next_label)
        info_layout.addWidget(self.level_info_label)
        info_layout.addWidget(self.affix_info_label)
        info_layout.addWidget(self.cost_label)
        info_layout.addWidget(self.stone_cost_label)
        info_layout.addWidget(self.rate_label)

        right_layout.addWidget(info_frame)

        items_frame = QFrame()
        items_frame.setStyleSheet("""
            QFrame {
                background-color: #252538;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        items_layout = QVBoxLayout(items_frame)
        items_layout.setSpacing(8)

        items_title = QLabel("辅助道具")
        items_title_font = QFont()
        items_title_font.setBold(True)
        items_title.setFont(items_title_font)
        items_title.setStyleSheet("color: #eee; font-size: 13px;")
        items_layout.addWidget(items_title)

        self.protect_checkbox = QCheckBox()
        self.protect_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffaa88;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #666;
                background-color: #1a1a28;
            }
            QCheckBox::indicator:checked {
                background-color: #4a7acc;
                border: 1px solid #5a9aff;
            }
        """)
        self.protect_checkbox.stateChanged.connect(self._refresh_rate_display)
        items_layout.addWidget(self.protect_checkbox)

        self.lucky_checkbox = QCheckBox()
        self.lucky_checkbox.setStyleSheet("""
            QCheckBox {
                color: #aaffaa;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #666;
                background-color: #1a1a28;
            }
            QCheckBox::indicator:checked {
                background-color: #4a7acc;
                border: 1px solid #5a9aff;
            }
        """)
        self.lucky_checkbox.stateChanged.connect(self._refresh_rate_display)
        items_layout.addWidget(self.lucky_checkbox)

        right_layout.addWidget(items_frame)

        self.upgrade_button = QPushButton("开始强化")
        self.upgrade_button.setEnabled(False)
        self.upgrade_button.setFixedHeight(50)
        btn_font = QFont()
        btn_font.setPointSize(14)
        btn_font.setBold(True)
        self.upgrade_button.setFont(btn_font)
        self.upgrade_button.setStyleSheet("""
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
        self.upgrade_button.clicked.connect(self._on_upgrade_clicked)
        right_layout.addWidget(self.upgrade_button)

        self.reforge_button = QPushButton("🔨 重铸品质 (500金币)")
        self.reforge_button.setEnabled(False)
        self.reforge_button.setFixedHeight(40)
        reforge_btn_font = QFont()
        reforge_btn_font.setPointSize(12)
        reforge_btn_font.setBold(True)
        self.reforge_button.setFont(reforge_btn_font)
        self.reforge_button.setCursor(Qt.PointingHandCursor)
        self.reforge_button.setStyleSheet("""
            QPushButton {
                background-color: #cc6633;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover:enabled {
                background-color: #dd7744;
            }
            QPushButton:pressed:enabled {
                background-color: #bb5522;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.reforge_button.clicked.connect(self._on_reforge_clicked)
        right_layout.addWidget(self.reforge_button)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        result_font = QFont()
        result_font.setPointSize(12)
        self.result_label.setFont(result_font)
        right_layout.addWidget(self.result_label)

        right_layout.addStretch()

        main_layout.addWidget(right_panel, 1)

    def refresh_data(self):
        self.api.get_equipment(self._on_equipment_loaded)
        self.api.get_player(self._on_player_loaded)

    def _on_equipment_loaded(self, equipment):
        if equipment:
            self.equipment_list = equipment
            for equip in equipment:
                slot_key = equip["slot"]
                if slot_key in self.slots:
                    self.slots[slot_key].update_data(equip)

        if self.selected_slot and self.selected_slot in self.slots:
            self._update_upgrade_panel()
        else:
            weapon_slot = self.slots.get("weapon")
            if weapon_slot and not weapon_slot.is_empty:
                self._on_slot_clicked("weapon")

    def _on_player_loaded(self, player):
        if player and player.get("gold") is not None:
            self.gold_updated.emit(player["gold"])
        if player and player.get("enhance_stones") is not None:
            self.stones_updated.emit(player["enhance_stones"])
        if player and player.get("protect_scrolls") is not None:
            self.player_scrolls = player["protect_scrolls"]
            self.scrolls_updated.emit(player["protect_scrolls"])
            self._update_item_labels()
        if player and player.get("lucky_charms") is not None:
            self.player_charms = player["lucky_charms"]
            self.charms_updated.emit(player["lucky_charms"])
            self._update_item_labels()

    def _update_item_labels(self):
        self.protect_checkbox.setText(f"🛡 使用保护卷（失败不扣强化石）  持有：{self.player_scrolls} 张")
        self.lucky_checkbox.setText(f"🍀 使用幸运符（成功率+15%）  持有：{self.player_charms} 张")
        if self.player_scrolls <= 0:
            self.protect_checkbox.setChecked(False)
            self.protect_checkbox.setEnabled(False)
        else:
            self.protect_checkbox.setEnabled(True)
        base_rate = self._current_info.get("success_rate", 0.0) if self._current_info and not self._current_info.get("is_max") else 0.0
        lucky_useless = base_rate >= 1.0
        if self.player_charms <= 0 or lucky_useless:
            self.lucky_checkbox.setChecked(False)
            self.lucky_checkbox.setEnabled(False)
        else:
            self.lucky_checkbox.setEnabled(True)

    def _refresh_rate_display(self):
        if not self._current_info or self._current_info.get("is_max"):
            return
        base_rate = self._current_info.get("success_rate", 0.0)
        use_lucky = self.lucky_checkbox.isChecked()
        final_rate = min(base_rate + 0.15 if use_lucky else base_rate, 1.0)
        if use_lucky:
            self.rate_label.setText(f"成功率：{base_rate * 100:.1f}% → {final_rate * 100:.1f}%（幸运符+15%）")
        else:
            self.rate_label.setText(f"成功率：{final_rate * 100:.1f}%")

    def _on_slot_clicked(self, slot_key):
        for key, slot in self.slots.items():
            slot.set_selected(key == slot_key)

        self.selected_slot = slot_key
        self.result_label.setText("")
        self._update_upgrade_panel()

    def _update_upgrade_panel(self):
        if not self.selected_slot:
            return

        slot = self.slots[self.selected_slot]
        if slot.is_empty:
            self.current_equip_label.setText(f"{SLOT_NAMES.get(self.selected_slot, '')}：未装备")
            self.current_equip_label.setStyleSheet("color: #888; padding: 10px;")
            self.quality_info_label.setText("品质：-")
            self.attr_current_label.setText("当前属性：-")
            self.attr_next_label.setText("")
            self.level_info_label.setText("等级：-")
            self.affix_info_label.setText("")
            self.cost_label.setText("消耗金币：-")
            self.stone_cost_label.setText("消耗强化石：-")
            self.rate_label.setText("成功率：-")
            self.upgrade_button.setEnabled(False)
            self.reforge_button.setEnabled(False)
            return

        equip_data = None
        for e in self.equipment_list:
            if e.get("slot") == self.selected_slot:
                equip_data = e
                break

        quality_name = equip_data.get("quality_name", "普通") if equip_data else "普通"
        quality_color_key = equip_data.get("quality_color", "white") if equip_data else "white"
        quality_color = QUALITY_COLORS.get(quality_color_key, "#dddddd")
        self.quality_info_label.setText(f"品质：【{quality_name}】")
        self.quality_info_label.setStyleSheet(f"color: {quality_color}; font-size: 13px; font-weight: bold;")

        if equip_data and equip_data.get("attribute"):
            attr = equip_data["attribute"]
            multiplier = attr.get("multiplier", 1.0)
            if attr.get("is_percent"):
                text = f'当前属性：{attr["icon"]} {attr["name"]} +{attr["value"]}%'
            else:
                text = f'当前属性：{attr["icon"]} {attr["name"]} +{attr["value"]}'
            if multiplier != 1.0:
                text += f' (品质x{multiplier})'
            self.attr_current_label.setText(text)
        else:
            self.attr_current_label.setText("当前属性：-")
        self.attr_next_label.setText("")

        has_affix = equip_data.get("has_affix", False) if equip_data else False
        affix = equip_data.get("affix") if equip_data else None
        if has_affix and affix:
            affix_name = affix.get("name", "")
            affix_value = affix.get("value", 0)
            self.affix_info_label.setText(f"✨ 特殊词条：{affix_name} +{int(affix_value * 100)}%")
        elif equip_data and equip_data.get("level", 0) < 10:
            self.affix_info_label.setText(f"🔒 +10解锁特殊词条（当前+{equip_data.get('level', 0)}）")
        else:
            self.affix_info_label.setText("")

        self.level_info_label.setText("加载中...")
        self.cost_label.setText("消耗金币：-")
        self.stone_cost_label.setText("消耗强化石：-")
        self.rate_label.setText("成功率：-")
        self.upgrade_button.setEnabled(False)
        self.reforge_button.setEnabled(False)

        self.api.get_upgrade_info(slot.equipment_id, self._on_upgrade_info_loaded)

    def _on_upgrade_info_loaded(self, info):
        if not info:
            self.upgrade_button.setEnabled(False)
            return

        self._current_info = info

        slot = self.slots.get(self.selected_slot)
        if not slot:
            return

        equip_data = None
        for e in self.equipment_list:
            if e.get("slot") == self.selected_slot:
                equip_data = e
                break

        if info.get("is_max"):
            self.current_equip_label.setText(f"+{info['current_level']} {slot.equip_name_label.text()}")
            self.current_equip_label.setStyleSheet("color: #ff88ff; padding: 10px;")
            if equip_data and equip_data.get("attribute"):
                attr = equip_data["attribute"]
                if attr.get("is_percent"):
                    self.attr_current_label.setText(f'当前属性：{attr["icon"]} {attr["name"]} +{attr["value"]}% (已满级)')
                else:
                    self.attr_current_label.setText(f'当前属性：{attr["icon"]} {attr["name"]} +{attr["value"]} (已满级)')
            self.attr_next_label.setText("")
            self.level_info_label.setText(f"已达最高等级 +{info['max_level']}")
            self.cost_label.setText("消耗金币：-")
            self.stone_cost_label.setText("消耗强化石：-")
            self.rate_label.setText("成功率：-")
            self.protect_checkbox.setEnabled(False)
            self.lucky_checkbox.setEnabled(False)
            self.upgrade_button.setEnabled(False)
            self.upgrade_button.setText("已满级")
            return

        self.current_equip_label.setText(f"+{info['current_level']} {slot.equip_name_label.text()}")
        self.current_equip_label.setStyleSheet("color: #ffcc44; padding: 10px;")

        if equip_data and equip_data.get("next_attribute"):
            next_attr = equip_data["next_attribute"]
            cur_attr = equip_data.get("attribute")
            if next_attr.get("is_percent"):
                cur_val = cur_attr["value"] if cur_attr else 0
                self.attr_next_label.setText(
                    f'强化后：{next_attr["icon"]} {next_attr["name"]} +{cur_val}% → +{next_attr["value"]}%'
                )
            else:
                cur_val = cur_attr["value"] if cur_attr else 0
                self.attr_next_label.setText(
                    f'强化后：{next_attr["icon"]} {next_attr["name"]} +{cur_val} → +{next_attr["value"]}'
                )

        self.level_info_label.setText(
            f"当前等级：+{info['current_level']}   →   目标：+{info['next_level']}"
        )
        self.cost_label.setText(f"消耗金币：{info['cost']}")
        self.stone_cost_label.setText(f"消耗强化石：{info['stone_cost']} 颗")
        self._update_item_labels()
        self._refresh_rate_display()
        if not self._upgrade_pending:
            self.upgrade_button.setEnabled(True)
        self.upgrade_button.setText("开始强化")

        if not self._reforge_pending:
            self.reforge_button.setEnabled(True)

    def _on_upgrade_clicked(self):
        if not self.selected_slot or self._upgrade_pending:
            return

        slot = self.slots[self.selected_slot]
        if slot.is_empty or not slot.equipment_id:
            return

        use_protect = self.protect_checkbox.isChecked()
        use_lucky = self.lucky_checkbox.isChecked()

        self._upgrade_pending = True
        self.result_label.setText("强化中...")
        self.result_label.setStyleSheet("color: #aaa;")
        self.upgrade_button.setEnabled(False)
        self.upgrade_button.setText("强化中...")
        self.protect_checkbox.setEnabled(False)
        self.lucky_checkbox.setEnabled(False)

        self.api.upgrade_equipment(
            slot.equipment_id, self._on_upgrade_result,
            use_protect_scroll=use_protect, use_lucky_charm=use_lucky
        )

    def _on_upgrade_result(self, result):
        self._upgrade_pending = False

        if not result:
            self.result_label.setText("错误：无法连接服务器")
            self.result_label.setStyleSheet("color: #ff6666;")
            self.upgrade_button.setEnabled(True)
            self.upgrade_button.setText("开始强化")
            self._update_item_labels()
            return

        if result.get("success"):
            self.result_label.setText(result.get("message", "强化成功！"))
            self.result_label.setStyleSheet("color: #66ff66;")
        else:
            self.result_label.setText(result.get("message", "强化失败"))
            self.result_label.setStyleSheet("color: #ff8866;")

        if result.get("gold") is not None:
            self.gold_updated.emit(result["gold"])

        if result.get("enhance_stones") is not None:
            self.stones_updated.emit(result["enhance_stones"])

        if result.get("protect_scrolls") is not None:
            self.player_scrolls = result["protect_scrolls"]
            self.scrolls_updated.emit(result["protect_scrolls"])

        if result.get("lucky_charms") is not None:
            self.player_charms = result["lucky_charms"]
            self.charms_updated.emit(result["lucky_charms"])

        self.refresh_data()

    def _on_reforge_clicked(self):
        if not self.selected_slot or self._reforge_pending:
            return

        slot = self.slots[self.selected_slot]
        if slot.is_empty or not slot.equipment_id:
            return

        reply = QMessageBox.question(
            self, "重铸确认",
            "确定要花费 500 金币重铸这件装备的品质吗？\n重铸后品质将随机变化，特殊词条也会重新生成。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._reforge_pending = True
        self.result_label.setText("重铸中...")
        self.result_label.setStyleSheet("color: #aaa;")
        self.reforge_button.setEnabled(False)
        self.reforge_button.setText("重铸中...")
        self.upgrade_button.setEnabled(False)

        self.api.reforge_equipment(slot.equipment_id, self._on_reforge_result)

    def _on_reforge_result(self, result):
        self._reforge_pending = False

        if not result:
            self.result_label.setText("错误：无法连接服务器")
            self.result_label.setStyleSheet("color: #ff6666;")
            self.reforge_button.setEnabled(True)
            self.reforge_button.setText("🔨 重铸品质 (500金币)")
            return

        if result.get("success"):
            self.result_label.setText(result.get("message", "重铸成功！"))
            self.result_label.setStyleSheet("color: #ffaa33;")
        else:
            self.result_label.setText(result.get("message", "重铸失败"))
            self.result_label.setStyleSheet("color: #ff8866;")

        if result.get("gold") is not None:
            self.gold_updated.emit(result["gold"])

        self.refresh_data()
