#!/bin/bash
#/usr/bin/pyuic5 main_window.ui -o ../main_window.py
#/usr/bin/pyuic5 import_window.ui -o ../import_window.py
pyuic5 main_window.ui -o main_window.py --import-from=words.qt_gui
pyuic5 import_window.ui -o import_window.py --import-from=words.qt_gui

pyrcc5 resources.qrc -o resources_rc.py 



