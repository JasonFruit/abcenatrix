from PySide.QtCore import *
from PySide.QtGui import *
import os
from abcv.tunebook import AbcTune, AbcTunebook, tune_from_abc
from abcv.scrollable_svg import ScrollableSvgWidget, fits
from uuid import uuid4

tune_template = """X:0
T:Title
M:4/4
L:1/8
Z:""" + os.environ["USER"] + """
K:C
C4"""

class AbcTuneEditor(QDialog):
    def __init__(self, tune=None, parent=None):
        QDialog.__init__(self, parent=parent)
        self.setMinimumSize(QSize(800, 600))
        self.setModal(True)

        if not tune:
            tune = tune_from_abc(tune_template)
            
        self._tune = tune
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox, stretch=1)
        
        self.editor = QPlainTextEdit()

        self.editor.document().setPlainText(tune.content)

        self.editor.textChanged.connect(self._on_text_change)

        self.hbox.addWidget(self.editor)

        self.svg = ScrollableSvgWidget(self.height(),
                                       self.width(),
                                       fit_style=fits.FIT_WIDTH)

        self.tmp_svg = None

        # the scroll widget to contain the SVG tune
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Light)
        self.scroll_area.setWidget(self.svg)
        self.svg.load("tmp.svg")
        self.hbox.addWidget(self.scroll_area)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.vbox.addWidget(self.buttons)
        
        self.redraw_tune()

    def _on_text_change(self, *args, **kwargs):
        self._tune.content = self.editor.document().toPlainText()
        self.redraw_tune()

    def redraw_tune(self):
        if self.tmp_svg:
            try:
                os.unlink(self.tmp_svg)
            except:
                pass
                
        self.tmp_svg = "/tmp/%s.svg" % uuid4()
        self._tune.write_svg(self.tmp_svg)

        if os.path.exists(self.tmp_svg):
            self.svg.load(self.tmp_svg)

    @property
    def tune(self):
        return tune_from_abc(self.editor.document().toPlainText().strip())

    @tune.setter
    def tune(self, new_tune):
        self._tune = new_tune
        self.editor.document().setPlainText(new_tune.content.strip())
        self.redraw_tune()

    def resizeEvent(self, *args, **kwargs):
        self.svg.visible_width, self.svg.visible_height = self.scroll_area.size().toTuple()
        self.redraw_tune()
        
def edit_tune(tune, parent=None):
    dlg = AbcTuneEditor(tune, parent=parent)
    accepted = dlg.exec_()
    return (dlg.tune, accepted)

if __name__ == "__main__":
    import sys
    qt_app = QApplication(sys.argv)
    app = AbcTuneEditor()
    app.exec_()
    
    # Run the application's event loop
    qt_app.exec_()

    print(app.tune.content)
