import os

import pandas as pd
import playsound
from gtts import gTTS
from PyQt5.QtWidgets import QFileDialog

from modules import Dictionary, FileSystem
from qt_gui.import_window import Ui_ImportWindow
from qt_gui.main_window import QtCore, QtGui, QtWidgets, Ui_MainWindow
from testing.debug import debug


class validSearchClass(QtGui.QValidator):
    def __init__(self, wrds, parent):
        super().__init__(parent)
        self.validWords = wrds

    def validate(self, wrd, index):
        if wrd in self.validWords:
            state = QtGui.QValidator.Acceptable
        elif any([i.startswith(wrd) for i in self.validWords]):
            state = QtGui.QValidator.Intermediate
        else:
            state = QtGui.QValidator.Invalid
        return state, wrd, index

    def fixup(self, wrd):
        pass


class GUIWords(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class myQTextEdit(QtWidgets.QTextEdit):
    """need to subclass QTextEdit to add double click handler
    """
    double_click = QtCore.pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.double_click.emit()


class GUIImport(QtWidgets.QDialog, Ui_ImportWindow, myQTextEdit):
    def __init__(self, err='', imp=''):
        self.data = imp
        super().__init__()
        self.setupUi(self)
        # need to manually add myQTextEdit with implemented double click
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
        """When word double clicked in error tab
        switch to status pane and highlight the row with the word
        We override the mouseDoubleClicked, so also default behaviour of selecting double clicked word
        need to restore default behaviour
        """
        txt = self.import_error_list.textCursor()
        # find beginning of word
        txt.movePosition(txt.WordLeft, txt.MoveAnchor, 1)
        # select the word
        txt.movePosition(txt.WordRight, txt.KeepAnchor, 1)
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
            self.import_status_table.setCurrentCell(row_i, 1, sel_mod)
        else:
            self.label_2.setText('Double click a word to see in context. Word not found.')

    def _errors(self, txt: pd):
        self.import_error_list.setText(txt)
        self.import_error_list.setReadOnly

    def _status(self):
        # set table size
        rows = self.data.shape[0]
        if not rows:  # nothing to import
            self.import_status_table.setColumnCount(1)
            self.import_status_table.setRowCount(1)
            self.import_status_table.setHorizontalHeaderLabels(['info'])
            col = self.import_status_table.horizontalHeader()
            col.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            cell = QtWidgets.QTableWidgetItem('Nothing to import. See "error" tab')
            self.import_status_table.setItem(0, 0, cell)
            return
        cols = self.data.shape[1]
        self.import_status_table.setColumnCount(cols)
        self.import_status_table.setRowCount(rows)
        # set column labels
        self.import_status_table.setHorizontalHeaderLabels(['ru', 'pl'])
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
        self.data.iloc[row, col] = self.import_status_table.item(row, col).text()


class GUIWordsCtr(QtCore.QObject):
    def __init__(self, view):
        super().__init__(view)
        self._view = view
        self._fs = FileSystem()
        self._logic = Dictionary(self._fs.getTags(), self._fs.getTrans())
        # description tab names
        self.tab_desc = ['tager', 'wiki']
        self.contextMenu()
        self._connectSignals()
        # add normal text and progress bar to statusbar
        self.statusbarMsg = QtWidgets.QLabel()
        self.statusbarProgress = QtWidgets.QProgressBar()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.statusbarProgress.setSizePolicy(sizePolicy)
        self.statusbarProgress.setMinimumSize(QtCore.QSize(20, 10))
        self.statusbarProgress.setRange(0, 100)
        self._view.statusbar.addWidget(self.statusbarMsg)
        self._view.statusbar.addPermanentWidget(self.statusbarProgress)

        self.disp_statusbar('init')

        # store selected txt from txt desc boxes
        self.selTxt = ''
        # read toolTips text
        file = self._fs.getGrammaExp()
        if file:
            self.toolTipTxt = pd.read_csv(file, sep='\t+', names=["abr", "exp", "del"],
                                          comment='#', engine='python', encoding='utf-8')
            self.toolTipTxt = self.toolTipTxt.iloc[:, 0:2]  # in case some tabs on end of the line

        # read configuration
        self._readLastDB()

        # available words for completer on search field
        self.fillCompleter()

    def contextMenu(self):
        # define menu
        self.newRU = QtWidgets.QAction("new Ru word", self)
        self.newPL = QtWidgets.QAction("new Pl word", self)
        self.addRU = QtWidgets.QAction("add Ru word", self)
        self.addPL = QtWidgets.QAction("add PL word", self)
        self.replRU = QtWidgets.QAction("replace Ru word", self)
        self.replPL = QtWidgets.QAction("replace Pl word", self)

        # install menu
        tabs_no = self._view.tabWidget_tager.count()
        for tab_s in self.tab_desc:
            for tab_i in range(tabs_no):
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)')
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.addAction(self.newRU)')
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.addAction(self.newPL)')
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.addAction(self.addRU)')
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.addAction(self.addPL)')
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.addAction(self.replRU)')
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.addAction(self.replPL)')
        self._view.txt_desc_goog.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self._view.txt_desc_goog.addAction(self.newRU)
        self._view.txt_desc_goog.addAction(self.newPL)
        self._view.txt_desc_goog.addAction(self.addRU)
        self._view.txt_desc_goog.addAction(self.addPL)
        self._view.txt_desc_goog.addAction(self.replRU)
        self._view.txt_desc_goog.addAction(self.replPL)

    def _installDblClick(self):
        """Install event handler on all txt desc boxes\n
        This will allow to catch dblClicks and write selected txt to self.selTxt
        """
        tabs_no = self._view.tabWidget_tager.count()
        for tab_s in self.tab_desc:
            for tab_i in range(tabs_no):
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.installEventFilter(self)')
        self._view.txt_desc_goog.installEventFilter(self)

    def disp_statusbar(self, event=''):
        """Display text in status bar. Possible events:\n
        - init: "Open DB or import from TXT"
        - saved
        - openDB
        - saved_as
        - imported
        - exported
        - newDB
        - modDB
        - addROW
        - delROW
        - clip: txt copied to clipboard
        - noMP3: gtts failed and we don't have sound
        - trans: translation proposed from google
        """

        # status bar is showing tooltip when hoover the menu
        # restore statusbar when empty
        if event == 'init':
            self.statusbarMsg.setText('Open DB or import from TXT')
        elif event == 'saved':
            self.statusbarMsg.setText(f'Saved DB: <i>{self._fs.getDB(file=True)}</i>')
        elif event == 'openDB':
            self.statusbarMsg.setText(f'Opened DB: <i>{self._fs.getDB(file=True)}</i>')
            self._view.setWindowTitle(self._fs.getDB())
        elif event == 'modDB':
            err = self._logic.err.replace("</p>", '')
            err = err.replace('<p>', '')
            self.statusbarMsg.setText(f'Modified DB: <i>{self._fs.getDB(file=True)}</i>. {err}')
        elif event == 'saved_as':
            self.statusbarMsg.setText(f'Opened DB: <i>{self._fs.getDB(file=True)}</i>')
            self._view.setWindowTitle(self._fs.getDB())
        elif event == 'imported':
            if self._fs.getDB():
                self.statusbarMsg.setText(
                    f'Imported <i>{self._fs.getIMP(file=True)}</i>. Added to DB <i>{self._fs.getDB(file=True)}</i>.')
            else:
                self.statusbarMsg.setText(f'Imported <i>{self._fs.getIMP(file=True)}</i>.')
        elif event == 'exported':
            self.statusbarMsg.setText(f'Exported DB to {self._fs.getIMP(file=True)}')
        elif event == 'newDB':
            self.statusbarMsg.setText(f'Created new empty DB: <i>{self._fs.getDB(file=True)}</i>')
            self._view.setWindowTitle(self._fs.getDB())
        elif event == 'addROW':
            self.statusbarMsg.setText('added empty row to DB')
        elif event == 'delROW':
            self.statusbarMsg.setText('deleted row from DB')
        elif event == 'clip':
            self.statusbarMsg.setText(f'<i>{self.selTxt}</i> copied to clipboard')
        elif event == 'noMP3':
            self.statusbarMsg.setText('no sound file')
        elif event == 'trans':
            self.statusbarMsg.setText('translation from google. Check carefully')

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
        self._view.save_as_DB.triggered.connect(self._save_as_DB)
        self._view.import_TXT.triggered.connect(self._import_TXT)
        self._view.export_TXT.triggered.connect(self._export_TXT)
        self._view.exit.triggered.connect(self._exit)
        # text mods
        self._view.txt_pl.editingFinished.connect(self._edit_txt)
        self._view.txt_ru.editingFinished.connect(self._edit_txt)
        # catch exit signal
        self._view.installEventFilter(self)
        # catch dbl click on desc txt
        self._installDblClick()
        # catch link hoovered on description boxes
        tabs_no = self._view.tabWidget_tager.count()
        for tab_s in self.tab_desc:
            for tab_i in range(tabs_no):
                exec(f'self._view.txt_desc_{tab_s}_{tab_i + 1}.linkHovered.connect(self.toolTipHovered)')
        # catch link clicked (to translate ru_wiki exemples)
        for tab_i in range(tabs_no):
            exec(f'self._view.txt_desc_wiki_{tab_i + 1}.linkActivated.connect(self.toolTipActivated)')
        # search box
        self._view.search.editingFinished.connect(self.found)
        self._view.search.installEventFilter(self)  # selected from completer by mouse
        # install right click menu
        self.newRU.triggered.connect(
            lambda: self._add(ru=self.selTxt, action='new', checked=self._view.btn_add.isChecked()))
        self.newPL.triggered.connect(
            lambda: self._add(pl=self.selTxt, action='new', checked=self._view.btn_add.isChecked()))
        self.addRU.triggered.connect(
            lambda: self._add(ru=self.selTxt, action='add', checked=self._view.btn_add.isChecked()))
        self.addPL.triggered.connect(
            lambda: self._add(pl=self.selTxt, action='add', checked=self._view.btn_add.isChecked()))
        self.replRU.triggered.connect(
            lambda: self._add(ru=self.selTxt, action='repl', checked=self._view.btn_add.isChecked()))
        self.replPL.triggered.connect(
            lambda: self._add(pl=self.selTxt, action='repl', checked=self._view.btn_add.isChecked()))

    def found(self):
        txt = self._view.search.text()
        if txt not in [self._view.txt_pl.text(), self._view.txt_ru] and txt != '':
            row = self._logic.db.loc[self._logic.db.pl == txt]
            if row.empty:
                row = self._logic.db.loc[self._logic.db.ru == txt]
            self.setDisplayText(self._logic.print(row.index[0]))
            self._view.search.setText('')
        else:
            self._view.search.setText('')

    def fillCompleter(self):
        self._view.search.setCompleter(None)
        self._view.search.setValidator(None)
        words = self._logic.db.ru.to_list()
        words += self._logic.db.pl.to_list()
        completer = QtWidgets.QCompleter(words)
        completer.setCaseSensitivity(False)
        self._view.search.setCompleter(completer)
        validSearch = validSearchClass(words, self)
        self._view.search.setValidator(validSearch)

    def toolTipHovered(self, href):
        if href[-1] == 'G': # to be translated by google and shall be handled by self.toolTipActivated
            return
        try:
            exp = self.toolTipTxt.exp[self.toolTipTxt.abr == href]
            exp = '<div style=\"width: 300px;\">' + exp.iloc[0] + '</div>'
        except:
            exp = ''
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), exp)
    
    def toolTipActivated(self, href):
        if href[-1] != 'G': # translate only links from ru_wiki example
            return
        try:
            exp = self._logic.googl.translate_q(href[:-1])
            exp = '<div style=\"width: 300px;\">' + exp + '</div>'
        except:
            exp = ''
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), exp)

    def _edit_txt(self):
        if self._view.btn_add.isChecked():
            # we want to add row
            if self._view.focusWidget() in [self._view.txt_pl, self._view.txt_ru]:
                # switching focus between pl and ru doesn't finish adding
                return
            # if pl nd ru changed, we end adding also if btn_add still checked
            if self._view.txt_ru.text() and self._view.txt_pl.text():
                self._view.btn_add.setChecked(False)
                self._add(checked=False)
                return
        else:
            row = self._logic.print(self._logic.history[self._logic.history_index])
            if not self._view.txt_ru.text() and row.ru == 'none':
                # if finished adding and row.ru is none
                # if no new ru word added, get rid of none from DB
                # and restore last db
                # last chance: check if google can translate
                try:
                    trans = self._logic.googl.translate_q(self._view.txt_pl.text(), 'pl')
                except:
                    trans = ''
                if trans:
                    self._view.txt_ru.setText(trans)
                    self._edit_txt()
                    return
                self._logic.drop(row.name)
                row = self._logic.print(self._logic.history[self._logic.history_index])
                self.setDisplayText(row)
                return
            if row.ru != self._view.txt_ru.text() or row.pl != self._view.txt_pl.text():
                # both pl and ru have changed, so we end edit and write changes
                self._logic.drop(row.name)
                self._logic.importTXT(self._view.txt_ru.text() + '\t   ' + self._view.txt_pl.text())
                self._logic.commit()
                self._logic.write_sql_db(self._fs.getDB())
                self.disp_statusbar('modDB')
                # enable all btn
                self._view.btn_del.setDisabled(False)
                self._view.btn_previous.setDisabled(False)
                self._view.btn_rand.setDisabled(False)
                self._view.btn_next.setDisabled(False)
                # uncheck the btn_add
                self._view.btn_add.setChecked(False)
                # finally, we rewrite desc text
                # must be at end, 'couse triggering self._edit_txt again (loose focus)
                self.setDisplayText(self._logic.print(self._logic.history[self._logic.history_index]))
                self.fillCompleter()

    def _print(self):
        self.setDisplayText(self._logic.print())

    def _next(self):
        self.setDisplayText(self._logic.next())

    def _prev(self):
        self.setDisplayText(self._logic.previous())

    def _add(self, checked, ru='', pl='', action=''):
        """Adds empty row to DB(none   ''). Clears pl and ru txt. Pressing enter will be\n
        caught by self._edit_txt and write to DB.\n
        Used also by context menu, with possible actions:\n
        - new\n
        - add\n
        - replace
        """
        if action == 'new':
            self._view.btn_add.setChecked(True)
            checked = True
        if action == 'add':
            if ru:
                self._view.txt_ru.setText(self._view.txt_ru.text() + ', ' + ru)
                self._view.txt_ru.setFocus()
            else:
                self._view.txt_pl.setText(self._view.txt_pl.text() + ', ' + pl)
                self._view.txt_pl.setFocus()
            self._view.btn_add.setChecked(True)
        if action == 'repl':
            if ru:
                self._view.txt_ru.setText(ru)
                self._view.txt_ru.setFocus()
            else:
                self._view.txt_pl.setText(pl)
                self._view.txt_pl.setFocus()
            self._view.btn_add.setChecked(True)

        if checked:
            # create new row in db
            self._logic.importTXT('none')
            self._logic.commit()
            # clean GUI
            self._view.txt_ru.setText(ru)
            self._view.txt_pl.setText(pl)
            self._view.txt_ru.setFocus()  # will rise event, which will send to self._edit_txt
            # disable other btns
            self._view.btn_del.setDisabled(True)
            self._view.btn_previous.setDisabled(True)
            self._view.btn_rand.setDisabled(True)
            self._view.btn_next.setDisabled(True)
            # change background
            self._view.btn_add.setStyleSheet('background-color: red;')
        else:  # un click
            self._view.btn_add.setChecked(False)
            # enable other btns
            self._view.btn_del.setDisabled(False)
            self._view.btn_previous.setDisabled(False)
            self._view.btn_rand.setDisabled(False)
            self._view.btn_next.setDisabled(False)
            # stop animation and restore
            self._view.btn_add.setStyleSheet('background-color: #F1F1F3;')
            self._edit_txt()

    def _del(self):
        row = self._logic.print(self._logic.history[self._logic.history_index])
        self._logic.drop(row.name)
        self._logic.write_sql_db(self._fs.getDB())
        self.disp_statusbar('delROW')
        self.setDisplayText(self._logic.print(self._logic.history[self._logic.history_index]))
        self.fillCompleter()

    def _play(self, repeat=False):
        row = self._logic.print(self._logic.history[self._logic.history_index])
        if row.ru:
            if not repeat:
                # win will not allow opening the file again
                # but allows to delete...
                try:
                    os.remove(self._fs.getMP3())
                except:
                    pass
                try:
                    # gTTS module is not very stable
                    # has problem with tokens sometimes
                    word_sound = gTTS(text=row.ru, lang='ru', lang_check=False)
                    word_sound.save(self._fs.getMP3())
                except:
                    os.remove(self._fs.getMP3())
                    self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    self.disp_statusbar("noMP3")
                    return
            if os.path.exists(self._fs.getMP3()):
                playsound.playsound(self._fs.getMP3())

    # menu function
    def _new_DB(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Save As SQlite3 file',
                                           directory='',
                                           filter=self._fs.getDB(ext=True))
        # Qt lib returning always / as path separator
        # we need system specific, couse we are checking for file existence
        path = QtCore.QDir.toNativeSeparators(file[0])
        if path:
            self._logic.write_sql_db(self._fs.getDB())
            self._fs.setDB(path)
        else:  # operation canceled
            return
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self._logic = Dictionary(self._fs.getTags(), self._fs.getTrans())  # drops DB, create new instance
        self._logic.write_sql_db(self._fs.getDB())
        # self._logic.open_sql_db(self._fs.getDB())
        self.setDisplayText(self._logic.print())
        self.disp_statusbar('newDB')
        self._fs.writeOpt("LastDB", self._fs.getDB())
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def _open_DB(self):
        file = QFileDialog.getOpenFileName(self._view, caption='Choose SQlite3 file',
                                           directory='',
                                           filter=self._fs.getDB(ext=True))
        # Qt lib returning always / as path separator
        # we need system specific, couse we are checking for file existence
        path = QtCore.QDir.toNativeSeparators(file[0])
        if path:
            self._fs.setDB(path)
        else:  # operation canceled
            return
        if self._logic.open_sql_db(self._fs.getDB()) is not None:  # return None if fail
            self.setDisplayText(self._logic.print())
            self.disp_statusbar('openDB')
            self._fs.writeOpt("LastDB", self._fs.getDB())
        self.fillCompleter()

    def _saveDB(self):
        if self._fs.getDB():
            self._logic.write_sql_db(self._fs.getDB())
            self.disp_statusbar('saved')
        else:
            self._save_as_DB()

    def _save_as_DB(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Save As SQlite3 file',
                                           directory=self._fs.getDB(),
                                           filter=self._fs.getDB(ext=True))
        # Qt lib returning always / as path separator
        # we need system specific, couse we are checking for file existence
        path = QtCore.QDir.toNativeSeparators(file[0])
        if not path:  # operation canceled
            return
        self._logic.write_sql_db(self._fs.getDB())
        self._fs.setDB(path)
        self._logic.write_sql_db(self._fs.getDB())
        self._logic.open_sql_db(self._fs.getDB())
        self.disp_statusbar('saved_as')

    def _import_TXT(self):
        file = QFileDialog.getOpenFileName(self._view, caption='Choose TXT od S3DB file',
                                           directory='',
                                           filter=self._fs.getIMP(ext=True))
        # Qt lib returning always / as path separator
        # we need system specific, couse we are checking for file existence
        path = QtCore.QDir.toNativeSeparators(file[0])
        if path:
            self._fs.setIMP(path)
        else:
            return  # operation canceled
        # there is fackup when reading files created in linux into win
        # but it can be a more general problem when we don't know encoding
        # so read as bytes and than decode with 'utf-8'
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        ext = self._fs._split_path(path)[2]
        if ext == self._fs.typeDB[1]: # sqlite file
            imp = self._logic.importTXT(path, txt=False)
        else:
            file = []
            with open(self._fs.getIMP(), 'rb') as f:
                for line in f.readlines():
                    file.append(line.decode('utf-8'))
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
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.fillCompleter()

    def _export_TXT(self):
        file = QFileDialog.getSaveFileName(self._view, caption='Export DB to TXT file',
                                           directory=self._fs.getDB(),
                                           filter=self._fs.getIMP(ext=True))
        path = QtCore.QDir.toNativeSeparators(file[0])
        if not path:  # operation canceled
            return
        self._fs.setIMP(path)
        self._logic.db.to_csv(path, sep='\t', index=False, header=False, columns=['ru', 'pl'])
        self.disp_statusbar('exported')

    # other helpers
    def _readLastDB(self):
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        if self._logic.open_sql_db(self._fs.getDB()) is not None:  # return None if fail
            self.setDisplayText(self._logic.print())
            self.disp_statusbar('openDB')
        else:  # missing file, display welcome message
            self.setDescText()
            self._view.tabWidget_tager.setTabVisible(0, True)
            self._view.tabWidget_tager.setTabText(0, 'welcome')
            wel_txt = self._fs.getOpt('welcome')
            self._view.txt_desc_tager_1.setText(wel_txt)
            self._view.tabWidget_desc.setCurrentIndex(0)
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def _exit(self):
        # delete MP3 file
        try:
            os.remove(self._fs.getMP3())
        except:
            pass
        # save DB and store the name in conf file
        if self._fs.getDB():
            self._saveDB()
            self._fs.writeOpt("LastDB", self._fs.getDB())
        self._view.close()

    def eventFilter(self, source, event):
        """Catch signal:\n
        - if user closed the window\n
        - if user resize the window\n
        - double click on desc text box
        """
        if event.type() == QtCore.QEvent.Close:
            self._exit()
        elif event.type() == QtCore.QEvent.Resize and \
                source.__class__ is QtWidgets.QLineEdit:
            self.adjDisplaySize()
        elif event.type() == QtCore.QEvent.MouseButtonDblClick and \
                source.__class__ is QtWidgets.QLabel:
            # we start timer to allow standard handling of dbl click:
            # that is text select
            # after 100msec we get the text
            QtCore.QTimer.singleShot(100, lambda: self.selectTxt(source))
        elif event.type() == QtCore.QEvent.MouseButtonRelease and \
                source.__class__ is QtWidgets.QLabel:
            self.selectTxt(source)
        # selected from completer by mouse
        elif event.type() == QtCore.QEvent.InputMethodQuery and \
                source.__class__ is QtWidgets.QLineEdit and \
                self._view.search.text() != '' and \
                self._view.search.hasAcceptableInput():
            self.found()
        return False

    def selectTxt(self, source):
        self.selTxt = source.selectedText()
        # get selected tex and copy to clipboard
        if self.selTxt:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(self.selTxt)
            self.disp_statusbar('clip')

    def setDisplayText(self, row):
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self._view.txt_ru.setText(row.ru)
        self._view.txt_pl.setText(row.pl)
        # if one word is missing: propose translation
        if not self._view.txt_pl.text():
            try:
                trans = self._logic.googl.translate_q(self._view.txt_ru.text(), 'ru')
            except:
                trans = ''
            self._view.txt_pl.setText(trans)
            self.disp_statusbar('trans')
            self._view.txt_pl.selectAll()
            self._view.txt_pl.setFocus()
        if not self._view.txt_ru.text():
            try:
                trans = self._logic.googl.translate_q(self._view.txt_pl.text(), 'pl')
            except:
                trans = ''
            self._view.txt_ru.setText(trans)
            self.disp_statusbar('trans')
            self._view.txt_ru.selectAll()
            self._view.txt_ru.setFocus()
        self.adjDisplaySize()
        self.setDescText()

        self._logic.score()
        self._play()
        # update the progress
        zero = len(self._logic.db.loc[self._logic.db.try_n == 0])
        tot = len(self._logic.db)
        self.statusbarProgress.setValue(int(((tot - zero) / tot) * 100))
        self._view.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

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
                if widget_width < txt_width + 5:
                    font_size -= 1
                    font.setPointSize(font_size)
                    widget[i].setFont(font)
                    widget[(i + 1) % 2].setFont(font)  # other than i widget
                    if font_size < 4:
                        break
                else:
                    break

    def setDescText(self):
        # check how many words, unhide only tabs needed,
        # change name of tabs
        # we have only five tabs, should be enough, but if not, drops other words
        tabs_no = self._view.tabWidget_tager.count()
        wrds_no = len(self._logic.tager.wrd)
        if wrds_no > tabs_no:
            wrds_no = tabs_no
        for tab_s in self.tab_desc:  # googl tab need to set separately
            for tab_i in range(tabs_no):
                if tab_i > wrds_no - 1:  # hide tabs if more than wrds
                    exec(f'self._view.tabWidget_{tab_s}.setTabVisible({tab_i}, False)')
                else:
                    exec(f'self._view.tabWidget_{tab_s}.setTabVisible({tab_i}, True)')
                    exec(f'self._view.tabWidget_{tab_s}.setTabText({tab_i}, self._logic.tager.wrd[{tab_i}])')
        # set description
        for wrd_i in range(wrds_no):
            exec(f'self._view.txt_desc_tager_{wrd_i + 1}.setText(self._logic.tager.formatAll({wrd_i}))')
            exec(f'self._view.txt_desc_wiki_{wrd_i + 1}.setText(self._logic.wiki.readData({wrd_i}))')
        self._view.txt_desc_goog.setText(self._logic.googl.formatAll())
