# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

from PySide.QtCore import *
from PySide.QtGui import *

class SettingsDialog(QDialog):
    def __init__(self, settings=None, parent=None):
        QDialog.__init__(self, parent=parent)
        self.setMinimumSize(QSize(600, 0))
        self.setModal(True)
        self.settings = settings
        self.set_up()

    def set_up(self):

        self.frm = QFormLayout()
        self.setLayout(self.frm)

        self.frm.addRow(QLabel("Default identity (for new tunes):"))

        self.username_edit = QLineEdit()
        self.username_edit.setText(self.settings.get("User name"))
        self.frm.addRow("User name", self.username_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setText(self.settings.get("User email"))
        self.frm.addRow("Email", self.email_edit)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        self.frm.addRow(line)

        self.frm.addRow(QLabel("Display options:"))
        
        self.fit_list = QComboBox()

        fits = ["width", "height", "all"]
        self.fit_list.addItems(fits)
        self.fit_list.setCurrentIndex(fits.index(self.settings.get("Default fit")))
        self.frm.addRow("Fit page to", self.fit_list)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        
        self.buttons.accepted.connect(self._update_settings)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.frm.addRow(self.buttons)

    def _update_settings(self, *args, **kwargs):
        self.settings.set("User name", self.username_edit.text())
        self.settings.set("User email", self.email_edit.text())
        self.settings.set("Default fit", self.fit_list.currentText())
        
