import sys

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QTextEdit)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtCore import pyqtSignal

class myTextEdit(QTextEdit):
    double_click = pyqtSignal()
    def mouseDoubleClickEvent(self, event):
        self.double_click.emit()

class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
       #self.p_txt = QPlainTextEdit(self)
       self.txt = myTextEdit(self)
       self.installEventFilter(self)
       vbox = QVBoxLayout()
       vbox.addWidget(self.txt)
       #vbox.addWidget(self.p_txt)
       self.setLayout(vbox)
       self.txt.double_click.connect(self.print_txt)
       self.setGeometry(250, 250, 250, 150)
       self.setWindowTitle('Events demo') 
       self.show()
    
    def eventFilter(self, source, event):
        print(event.type())
        if event.type() == QEvent.Close:
            print('closing...')
        return False
    
    # def closeEvent(self, event):
    #     print('zamykam')
    #     print(event.type())
    #     return False
    
    def print_txt(self):
        print('cos')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())