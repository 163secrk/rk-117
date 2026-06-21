from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

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
    "blue": "#66aaff",
    "purple": "#cc66ff",
    "orange": "#ffaa33",
}


class InventoryItemCard(QFrame):
    equip_clicked = Signal(int)
    reforge_clicked = Signal(int)

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.inventory_id = item_data["id"]
        self.is_equipped = item_data.get("is_equipped", False)

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(self._get_style())
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        slot = item_data.get("slot", "")
        level = item_data.get("level", 0)
        quality = item_data.get("quality", "普通")
        quality_color = item_data.get("quality_color", "white")
        color = QUALITY_COLORS.get(quality_color, "#dddddd")

        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        slot_icon = SLOT_ICONS.get(slot, "❓")
        slot_label = QLabel(slot_icon)
        slot_font = QFont()
        slot_font.setPointSize(20)
        slot_label.setFont(slot_font)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        display_name = item_data.get("display_name", item_data.get("name", ""))
        name_label = QLabel(display_name)
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {color};")

        quality_label = QLabel(f"【{quality}】")
        quality_font = QFont()
        quality_font.setPointSize(10)
        quality_label.setFont(quality_font)
        quality_label.setStyleSheet(f"color: {color};")

        name_layout.addWidget(name_label)
        name_layout.addWidget(quality_label)

        top_layout.addWidget(slot_label)
        top_layout.addLayout(name_layout, 1)

        layout.addLayout(top_layout)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        slot_name = SLOT_NAMES.get(slot, slot)
        slot_label_text = QLabel(f"{slot_name}")
        slot_label_text.setStyleSheet("color: #aaa; font-size: 11px;")

        level_label = QLabel(f"等级 +{level}" if level > 0 else "等级 0")
        level_label.setStyleSheet("color: #88ddff; font-size: 11px;")

        info_layout.addWidget(slot_label_text)
        info_layout.addStretch()
        info_layout.addWidget(level_label)

        layout.addLayout(info_layout)

        attr = item_data.get("attribute")
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
            attr_label = QLabel(attr_text)
            attr_label.setStyleSheet("color: #88ddff; font-size: 11px;")
            layout.addWidget(attr_label)

        has_affix = item_data.get("has_affix", False)
        affix = item_data.get("affix")
        if has_affix and affix:
            affix_name = affix.get("name", "")
            affix_value = affix.get("value", 0)
            affix_text = f"✨ 特殊词条：{affix_name} +{int(affix_value * 100)}%"
            affix_label = QLabel(affix_text)
            affix_label.setStyleSheet("color: #ffaa33; font-size: 11px; font-weight: bold;")
            affix_label.setWordWrap(True)
            layout.addWidget(affix_label)
        elif level >= 10 and not has_affix:
            affix_label = QLabel("✨ +10解锁特殊词条")
            affix_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(affix_label)
        elif level < 10:
            affix_label = QLabel(f"🔒 +10解锁特殊词条（当前+{level}）")
            affix_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(affix_label)

        if self.is_equipped:
            equip_label = QLabel("✅ 已装备")
            equip_label.setAlignment(Qt.AlignCenter)
            equip_label.setStyleSheet("color: #66ff66; font-size: 11px; font-weight: bold;")
            layout.addWidget(equip_label)

            self.reforge_button = QPushButton("🔨 重铸品质 (500金币)")
            self.reforge_button.setFixedHeight(28)
            btn_font = QFont()
            btn_font.setPointSize(10)
            btn_font.setBold(True)
            self.reforge_button.setFont(btn_font)
            self.reforge_button.setCursor(Qt.PointingHandCursor)
            self.reforge_button.setStyleSheet("""
                QPushButton {
                    background-color: #cc6633;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background-color: #dd7744;
                }
                QPushButton:pressed {
                    background-color: #bb5522;
                }
            """)
            self.reforge_button.clicked.connect(self._on_reforge_clicked)
            layout.addWidget(self.reforge_button)
        else:
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(6)

            self.equip_button = QPushButton("一键换上")
            self.equip_button.setFixedHeight(28)
            btn_font = QFont()
            btn_font.setPointSize(11)
            btn_font.setBold(True)
            self.equip_button.setFont(btn_font)
            self.equip_button.setCursor(Qt.PointingHandCursor)
            self.equip_button.setStyleSheet("""
                QPushButton {
                    background-color: #4a7acc;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background-color: #5a8adc;
                }
                QPushButton:pressed {
                    background-color: #3a6abc;
                }
            """)
            self.equip_button.clicked.connect(self._on_equip_clicked)

            self.reforge_button = QPushButton("🔨 重铸")
            self.reforge_button.setFixedHeight(28)
            self.reforge_button.setFont(btn_font)
            self.reforge_button.setCursor(Qt.PointingHandCursor)
            self.reforge_button.setStyleSheet("""
                QPushButton {
                    background-color: #cc6633;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background-color: #dd7744;
                }
                QPushButton:pressed {
                    background-color: #bb5522;
                }
            """)
            self.reforge_button.clicked.connect(self._on_reforge_clicked)

            btn_layout.addWidget(self.equip_button, 1)
            btn_layout.addWidget(self.reforge_button, 1)
            layout.addLayout(btn_layout)

    def _get_style(self):
        if self.is_equipped:
            return """
                QFrame {
                    background-color: #2a3a4a;
                    border: 2px solid #5a9aff;
                    border-radius: 8px;
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

    def _on_equip_clicked(self):
        self.equip_clicked.emit(self.inventory_id)

    def _on_reforge_clicked(self):
        self.reforge_clicked.emit(self.inventory_id)


class InventoryPage(QWidget):
    gold_updated = Signal(int)
    stones_updated = Signal(int)
    scrolls_updated = Signal(int)
    charms_updated = Signal(int)
    equipment_changed = Signal()

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.items = []
        self._equip_pending = False
        self._reforge_pending = False

        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("🎒 背包")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #eee;")

        self.count_label = QLabel("加载中...")
        self.count_label.setStyleSheet("color: #888; font-size: 13px;")

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a5a;
                color: #ddd;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #4a4a6a;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #2a2a4a;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)

        header_layout.addWidget(title)
        header_layout.addSpacing(15)
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)

        main_layout.addWidget(header_frame)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a28;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777;
            }
        """)

        self.items_container = QWidget()
        self.items_layout = QGridLayout(self.items_container)
        self.items_layout.setContentsMargins(5, 5, 5, 5)
        self.items_layout.setSpacing(12)

        self.scroll_area.setWidget(self.items_container)
        main_layout.addWidget(self.scroll_area, 1)

        self.empty_label = QLabel("背包空空如也，快去野外狩猎获取装备吧！")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
        self.empty_label.setVisible(False)
        main_layout.addWidget(self.empty_label)

        self.tip_label = QLabel("💡 提示：点击装备卡片上的\"一键换上\"按钮即可装备，已装备的装备会有蓝色边框标记")
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setStyleSheet("color: #888; font-size: 12px;")
        main_layout.addWidget(self.tip_label)

    def refresh_data(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("刷新中...")
        self.api.get_inventory(self._on_inventory_loaded)

    def _on_inventory_loaded(self, result):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")

        if not result:
            self.count_label.setText("加载失败")
            return

        if not result.get("success"):
            self.count_label.setText(result.get("message", "加载失败"))
            return

        self.items = result.get("items", [])
        self.count_label.setText(result.get("message", f"共 {len(self.items)} 件装备"))
        self._display_items()

    def _display_items(self):
        for i in reversed(range(self.items_layout.count())):
            item = self.items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        if not self.items:
            self.scroll_area.setVisible(False)
            self.empty_label.setVisible(True)
            return

        self.scroll_area.setVisible(True)
        self.empty_label.setVisible(False)

        columns = 3
        equipped_items = [item for item in self.items if item.get("is_equipped")]
        unequipped_items = [item for item in self.items if not item.get("is_equipped")]
        sorted_items = equipped_items + unequipped_items

        for idx, item_data in enumerate(sorted_items):
            row = idx // columns
            col = idx % columns
            card = InventoryItemCard(item_data)
            card.equip_clicked.connect(self._on_equip_clicked)
            card.reforge_clicked.connect(self._on_reforge_clicked)
            self.items_layout.addWidget(card, row, col)

    def _on_equip_clicked(self, inventory_id):
        if self._equip_pending:
            return

        self._equip_pending = True
        self.api.equip_item(inventory_id, self._on_equip_result)

    def _on_equip_result(self, result):
        self._equip_pending = False

        if not result:
            QMessageBox.critical(self, "错误", "无法连接服务器")
            return

        if result.get("success"):
            QMessageBox.information(self, "成功", result.get("message", "装备成功"))

            if result.get("gold") is not None:
                self.gold_updated.emit(result["gold"])
            if result.get("enhance_stones") is not None:
                self.stones_updated.emit(result["enhance_stones"])
            if result.get("protect_scrolls") is not None:
                self.scrolls_updated.emit(result["protect_scrolls"])
            if result.get("lucky_charms") is not None:
                self.charms_updated.emit(result["lucky_charms"])

            self.equipment_changed.emit()
            self.refresh_data()
        else:
            QMessageBox.warning(self, "失败", result.get("message", "装备失败"))

    def _on_reforge_clicked(self, inventory_id):
        if self._reforge_pending:
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
        self.api.reforge_inventory(inventory_id, self._on_reforge_result)

    def _on_reforge_result(self, result):
        self._reforge_pending = False

        if not result:
            QMessageBox.critical(self, "错误", "无法连接服务器")
            return

        if result.get("success"):
            QMessageBox.information(self, "重铸成功", result.get("message", "重铸成功"))

            if result.get("gold") is not None:
                self.gold_updated.emit(result["gold"])

            self.equipment_changed.emit()
            self.refresh_data()
        else:
            QMessageBox.warning(self, "失败", result.get("message", "重铸失败"))
