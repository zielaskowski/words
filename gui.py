from words.qt_gui.main_window import QtCore, QtGui, QtWidgets, Ui_MainWindow
from words.qt_gui.import_window import Ui_ImportWindow
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtMultimedia
from gtts import gTTS
from words.modules import FileSystem, Dictionary, Wiki
import json
import pandas as pd



class GUIWords(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class myQTextEdit(QtWidgets.QTextEdit):
    '''need to subclass QTextEdit to add double click handler
    '''
    double_click = QtCore.pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.double_click.emit()


class GUIImport(QtWidgets.QDialog, Ui_ImportWindow, myQTextEdit):
    def __init__(self, err='', imp=''):
        self.data = imp
        super().__init__()
        self.setupUi(self)
        # need to manually add my QTextEdit with implemented double click
        self.import_error_list = myQTextEdit(self.errorTab)
        self.import_error_list.setObjectName("import_error_list")
        self.verticalLayout_2.addWidget(self.import_error_list)
        self.label_2 = QtWidgets.QLabel(self.errorTab)
        self.label_2.setObjectName("label_2")
        self.label_2.setText('Double click a word to see in context')
        self.verticalLayout_2.addWidget(self.label_2)
        # now we can connect to double click in TextEdit
        self.import_error_list.double_click.connect(self.err_in_cont)
        self._errors(err)
        self._status()
        # the import can be modified so need to return on ACCEPT
        self.import_status_btn.accepted.connect(self.accepted)
        # catch cell modification
        self.import_status_table.cellChanged.connect(self.changed)
    
    def err_in_cont(self):
        '''When word double clicked in error tab
        switch to status pane and highlight the row with the word
        We ovverride the mouseDoubleClicked, so also default behaviour of selecting double clicked word
        need to restore default behaviour
        '''
        txt = self.import_error_list.textCursor()
        # find begining of word
        txt.movePosition(txt.WordLeft, txt.MoveAnchor, 1)
        # select the word
        txt.movePosition(txt.WordRight,txt.KeepAnchor, 1)
        # makes selection visible
        self.import_error_list.setTextCursor(txt)
        # look up the word selected
        what = txt.selectedText().strip()
        found = self.import_status_table.findItems(what, QtCore.Qt.MatchContains)
        if found:
            self.label_2.setText('Double click a word to see in context.')
            self.importedTab.setCurrentIndex(0)
            row_i = self.import_status_table.row(found[0])
            sel_mod = QtCore.QItemSelectionModel.ClearAndSelect
            self.import_status_table.setCurrentCell(row_i, 0, sel_mod)
            sel_mod = QtCore.QItemSelectionModel.Select
            self.import_status_table.setCurrentCell(row_i,1, sel_mod)
        else:
            self.label_2.setText('Double click a word to see in context. Word not found.')

    def _errors(self, txt:pd):
        self.import_error_list.setText(txt)
        self.import_error_list.setReadOnly
    
    def _status(self):
        # set table size
        rows = self.data.shape[0]
        if not rows: #  nothing to import
            self.import_status_table.setColumnCount(1)
            self.import_status_table.setRowCount(1)
            self.import_status_table.setHorizontalHeaderLabels('info')
            col = self.import_status_table.horizontalHeader()
            col.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            cell = QtWidgets.QTableWidgetItem('Nothing to import. See "error" tab')
            self.import_status_table.setItem(0,0,cell)
            return
        cols = self.data.shape[1]
        self.import_status_table.setColumnCount(cols)
        self.import_status_table.setRowCount(rows)
        # set column labels
        self.import_status_table.setHorizontalHeaderLabels(['ru','pl'])
        col = self.import_status_table.horizontalHeader()
        col.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        # populate table
        for x in range(cols):
            for y in range(rows):
                cell = QtWidgets.QTableWidgetItem(str(self.data.iloc[y, x]))
                self.import_status_table.setItem(y, x, cell)

    def accepted(self):
        return self.data

    def changed(self, row, col):
        self.data.iloc[row,col] = self.import_status_table.item(row,col).text()


class GUIWordsCtr(QtCore.QObject):
    def __init__(self, view):
        super().__init__(view)
        self._view = view
        self._fs = FileSystem()
        self._logic = Dictionary(self._fs.getTags(), self._fs.getTagsTrans())
        self._connectSignals()
        # add normal text to statusbar
        self.statusbarMsg = QtWidgets.QLabel()
        self._view.statusbar.addWidget(self.statusbarMsg)
        self.disp_statusbar('init')
        # read configuration
        self._readLastDB()
        # catch exit signal
        self._view.installEventFilter(self)
        
    def disp_statusbar(self, event=''):
        """Display text in status bar. Possible events:\n
        - init: "Open DB or import from TXT"
        - saved
        - openDB
        - saved_as
        - import
        - newDB
        - modDB
        - addROW
        - delROW
        """

        # status bar is showing tooltip when hoover the menu
        # restore statusbar when empty
        if event == 'init':
            self.statusbarMsg.setText('Open DB or import from TXT')
        elif event == 'saved':
            self.statusbarMsg.setText(f'Saved DB: <i>{self._fs.getDB(file=True)}</i>')
        elif event == 'openDB':
            self.statusbarMsg.setText(f'Opened DB: <i>{self._fs.getDB(file=True)}</i>')
        elif event == 'modDB':
            self.statusbarMsg.setText(f'Modified DB: <i>{self._fs.getDB(file=True)}</i>. {self._logic.err}')
        elif event == 'saved_as':
            self.statusbarMsg.setText(f'Opened DB: <i>{self._fs.getDB(file=True)}</i>')
        elif event == 'imported':
            if self._fs.getDB():
                self.statusbarMsg.setText(f'Imported <i>{self._fs.getIMP(file=True)}</i>. Added to DB <i>{self._fs.getDB(file=True)}</i>.')
            else:
                self.statusbarMsg.setText(f'Imported <i>{self._fs.getIMP(file=True)}</i>.')
        elif event == 'newDB':
            self.statusbarMsg.setText(f'Created new empty DB: {self._fs.getDB(file=True)}')
        elif event == 'addROW':
            self.statusbarMsg.setText('added empty row to DB')
        elif event == 'delROW':
            self.statusbarMsg.setText('deleted row from DB')

    def _connectSignals(self):
        # buttons
        self._view.btn_rand.clicked.connect(self._print)
        self._view.btn_next.clicked.connect(self._next)
        self._view.btn_previous.clicked.connect(self._prev)
        self._view.btn_sound.clicked.connect(lambda: self._play(repeat=True))
        self._view.btn_add.clicked.connect(self._add)
        self._view.btn_del.clicked.connect(self._del)
        # menu entries
        self._view.new_DB.triggered.connect(self._new_DB)
        self._view.open_DB.triggered.connect(self._open_DB)
        # self._view.save_DB.triggered.connect(self._saveDB)
        self._view.save_as_DB.triggered.connect(self._save_as_DB)
        self._view.import_TXT.triggered.connect(self._import_TXT)
        self._view.exit.triggered.connect(self._exit)
        # text mods
        self._view.txt_pl.returnPressed.connect(self._edit_txt)
        self._view.txt_ru.returnPressed.connect(self._edit_txt)
        
    def _edit_txt(self):
        row = self._logic.print(self._logic.history[self._logic.history_index])
        self._logic.drop(row.name)
        self._logic.importTXT(self._view.txt_ru.text() + '   ' + self._view.txt_pl.text())
        self._logic.commit()
        self._logic.write_sql_db(self._fs.getDB())
        self.disp_statusbar('modDB')
        self.setDisplayText(self._logic.print(self._logic.history[self._logic.history_index]))

    def _print(self):
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.setDisplayText(self._logic.print())
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def _next(self):
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.setDisplayText(self._logic.next())
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def _prev(self):
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.setDisplayText(self._logic.previous())
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    
    def _add(self, event, wrd_ru='_', wrd_pl='_'):
        self._logic.importTXT(wrd_ru + '    ' + wrd_pl)
        self._logic.commit()
        self._logic.write_sql_db(self._fs.getDB())
        self.disp_statusbar('addROW')
        self.setDisplayText(self._logic.print(self._logic.history[self._logic.history_index]))

    def _del(self):
        row = self._logic.print(self._logic.history[self._logic.history_index])
        self._logic.drop(row.name)
        self._logic.write_sql_db(self._fs.getDB())
        self.disp_statusbar('delROW')
        self.setDisplayText(self._logic.print(self._logic.history[self._logic.history_index]))

    def _play(self, repeat=False):
        row = self._logic.print(self._logic.history[self._logic.history_index])
        if row.ru:
            if not repeat:
                word_sound = gTTS(text=row.ru, lang='ru')
                word_sound.save(self._fs.getMP3())
            file = QtCore.QUrl.fromLocalFile(self._fs.getMP3())
            player = QtMultimedia.QMediaPlayer(self)
            player.setMedia(QtMultimedia.QMediaContent(file))
            player.setVolume(50)
            player.play()

    
        pass

    # menu function
    def _new_DB(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Save As SQlite3 file',
                                                                directory='',
                                                                filter=self._fs.getDB(ext=True))        
        if file[0]:
            self._logic.write_sql_db(self._fs.getDB())
            self._fs.setDB(file[0])
        else:  # operation canceled
            return
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self._logic = Dictionary(self._fs.getTags(), self._fs.getTagsTrans())  # drops DB, create new instance
        self._logic.write_sql_db(self._fs.getDB())
        #self._logic.open_sql_db(self._fs.getDB())
        self.setDisplayText(self._logic.print())
        self.disp_statusbar('newDB')
        self._fs.writeOpt("LastDB",self._fs.getDB())
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def _open_DB(self):
        file = QFileDialog.getOpenFileName(self._view, caption='Choose SQlite3 file',
                                                                directory='',
                                                                filter=self._fs.getDB(ext=True))
        if file[0]:
            self._fs.setDB(file[0])
        else:  # operation canceled
            return
        if self._logic.open_sql_db(self._fs.getDB()) != None: # return None if fail
            self.setDisplayText(self._logic.print())
            self.disp_statusbar('openDB')
            self._fs.writeOpt("LastDB",self._fs.getDB())

    def _saveDB(self):
        if self._fs.getDB():
            self._logic.write_sql_db(self._fs.getDB())
            self.disp_statusbar('saved')
        else:
            self._save_as_DB()

    def _save_as_DB(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Save As SQlite3 file',
                                                                directory='',
                                                                filter=self._fs.getDB(ext=True))        
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
                                                                filter=self._fs.getIMP(ext=True))
        if file[0]:
            self._fs.setIMP(file)
        else:
            return  # operation canceled
        with open(self._fs.getIMP(), 'r') as f:
            file = f.readlines()
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        imp = self._logic.importTXT(file)
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        importView = GUIImport(self._logic.err, imp)
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        if importView.exec_():  # if ACCEPTED
            self._logic.db_temp = importView.data
            self._logic.commit()
            self._logic.write_sql_db(self._fs.getDB())
            self.setDisplayText(self._logic.print())
            self.disp_statusbar('imported')
        else:
            # import is using Wiki.checkWiki() and TTager.tag(), so
            # - wrd in Wiki class are now random
            # - TTager._lemma() is random
            # need to re-run wiki and tagger check and set wrds accordingly to what displayed
            self._logic.tager.tag(self._view.txt_ru.text())
            self._logic.wiki.checkWiki(self._logic.tager._lemma)
            print()
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    # other helpers

    def _readLastDB(self):
        self._fs.setDB(self._fs.getOpt('LastDB'))
        if self._logic.open_sql_db(self._fs.getDB()) != None: # return None if fail
            self.setDisplayText(self._logic.print())
            self.disp_statusbar('openDB')
        else:
            self.setDescText()
            self._view.tabWidget_tager.setTabVisible(0, True)
            self._view.tabWidget_tager.setTabText(0, 'welcome')
            wel_txt = self._fs.getOpt('welcome')
            self._view.txt_desc_tager_1.setText(wel_txt)
            self._view.tabWidget_desc.setCurrentIndex(0)

    def _exit(self):
        #TODO question if save?
        if self._fs.getDB():
            self._saveDB()
            self._fs.writeOpt("LastDB",self._fs.getDB())
        self._view.close()

    def eventFilter(self,source, event):
        '''Catch signal:
        
        if user closed the window

        If user resize the window
        '''
        if event.type() == QtCore.QEvent.Close:
            self._exit()
        elif event.type() == QtCore.QEvent.Resize:
            self.adjDisplaySize()
        return False

    def setDisplayText(self, row):
        self._view.txt_ru.setText(row.ru)
        self._view.txt_pl.setText(row.pl)
        self.adjDisplaySize()
        self.setDescText()

        self._logic.score()
        self._play()

    def adjDisplaySize(self):
        # resize text to fit in window
        # text drives the QtextLabel size, so we have two possibilities:
        # 1.restore widget size after setting the font size
        # 2.set text size the same in both widgets - THIS WILL TAKE
        # 3....find option to break dependency between text size and box size....
        widget = [self._view.txt_pl, self._view.txt_ru]
        # set back the font size to std for both widget
        font_size = 18
        font = widget[0].font()
        font.setPointSize(font_size)
        [widget[i].setFont(font) for i in (0, 1)]
        for i in (0, 1):            
            while True:
                txt_width = widget[i].fontMetrics().width(widget[i].text())
                widget_width = widget[i].width()
                if  widget_width < txt_width + 5:
                    font_size -= 1
                    font.setPointSize(font_size)
                    widget[i].setFont(font)
                    widget[(i + 1) % 2].setFont(font) # other than i widget
                    if font_size < 4: break
                else:
                    break

    def setDescText(self):
        tab_source = ['tager', 'wiki', 'goog']
        # check how many words, unhide only tabs needed,
        # change name of tabs
        # we have only five tabs, should be enough, but if not, drops other words
        tabs_no = self._view.tabWidget_tager.count()
        wrds_no = len(self._logic.tager.wrd)
        if wrds_no > tabs_no:
            wrds_no = tabs_no
        for tab_s in tab_source:
            for tab_i in range(tabs_no): 
                if tab_i > wrds_no - 1: #hide tabs if more than wrds
                    exec(f'self._view.tabWidget_{tab_s}.setTabVisible({tab_i}, False)')
                else:
                    exec(f'self._view.tabWidget_{tab_s}.setTabVisible({tab_i}, True)')
                    exec(f'self._view.tabWidget_{tab_s}.setTabText({tab_i}, self._logic.tager.wrd[{tab_i}])')
        # set description
        for wrd_i in range(wrds_no):
            exec(f'self._view.txt_desc_tager_{wrd_i + 1}.setText(self._logic.tager.formatAll({wrd_i}))')
            exec(f'self._view.txt_desc_wiki_{wrd_i + 1}.setText(self._logic.wiki.readData({wrd_i}))')
            #exec(f'self._view.txt_desc_goog_{wrd_i + 1}.setText(self._logic.tager.formatAll(wrd_i))')

