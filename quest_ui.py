from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QProgressBar, QComboBox, QMessageBox, QDialog, QLineEdit,
    QTabWidget, QFrame, QGridLayout, QScrollArea, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIntValidator
from quest_data import (
    load_data, save_data, TYPE_COLORS, TASK_TYPES,
    can_level_up, xp_needed_for_next_level
)
from quest_editor import QuestEditor
from datetime import datetime, date, timedelta
from settings_dialog import SettingsDialog

CATEGORY_MAP = {
    "Все": TASK_TYPES,
    "Ежедневные задачи": ["Ежедневное задание", "Продвинутое ежедневное задание"],
    "Задачи": ["Обычное задание", "Умеренное задание", "Задание повышенной сложности"],
    "Достижения": ["Обычное достижение", "Умеренное достижение", "Продвинутое достижение"],
    "Испытания": ["Испытание", "Продвинутое испытание"],
    "Мастерство": ["Мастерство"]
}
class QuestLogUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Achievle")
        self.resize(950, 700)
        self.data = load_data()
        self.init_ui()
        self.apply_styles()
        self.update_display()

        from PyQt6.QtCore import QTimer
        self.daily_check_timer = QTimer(self)
        self.daily_check_timer.timeout.connect(self.check_daily_archive)
        self.daily_check_timer.start(60 * 60 * 1000)

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

        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.clicked.connect(self.open_settings)
        main_layout.addWidget(settings_btn)

        add_btn = QPushButton("➕ Добавить достижение")
        add_btn.clicked.connect(self.open_editor)
        main_layout.addWidget(add_btn)

        self.archive_tab = QWidget()
        self.tabs.addTab(self.archive_tab, "Архив")
        self.setup_archive_tab()

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

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORY_MAP.keys())
        self.category_combo.setCurrentText("Все")
        self.category_combo.currentTextChanged.connect(self.update_display)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Сортировка:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["По названию", "По типу", "По XP (↓)", "По XP (↑)"])
        self.sort_combo.currentTextChanged.connect(self.update_display)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        layout.addLayout(sort_layout)

        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Segoe UI", 9))
        self.stats_label.setStyleSheet("color: #6B7280; padding: 4px;")
        sort_layout.addWidget(self.stats_label)

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

        self.apply_stats_theme()

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

    def apply_styles(self):
        theme = self.data.get("theme", "light")
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background: #111827; }
                QLabel { color: #E5E7EB; font-family: 'Segoe UI'; }
                QPushButton {
                    padding: 8px 16px; border-radius: 8px; font-weight: 600;
                    background: #4F46E5; color: white; border: none;
                }
                QPushButton:hover { background: #4338CA; }
                QListWidget { border: none; background: transparent; }
                QComboBox, QSpinBox, QLineEdit {
                    padding: 6px; border: 1px solid #374151; border-radius: 6px;
                    background: #1F2937; color: #E5E7EB;
                }
                QProgressBar {
                    border: none; border-radius: 6px; background: #1F2937;
                }
                QProgressBar::chunk { background: #818CF8; border-radius: 6px; }
                QTabWidget::pane { border: 1px solid #374151; border-radius: 12px; }
                QTabBar::tab { padding: 8px 16px; background: #1F2937; color: #E5E7EB; }
                QTabBar::tab:selected { background: #374151; }
            """)
        else:
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
        daily_types = {"Ежедневное задание", "Продвинутое ежедневное задание"}

        pinned = []
        daily_unpinned = []
        others = []

        for q in quests:
            if q.get("is_pinned", False):
                pinned.append(q)
            elif q["type"] in daily_types:
                daily_unpinned.append(q)
            else:
                others.append(q)

        pinned.sort(key=lambda x: (
            x["type"] not in daily_types,  
            x.get("completed_today", False), 
            x["title"]  
        ))

        daily_unpinned.sort(key=lambda x: x.get("completed_today", False))

        mode = self.sort_combo.currentText()
        if mode == "По названию":
            others.sort(key=lambda x: x["title"])
        elif mode == "По типу":
            type_order = {t: i for i, t in enumerate(TASK_TYPES)}
            others.sort(key=lambda x: type_order.get(x["type"], 999))
        elif mode == "По XP (↓)":
            others.sort(key=lambda x: x["xp"], reverse=True)
        elif mode == "По XP (↑)":
            others.sort(key=lambda x: x["xp"])

        return pinned + daily_unpinned + others

    def update_display(self):
        self.quest_list.clear()

        search_text = self.search_input.text().strip().lower()

        selected_category = self.category_combo.currentText()
        allowed_types = set(CATEGORY_MAP[selected_category])

        filtered_quests = []
        for q in self.data["quests"]:
            if search_text:
                if not (search_text in q["title"].lower() or search_text in q.get("desc", "").lower()):
                    continue
            if q["type"] not in allowed_types:
                continue
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
            
            due_date = q.get("due_date")
            if due_date:
                try:
                    due = date.fromisoformat(due_date)
                    today = date.today()
                    if today > due:
                        due_text = f"⚠️ Просрочено: {due_date}"
                        due_color = "#EF4444"
                    elif today == due:
                        due_text = f"🔥 Сегодня: {due_date}"
                        due_color = "#F59E0B"
                    else:
                        due_text = f"📅 До: {due_date}"
                        due_color = "#10B981"
                    due_label = QLabel(due_text)
                    due_label.setFont(QFont("Segoe UI", 9))
                    due_label.setStyleSheet(f"color: {due_color};")
                    name_layout.addWidget(due_label)
                except ValueError:
                    pass 

            exp_label = QLabel(f"{q['xp']} XP")
            exp_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            exp_label.setStyleSheet(f"color: {TYPE_COLORS[q['type']]};")

            pin_btn = QPushButton("📌" if q.get("is_pinned", False) else "📍")
            pin_btn.setFixedSize(24, 24)
            pin_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    padding: 0;
                }
                QPushButton:hover {
                    color: #F59E0B;
                }
            """)
            pin_btn.clicked.connect(lambda _, q=q: self.toggle_pin_quest(q))
            top.addWidget(pin_btn)

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

            is_daily = q["type"] in ["Ежедневное задание", "Продвинутое ежедневное задание"]
            is_completed_today = q.get("completed_today", False)

            btn_layout = QHBoxLayout()
            complete_btn = QPushButton()
            complete_btn.setFixedWidth(124)
            complete_btn.setFixedHeight(34)
            complete_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))

            if is_daily and is_completed_today:
                complete_btn.setText("✅ Выполнено")
                complete_btn.setEnabled(False)
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
        xp_needed = xp_needed_for_next_level(level)
        self.level_label.setText(f"Уровень {level} • {xp} / {xp_needed} XP")
        self.xp_bar.setRange(0, xp_needed)
        self.xp_bar.setValue(xp)

        self.update_active_stats()
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
        type_widget.setStyleSheet(self.get_card_style())
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
            top_widget.setStyleSheet(self.get_card_style())
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
        card.setStyleSheet(self.get_card_style())
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        layout.addWidget(QLabel(f"<h2 style='margin: 8px 0;'>{value}</h2>"))
        if subtitle:
            color = "#6B7280" if self.data.get("theme") == "light" else "#9CA3AF"
            layout.addWidget(QLabel(f"<span style='color:{color};'>{subtitle}</span>"))
        self.stats_layout.addWidget(card)

    def open_editor(self):
        try:
            editor = QuestEditor(self)
            if editor.exec():
                data = editor.get_data()
                if not data["title"]:
                    QMessageBox.warning(self, "Ошибка", "Укажите название.")
                    return
                self.data["quests"].append(data)
                save_data(self.data)
                self.update_display()
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось открыть редактор:\n{str(e)}")

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

        quest_id = item.data(Qt.ItemDataRole.UserRole)
        if not quest_id:
            return

        quest = None
        for q in self.data["quests"]:
            if q["id"] == quest_id:
                quest = q
                break

        if quest is None:
            return  

        menu = QMenu(self)

        edit_action = menu.addAction("✏️ Редактировать")
        delete_action = menu.addAction("🗑️ Удалить")
        archive_action = menu.addAction("📦 Архивировать")

        if quest.get("is_cumulative", False):
            menu.addSeparator()
            reset_action = menu.addAction("🔄 Сбросить прогрress")
            set_action = menu.addAction("🔢 Установить вручную")
            reset_action.triggered.connect(lambda _, q=quest: self.reset_cumulative_progress(q))
            set_action.triggered.connect(lambda _, q=quest: self.set_cumulative_progress(q))

        edit_action.triggered.connect(lambda _, q=quest: self.edit_selected_quest_by_id(q["id"]))
        delete_action.triggered.connect(lambda _, q=quest: self.delete_selected_quest_by_id(q["id"]))
        archive_action.triggered.connect(lambda _, q=quest: self.archive_selected_quest(q))

        menu.popup(self.quest_list.mapToGlobal(position))

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
                    self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest["id"]]
                    
                    completed_copy = quest.copy()
                    completed_copy["date"] = str(date.today())
                    self.data["completed_quests"].append(completed_copy)
                    
                    self.data["xp"] += quest["xp"]
                    while can_level_up(self.data["level"], self.data["xp"]):
                        self.data["level"] += 1
                    
                    save_data(self.data)
                    self.update_display()
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
            if is_daily:
                self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest["id"]]
                
                completed_copy = quest.copy()
                completed_copy["date"] = str(date.today())
                completed_copy["completed_today"] = True
                self.data["completed_quests"].append(completed_copy)
                
                self.data["xp"] += quest["xp"]
                while can_level_up(self.data["level"], self.data["xp"]):
                    self.data["level"] += 1
                
                save_data(self.data)
                self.update_display()
                QMessageBox.information(self, "✅ Успех!", f"Достижение «{quest['title']}» завершено!")
            else:
                reply = QMessageBox.question(
                    self,
                    "Подтвердите",
                    f"Завершить достижение «{quest['title']}»?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest["id"]]
                completed_quest = quest.copy()
                completed_quest["date"] = str(date.today())
                self.data["xp"] += completed_quest["xp"]
                self.data["completed_quests"].append(completed_quest)
                while can_level_up(self.data["level"], self.data["xp"]):
                    self.data["level"] += 1
                save_data(self.data)
                self.update_display()
                QMessageBox.information(self, "✅ Успех!", f"Достижение «{quest['title']}» завершено!")
    
    def open_settings(self):
        settings = SettingsDialog(
            self,
            current_theme=self.data.get("theme", "light"),
            on_theme_change=self.apply_theme,
            on_data_change=self.on_data_changed
        )
        settings.exec()

    def apply_theme(self, theme):
        self.data["theme"] = theme
        save_data(self.data)
        self.apply_styles()
        self.apply_stats_theme()
        self.update_display()

    def on_data_changed(self, new_data):
        """Обновляет данные после импорта или сброса."""
        self.data = new_data
        self.update_display()

    def get_current_theme(self):
        return self.data.get("theme", "light")
    
    def get_card_style(self):
        """Возвращает стиль карточки в зависимости от темы."""
        theme = self.data.get("theme", "light")
        if theme == "dark":
            return """
                background: #1F2937;
                border-radius: 12px;
                border: 1px solid #374151;
                padding: 16px;
            """
        else:
            return """
                background: white;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
                padding: 16px;
            """
    
    def apply_scroll_content_style(self):
        theme = self.data.get("theme", "light")
        if theme == "dark":
            self.scroll_content.setStyleSheet("""
                background-color: #111827;
                color: #E5E7EB;
            """)
        else:
            self.scroll_content.setStyleSheet("""
                background-color: #F9FAFB;
                color: #1F2937;
            """)

    def apply_stats_theme(self):
        theme = self.data.get("theme", "light")
        if theme == "dark":
            self.scroll_content.setStyleSheet("background-color: #111827;")
            self.scroll_area.setStyleSheet("background-color: #111827; border: none;")
        else:
            self.scroll_content.setStyleSheet("background-color: #F9FAFB;")
            self.scroll_area.setStyleSheet("background-color: #F9FAFB; border: none;")
    
    def update_active_stats(self):
        """Обновляет метку со статистикой активных задач и ежедневных заданий (с учётом фильтра)."""
        search_text = self.search_input.text().strip().lower()
        selected_category = self.category_combo.currentText()
        allowed_types = set(CATEGORY_MAP[selected_category])

        filtered_quests = []
        for q in self.data["quests"]:
            if search_text:
                if not (search_text in q["title"].lower() or search_text in q.get("desc", "").lower()):
                    continue
            if q["type"] not in allowed_types:
                continue
            filtered_quests.append(q)

        total_active = len(filtered_quests)

        daily_types = {"Ежедневное задание", "Продвинутое ежедневное задание"}
        daily_quests = [q for q in filtered_quests if q["type"] in daily_types]
        completed_daily = [q for q in daily_quests if q.get("completed_today", False)]
        pending_daily = len(daily_quests) - len(completed_daily)

        stats_text = f"Всего: {total_active}"
        if daily_quests:
            stats_text += f" | Ежедневных: {len(completed_daily)}/{len(daily_quests)}"

        self.stats_label.setText(stats_text)

    def reset_cumulative_progress(self, quest):
        """Сбрасывает прогресс накопительного задания до 0."""
        quest["current_value"] = 0
        save_data(self.data)
        self.update_display()
        QMessageBox.information(self, "🔄 Прогресс сброшен", f"Прогресс задания «{quest['title']}» сброшен.")

    def set_cumulative_progress(self, quest):
        """Позволяет вручную установить текущее значение прогресса."""
        dialog = QDialog(self)
        dialog.setWindowTitle("🔢 Установить прогресс")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"Цель: {quest['target_value']}"))
        layout.addWidget(QLabel(f"Текущий прогресс: {quest['current_value']}"))

        input_field = QLineEdit()
        input_field.setValidator(QIntValidator(0, quest["target_value"]))
        input_field.setText(str(quest["current_value"]))
        input_field.setPlaceholderText(f"0–{quest['target_value']}")
        layout.addWidget(input_field)

        def apply_manual_value():
            try:
                new_value = int(input_field.text())
                if 0 <= new_value <= quest["target_value"]:
                    quest["current_value"] = new_value
                    save_data(self.data)
                    self.update_display()
                    dialog.accept()

                    if new_value >= quest["target_value"]:
                        self.complete_quest(quest) 
                else:
                    QMessageBox.warning(dialog, "⚠️ Ошибка", "Значение вне допустимого диапазона.")
            except ValueError:
                QMessageBox.warning(dialog, "⚠️ Ошибка", "Введите корректное число.")

        btn = QPushButton("Применить")
        btn.clicked.connect(apply_manual_value)
        layout.addWidget(btn)

        dialog.exec()
    
    def toggle_pin_quest(self, quest):
        """Переключает статус закрепления задачи."""
        quest["is_pinned"] = not quest.get("is_pinned", False)
        save_data(self.data)
        self.update_display()

    def setup_archive_tab(self):
        layout = QVBoxLayout(self.archive_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.archive_search = QLineEdit()
        self.archive_search.setPlaceholderText("Введите название или описание...")
        self.archive_search.textChanged.connect(self.update_archive_display)
        search_layout.addWidget(self.archive_search)
        layout.addLayout(search_layout)

        self.archive_list = QListWidget()
        self.archive_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.archive_list.customContextMenuRequested.connect(self.show_archive_context_menu)
        layout.addWidget(self.archive_list)

        restore_all_btn = QPushButton("↩️ Вернуть всё в активные")
        restore_all_btn.clicked.connect(self.restore_all_archived)
        layout.addWidget(restore_all_btn)

    def update_archive_display(self):
        self.archive_list.clear()
        search_text = self.archive_search.text().strip().lower()
        archived = self.data["archived_quests"]

        for quest in archived:
            if search_text:
                if not (search_text in quest["title"].lower() or search_text in quest.get("desc", "").lower()):
                    continue

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, quest["id"])
            self.archive_list.addItem(item)

            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(12, 8, 12, 8)

            top = QHBoxLayout()
            icon_label = QLabel(quest.get("icon", "🎮"))
            icon_label.setFixedSize(32, 32)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(f"background: {TYPE_COLORS.get(quest['type'], '#4A6CF7')}; color: white; border-radius: 6px;")

            name_label = QLabel(f"<b>{quest['title']}</b>")
            name_label.setWordWrap(True)
            name_label.setMaximumWidth(300)

            xp_label = QLabel(f"{quest['xp']} XP")
            xp_label.setStyleSheet(f"color: {TYPE_COLORS.get(quest['type'], '#4A6CF7')};")

            top.addWidget(icon_label)
            top.addWidget(name_label, 1)
            top.addWidget(xp_label)
            layout.addLayout(top)

            if quest.get("desc"):
                desc_label = QLabel(quest["desc"])
                desc_label.setFont(QFont("Segoe UI", 9))
                desc_label.setStyleSheet("color: #6B7280;")
                desc_label.setWordWrap(True)
                layout.addWidget(desc_label)

            type_label = QLabel(f"<i>{quest['type']}</i>")
            type_label.setFont(QFont("Segoe UI", 8))
            type_label.setStyleSheet("color: #9CA3AF;")
            layout.addWidget(type_label)

            item.setSizeHint(QSize(0, 80))
            self.archive_list.setItemWidget(item, widget)
    
    def show_archive_context_menu(self, position):
        item = self.archive_list.itemAt(position)
        if not item:
            return

        quest_id = item.data(Qt.ItemDataRole.UserRole)
        quest = next((q for q in self.data["archived_quests"] if q["id"] == quest_id), None)
        if not quest:
            return

        menu = QMenu(self)
        restore_action = menu.addAction("↩️ Вернуть в активные")
        delete_action = menu.addAction("🗑️ Удалить навсегда")

        restore_action.triggered.connect(lambda: self.restore_archived_quest(quest))
        delete_action.triggered.connect(lambda: self.delete_archived_quest(quest, item))

        menu.popup(self.archive_list.mapToGlobal(position))

    def restore_archived_quest(self, quest):
        """Возвращает задачу из архива в активные."""
        self.data["archived_quests"] = [q for q in self.data["archived_quests"] if q["id"] != quest["id"]]
        if quest.get("is_cumulative"):
            quest["current_value"] = 0
        if quest["type"] in ["Ежедневное задание", "Продвинутое ежедневное задание"]:
            quest["completed_today"] = False
        self.data["quests"].append(quest)
        save_data(self.data)
        self.update_display()
        self.update_archive_display()
        QMessageBox.information(self, "✅ Восстановлено", f"«{quest['title']}» возвращено в активные.")

    def delete_archived_quest(self, quest, item):
        """Удаляет задачу из архива навсегда."""
        reply = QMessageBox.warning(
            self, "🗑️ Удалить навсегда?",
            f"Удалить «{quest['title']}» из архива?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data["archived_quests"] = [q for q in self.data["archived_quests"] if q["id"] != quest["id"]]
            save_data(self.data)
            self.update_archive_display()
            QMessageBox.information(self, "✅ Удалено", "Задача удалена.")

    def restore_all_archived(self):
        """Возвращает все задачи из архива в активные."""
        if not self.data["archived_quests"]:
            return
        reply = QMessageBox.question(
            self, "↩️ Вернуть всё?",
            f"Вернуть {len(self.data['archived_quests'])} задач в активные?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for quest in self.data["archived_quests"]:
                if quest.get("is_cumulative"):
                    quest["current_value"] = 0
                if quest["type"] in ["Ежедневное задание", "Продвинутое ежедневное задание"]:
                    quest["completed_today"] = False
                self.data["quests"].append(quest)
            self.data["archived_quests"] = []
            save_data(self.data)
            self.update_display()
            self.update_archive_display()
            QMessageBox.information(self, "✅ Готово", "Все задачи возвращены в активные.")
    
    def archive_selected_quest(self, quest):
        """Перемещает задачу из активных в архив."""
        self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest["id"]]
        archived_copy = quest.copy()
        self.data["archived_quests"].append(archived_copy)
        save_data(self.data)
        self.update_display()
        self.update_archive_display()
        QMessageBox.information(self, "📦 В архиве", f"«{quest['title']}» перемещено в архив.")
    
    def edit_selected_quest_by_id(self, quest_id):
        """Редактирует задачу по ID."""
        for q in self.data["quests"]:
            if q["id"] == quest_id:
                self.edit_selected_quest_by_ref(q)
                return

    def edit_selected_quest_by_ref(self, quest):
        """Редактирует задачу по ссылке."""
        editor = QuestEditor(self, quest_data=quest)
        if editor.exec():
            updated = editor.get_data()
            for i, q in enumerate(self.data["quests"]):
                if q["id"] == quest["id"]:
                    self.data["quests"][i] = updated
                    break
            save_data(self.data)
            self.update_display()

    def delete_selected_quest_by_id(self, quest_id):
        """Удаляет задачу по ID."""
        for q in self.data["quests"]:
            if q["id"] == quest_id:
                self.confirm_delete_quest(q)
                return

    def confirm_delete_quest(self, quest):
        """Подтверждает удаление задачи."""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить задание «{quest['title']}»?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data["quests"] = [q for q in self.data["quests"] if q["id"] != quest["id"]]
            save_data(self.data)
            self.update_display()
    
    def check_daily_archive(self):
        from quest_data import archive_expired_quests, restore_daily_quests, save_data
        old_data = self.data.copy()  
        self.data = archive_expired_quests(self.data)
        self.data = restore_daily_quests(self.data)  
        if self.data != old_data:  
            save_data(self.data)
            self.update_display()
            self.update_archive_display()

    def closeEvent(self, event):
        save_data(self.data)
        event.accept()