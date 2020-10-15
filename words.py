from gui import GUIWords, GUIWordsCtr
from PyQt5.QtWidgets import QApplication
import sys



app = QApplication([])
view = GUIWords()
view.show()
GUIWordsCtr(view)
sys.exit(app.exec())



