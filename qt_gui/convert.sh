#!/bin/bash
#/usr/bin/pyuic5 main_window.ui -o ../main_window.py
#/usr/bin/pyuic5 import_window.ui -o ../import_window.py
/home/mi/.backup/venv/words/bin/pyuic5 main_window.ui -o main_window.py --import-from=qt_gui
/home/mi/.backup/venv/words/bin/pyuic5 import_window.ui -o import_window.py --import-from=qt_gui

/home/mi/.backup/venv/words/bin/pyrcc5 resources.qrc -o resources_rc.py 



