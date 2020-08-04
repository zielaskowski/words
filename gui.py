from main_window import QtCore, QtGui, QtWidgets, Ui_MainWindow
from import_window import Ui_ImportWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtMultimedia
from gtts import gTTS
from modules import FileSystem, Dictionary


class GUIWords(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
    

class GUIImport(QtWidgets.QDialog, Ui_ImportWindow):
    def __init__(self, err='', imp=''):
        super().__init__()
        self.setupUi(self)
        self._errors(err)
        self._status(imp)
    
    def _errors(self, txt):
        self.import_error_list.setPlainText(txt)
        self.import_error_list.setReadOnly
    
    def _status(self, txt):
        self.import_status_list.setPlainText(txt)
        self.import_status_list.setReadOnly


class GUIWordsCtr(QtCore.QObject):
    def __init__(self, view):
        super().__init__(view)
        self._view = view
        self._logic = Dictionary()
        self._fs = FileSystem()
        self._connectSignals()
        # add normal text to statusbar
        self.statusbarMsg = QtWidgets.QLabel()
        self._view.statusbar.addWidget(self.statusbarMsg)
        self.disp_statusbar('init')
        
    def disp_statusbar(self, event=''):
        """Display text in status bar. Possible events:\n
        - init: "Open DB or import from TXT"
        - saved
        - openDB
        - saved_as
        - import
        - newDB
        - modDB
        """

        # status bar is showing tooltip when hoover the menu
        # restore statusbar when empty
        if event == 'init':
            self.statusbarMsg.setText('Open DB or import from TXT')
        elif event == 'saved':
            self.statusbarMsg.setText(f'Saved DB: {self._fs.getDB(file_only=True)}')
        elif event == 'openDB':
            self.statusbarMsg.setText(f'Opened DB: {self._fs.getDB(file_only=True)}')
        elif event == 'modDB':
            self.statusbarMsg.setText(f'Modified DB: {self._fs.getDB(file_only=True)}. {self._logic.err}')
        elif event == 'saved_as':
            self.statusbarMsg.setText(f'Opened DB: {self._fs.getDB(file_only=True)}')
        elif event == 'imported':
            if self._fs.getDB():
                self.statusbarMsg.setText(f'Imported {self._fs.getIMP(file_only=True)}. Added to DB {self._fs.getDB(file_only=True)}. Not saved DB!')
            else:
                self.statusbarMsg.setText(f'Imported {self._fs.getIMP(file_only=True)}. Not saved DB!')
        elif event == 'newDB':
            self.statusbarMsg.setText(f'Created new empty DB: {self._fs.getDB(file_only=True)}')

    def _connectSignals(self):
        # buttons
        self._view.btn_rand.clicked.connect(self._print)
        self._view.btn_next.clicked.connect(self._next)
        self._view.btn_previous.clicked.connect(self._prev)
        self._view.btn_sound.clicked.connect(self._play)
        # menu entries
        self._view.new_DB.triggered.connect(self._new_DB)
        self._view.open_DB.triggered.connect(self._open_DB)
        self._view.save_DB.triggered.connect(self._saveDB)
        self._view.save_as_DB.triggered.connect(self._save_as_DB)
        self._view.import_TXT.triggered.connect(self._import_TXT)
        self._view.exit.triggered.connect(self._exit)
        # text mods
        self._view.txt_pl.returnPressed.connect(self._edit_txt)
        self._view.txt_ru.returnPressed.connect(self._edit_txt)
        

    def _edit_txt(self):
        row = self._logic.print()
        self._logic.drop(row.name)
        self._logic.importTXT(self._view.txt_ru.text() + '   ' + self._view.txt_pl.text())
        self.disp_statusbar('modDB')

    def _print(self):
        self.setDisplayText(self._logic.print())
        self.disp_statusbar('openDB')

    def _next(self):
        self.setDisplayText(self._logic.next())
        self.disp_statusbar('openDB')

    def _prev(self):
        self.setDisplayText(self._logic.previous())
        self.disp_statusbar('openDB')
    
    def _play(self):
        row = self._logic.print(self._logic.history[self._logic.history_index])
        if not row.empty:
            word_sound = gTTS(text=row.ru, lang='ru')
            word_sound.save(self._fs.getMP3())
            file = QtCore.QUrl.fromLocalFile(self._fs.getMP3())
            player = QtMultimedia.QMediaPlayer(self)
            player.setMedia(QtMultimedia.QMediaContent(file))
            player.setVolume(50)
            player.play()

    # menu function
    def _new_DB(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Save As SQlite3 file',
                                                                directory='',
                                                                filter=self._fs.getDB(ext_type=True))        
        if file[0]:
            self._fs.setDB(file)
        else:  # operation canceled
            return
        self._logic = Dictionary()  # drops DB, create new instance
        self._logic.write_sql_db(self._fs.getDB())
        self._logic.open_sql_db(self._fs.getDB())
        self.setDisplayText(self._logic.print())
        self.disp_statusbar('new_DB')

    
    def _open_DB(self):
        file = QFileDialog.getOpenFileName(self._view, caption='Choose SQlite3 file',
                                                                directory='',
                                                                filter=self._fs.getDB(ext_type=True))
        if file[0]:
            self._fs.setDB(file)
        else:  # operation canceled
            return
        self._logic.open_sql_db(self._fs.getDB())
        self.setDisplayText(self._logic.print())
        self.disp_statusbar('openDB')

    def _saveDB(self):
        if self._fs.getDB():
            self._logic.write_sql_db(self._fs.getDB())
            self.disp_statusbar('saved')
        else:
            self._save_as_DB()

    def _save_as_DB(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Save As SQlite3 file',
                                                                directory='',
                                                                filter=self._fs.getDB(ext_type=True))        
        if file[0]:
            self._fs.setDB(file)
        else:  # operation canceled
            return
        self._logic.write_sql_db(self._fs.getDB())
        self._logic.open_sql_db(self._fs.getDB())
        self.disp_statusbar('saved_as')

    def _import_TXT(self):
        file = QFileDialog.getOpenFileName(self._view, caption='Choose TXT file',
                                                                directory='',
                                                                filter=self._fs.getIMP(ext_type=True))
        if file[0]:
            self._fs.setIMP(file)
        else:
            return  # operation canceled
        with open(self._fs.getIMP(), 'r') as f:
            file = f.readlines()
        imp = self._logic.importTXT(file)
        importView = GUIImport(self._logic.err, imp)
        if importView.exec_():  # if ACCEPTED
            self._logic.commit()
            self.setDisplayText(self._logic.print())
            self.disp_statusbar('imported')
        

    def _exit(self):
        #TODO question if save?
        self._view.close()

    def setDisplayText(self, row):
        self._view.txt_ru.setText(row.ru)
        self._view.txt_pl.setText(row.pl)

        self._logic.score()
        self._play()
        # resize text to fit in window
        # text drives the QtextLabel size, so we have two possibilities:
        # 1.restore widget size after setting the font size
        # 2.set text size the same in both widgets - THIS WILL TAKE
        # 3....find option to break dependency between text size and box size....
        font_size = 18
        for widget in [self._view.txt_pl, self._view.txt_ru]:
            # set back the font size to std for first widget
            # second widget will start with font already scaled down
            font = widget.font()
            font.setPointSize(font_size)
            widget.setFont(font)
            while True:
                txt_width = widget.fontMetrics().width(widget.text())
                widget_width = widget.width()
                if  widget_width < txt_width:
                    font_size -= 1
                    font.setPointSize(font_size)
                    widget.setFont(font)
                else:
                    break
