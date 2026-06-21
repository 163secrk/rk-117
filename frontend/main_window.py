import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QStatusBar, QFrame, QPushButton, QDialog,
    QSpinBox, QMessageBox, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from api_client import ApiClient
from upgrade_page import UpgradePage


SHOP_ITEMS = [
    {"key": "stones", "name": "强化石", "icon": "💎", "price": 10, "unit": "颗"},
    {"key": "protect", "name": "保护卷", "icon": "🛡", "price": 500, "unit": "张"},
    {"key": "lucky", "name": "幸运符", "icon": "🍀", "price": 800, "unit": "张"},
]


class ShopDialog(QDialog):
    def __init__(self, api_client, current_gold, current_stones, current_scrolls, current_charms, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.setWindowTitle("商店")
        self.setFixedSize(420, 380)
        self.setStyleSheet("""
            QDialog {
                background-color: #14141e;
            }
            QLabel {
                color: #ddd;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4a7acc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
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
            QSpinBox, QComboBox {
                background-color: #2a2a3e;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("🏪 商店")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffcc44;")
        layout.addWidget(title)

        self.gold_label = QLabel(f"💰 当前金币：{current_gold:,}")
        self.gold_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.gold_label)

        resources_layout = QHBoxLayout()
        resources_layout.setSpacing(15)
        self.stones_label = QLabel(f"💎 强化石：{current_stones:,}")
        self.stones_label.setAlignment(Qt.AlignCenter)
        self.scrolls_label = QLabel(f"🛡 保护卷：{current_scrolls:,}")
        self.scrolls_label.setAlignment(Qt.AlignCenter)
        self.charms_label = QLabel(f"🍀 幸运符：{current_charms:,}")
        self.charms_label.setAlignment(Qt.AlignCenter)
        resources_layout.addWidget(self.stones_label)
        resources_layout.addWidget(self.scrolls_label)
        resources_layout.addWidget(self.charms_label)
        layout.addLayout(resources_layout)

        item_layout = QHBoxLayout()
        item_layout.setSpacing(10)
        item_label = QLabel("选择商品：")
        self.item_combo = QComboBox()
        for item in SHOP_ITEMS:
            self.item_combo.addItem(f"{item['icon']} {item['name']} ({item['price']}金币/{item['unit']})", item["key"])
        self.item_combo.currentIndexChanged.connect(self._update_total)
        item_layout.addWidget(item_label)
        item_layout.addWidget(self.item_combo, 1)
        layout.addLayout(item_layout)

        self.desc_label = QLabel("")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(self.desc_label)

        amount_layout = QHBoxLayout()
        amount_layout.setSpacing(10)
        amount_label = QLabel("购买数量：")
        self.amount_spin = QSpinBox()
        self.amount_spin.setMinimum(1)
        self.amount_spin.setMaximum(999999)
        self.amount_spin.setValue(1)
        self.amount_spin.valueChanged.connect(self._update_total)
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_spin)
        layout.addLayout(amount_layout)

        self.total_label = QLabel("总计：10 金币")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("color: #ffcc44; font-weight: bold; font-size: 15px;")
        layout.addWidget(self.total_label)

        self.buy_button = QPushButton("购买")
        self.buy_button.clicked.connect(self._on_buy_clicked)
        layout.addWidget(self.buy_button)

        layout.addStretch()

        self._update_total()

    def _get_current_item(self):
        key = self.item_combo.currentData()
        return next((item for item in SHOP_ITEMS if item["key"] == key), SHOP_ITEMS[0])

    def _update_total(self):
        item = self._get_current_item()
        amount = self.amount_spin.value()
        total = amount * item["price"]
        self.total_label.setText(f"总计：{total:,} 金币")
        if item["key"] == "protect":
            self.desc_label.setText("保护卷：强化失败时不扣除强化石，每次消耗1张")
        elif item["key"] == "lucky":
            self.desc_label.setText("幸运符：强化成功率+15%，每次消耗1张")
        else:
            self.desc_label.setText("强化石：装备强化必需材料")

    def _on_buy_clicked(self):
        item = self._get_current_item()
        amount = self.amount_spin.value()
        self.buy_button.setEnabled(False)
        self.buy_button.setText("购买中...")
        if item["key"] == "stones":
            self.api.buy_stones(amount, self._on_buy_result)
        elif item["key"] == "protect":
            self.api.buy_protect_scrolls(amount, self._on_buy_result)
        elif item["key"] == "lucky":
            self.api.buy_lucky_charms(amount, self._on_buy_result)

    def _on_buy_result(self, result):
        if not result:
            QMessageBox.critical(self, "错误", "无法连接服务器")
            self.buy_button.setEnabled(True)
            self.buy_button.setText("购买")
            return

        if result.get("success"):
            QMessageBox.information(self, "成功", result.get("message", "购买成功"))
            if result.get("gold") is not None:
                self.gold_label.setText(f"💰 当前金币：{result['gold']:,}")
            if result.get("enhance_stones") is not None:
                self.stones_label.setText(f"💎 强化石：{result['enhance_stones']:,}")
            if result.get("protect_scrolls") is not None:
                self.scrolls_label.setText(f"🛡 保护卷：{result['protect_scrolls']:,}")
            if result.get("lucky_charms") is not None:
                self.charms_label.setText(f"🍀 幸运符：{result['lucky_charms']:,}")
            if hasattr(self.parent(), '_on_player_loaded'):
                self.parent()._on_player_loaded({
                    "gold": result.get("gold"),
                    "enhance_stones": result.get("enhance_stones"),
                    "protect_scrolls": result.get("protect_scrolls"),
                    "lucky_charms": result.get("lucky_charms"),
                })
        else:
            QMessageBox.warning(self, "失败", result.get("message", "购买失败"))

        self.buy_button.setEnabled(True)
        self.buy_button.setText("购买")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("装备强化游戏")
        self.setMinimumSize(900, 720)
        self.resize(1000, 750)

        self.api = ApiClient()
        self.current_stones = 0
        self.current_scrolls = 0
        self.current_charms = 0

        self._apply_global_style()
        self._init_ui()

    def _apply_global_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #14141e;
            }
            QTabWidget::pane {
                border: none;
                background-color: #14141e;
            }
            QTabBar::tab {
                background-color: #1e1e2e;
                color: #aaa;
                padding: 12px 30px;
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #2a2a3e;
                color: #ffcc44;
            }
            QTabBar::tab:hover:!selected {
                background-color: #252538;
                color: #ccc;
            }
            QStatusBar {
                background-color: #1a1a28;
                color: #ddd;
                border-top: 1px solid #333;
            }
            QLabel {
                color: #ddd;
            }
        """)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.status_bar_frame = QFrame()
        self.status_bar_frame.setFixedHeight(45)
        self.status_bar_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a28;
                border-bottom: 1px solid #333;
            }
        """)
        status_layout = QHBoxLayout(self.status_bar_frame)
        status_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("装备强化游戏")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffcc44;")

        self.gold_label = QLabel("💰 金币：0")
        gold_font = QFont()
        gold_font.setPointSize(13)
        gold_font.setBold(True)
        self.gold_label.setFont(gold_font)
        self.gold_label.setStyleSheet("color: #ffcc44;")

        self.stones_label = QLabel("💎 强化石：0")
        stones_font = QFont()
        stones_font.setPointSize(13)
        stones_font.setBold(True)
        self.stones_label.setFont(stones_font)
        self.stones_label.setStyleSheet("color: #88ddff;")

        self.scrolls_label = QLabel("🛡 保护卷：0")
        scrolls_font = QFont()
        scrolls_font.setPointSize(13)
        scrolls_font.setBold(True)
        self.scrolls_label.setFont(scrolls_font)
        self.scrolls_label.setStyleSheet("color: #ffaa88;")

        self.charms_label = QLabel("🍀 幸运符：0")
        charms_font = QFont()
        charms_font.setPointSize(13)
        charms_font.setBold(True)
        self.charms_label.setFont(charms_font)
        self.charms_label.setStyleSheet("color: #aaffaa;")

        self.shop_button = QPushButton("🏪 商店")
        shop_font = QFont()
        shop_font.setPointSize(12)
        shop_font.setBold(True)
        self.shop_button.setFont(shop_font)
        self.shop_button.setCursor(Qt.PointingHandCursor)
        self.shop_button.setStyleSheet("""
            QPushButton {
                background-color: #4a7acc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #5a8adc;
            }
            QPushButton:pressed {
                background-color: #3a6abc;
            }
        """)
        self.shop_button.clicked.connect(self._open_shop)

        status_layout.addWidget(title_label)
        status_layout.addStretch()
        status_layout.addWidget(self.gold_label)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.stones_label)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.scrolls_label)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.charms_label)
        status_layout.addSpacing(15)
        status_layout.addWidget(self.shop_button)

        main_layout.addWidget(self.status_bar_frame)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        self.upgrade_page = UpgradePage(self.api)
        self.upgrade_page.gold_updated.connect(self._update_gold)
        self.upgrade_page.stones_updated.connect(self._update_stones)
        self.upgrade_page.scrolls_updated.connect(self._update_scrolls)
        self.upgrade_page.charms_updated.connect(self._update_charms)
        self.tab_widget.addTab(self.upgrade_page, "强化")

        main_layout.addWidget(self.tab_widget, 1)

        self._refresh_gold()

    def _refresh_gold(self):
        self.api.get_player(self._on_player_loaded)

    def _on_player_loaded(self, player):
        if player and player.get("gold") is not None:
            self._update_gold(player["gold"])
        if player and player.get("enhance_stones") is not None:
            self._update_stones(player["enhance_stones"])
        if player and player.get("protect_scrolls") is not None:
            self._update_scrolls(player["protect_scrolls"])
        if player and player.get("lucky_charms") is not None:
            self._update_charms(player["lucky_charms"])

    def _update_gold(self, gold: int):
        self.gold_label.setText(f"💰 金币：{gold:,}")

    def _update_stones(self, stones: int):
        self.current_stones = stones
        self.stones_label.setText(f"💎 强化石：{stones:,}")

    def _update_scrolls(self, scrolls: int):
        self.current_scrolls = scrolls
        self.scrolls_label.setText(f"🛡 保护卷：{scrolls:,}")

    def _update_charms(self, charms: int):
        self.current_charms = charms
        self.charms_label.setText(f"🍀 幸运符：{charms:,}")

    def _open_shop(self):
        current_gold = 0
        try:
            gold_text = self.gold_label.text()
            gold_num = gold_text.replace("💰 金币：", "").replace(",", "")
            current_gold = int(gold_num)
        except:
            pass

        dialog = ShopDialog(self.api, current_gold, self.current_stones, self.current_scrolls, self.current_charms, self)
        dialog.exec()
        self.upgrade_page.refresh_data()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
