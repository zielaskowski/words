# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(619, 270)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.learn = QtWidgets.QWidget()
        self.learn.setObjectName("learn")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.learn)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.txt_ru = QtWidgets.QLineEdit(self.learn)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.txt_ru.setFont(font)
        self.txt_ru.setObjectName("txt_ru")
        self.horizontalLayout.addWidget(self.txt_ru)
        self.txt_pl = QtWidgets.QLineEdit(self.learn)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.txt_pl.setFont(font)
        self.txt_pl.setObjectName("txt_pl")
        self.horizontalLayout.addWidget(self.txt_pl)
        self.btn_sound = QtWidgets.QPushButton(self.learn)
        self.btn_sound.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_sound.sizePolicy().hasHeightForWidth())
        self.btn_sound.setSizePolicy(sizePolicy)
        self.btn_sound.setMinimumSize(QtCore.QSize(47, 47))
        self.btn_sound.setMaximumSize(QtCore.QSize(47, 47))
        self.btn_sound.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/resources/resources/sound.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_sound.setIcon(icon)
        self.btn_sound.setIconSize(QtCore.QSize(35, 35))
        self.btn_sound.setObjectName("btn_sound")
        self.horizontalLayout.addWidget(self.btn_sound)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btn_previous = QtWidgets.QPushButton(self.learn)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_previous.sizePolicy().hasHeightForWidth())
        self.btn_previous.setSizePolicy(sizePolicy)
        self.btn_previous.setMinimumSize(QtCore.QSize(80, 0))
        self.btn_previous.setObjectName("btn_previous")
        self.horizontalLayout_2.addWidget(self.btn_previous)
        self.btn_rand = QtWidgets.QPushButton(self.learn)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_rand.sizePolicy().hasHeightForWidth())
        self.btn_rand.setSizePolicy(sizePolicy)
        self.btn_rand.setMinimumSize(QtCore.QSize(80, 0))
        self.btn_rand.setObjectName("btn_rand")
        self.horizontalLayout_2.addWidget(self.btn_rand)
        self.btn_next = QtWidgets.QPushButton(self.learn)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_next.sizePolicy().hasHeightForWidth())
        self.btn_next.setSizePolicy(sizePolicy)
        self.btn_next.setMinimumSize(QtCore.QSize(80, 0))
        self.btn_next.setObjectName("btn_next")
        self.horizontalLayout_2.addWidget(self.btn_next)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.tabWidget.addTab(self.learn, "")
        self.test = QtWidgets.QWidget()
        self.test.setObjectName("test")
        self.tabWidget.addTab(self.test, "")
        self.horizontalLayout_3.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 619, 30))
        self.menubar.setToolTip("")
        self.menubar.setToolTipDuration(-1)
        self.menubar.setStatusTip("")
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setToolTip("")
        self.menu.setToolTipDuration(-1)
        self.menu.setToolTipsVisible(False)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.open_DB = QtWidgets.QAction(MainWindow)
        self.open_DB.setObjectName("open_DB")
        self.save_DB = QtWidgets.QAction(MainWindow)
        self.save_DB.setObjectName("save_DB")
        self.import_TXT = QtWidgets.QAction(MainWindow)
        self.import_TXT.setObjectName("import_TXT")
        self.exit = QtWidgets.QAction(MainWindow)
        self.exit.setObjectName("exit")
        self.actionedit_DB = QtWidgets.QAction(MainWindow)
        self.actionedit_DB.setObjectName("actionedit_DB")
        self.save_as_DB = QtWidgets.QAction(MainWindow)
        self.save_as_DB.setObjectName("save_as_DB")
        self.new_DB = QtWidgets.QAction(MainWindow)
        self.new_DB.setObjectName("new_DB")
        self.menu.addAction(self.new_DB)
        self.menu.addAction(self.open_DB)
        self.menu.addAction(self.save_DB)
        self.menu.addAction(self.save_as_DB)
        self.menu.addAction(self.actionedit_DB)
        self.menu.addSeparator()
        self.menu.addAction(self.import_TXT)
        self.menu.addAction(self.exit)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Learn Words"))
        self.btn_previous.setText(_translate("MainWindow", "Previous"))
        self.btn_rand.setText(_translate("MainWindow", "Random"))
        self.btn_next.setText(_translate("MainWindow", "Next"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.learn), _translate("MainWindow", "learn"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.test), _translate("MainWindow", "test"))
        self.menu.setStatusTip(_translate("MainWindow", "Handle DB or import TXT"))
        self.menu.setTitle(_translate("MainWindow", "Menu"))
        self.open_DB.setText(_translate("MainWindow", "open DB"))
        self.open_DB.setToolTip(_translate("MainWindow", "open DB"))
        self.open_DB.setStatusTip(_translate("MainWindow", "select SQlite file to load"))
        self.save_DB.setText(_translate("MainWindow", "save DB"))
        self.save_DB.setToolTip(_translate("MainWindow", "save DB"))
        self.save_DB.setStatusTip(_translate("MainWindow", "save opened DB"))
        self.import_TXT.setText(_translate("MainWindow", "import TXT"))
        self.import_TXT.setToolTip(_translate("MainWindow", "import TXT"))
        self.import_TXT.setStatusTip(_translate("MainWindow", "import pair of words from TXT file"))
        self.exit.setText(_translate("MainWindow", "Exit"))
        self.exit.setToolTip(_translate("MainWindow", "Exit"))
        self.exit.setStatusTip(_translate("MainWindow", "Exit"))
        self.actionedit_DB.setText(_translate("MainWindow", "edit DB"))
        self.actionedit_DB.setToolTip(_translate("MainWindow", "edit DB"))
        self.actionedit_DB.setStatusTip(_translate("MainWindow", "display opened DB and alows edit"))
        self.save_as_DB.setText(_translate("MainWindow", "save as DB"))
        self.save_as_DB.setToolTip(_translate("MainWindow", "save as DB"))
        self.save_as_DB.setStatusTip(_translate("MainWindow", "save opened DB under new name and opens it"))
        self.new_DB.setText(_translate("MainWindow", "new DB"))
        self.new_DB.setStatusTip(_translate("MainWindow", "create new and empty SQlite3 file"))
import resources_rc
