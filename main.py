import sys
from words.gui import GUIWords, GUIWordsCtr
from PyQt5.QtWidgets import QApplication



app = QApplication([])
view = GUIWords()
view.show()
GUIWordsCtr(view)
sys.exit(app.exec())


