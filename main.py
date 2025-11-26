import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from quest_ui import QuestLogUI

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = QuestLogUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()