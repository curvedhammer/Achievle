import json
import os
import uuid
import shutil
from datetime import date, datetime


DATA_FILE = "quests.json"

TASK_TYPES = [
    "Ежедневное задание",
    "Продвинутое ежедневное задание",
    
    "Обычное задание",
    "Умеренное задание",
    "Задание повышенной сложности",

    "Обычное достижение",
    "Умеренное достижение",
    "Продвинутое достижение",
    
    "Испытание",
    "Продвинутое испытание",
    
    "Мастерство"
]

TYPE_COLORS = {
    "Обычное достижение": "#4A6CF7",
    "Умеренное достижение": "#60A5FA",
    "Продвинутое достижение": "#3B82F6",
    
    "Испытание": "#F59E0B",
    "Продвинутое испытание": "#F97316",
    
    "Мастерство": "#6D28D9",
    
    "Ежедневное задание": "#10B981",
    "Продвинутое ежедневное задание": "#059669",
    
    "Обычное задание": "#3B82F6",
    "Умеренное задание": "#8B5CF6",
    "Задание повышенной сложности": "#EC4899"
}

ICONS = [
    "🎮", "🏆", "🔥", "🚀", "🎯", "💡", "⚡", "✨", "🛡️", "📚",
    "🛠️", "💎", "🏅", "🌟", "💼", "🌱", "🧭", "🧠", "💪", "📊"
    "📝", "📌", "❗"
]

DEFAULT_DATA = {
    "level": 1,
    "xp": 0,
    "quests": [],
    "completed_quests": [],
    "daily_reset": str(date.today()),
    "theme": "light"
}

def _migrate_quest(quest):
    """Добавляет недостающие поля в старую задачу."""
    quest.setdefault("id", str(uuid.uuid4()))
    quest.setdefault("icon", "🎮")
    quest.setdefault("type", "Обычное достижение")
    quest.setdefault("xp", 10)
    quest.setdefault("is_cumulative", False)
    quest.setdefault("target_value", 100 if quest["is_cumulative"] else 0)
    quest.setdefault("current_value", 0)
    quest.setdefault("completed_today", False)
    return quest

def restore_daily_quests(data):
    """Восстанавливает ежедневные задания, если наступил новый день."""
    today = str(date.today())
    if data["daily_reset"] != today:
        daily_types = ["Ежедневное задание", "Продвинутое ежедневное задание"]
        restored = []
        remaining_completed = []

        for q in data["completed_quests"]:
            if q["type"] in daily_types:
                q = _migrate_quest(q)
                q["current_value"] = 0
                q.pop("date", None)
                restored.append(q)
            else:
                remaining_completed.append(q)
        
        for q in data["quests"]:
            if q["type"] in daily_types:
                q["completed_today"] = False
                q["current_value"] = 0

        data["quests"].extend(restored)
        data["completed_quests"] = remaining_completed
        data["daily_reset"] = today
        save_data(data)
    return data

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = DEFAULT_DATA.copy()

    data.setdefault("level", 1)
    data.setdefault("xp", 0)
    data.setdefault("quests", [])
    data.setdefault("completed_quests", [])
    data.setdefault("daily_reset", str(date.today()))

    data["quests"] = [_migrate_quest(q) for q in data.get("quests", [])]
    data["completed_quests"] = [_migrate_quest(q) for q in data.get("completed_quests", [])]

    data = restore_daily_quests(data)
    return data

def save_data(data):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE + ".bak", "w", encoding="utf-8") as bak:
            with open(DATA_FILE, "r", encoding="utf-8") as orig:
                bak.write(orig.read())
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def xp_needed_for_next_level(current_level):
    """
    Возвращает, сколько XP нужно для перехода с current_level на current_level + 1.
    Уровень 1 → 2: 100 XP
    Уровень 2 → 3: 150 XP
    Уровень 3 → 4: 300 XP
    Уровень n → n+1: total_xp(n) + 50
    """
    if current_level < 1:
        current_level = 1

    # Начинаем с уровня 1
    total_xp = 0
    # Вычисляем total_xp для текущего уровня
    for lvl in range(1, current_level):
        delta = total_xp + 50 if lvl > 1 else 100
        total_xp += delta

    # Теперь вычисляем delta для перехода на следующий уровень
    if current_level == 1:
        return 100
    else:
        return total_xp + 50


def can_level_up(current_level, current_xp):
    """Проверяет, можно ли повысить уровень."""
    needed = xp_needed_for_next_level(current_level)
    return current_xp >= needed


def total_xp_for_level(target_level):
    """Возвращает общий XP, необходимый для достижения target_level."""
    if target_level <= 1:
        return 0
    total = 0
    for lvl in range(1, target_level):
        if lvl == 1:
            delta = 100
        else:
            delta = total + 50
        total += delta
    return total

def export_data(filepath):
    """Копирует quests.json в указанный файл."""
    shutil.copy2(DATA_FILE, filepath)

def import_data(filepath):
    """Загружает данные из указанного файла."""
    shutil.copy2(filepath, DATA_FILE)
    return load_data()

def reset_data():
    """Сбрасывает все данные к начальному состоянию."""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    return load_data()