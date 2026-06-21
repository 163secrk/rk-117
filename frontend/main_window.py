import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QStatusBar, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from api_client import ApiClient
from upgrade_page import UpgradePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("装备强化游戏")
        self.setMinimumSize(900, 650)
        self.resize(960, 680)

        self.api = ApiClient()

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

        status_layout.addWidget(title_label)
        status_layout.addStretch()
        status_layout.addWidget(self.gold_label)

        main_layout.addWidget(self.status_bar_frame)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        self.upgrade_page = UpgradePage(self.api)
        self.upgrade_page.gold_updated.connect(self._update_gold)
        self.tab_widget.addTab(self.upgrade_page, "强化")

        main_layout.addWidget(self.tab_widget, 1)

        self._refresh_gold()

    def _refresh_gold(self):
        self.api.get_player(self._on_player_loaded)

    def _on_player_loaded(self, player):
        if player and player.get("gold") is not None:
            self._update_gold(player["gold"])

    def _update_gold(self, gold: int):
        self.gold_label.setText(f"💰 金币：{gold:,}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
