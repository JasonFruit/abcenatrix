# -*- coding: utf-8 -*-

# be futuristic!  That is, basically use Python 3.
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import os, sys, tempfile, codecs
from uuid import uuid4
import webbrowser as wb

from PySide.QtCore import *
from PySide.QtGui import *

from abcv.tunebook import AbcTune, AbcTunebook, information_fields
from abcv.scrollable_svg import ScrollableSvgWidget, fits
from abcv.tune_editor import AbcTuneEditor
from abcv.midiplayer import MidiPlayer
from abcv.filter_dialog import FilterDialog
from abcv.settings_dialog import SettingsDialog
from abcv.about import about_text

class TuneListItem(QListWidgetItem):
    def __init__(self, tune):
        QListWidgetItem.__init__(self, tune.title)
        self.tune = tune

def show_tune_info(tune, parent=None):
    message = []
    defined = information_fields.keys()
    
    for k in tune.keys():
        if k in defined:
            message.append("%s: %s" % (information_fields[k],
                                       "\n".join(tune[k])))
            
    dlg = QMessageBox(parent)
    dlg.setText("\n".join(message))
    
    return dlg.exec_()

class Application(QMainWindow):
    def __init__(self, settings, filename=None):
        QMainWindow.__init__(self)
        self.setWindowIcon(
            QIcon(os.path.join(os.path.dirname(__file__),
                               "/usr/share/pixmaps/abcviewer.png")))

        self._dirty = False
        
        self.midi = MidiPlayer()
        
        self.settings = settings
        self._current_tune = None
        self._setUpMenus()

        # there must be one main widget, so we need this one; we'll
        # add the hbox layout to it
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # the main layout; title list on the left, scrollable tune
        # display on the right
        self.tunebook_hbox = QHBoxLayout()
        self.central_widget.setLayout(self.tunebook_hbox)

        self.title_vbox = QVBoxLayout()

        self.title_control_hbox = QHBoxLayout()

        self.title_filter_btn = QPushButton("&Filter")
        self.filter_menu = self._set_up_filter_menu()
        self.title_filter_btn.setMenu(self.filter_menu)

        self.title_control_hbox.addWidget(self.title_filter_btn, stretch=0)

        self.title_vbox.addLayout(self.title_control_hbox, stretch=0)

        self.title_list = QListWidget()
        self.title_list.currentItemChanged.connect(self._on_index_change)
        
        self.title_vbox.addWidget(self.title_list, stretch=1)
        
        self.tunebook_hbox.addLayout(self.title_vbox, stretch=0) # fixed width

        # get the width and height of the window
        width, height = self.size().toTuple()

        if self.settings.get("Default fit") == "width":
            fit = fits.FIT_WIDTH
        elif self.settings.get("Default fit") == "all":
            fit = fits.FIT_ALL
        elif self.settings.get("Default fit") == "height":
            fit = fits.FIT_HEIGHT
        else:
            # the default default, I guess
            fit = fits.FIT_ALL
            
        # the tune is in an SVG display widget that changes height
        # based on fit parameters
        self.abc_display = ScrollableSvgWidget(height,
                                               width,
                                               fit_style=fit)

        # the scroll widget to contain the SVG tune
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Light)
        self.scroll_area.setWidget(self.abc_display)

        # stretches horizontally to fill screen
        self.tunebook_hbox.addWidget(self.scroll_area, stretch=1.0)

        self.tmp_svg = None

        # if a filename was passed in, load it
        if filename:
            self._load(filename)
        else:
            self._new_tunebook()

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, val):
        self._dirty = val
        if self._dirty:
            if self.abc_file.filename != None:
                self.setWindowTitle("%s (modified)" % self.abc_file.filename)
            else:
                self.setWindowTitle("New tunebook (modified)")
        else:
            if self.abc_file.filename != None:
                self.setWindowTitle(self.abc_file.filename)
            else:
                self.setWindowTitle("New tunebook")
                

    def _setUpMenus(self):
        # top-level menus
        self.file_menu = self.menuBar().addMenu("Tune&book")
        self.view_menu = self.menuBar().addMenu("Vie&w")
        self.tune_menu = self.menuBar().addMenu("&Tune")
        self.playback_menu = self.menuBar().addMenu("&Playback")
        self.app_menu = self.menuBar().addMenu("&ABCenatrix")
        
        # open and save go in the file menu
        self.file_open = QAction("&Open", self)
        self.file_open.setShortcut("Ctrl+O")
        self.file_open.setStatusTip("Open a tunebook")
        self.file_open.triggered.connect(self._prompt_load)

        self.file_save = QAction("&Save", self)
        self.file_save.setShortcut("Ctrl+S")
        self.file_save.setStatusTip("Save the tunebook")
        self.file_save.triggered.connect(self._save_tunebook)

        self.file_new = QAction("&New", self)
        self.file_new.setShortcut("Ctrl+Shift+N")
        self.file_new.setStatusTip("Create new tunebook")
        self.file_new.triggered.connect(self._new_tunebook)

        self.file_close = QAction("&Close", self)
        self.file_close.setShortcut("Ctrl+W")
        self.file_close.setStatusTip("Close the current tunebook")
        self.file_close.triggered.connect(self._new_tunebook)

        self.file_menu.addAction(self.file_open)
        self.file_menu.addAction(self.file_save)
        self.file_menu.addAction(self.file_new)
        self.file_menu.addAction(self.file_close)

        # fit choices go in a Fit submenu of the view menu
        self.view_fit_menu = self.view_menu.addMenu("Fit")
        
        self.view_fit_width = QAction("Width", self)
        self.view_fit_width.triggered.connect(self._fit_width)
        self.view_fit_height = QAction("Height", self)
        self.view_fit_height.triggered.connect(self._fit_height)
        self.view_fit_all = QAction("All", self)
        self.view_fit_all.triggered.connect(self._fit_all)
        
        self.view_fit_menu.addAction(self.view_fit_width)
        self.view_fit_menu.addAction(self.view_fit_height)
        self.view_fit_menu.addAction(self.view_fit_all)

        self.tune_transpose = QAction("Tra&nspose…", self)
        self.tune_transpose.triggered.connect(self._transpose)

        self.tune_menu.addAction(self.tune_transpose)

        self.tune_edit = QAction("&Edit the current tune", self)
        self.tune_edit.setShortcut("Ctrl+E")
        self.tune_edit.setStatusTip("Edit the tune with live preview")
        self.tune_edit.triggered.connect(self._edit_tune)

        self.tune_menu.addAction(self.tune_edit)

        self.tune_new_tune = QAction("&New tune", self)
        self.tune_new_tune.setShortcut("Ctrl+N")
        self.tune_new_tune.setStatusTip("Edit a new tune with live preview")
        self.tune_new_tune.triggered.connect(self._new_tune)

        self.tune_menu.addAction(self.tune_new_tune)

        self.tune_delete_tune = QAction("&Delete tune", self)
        self.tune_delete_tune.setShortcut("Ctrl+D")
        self.tune_delete_tune.setStatusTip("Delete selected tune")
        self.tune_delete_tune.triggered.connect(self._delete_tune)

        self.tune_menu.addAction(self.tune_delete_tune)

        self.tune_add_to_menu = self.tune_menu.addMenu("&Add to:")
        
        self.tune_add_to_book = QAction("E&xisting tunebook…", self)
        self.tune_add_to_book.setStatusTip("Copy tune to an existing ABC file")
        self.tune_add_to_book.triggered.connect(self._add_tune_to_tunebook)

        self.tune_add_to_menu.addAction(self.tune_add_to_book)

        self.tune_add_to_new_book = QAction("&New tunebook…", self)
        self.tune_add_to_new_book.setStatusTip(
            "Create a new ABC file with only this tune")
        self.tune_add_to_new_book.triggered.connect(
            self._add_tune_to_new_tunebook)

        self.tune_add_to_menu.addAction(self.tune_add_to_new_book)

        self.tune_print = QAction("&Print", self)
        self.tune_print.setShortcut("Ctrl+P")
        self.tune_print.setStatusTip("Print a tune")
        self.tune_print.triggered.connect(self._print)

        self.tune_menu.addAction(self.tune_print)

        self.tune_info = QAction("&Info", self)
        self.tune_info.setShortcut("Ctrl+I")
        self.tune_info.setStatusTip("Info on the selected tune")
        self.tune_info.triggered.connect(self._tune_info)

        self.tune_menu.addAction(self.tune_info)

        self.playback_start = QAction("&Start/Stop", self)
        self.playback_start.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self.playback_start.setStatusTip("Play/stop the selected tune")
        self.playback_start.triggered.connect(self._playback_start)

        self.playback_menu.addAction(self.playback_start)

        self.playback_restart = QAction("&Jump to start", self)
        self.playback_restart.setShortcut("Ctrl+J")
        self.playback_restart.setStatusTip("Restart the selected tune")
        self.playback_restart.triggered.connect(self._playback_restart)

        self.playback_menu.addAction(self.playback_restart)

        self.app_settings = QAction("&Settings…", self)
        self.app_settings.setStatusTip("Edit app settings")
        self.app_settings.triggered.connect(self._app_settings)

        self.app_menu.addAction(self.app_settings)

        self.app_menu.addSeparator()

        self.app_about_abc = QAction("&About ABC notation", self)
        self.app_about_abc.setStatusTip("Information about ABC notation")
        self.app_about_abc.triggered.connect(self._about_abc)

        self.app_menu.addAction(self.app_about_abc)

        self.app_learn_abc = QAction("&Learn ABC notation", self)
        self.app_learn_abc.setStatusTip("Resources for learning ABC notation")
        self.app_learn_abc.triggered.connect(self._learn_abc)

        self.app_menu.addAction(self.app_learn_abc)

        self.app_menu.addSeparator()
        
        self.app_about = QAction("&About the ABCenatrix", self)
        self.app_about.setStatusTip("Information about the ABCenatrix")
        self.app_about.triggered.connect(self._app_about)

        self.app_menu.addAction(self.app_about)

    def _set_up_filter_menu(self):
        menu = QMenu("&Filter", self)

        self.apply_filter = QAction("&Apply filter…", self)
        self.apply_filter.setStatusTip("Create and apply a filter")
        self.apply_filter.triggered.connect(self._apply_filter)

        menu.addAction(self.apply_filter)
        
        self.clear_filter = QAction("&Clear filter", self)
        self.clear_filter.setStatusTip("Clear filter")
        self.clear_filter.triggered.connect(self._clear_filter)

        menu.addAction(self.clear_filter)

        return menu

    def _fit_width(self, *args, **kwargs):
        self.abc_display.fit_style = fits.FIT_WIDTH
        self.abc_display.repaint()
        self.settings.set("Default fit", "width")

    def _fit_height(self, *args, **kwargs):
        self.abc_display.fit_style = fits.FIT_HEIGHT
        self.abc_display.repaint()
        self.settings.set("Default fit", "height")

    def _fit_all(self, *args, **kwargs):
        self.abc_display.fit_style = fits.FIT_ALL
        self.abc_display.repaint()
        self.settings.set("Default fit", "all")
        
    def _prompt_load(self):
        """Prompt for a file to load"""

        if not self._confirm_discard_changes():
            return
        
        dirname = self.settings.get("Open directory")
            
        filename, accept = QFileDialog.getOpenFileName(
            self,
            "Open Tunebook",
            dirname,    
            "ABC tunebooks (*.abc *.abc.txt)")

        if accept:
            self._load(filename)

    def _load(self, filename):
        """Load a new ABC file"""

        self.settings.set("Open directory", os.path.dirname(filename))

        self.abc_file = AbcTunebook(filename)
        
        self.setWindowTitle(self.abc_file.filename)

        self.title_list.clear()

        for tune in self.abc_file:
            self.title_list.addItem(TuneListItem(tune))

        self.dirty = False

    def _new_tunebook(self, *args, **kwargs):
        """Create a new, empty ABC tunebook"""
        if not self._confirm_discard_changes():
            return

        self.abc_file = AbcTunebook()
        self.title_list.clear()
        self.dirty = False
        

    def _save_tunebook(self, *args, **kwargs):
        self._save()


    def _prompt_save(self):
        """Prompt for a file to load"""
        dirname = self.settings.get("Save directory")
            
        filename, accept = QFileDialog.getSaveFileName(
            self,
            "Save Tunebook",
            dirname,    
            "ABC tunebooks (*.abc *.abc.txt)")

        if accept:
            self._save(filename)
    
    def _save(self, filename=None):
        if not filename:
            if self.abc_file.filename:
                filename = self.abc_file.filename
            else:
                return self._prompt_save()

        self.settings.set("Save directory", os.path.dirname(filename))
        self.abc_file.write(filename)
        self.dirty = False

    def _on_index_change(self, current, previous):
        # try to delete the last temp SVG file
        if self.tmp_svg:
            try:
                os.unlink(self.tmp_svg)
            except:
                pass # oh well

        if current:
            self._current_tune = current.tune
            self.display_current_tune()

    def display_current_tune(self):
        #export the selected tune as an SVG and display it
        tempdir = tempfile.gettempdir()
        self.tmp_svg = os.path.join(tempdir, "%s.svg" % uuid4())
        self.tmp_midi = self.tmp_svg.replace(".svg", ".mid")
        
        self._current_tune.write_svg(self.tmp_svg)
        self._current_tune.write_midi(self.tmp_midi)
        self.abc_display.load(self.tmp_svg)
        if self.midi.playing:
            self.midi.stop()
            
        self.midi.load(self.tmp_midi)
        
    def _print(self, *args, **kwargs):
        # save the fit for display and change to fit the whole page,
        # which is okay for most printers
        old_fit = self.abc_display.fit_style
        self.abc_display.fit_style = fits.FIT_ALL
        
        printDialog = QPrintDialog(self)

        if printDialog.exec_() == QDialog.Accepted:
            pageSize = (printDialog.printer().width(),
                        printDialog.printer().height())
            painter = QPainter()
            painter.begin(printDialog.printer())
            self.abc_display.renderer().render(painter, QRect(0,
                                                              0,
                                                              pageSize[0],
                                                              pageSize[1]))

        # reset the fit for screen display
        self.abc_display.fit_style = old_fit

    def _transpose(self, *args, **kwargs):
        steps, accept = QInputDialog.getInteger(self,
                                                "Transpose Tune",
                                                "Semitones",
                                                value=0,
                                                min=-12,
                                                max=12)

        if accept:
            self._current_tune.transpose(steps)
            self.display_current_tune()
            self.dirty = True

    def _add_tune_to_tunebook(self, *args, **kwargs):
        """Prompt for a tunebook file to add tune to"""
        filename, accept = QFileDialog.getOpenFileName(self,
                                                       "Add to Tunebook",
                                                       os.environ["HOME"],
                                                       "ABC tunebooks (*.abc *.abc.txt)")
        if accept:
            out_tb = AbcTunebook(filename)
            out_tb.append(self._current_tune)
            out_tb.write(filename)

    def _add_tune_to_new_tunebook(self, *args, **kwargs):
        """Prompt for a tunebook file to add tune to"""
        filename, accept = QFileDialog.getSaveFileName(
            self,
            "Create New Tunebook",
            os.path.join(self.settings.get("Save directory"),
                         "new.abc"),
            "ABC tunebooks (*.abc *.abc.txt)")

        if accept:
            if not filename.endswith(".abc"):
                filename = filename + ".abc"

            self.settings.set("Save directory", os.path.dirname(filename))
            
            out_tb = AbcTunebook()
            out_tb.append(self._current_tune)
            out_tb.write(filename)

    def _edit_tune(self, *args, **kwargs):
        dlg = AbcTuneEditor(self.settings, self._current_tune, parent=self)
        accepted = dlg.exec_()
        if accepted:
            self._current_tune.update_from_abc(dlg.tune.content)
            self.display_current_tune()
            self.dirty = True

    def _delete_tune(self, *args, **kwargs):

        if self._confirm("Delete Tune", "Really delete %s?" % self._current_tune.title):
            self.abc_file.remove(self._current_tune)

            self.title_list.clear()

            for tune in self.abc_file:
                self.title_list.addItem(TuneListItem(tune))

            self.dirty = True

    def _new_tune(self, *args, **kwargs):
        dlg = AbcTuneEditor(self.settings, parent=self)
        accepted = dlg.exec_()
        if accepted:
            tune = dlg.tune
            self.abc_file.append(tune)
            item = TuneListItem(tune)
            self.title_list.addItem(item)
            self.title_list.setCurrentItem(item)
            self.display_current_tune()
            self.dirty = True

    def _confirm(self, title, message):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle(title)
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Ok)
        return msgBox.exec_() == QMessageBox.Ok

    def _confirm_discard_changes(self):
        if self.dirty:
            return self._confirm("Discard changes",
                                 "You have unsaved changes.  OK to discard them?")
        else:
            return True

    def _tune_info(self):
        tune = self._current_tune
        show_tune_info(tune, self)
        

    def resizeEvent(self, *args, **kwargs):
        """resize the ABC display to match the new window size"""
        self.abc_display.visible_width, self.abc_display.visible_height = self.scroll_area.size().toTuple()

    def _playback_start(self, *args, **kwargs):
        if self.midi.playing:
            if self.paused:
                self.midi.unpause()
                self.paused = False
            else:
                self.midi.pause()
                self.paused = True
        else:
            self.midi.play()
            self.paused = False

    def _playback_restart(self, *args, **kwargs):
        self.midi.stop()
        self.paused = False

    def _apply_filter(self, *args, **kwargs):
        dlg = FilterDialog(self)
        accepted = dlg.exec_()
        if accepted:

            filter = dlg.filter
            filter.apply(self.title_list)
                    

    def _clear_filter(self, *args, **kwargs):
        for i in range(self.title_list.count()):
            item = self.title_list.item(i)
            item.setHidden(False)

    def _app_settings(self, *args, **kwargs):
        dlg = SettingsDialog(self.settings)
        accepted = dlg.exec_()
        #shouldn't have to do anything

    def _app_about(self, *args, **kwargs):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("About the ABCenatrix")
        msgBox.setInformativeText(about_text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        return msgBox.exec_() == QMessageBox.Ok

    def _about_abc(self, *args, **kwargs):
        wb.open("http://abcnotation.com/about#abc")

    def _learn_abc(self, *args, **kwargs):
        wb.open("http://abcnotation.com/learn")

