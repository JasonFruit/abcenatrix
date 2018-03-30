# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from abcv.general_midi import general_midi
from abcv.tools import commands

def line():
    out = QFrame()
    out.setFrameShape(QFrame.HLine)
    out.setFrameShadow(QFrame.Sunken)
    return out


def short_path_name(long_name):
    """
    Gets the short path name of a given long path.
    http://stackoverflow.com/a/23598461/200291
    """

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        _GetShortPathNameW.restype = wintypes.DWORD

        output_buf_size = 0
        
        while True:
            output_buf = ctypes.create_unicode_buffer(output_buf_size)
            needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
            if output_buf_size >= needed:
                return output_buf.value
            else:
                output_buf_size = needed
                
    else:
        
        return long_name

class ToolSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        QDialog.__init__(self, parent=parent)
        self.setMinimumSize(QSize(480, 0))
        self.setModal(True)
        self.settings = settings
        self.set_up()

    def set_up(self):
        self.command_entries = {}
        
        self.frm = QFormLayout()
        self.setLayout(self.frm)

        for command in commands.keys():
            def addRowFn(cmd):
                lbl, entry, btn = (QLabel("%s location:" % cmd),
                                   QLineEdit(),
                                   QPushButton("..."))

                self.command_entries[cmd] = entry
                
                entry.setText(self.settings.get("%s location" % command))
                
                wid = QWidget()
                hbx = QHBoxLayout()
                wid.setLayout(hbx)
                hbx.addWidget(lbl)
                hbx.addWidget(entry)
                self.frm.addRow(wid, btn)

                btn.command = cmd

                def fn(*args, **kwargs):
                    fn, accept = QFileDialog.getOpenFileName(
                        self,
                        "Location of %s" % btn.command,
                        entry.text())

                    if accept:
                        entry.setText(fn)

                btn.clicked.connect(fn)

            addRowFn(command)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        
        self.buttons.accepted.connect(self._update_settings)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.frm.addRow(self.buttons)

    def _update_settings(self, *args, **kwargs):
        for command in self.command_entries.keys():
            location = self.command_entries[command].text()

            location = short_path_name(location)
            # if not location.startswith('"'):
            #     location = '"%s"' % location
                
            self.settings.set("%s location" % command,
                              location)

            
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

        self.frm.addRow(line())

        self.frm.addRow(QLabel("Display options:"))
        
        self.fit_list = QComboBox()

        fits = ["width", "height", "all"]
        self.fit_list.addItems(fits)
        self.fit_list.setCurrentIndex(fits.index(self.settings.get("Default fit")))
        self.frm.addRow("Fit page to", self.fit_list)

        self.frm.addRow(line())

        self.frm.addRow(QLabel("MIDI options"))

        self.instrument_list = QComboBox()

        current_instrument = self.settings.get("MIDI instrument")
        
        for k in general_midi.keys():
            self.instrument_list.addItem(general_midi[k])
            if k == current_instrument:
                self.instrument_list.setCurrentIndex(k-1)

        self.frm.addRow(QLabel("MIDI instrument"), self.instrument_list)

        self.tune_settings_btn = QPushButton("Tool settings...")
        self.tune_settings_btn.clicked.connect(self._show_tool_settings)
        self.frm.addRow(self.tune_settings_btn)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        
        self.buttons.accepted.connect(self._update_settings)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.frm.addRow(self.buttons)

    def _show_tool_settings(self, *args, **kwargs):
        tsd = ToolSettingsDialog(self.settings)
        tsd.exec_()

    def _update_settings(self, *args, **kwargs):
        self.settings.set("User name", self.username_edit.text())
        self.settings.set("User email", self.email_edit.text())
        self.settings.set("Default fit", self.fit_list.currentText())
        for k in general_midi.keys():
            if general_midi[k] == self.instrument_list.currentText():
                self.settings.set("MIDI instrument", k)
                return
