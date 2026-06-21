from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QSizePolicy
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

        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(170, 210)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._get_style(False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        self.icon_label = QLabel(SLOT_ICONS.get(slot_key, "?"))
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(36)
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

        layout.addWidget(self.icon_label)
        layout.addWidget(self.slot_name_label)
        layout.addWidget(self.equip_name_label)
        layout.addWidget(self.level_label)
        layout.addWidget(self.attr_label)
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
            self.equip_name_label.setText(equip_data["base_name"])
            self.equip_name_label.setStyleSheet("color: #ddd;")
            if self.level > 0:
                self.level_label.setText(f"+{self.level}")
                self.level_label.setStyleSheet("color: #ffcc44;")
            else:
                self.level_label.setText("")
            self.attribute = equip_data.get("attribute")
            if self.attribute:
                val = self.attribute["value"]
                name = self.attribute["name"]
                if self.attribute.get("is_percent"):
                    self.attr_label.setText(f'{self.attribute["icon"]} {name} +{val}%')
                else:
                    self.attr_label.setText(f'{self.attribute["icon"]} {name} +{val}')
                self.attr_label.setStyleSheet("color: #88ddff;")
            else:
                self.attr_label.setText("")
        else:
            self.is_empty = True
            self.equipment_id = None
            self.level = 0
            self.attribute = None
            self.equip_name_label.setText("（空）")
            self.equip_name_label.setStyleSheet("color: #888;")
            self.level_label.setText("")
            self.attr_label.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.slot_key)
        super().mousePressEvent(event)


class UpgradePage(QWidget):
    gold_updated = Signal(int)
    stones_updated = Signal(int)

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.selected_slot = None
        self.slots = {}
        self.equipment_list = []
        self._upgrade_pending = False

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

        self.attr_current_label = QLabel("当前属性：-")
        self.attr_current_label.setStyleSheet("color: #88ddff; font-size: 13px;")

        self.attr_next_label = QLabel("")
        self.attr_next_label.setStyleSheet("color: #88ff88; font-size: 13px;")

        self.level_info_label = QLabel("等级：-")
        self.level_info_label.setStyleSheet("color: #ddd; font-size: 13px;")

        self.cost_label = QLabel("消耗金币：-")
        self.cost_label.setStyleSheet("color: #ffcc44; font-size: 13px;")

        self.stone_cost_label = QLabel("消耗强化石：-")
        self.stone_cost_label.setStyleSheet("color: #88ddff; font-size: 13px;")

        self.rate_label = QLabel("成功率：-")
        self.rate_label.setStyleSheet("color: #88ff88; font-size: 13px;")

        info_layout.addWidget(self.attr_current_label)
        info_layout.addWidget(self.attr_next_label)
        info_layout.addWidget(self.level_info_label)
        info_layout.addWidget(self.cost_label)
        info_layout.addWidget(self.stone_cost_label)
        info_layout.addWidget(self.rate_label)

        right_layout.addWidget(info_frame)

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

    def _on_slot_clicked(self, slot_key):
        for key, slot in self.slots.items():
            slot.set_selected(key == slot_key)

        self.selected_slot = slot_key
        self._update_upgrade_panel()

    def _update_upgrade_panel(self):
        if not self.selected_slot:
            return

        slot = self.slots[self.selected_slot]
        if slot.is_empty:
            self.current_equip_label.setText(f"{SLOT_NAMES.get(self.selected_slot, '')}：未装备")
            self.current_equip_label.setStyleSheet("color: #888; padding: 10px;")
            self.attr_current_label.setText("当前属性：-")
            self.attr_next_label.setText("")
            self.level_info_label.setText("等级：-")
            self.cost_label.setText("消耗金币：-")
            self.stone_cost_label.setText("消耗强化石：-")
            self.rate_label.setText("成功率：-")
            self.upgrade_button.setEnabled(False)
            return

        equip_data = None
        for e in self.equipment_list:
            if e.get("slot") == self.selected_slot:
                equip_data = e
                break

        if equip_data and equip_data.get("attribute"):
            attr = equip_data["attribute"]
            if attr.get("is_percent"):
                self.attr_current_label.setText(f'当前属性：{attr["icon"]} {attr["name"]} +{attr["value"]}%')
            else:
                self.attr_current_label.setText(f'当前属性：{attr["icon"]} {attr["name"]} +{attr["value"]}')
        else:
            self.attr_current_label.setText("当前属性：-")
        self.attr_next_label.setText("")

        self.level_info_label.setText("加载中...")
        self.cost_label.setText("消耗金币：-")
        self.stone_cost_label.setText("消耗强化石：-")
        self.rate_label.setText("成功率：-")
        self.upgrade_button.setEnabled(False)

        self.api.get_upgrade_info(slot.equipment_id, self._on_upgrade_info_loaded)

    def _on_upgrade_info_loaded(self, info):
        if not info:
            self.upgrade_button.setEnabled(False)
            return

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
        self.rate_label.setText(f"成功率：{info['success_rate'] * 100:.1f}%")
        if not self._upgrade_pending:
            self.upgrade_button.setEnabled(True)
        self.upgrade_button.setText("开始强化")

    def _on_upgrade_clicked(self):
        if not self.selected_slot or self._upgrade_pending:
            return

        slot = self.slots[self.selected_slot]
        if slot.is_empty or not slot.equipment_id:
            return

        self._upgrade_pending = True
        self.result_label.setText("强化中...")
        self.result_label.setStyleSheet("color: #aaa;")
        self.upgrade_button.setEnabled(False)
        self.upgrade_button.setText("强化中...")

        self.api.upgrade_equipment(slot.equipment_id, self._on_upgrade_result)

    def _on_upgrade_result(self, result):
        self._upgrade_pending = False

        if not result:
            self.result_label.setText("错误：无法连接服务器")
            self.result_label.setStyleSheet("color: #ff6666;")
            self.upgrade_button.setEnabled(True)
            self.upgrade_button.setText("开始强化")
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

        self.refresh_data()
