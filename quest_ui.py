from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QProgressBar, QComboBox, QMessageBox, QDialog, QLineEdit,
    QTabWidget, QFrame, QGridLayout, QScrollArea, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIntValidator
from quest_data import load_data, save_data, TYPE_COLORS, TASK_TYPES, level_up_required
from quest_editor import QuestEditor
from datetime import datetime, date, timedelta


class QuestLogUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Achievle")
        self.resize(950, 700)
        self.data = load_data()
        self.init_ui()
        self.apply_styles()
        self.update_display()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        title = QLabel("✨ Achievle")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        status_layout = QHBoxLayout()
        self.level_label = QLabel()
        self.xp_bar = QProgressBar()
        self.xp_bar.setFixedHeight(12)
        status_layout.addWidget(self.level_label, 1)
        status_layout.addWidget(self.xp_bar, 3)
        main_layout.addLayout(status_layout)

        self.tabs = QTabWidget()
        self.active_tab = QWidget()
        self.stats_tab = QWidget()
        self.tabs.addTab(self.active_tab, "Активные задачи")
        self.tabs.addTab(self.stats_tab, "Статистика")
        main_layout.addWidget(self.tabs)

        self.setup_active_tab()
        self.setup_stats_tab()

        add_btn = QPushButton("➕ Добавить достижение")
        add_btn.clicked.connect(self.open_editor)
        main_layout.addWidget(add_btn)

    def setup_active_tab(self):
        layout = QVBoxLayout(self.active_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название или описание...")
        self.search_input.textChanged.connect(self.update_display)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Сортировка:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["По названию", "По типу", "По XP (↓)", "По XP (↑)"])
        self.sort_combo.currentTextChanged.connect(self.update_display)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        layout.addLayout(sort_layout)

        self.quest_list = QListWidget()
        self.quest_list.itemDoubleClicked.connect(self.edit_selected_quest)
        self.quest_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.quest_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.quest_list)

    def setup_stats_tab(self):
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.stats_layout = QVBoxLayout(self.scroll_content)
        self.stats_layout.setContentsMargins(24, 24, 24, 24)
        self.stats_layout.setSpacing(16)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background: #F9FAFB; }
            QLabel { color: #1F2937; font-family: 'Segoe UI'; }
            QPushButton {
                padding: 8px 16px; border-radius: 8px; font-weight: 600;
                background: #4A6CF7; color: white; border: none;
            }
            QPushButton:hover { background: #3a5bf5; }
            QListWidget { border: none; background: transparent; }
            QComboBox, QSpinBox, QLineEdit {
                padding: 6px; border: 1px solid #E5E7EB; border-radius: 6px;
            }
            QProgressBar {
                border: none; border-radius: 6px; background: #E5E7EB;
            }
            QProgressBar::chunk { background: #4A6CF7; border-radius: 6px; }
            QTabWidget::pane { border: 1px solid #E5E7EB; border-radius: 12px; }
            QTabBar::tab { padding: 8px 16px; }
        """)

    def calculate_widget_height(self, title, desc, is_cumulative):
        base_height = 40
        button_height = 34
        padding = 24
        if desc:
            lines = len(desc.splitlines())
            desc_height = max(1, lines) * 20
        else:
            desc_height = 0
        progress_height = 16 if is_cumulative else 0
        total_height = base_height + desc_height + progress_height + button_height + padding
        return max(100, int(total_height))

    def sort_quests(self, quests):
        mode = self.sort_combo.currentText()
        if mode == "По названию":
            return sorted(quests, key=lambda x: x["title"])
        elif mode == "По типу":
            type_order = {t: i for i, t in enumerate(TASK_TYPES)}
            return sorted(quests, key=lambda x: type_order.get(x["type"], 999))
        elif mode == "По XP (↓)":
            return sorted(quests, key=lambda x: x["xp"], reverse=True)
        elif mode == "По XP (↑)":
            return sorted(quests, key=lambda x: x["xp"])
        return quests

    def update_display(self):
        self.quest_list.clear()

        search_text = self.search_input.text().strip().lower()

        filtered_quests = []
        for q in self.data["quests"]:
            title_match = search_text in q["title"].lower()
            desc_match = search_text in q.get("desc", "").lower()
            if search_text == "" or title_match or desc_match:
                filtered_quests.append(q)

        sorted_quests = self.sort_quests(filtered_quests)

        for q in sorted_quests:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, q["id"])
            self.quest_list.addItem(item)

            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(12, 8, 12, 8)
            layout.setSpacing(6)

            top = QHBoxLayout()
            icon_text = q.get("icon", "🎮")
            icon = QLabel(icon_text)
            icon.setFixedSize(36, 36)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet(f"background: {TYPE_COLORS[q['type']]}; color: white; border-radius: 8px; font-size: 14px;")

            name_layout = QVBoxLayout()
            name_label = QLabel(f"<b>{q['title']}</b>")
            name_label.setFont(QFont("Segoe UI", 10))
            name_label.setWordWrap(True)
            name_label.setMaximumWidth(300)
            name_layout.addWidget(name_label)

            if q.get("desc"):
                desc_label = QLabel(q["desc"])
                desc_label.setFont(QFont("Segoe UI", 9))
                desc_label.setStyleSheet("color: #6B7280;")
                desc_label.setWordWrap(True)
                desc_label.setMaximumWidth(300)
                name_layout.addWidget(desc_label)

            exp_label = QLabel(f"{q['xp']} XP")
            exp_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            exp_label.setStyleSheet(f"color: {TYPE_COLORS[q['type']]};")

            top.addWidget(icon)
            top.addLayout(name_layout, 1)
            top.addWidget(exp_label)
            layout.addLayout(top)

            if q.get("is_cumulative"):
                pb = QProgressBar()
                target = q["target_value"]
                current = q["current_value"]
                pct = int(current / target * 100) if target else 0
                pb.setRange(0, 100)
                pb.setValue(pct)
                pb.setFormat(f"{pct}% ({current}/{target})")
                pb.setStyleSheet(f"""
                    QProgressBar::chunk {{ background: {TYPE_COLORS[q['type']]}; }}
                    QProgressBar {{ border-radius: 4px; background: #E5E7EB; }}
                """)
                pb.setFixedHeight(16)
                layout.addWidget(pb)

            # Определяем, ежедневное ли и выполнено ли сегодня
            is_daily = q["type"] in ["Ежедневное задание", "Продвинутое ежедневное задание"]
            is_completed_today = q.get("completed_today", False)

            # Кнопка
            btn_layout = QHBoxLayout()
            complete_btn = QPushButton()
            complete_btn.setFixedWidth(124)
            complete_btn.setFixedHeight(34)
            complete_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))

            if is_daily and is_completed_today:
                complete_btn.setText("✅ Выполнено")
                complete_btn.setEnabled(False)
                # Стиль: серый фон
                complete_btn.setStyleSheet("""
                    QPushButton {
                        background: #E5E7EB; color: #6B7280; border: none;
                    }
                """)
            else:
                complete_btn.setText("✅ Выполнить")
                complete_btn.setEnabled(True)
                complete_btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 16px; border-radius: 8px; font-weight: 600;
                        background: #4A6CF7; color: white; border: none;
                    }
                    QPushButton:hover { background: #3a5bf5; }
                """)
                complete_btn.clicked.connect(lambda _, q=q: self.complete_quest(q))

            btn_layout.addWidget(complete_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

            height = self.calculate_widget_height(q["title"], q.get("desc", ""), q.get("is_cumulative", False))
            item.setSizeHint(QSize(0, height))

            self.quest_list.setItemWidget(item, widget)

        level, xp = self.data["level"], self.data["xp"]
        xp_needed = level * 100
        self.level_label.setText(f"Уровень {level} • {xp} / {xp_needed} XP")
        self.xp_bar.setRange(0, xp_needed)
        self.xp_bar.setValue(xp)

        self.update_statistics()

    def update_statistics(self):
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        all_quests = self.data["quests"] + self.data["completed_quests"]
        completed = self.data["completed_quests"]
        total = len(all_quests)
        done = len(completed)

        title = QLabel("📊 Статистика прогресса")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.stats_layout.addWidget(title)

        self.add_stat_card(
            "Всего задач", f"{done} / {total}",
            f"Завершено {int(done/total*100) if total else 0}%"
        )

        self.add_stat_card("Всего XP заработано", str(self.data["xp"]), "Повышайте уровень!")

        type_stats = {}
        for t in TASK_TYPES:
            created = len([q for q in all_quests if q["type"] == t])
            finished = len([q for q in completed if q["type"] == t])
            type_stats[t] = (created, finished)

        type_widget = QFrame()
        type_widget.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB; padding: 16px;")
        type_layout = QVBoxLayout(type_widget)
        type_layout.addWidget(QLabel("<b>По типам:</b>"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        for i, (t, (cr, fin)) in enumerate(type_stats.items()):
            color = TYPE_COLORS[t]
            grid.addWidget(QLabel(f"<span style='color:{color}; font-size: 14px;'>●</span> {t}"), i, 0)
            grid.addWidget(QLabel(f"<b>{fin} / {cr}</b>"), i, 1, alignment=Qt.AlignmentFlag.AlignRight)
        type_layout.addLayout(grid)
        self.stats_layout.addWidget(type_widget)

        daily_types = ["Ежедневное задание", "Продвинутое ежедневное задание"]
        daily_done = len([q for q in completed if q["type"] in daily_types])
        self.add_stat_card("Выполнено ежедневных", str(daily_done), "Регулярность — ключ к успеху!")

        top_xp = sorted(completed, key=lambda x: x["xp"], reverse=True)[:3]
        if top_xp:
            top_widget = QFrame()
            top_widget.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E5E7EB; padding: 16px;")
            top_layout = QVBoxLayout(top_widget)
            top_layout.addWidget(QLabel("<b>Топ достижений по XP:</b>"))
            for q in top_xp:
                icon = q.get("icon", "🏆")
                top_layout.addWidget(QLabel(f"{icon} <b>{q['title']}</b> — {q['xp']} XP"))
            self.stats_layout.addWidget(top_widget)

        today = date.today()
        week_ago = today - timedelta(days=7)
        recent = [
            q for q in completed
            if "date" in q and datetime.strptime(q["date"], "%Y-%m-%d").date() >= week_ago
        ]
        self.add_stat_card("Завершено за неделю", str(len(recent)), "Ваша недавняя активность")

        self.stats_layout.addStretch()

    def add_stat_card(self, title, value, subtitle=""):
        card = QFrame()
        card.setStyleSheet("""
            background: white;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            padding: 16px;
        """)
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        layout.addWidget(QLabel(f"<h2 style='margin: 8px 0;'>{value}</h2>"))
        if subtitle:
            layout.addWidget(QLabel(f"<span style='color:#6B7280;'>{subtitle}</span>"))
        self.stats_layout.addWidget(card)

    def open_editor(self):
        editor = QuestEditor(self)
        if editor.exec():
            data = editor.get_data()
            if not data["title"]:
                QMessageBox.warning(self, "Ошибка", "Укажите название.")
                return
            self.data["quests"].append(data)
            save_data(self.data)
            self.update_display()

    def edit_selected_quest(self, item):
        quest_id = item.data(Qt.ItemDataRole.UserRole)
        quest = None
        for q in self.data["quests"]:
            if q["id"] == quest_id:
                quest = q
                break
        if quest is None:
            return

        editor = QuestEditor(self, quest_data=quest)
        if editor.exec():
            updated = editor.get_data()
            for i, q in enumerate(self.data["quests"]):
                if q["id"] == quest_id:
                    self.data["quests"][i] = updated
                    break
            save_data(self.data)
            self.update_display()

    def show_context_menu(self, position):
        item = self.quest_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("✏️ Редактировать")
        delete_action = menu.addAction("🗑️ Удалить")

        edit_action.triggered.connect(lambda: self.edit_selected_quest(item))
        delete_action.triggered.connect(lambda: self.delete_selected_quest(item))

        global_pos = self.quest_list.mapToGlobal(position)
        menu.popup(global_pos)
    


    def delete_selected_quest(self, item):
        quest_id = item.data(Qt.ItemDataRole.UserRole)
        quest = None
        for q in self.data["quests"]:
            if q["id"] == quest_id:
                quest = q
                break
        if not quest:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить задание «{quest['title']}»?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest_id]
            save_data(self.data)
            self.update_display()

    def complete_quest(self, quest):
        daily_types = ["Ежедневное задание", "Продвинутое ежедневное задание"]
        is_daily = quest["type"] in daily_types

        if quest.get("is_cumulative"):
            dialog = QDialog(self)
            dialog.setWindowTitle("Добавить прогресс")
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel(f"Цель: {quest['target_value']} (текущий: {quest['current_value']})"))

            input_field = QLineEdit()
            input_field.setValidator(QIntValidator(0, 10_000_000))
            input_field.setPlaceholderText("Сколько добавить?")
            layout.addWidget(input_field)

            def apply_progress():
                try:
                    add = int(input_field.text() or 0)
                except ValueError:
                    add = 0
                new_val = quest["current_value"] + add
                quest["current_value"] = new_val

                if new_val >= quest["target_value"]:
                    # Помечаем как выполненное сегодня
                    quest["completed_today"] = True
                    # Добавляем XP
                    self.data["xp"] += quest["xp"]
                    # Сохраняем в историю
                    completed_copy = quest.copy()
                    completed_copy["date"] = str(date.today())
                    self.data["completed_quests"].append(completed_copy)
                    # Повышаем уровень
                    while level_up_required(self.data["level"], self.data["xp"]):
                        self.data["level"] += 1
                    save_data(self.data)
                    self.update_display()  # ← ОБНОВЛЯЕМ ВИДЖЕТЫ!
                    QMessageBox.information(self, "✅ Успех!", f"Достижение «{quest['title']}» завершено!")
                    dialog.accept()
                else:
                    save_data(self.data)
                    self.update_display()
                    dialog.accept()

            btn = QPushButton("Добавить")
            btn.clicked.connect(apply_progress)
            layout.addWidget(btn)
            dialog.exec()
        else:
            # Простое задание
            if is_daily:
                # Ежедневное — просто помечаем как выполненное
                quest["completed_today"] = True
                self.data["xp"] += quest["xp"]
                completed_copy = quest.copy()
                completed_copy["date"] = str(date.today())
                self.data["completed_quests"].append(completed_copy)
                while level_up_required(self.data["level"], self.data["xp"]):
                    self.data["level"] += 1
                save_data(self.data)
                self.update_display()
                QMessageBox.information(self, "✅ Успех!", f"Достижение «{quest['title']}» завершено!")
            else:
                # Обычное — спрашиваем подтверждение и удаляем
                reply = QMessageBox.question(
                    self,
                    "Подтвердите",
                    f"Завершить достижение «{quest['title']}»?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                # Удаляем из списка
                self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest["id"]]
                completed_quest = quest.copy()
                completed_quest["date"] = str(date.today())
                self.data["xp"] += completed_quest["xp"]
                self.data["completed_quests"].append(completed_quest)
                while level_up_required(self.data["level"], self.data["xp"]):
                    self.data["level"] += 1
                save_data(self.data)
                self.update_display()
                QMessageBox.information(self, "✅ Успех!", f"Достижение «{quest['title']}» завершено!")

    def closeEvent(self, event):
        save_data(self.data)
        event.accept()