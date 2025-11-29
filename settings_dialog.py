import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from quest_data import save_data, export_data, import_data, reset_data


class SettingsDialog(QDialog):
    def __init__(self, parent, current_theme, on_theme_change, on_data_change):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройки")
        self.resize(400, 300)
        self.current_theme = current_theme
        self.on_theme_change = on_theme_change
        self.on_data_change = on_data_change
        self.setup_ui()

    def setup_ui(self):
        self.apply_theme_style()

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        theme_group = self.create_group("🎨 Внешний вид")
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.setCurrentText("Светлая" if self.current_theme == "light" else "Тёмная")
        theme_layout.addWidget(self.theme_combo)
        theme_group.layout().addLayout(theme_layout)

        data_group = self.create_group("🗃️ Управление данными")

        export_btn = QPushButton("📤 Экспортировать данные")
        export_btn.clicked.connect(self.export_data)
        data_group.layout().addWidget(export_btn)

        import_btn = QPushButton("📥 Импортировать данные")
        import_btn.clicked.connect(self.import_data)
        data_group.layout().addWidget(import_btn)

        reset_btn = QPushButton("🗑️ Удалить все данные")
        reset_btn.setStyleSheet("background-color: #EF4444; color: white;")
        reset_btn.clicked.connect(self.reset_data)
        data_group.layout().addWidget(reset_btn)

        layout.addWidget(theme_group)
        layout.addWidget(data_group)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_group(self, title):
        from PyQt6.QtWidgets import QFrame, QVBoxLayout
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        group_layout = QVBoxLayout(frame)
        group_layout.setContentsMargins(12, 12, 12, 12)
        group_layout.addWidget(QLabel(f"<b>{title}</b>"))
        return frame

    def export_data(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные", "achievements_backup.json", "JSON Files (*.json)"
        )
        if filename:
            try:
                export_data(filename)
                QMessageBox.information(self, "✅ Успех", "Данные успешно экспортированы!")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось экспортировать:\n{str(e)}")

    def import_data(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные", "", "JSON Files (*.json)"
        )
        if filename:
            reply = QMessageBox.warning(
                self, "⚠️ Внимание",
                "Все текущие данные будут заменены!\nПродолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    new_data = import_data(filename)
                    self.on_data_change(new_data)
                    QMessageBox.information(self, "✅ Успех", "Данные успешно импортированы!")
                    self.accept()
                except Exception as e:
                    QMessageBox.critical(self, "❌ Ошибка", f"Не удалось импортировать:\n{str(e)}")

    def reset_data(self):
        reply = QMessageBox.critical(
            self, "🗑️ Удалить все данные?",
            "Вы уверены? Все достижения и прогресс будут безвозвратно удалены!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            new_data = reset_data()
            self.on_data_change(new_data)
            QMessageBox.information(self, "✅ Сброс", "Все данные удалены.")
            self.accept()
    
    def apply_theme_style(self):
        if self.current_theme == "dark":
            self.setStyleSheet("""
                QDialog {
                    background-color: #111827;
                    color: #E5E7EB;
                    font-family: 'Segoe UI';
                }
                QLabel {
                    color: #E5E7EB;
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
                QComboBox {
                    padding: 6px;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    background: #1F2937;
                    color: #E5E7EB;
                }
                QFrame {
                    background: #1F2937;
                    border: 1px solid #374151;
                    border-radius: 10px;
                    padding: 12px;
                }
                QFrame QLabel {
                    color: #E5E7EB;
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
                QComboBox {
                    padding: 6px;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    background: white;
                }
                QFrame {
                    background: white;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)

    def accept(self):
        new_theme = "light" if self.theme_combo.currentText() == "Светлая" else "dark"
        if new_theme != self.current_theme:
            self.on_theme_change(new_theme)
        super().accept()