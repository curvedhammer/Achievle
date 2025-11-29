from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import uuid
from quest_data import TASK_TYPES, ICONS


class QuestEditor(QDialog):
    def __init__(self, parent=None, quest_data=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Новое достижение" if not quest_data else "✏️ Редактировать")
        self.setModal(True)
        self.resize(450, 450)
        self.quest_data = quest_data or {}

        self.theme = "light"
        if parent is not None:
            try:
                if hasattr(parent, 'get_current_theme'):
                    self.theme = parent.get_current_theme()
            except Exception:
                pass
        self.apply_theme(self.theme)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Название:"))
        self.title_input = QLineEdit(self.quest_data.get("title", ""))
        self.title_input.setPlaceholderText("Например: Пробежать 5 км")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Описание (не более 200 символов):"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(self.quest_data.get("desc", ""))
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setFixedHeight(80)
        self.desc_input.setPlaceholderText("Краткое описание")
        self.desc_input.setFont(QFont("Segoe UI", 10))
        self.desc_input.textChanged.connect(self.limit_description)
        layout.addWidget(self.desc_input)

        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel("Иконка:"))
        self.icon_combo = QComboBox()
        self.icon_combo.addItems(ICONS)
        icon = self.quest_data.get("icon")
        if icon in ICONS:
            self.icon_combo.setCurrentText(icon)
        else:
            self.icon_combo.setCurrentIndex(0)
        icon_layout.addWidget(self.icon_combo)
        layout.addLayout(icon_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(TASK_TYPES)
        current_type = self.quest_data.get("type", "Обычное достижение")
        if current_type in TASK_TYPES:
            self.type_combo.setCurrentText(current_type)
        else:
            self.type_combo.setCurrentIndex(0)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        xp_layout = QHBoxLayout()
        xp_layout.addWidget(QLabel("XP:"))
        self.xp_spin = QSpinBox()
        self.xp_spin.setRange(1, 1000)
        self.xp_spin.setValue(self.quest_data.get("xp", 10))
        self.xp_spin.setFixedWidth(100)
        self.xp_spin.setFixedHeight(36)
        xp_layout.addWidget(self.xp_spin)
        layout.addLayout(xp_layout)

        cumulative_layout = QHBoxLayout()
        cumulative_layout.addWidget(QLabel("Накопительное:"))
        self.cumulative_check = QComboBox()
        self.cumulative_check.addItems(["Нет", "Да"])
        self.cumulative_check.setCurrentText("Да" if self.quest_data.get("is_cumulative") else "Нет")
        self.cumulative_check.currentTextChanged.connect(self.toggle_target)
        cumulative_layout.addWidget(self.cumulative_check)

        self.target_label = QLabel("Цель:")
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 10_000_000)
        self.target_spin.setValue(self.quest_data.get("target_value", 100))
        self.target_spin.setFixedWidth(100)
        self.target_spin.setFixedHeight(36)

        is_cumulative = self.quest_data.get("is_cumulative", False)
        self.target_label.setVisible(is_cumulative)
        self.target_spin.setVisible(is_cumulative)

        cumulative_layout.addWidget(self.target_label)
        cumulative_layout.addWidget(self.target_spin)
        cumulative_layout.addStretch()
        layout.addLayout(cumulative_layout)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def toggle_target(self, text):
        visible = (text == "Да")
        self.target_label.setVisible(visible)
        self.target_spin.setVisible(visible)

    def limit_description(self):
        text = self.desc_input.toPlainText()
        if len(text) > 200:
            cursor = self.desc_input.textCursor()
            scroll_pos = cursor.verticalMovementX()
            self.desc_input.setPlainText(text[:200])
            new_cursor = self.desc_input.textCursor()
            new_cursor.movePosition(new_cursor.MoveOperation.End)
            self.desc_input.setTextCursor(new_cursor)

    def get_data(self):
        is_cum = self.cumulative_check.currentText() == "Да"
        return {
            "id": self.quest_data.get("id", str(uuid.uuid4())),
            "title": self.title_input.text().strip(),
            "desc": self.desc_input.toPlainText().strip(),
            "icon": self.icon_combo.currentText(),
            "type": self.type_combo.currentText(),
            "xp": self.xp_spin.value(),
            "is_cumulative": is_cum,
            "target_value": self.target_spin.value() if is_cum else 0,
            "current_value": self.quest_data.get("current_value", 0) if is_cum else 0,
        }
    
    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet("""
                QDialog {
                    background-color: #111827;
                    color: #E5E7EB;
                    font-family: 'Segoe UI';
                }
                QLabel {
                    color: #E5E7EB;
                }
                QLineEdit, QTextEdit, QComboBox, QSpinBox {
                    background: #1F2937;
                    color: #E5E7EB;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 4px;
                }
                QTextEdit {
                    padding: 6px;
                }
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-weight: 600;
                    background: #4F46E5;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background: #4338CA;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #F9FAFB;
                    color: #1F2937;
                    font-family: 'Segoe UI';
                }
                QLabel {
                    color: #1F2937;
                }
                QLineEdit, QTextEdit, QComboBox, QSpinBox {
                    background: white;
                    color: #1F2937;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    padding: 4px;
                }
                QTextEdit {
                    padding: 6px;
                }
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-weight: 600;
                    background: #4A6CF7;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background: #3a5bf5;
                }
            """)