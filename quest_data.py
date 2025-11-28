import json
import os
import uuid
from datetime import date

DATA_FILE = "quests.json"

TASK_TYPES = [
    "Обычное достижение",
    "Испытание",
    "Мастерство",
    "Ежедневное задание",
    "Продвинутое ежедневное задание"
]

TYPE_COLORS = {
    "Обычное достижение": "#4A6CF7",
    "Испытание": "#F59E0B",
    "Мастерство": "#6D28D9",
    "Ежедневное задание": "#10B981",
    "Продвинутое ежедневное задание": "#EF4444"
}

ICONS = [
    "🎮", "🏆", "🔥", "🚀", "🎯", "💡", "⚡", "✨", "🛡️", "📚",
    "🛠️", "💎", "🏅", "🌟", "💼", "🌱", "🧭", "🧠", "💪", "📊"
]

DEFAULT_DATA = {
    "level": 1,
    "xp": 0,
    "quests": [],
    "completed_quests": [],
    "daily_reset": str(date.today())
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

def level_up_required(level, xp):
    return xp >= level * 100