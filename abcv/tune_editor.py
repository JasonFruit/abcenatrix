# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

from uuid import uuid4

from PySide.QtCore import *
from PySide.QtGui import *
import os, tempfile
from abcv.tunebook import tune_from_abc

from abcv.abc_display import AbcDisplay, fits
from abcv.midi_mixin import MidiMixin

tune_template = """X:0
T:Title
M:2/4
L:1/16
Z: %s <%s>
K:A
A4"""


class AbcTuneEditor(QDialog, MidiMixin):
    def __init__(self, settings, tune=None, parent=None):
        QDialog.__init__(self, parent=parent)
        MidiMixin.__init__(self, settings.get("MIDI port"))
        self.setMinimumSize(QSize(800, 600))
        self.showMaximized()
        self.setModal(True)

        self.settings = settings

        self.tune_template = tune_template % (self.settings.get("User name"),
                                              self.settings.get("User email"))

        if not tune:
            tune = tune_from_abc(self.tune_template)
            
        self._tune = tune
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.menu_bar = QMenuBar(self)
        self.layout().setMenuBar(self.menu_bar)

        self._set_up_menus()
        
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox, stretch=1)
        
        self.editor = QPlainTextEdit()

        self.editor.document().setPlainText(tune.content)

        self.editor.textChanged.connect(self._on_text_change)

        self.hbox.addWidget(self.editor)

        self.abc_display = AbcDisplay(parent=self,
                                      fit=fits.FIT_WIDTH)

        self.hbox.addWidget(self.abc_display)

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
        self.export_midi()

    def redraw_tune(self):
        self.abc_display.tune = self._tune

    def export_midi(self):
        tempdir = tempfile.gettempdir()
        
        # export the tune as MIDI to get ready to play it
        self.tmp_midi = os.path.join(tempdir, "%s.mid" % uuid4())
        self._tune.write_midi(
            self.tmp_midi,
            midi_program=self.settings.get("MIDI instrument"))

        self.load_midi(self.tmp_midi)


    def _set_up_menus(self):
        self.playback_menu = self.menu_bar.addMenu("&Playback")
        self.editing_menu = self.menu_bar.addMenu("&Editing")

        def addAction(menu, label, shortcut, handler):
            """A helper function to add actions to menus"""
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            menu.addAction(action)
            return action

        addAction(self.playback_menu,
                  "Start/Stop",
                  "Ctrl+Space",
                  lambda *args, **kwargs: self.toggle_play())

        
    @property
    def tune(self):
        return tune_from_abc(self.editor.document().toPlainText().strip())

    @tune.setter
    def tune(self, new_tune):
        self._tune = new_tune
        self.editor.document().setPlainText(new_tune.content.strip())
        self.redraw_tune()
        
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            self.abc_display.resizeEvent(None)
            self.redraw_tune()
        QWidget.changeEvent(self, event)

