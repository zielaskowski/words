"""
system requirements:
Using treetagger wrapper, to work you need treetagger executable with parameter files:
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
    1. Download the tagger package for your system (PC-Linux, Mac OS-X, ARM64, ARMHF, ARM-Android, PPC64le-Linux).
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.3.tar.gz
    2. Download the installation script install-tagger.sh
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
    3. Download the parameter files for the languages you want to process.
    RU_params: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/russian.par.gz
    RU_tags: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/russian.par.gz
    Open a terminal window and run the installation script in the directory where you have downloaded the files:
    sh install-tagger.sh
using Gstreamer, you need (linux only):
- cairo-devel pkg-config python3-devel gcc gobject-introspection-devel libgirepository1.0-dev
"""


import sys
from gui import GUIWords, GUIWordsCtr
from PyQt5.QtWidgets import QApplication


app = QApplication([])
view = GUIWords()
view.show()
GUIWordsCtr(view)
sys.exit(app.exec())
