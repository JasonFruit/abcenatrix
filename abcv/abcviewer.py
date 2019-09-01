# -*- coding: utf-8 -*-

# be futuristic!  That is, basically use Python 3.
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import os, platform, sys, tempfile, codecs
from uuid import uuid4
import webbrowser as wb

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtPrintSupport import *

from abcv.tunebook import AbcTune, AbcTunebook, information_fields
from abcv.scrollable_svg import fits

# TODO: change this back to abcv.abc_display when fixed
from abcv.abc_display_win import AbcDisplay

from abcv.tune_editor import AbcTuneEditor
from abcv.filter_dialog import FilterDialog
from abcv.settings_dialog import SettingsDialog, ToolSettingsDialog
from abcv.about import about_text
from abcv.midi_mixin import MidiMixin
import abcv.tools as tools

ps_to_pdf_cmd = '%s -o %s -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress -dHaveTrueTypes=true -dEmbedAllFonts=true -dSubsetFonts=false -c ".setpdfwrite <</NeverEmbed [ ]>> setdistillerparams" -f %s'

class TuneListItem(QListWidgetItem):
    """A QListItem that can carry a tune"""
    def __init__(self, tune):
        QListWidgetItem.__init__(self, tune.title)
        self.tune = tune

def show_tune_info(tune, parent=None):
    """Show a dialog box with the information fields of an ABC tune"""
    
    message = []
    defined = information_fields.keys()
    
    for k in tune.keys():
        if k in defined:
            message.append("%s: %s" % (information_fields[k],
                                       "\n".join(tune[k])))
            
    dlg = QMessageBox(parent)
    dlg.setText("\n".join(message))
    
    return dlg.exec_()

class Application(QMainWindow, MidiMixin):
    """The main ABCenatrix application window"""
    def __init__(self, settings, filename=None):
        QMainWindow.__init__(self)
        
        MidiMixin.__init__(self, settings.get("MIDI port"))
            
        self.play_icon  = QIcon(
            "/usr/share/icons/Adwaita/48x48/actions/media-playback-start.png")
        self.pause_icon = QIcon(
            "/usr/share/icons/Adwaita/48x48/actions/media-playback-pause.png")
        self.stop_icon = QIcon(
            "/usr/share/icons/Adwaita/48x48/actions/media-playback-stop.png")


        self.setWindowIcon(
            QIcon(os.path.join(os.path.dirname(__file__),
                               "/usr/share/pixmaps/abcviewer.png")))

        # to the extent that there is a file, it starts unchanged
        self._dirty = False
        
        self.settings = settings

        # no tune 'til there's a tune
        self._current_tune = None

        # add menus and their contents
        self._setUpMenus()

        # there must be one main widget, so we need this one; we'll
        # add the hbox layout to it
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # the main layout; title list on the left, scrollable tune
        # display on the right
        self.tunebook_hbox = QHBoxLayout()
        self.central_widget.setLayout(self.tunebook_hbox)

        # holds the title list and its associated controls
        self.title_vbox = QVBoxLayout()

        # a menu button for title-list filter actions
        self.title_filter_btn = QPushButton("&Filter")
        self.filter_menu = self._set_up_filter_menu()
        self.title_filter_btn.setMenu(self.filter_menu)

        self.title_vbox.addWidget(self.title_filter_btn, stretch=0)

        # the list of tune titles
        self.title_list = QListWidget()
        self.title_list.currentItemChanged.connect(self._on_index_change)
        
        self.title_vbox.addWidget(self.title_list, stretch=1)

        self.title_move_hbox = QHBoxLayout()

        self.title_up_btn = QPushButton("↑")
        self.title_up_btn.setToolTip("Move selected item up")
        self.title_up_btn.clicked.connect(self._move_tune_up)
        self.title_down_btn = QPushButton("↓")
        self.title_down_btn.setToolTip("Move selected item down")
        self.title_down_btn.clicked.connect(self._move_tune_down)

        self.title_move_hbox.addWidget(self.title_up_btn)
        self.title_move_hbox.addWidget(self.title_down_btn)

        self.title_vbox.addLayout(self.title_move_hbox, stretch=0)
        
        
        self.tunebook_hbox.addLayout(self.title_vbox, stretch=0) # fixed width

        self.viewer_vbox = QVBoxLayout()
        
        # # get the width and height of the window
        # width, height = self.size().toTuple()

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
        self.abc_display = AbcDisplay(parent=self, fit=fit)

        # stretches vertically to fill screen
        self.viewer_vbox.addWidget(self.abc_display, stretch=1.0)

        self.midi_control_hbox = QHBoxLayout()

        self.midi_control_hbox.addStretch()

        self.scale_lbl = QLabel("Speed: 100%")
        self.midi_control_hbox.addWidget(self.scale_lbl, stretch=0.0)
        
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(25)
        self.scale_slider.setMaximum(400)
        self.scale_slider.setValue(100)
        self.scale_slider.setMaximumWidth(120)
        self.scale_slider.valueChanged.connect(self._scale_changed)
        
        self.midi_control_hbox.addWidget(self.scale_slider)

        self.play_pause_btn = QPushButton(self.play_icon, "")
        self.play_pause_btn.clicked.connect(self._playback_start)
        self.midi_control_hbox.addWidget(self.play_pause_btn)

        self.stop_btn = QPushButton(self.stop_icon, "")
        self.stop_btn.clicked.connect(self._playback_restart)
        self.midi_control_hbox.addWidget(self.stop_btn)

        self.viewer_vbox.addLayout(self.midi_control_hbox, stretch=0.0)

        # viewer vbox stretches horizontally to fill remaining space
        self.tunebook_hbox.addLayout(self.viewer_vbox, stretch=1.0)
        
        self.tmp_svg = None

        # if a filename was passed in, load it
        if filename:
            self._load(filename)
        else:
            self._new_tunebook()

        if not self.settings.get("MIDI port"):
            self._choose_midi_port()

        # try to update empty tool paths with something on the PATH
        for command in tools.commands:
            if not self.settings.get("%s location" % command):
                tmp_path = tools.default_tool_path(command)
                if tmp_path:
                    self.settings.set("%s location" % command,
                                      tmp_path)
                    
        # if there are any tools left without paths
        if "" in map(self.settings.get,
                     ["%s location" % cmd
                      for cmd in tools.commands]):
            tsd = ToolSettingsDialog(self.settings)
            tsd.exec_()

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, val):
        self._dirty = val

        # this is a property because we need to alter the window title
        # to indicate unsaved changes

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
        """Add the menus to the menu bar and fill them with a cornucopia of
        choices"""
        
        # top-level menus
        self.tunebook_menu = self.menuBar().addMenu("Tune&book")
        self.view_menu = self.menuBar().addMenu("Vie&w")
        self.tune_menu = self.menuBar().addMenu("&Tune")
        self.playback_menu = self.menuBar().addMenu("&Playback")
        self.app_menu = self.menuBar().addMenu("&ABCenatrix")
        
        def addAction(menu, label, shortcut, handler):
            """A helper function to add actions to menus"""
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            menu.addAction(action)
            return action

        # lines get a little long here but are unwrapped since they're
        # stereotyped and probably won't require frequent reading or
        # edits

        
        # Tunebook menu choices
        self.tunebook_open = addAction(self.tunebook_menu, "&Open", "Ctrl+O", self._prompt_load)
        self.tunebook_save = addAction(self.tunebook_menu, "&Save", "Ctrl+S", self._save_tunebook)
        self.tunebook_new = addAction(self.tunebook_menu, "&New", "Ctrl+Shift+N", self._new_tunebook)
        self.tunebook_close = addAction(self.tunebook_menu, "&Close", "Ctrl+W", self._new_tunebook)
        self.tunebook_revert = addAction(self.tunebook_menu, "&Revert", "", self._revert_tunebook)
        
        self.tunebook_export_menu = self.tunebook_menu.addMenu("E&xport tunebook:")
        self.tunebook_export_pdf = addAction(self.tunebook_export_menu, "As P&DF", "", self._export_pdf)
        self.tunebook_export_ps = addAction(self.tunebook_export_menu, "As Po&stscript", "", self._export_ps)
        
        self.tunebook_move_up = addAction(self.tunebook_menu, "Move tune &up", "Ctrl+Up", self._move_tune_up)
        self.tunebook_move_down = addAction(self.tunebook_menu, "Move tune &down", "Ctrl+Down", self._move_tune_down)
        
        # fit choices go in a Fit submenu of the view menu
        self.view_fit_menu = self.view_menu.addMenu("Fit")
        
        self.view_fit_width = addAction(self.view_fit_menu, "Width", "", self._fit_width)
        self.view_fit_height = addAction(self.view_fit_menu, "Height", "", self._fit_height)
        self.view_fit_all = addAction(self.view_fit_menu, "All", "", self._fit_all)

        # tune menu choices
        self.tune_transpose = addAction(self.tune_menu, "Tra&nspose…", "", self._transpose)
        self.tune_edit = addAction(self.tune_menu, "&Edit the current tune", "Ctrl+E", self._edit_tune)
        self.tune_new_tune = addAction(self.tune_menu, "&New tune", "Ctrl+N", self._new_tune)
        self.tune_delete_tune = addAction(self.tune_menu, "&Delete tune", "Ctrl+D", self._delete_tune)

        # options to add a tune to a different tunebook go in a submenu of the tune menu
        self.tune_add_to_menu = self.tune_menu.addMenu("&Add to:")
        
        self.tune_add_to_book = addAction(self.tune_add_to_menu, "E&xisting tunebook…", "", self._add_tune_to_tunebook)
        self.tune_add_to_new_book = addAction(self.tune_add_to_menu, "&New tunebook…", "", self._add_tune_to_new_tunebook)

        # rest of the tune menu choices
        self.tune_print = addAction(self.tune_menu, "&Print", "Ctrl+P", self._print)
        self.tune_info = addAction(self.tune_menu, "&Info", "Ctrl+I", self._tune_info)

        # playback menu choices
        self.playback_start = addAction(self.playback_menu, "&Start/Stop", " ", self._playback_start)
        self.playback_restart = addAction(self.playback_menu, "&Jump to start", "Ctrl+J", self._playback_restart)
        self.playback_port = addAction(self.playback_menu, "&Choose MIDI port", "", self._choose_midi_port)

        # app menu choices
        self.app_settings = addAction(self.app_menu, "&Settings…", "", self._app_settings)
        self.app_menu.addSeparator()
        self.app_about_abc = addAction(self.app_menu, "&About ABC notation", "", self._about_abc)
        self.app_learn_abc = addAction(self.app_menu, "&Learn ABC notation", "", self._learn_abc)
        self.app_menu.addSeparator()
        self.app_about = addAction(self.app_menu, "&About the ABCenatrix", "", self._app_about)

    def _set_up_filter_menu(self):
        """Set up the filter menu, which is attached to a button at the top of
        the title list"""
        
        menu = QMenu("&Filter", self)

        self.apply_filter = QAction("&Apply filter…", self)
        self.apply_filter.triggered.connect(self._apply_filter)

        menu.addAction(self.apply_filter)
        
        self.clear_filter = QAction("&Clear filter", self)
        self.clear_filter.triggered.connect(self._clear_filter)

        menu.addAction(self.clear_filter)

        return menu

    def _do_fit(self, fit, fit_dsc):
        """Fit the SVG display to the specified fit and save it in the
        settings"""
        
        self.abc_display.fit_style = fit
        self.abc_display.refresh()
        self.settings.set("Default fit", fit_dsc)
        
    def _fit_width(self, *args, **kwargs):
        self._do_fit(fits.FIT_WIDTH, "width")

    def _fit_height(self, *args, **kwargs):
        self._do_fit(fits.FIT_HEIGHT, "height")

    def _fit_all(self, *args, **kwargs):
        self._do_fit(fits.FIT_ALL, "all")
        
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

        # store the directory to start there next time
        self.settings.set("Open directory", os.path.dirname(filename))

        self.abc_file = AbcTunebook(filename)

        self._refresh_title_list()

        try:
            self.title_list.setCurrentItem(self.title_list.item(0))
        except:
            pass # if it can't be done, we don't care why

        self.dirty = False

    def _refresh_title_list(self):
        self.title_list.clear()

        for tune in self.abc_file:
            self.title_list.addItem(TuneListItem(tune))

    def _select_tune_title(self, tune):
        for i in range(self.title_list.count()):
            if self.title_list.item(i).tune == tune:
                self.title_list.setCurrentItem(self.title_list.item(i))
                return

    def _new_tunebook(self, *args, **kwargs):
        """Create a new, empty ABC tunebook"""
        
        if not self._confirm_discard_changes():
            return

        self.abc_file = AbcTunebook()
        self.title_list.clear()
        self.abc_display.clear()
        self.dirty = False

    def _revert_tunebook(self, *args, **kwargs):
        """Reload the tunebook from its original file"""

        if self._confirm_discard_changes():
            self._load(self.abc_file.filename)
        

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
        # if there's no filename either passed or in the tunebook,
        # prompt for one, then save
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

        # if you've changed to a tune, show it
        if current:
            self._current_tune = current.tune
            self.display_current_tune()

    def display_current_tune(self):
        """Show the current tune"""

        self.abc_display.tune = self._current_tune
        tempdir = tempfile.gettempdir()
        
        # export the tune as MIDI to get ready to play it
        self.tmp_midi = os.path.join(tempdir, "%s.mid" % uuid4())
        self._current_tune.write_midi(
            self.tmp_midi,
            midi_program=self.settings.get("MIDI instrument"))
        
        # if you're still playing the previous tune, stop that
        if self.midi.playing:
            self.midi.stop()

        # prepare the mixer to play the new MIDI file
        if os.path.exists(self.tmp_midi):
            self.load_midi(self.tmp_midi)
        
    def _print(self, *args, **kwargs):
        # save the fit for display and change to fit the whole page,
        # which is okay for most printers
        old_fit = self.abc_display.fit_style
        self.abc_display.fit_style = fits.FIT_ALL
        
        printDialog = QPrintDialog(self)

        if printDialog.exec_() == QDialog.Accepted:
            painter = QPainter(printDialog.printer())
            self.abc_display.svg.render(painter)
            painter.end()
            # self.abc_display.svg.print(printDialog.printer())

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
        dlg.showMaximized()
        accepted = dlg.exec_()
        if accepted:
            self._current_tune.update_from_abc(dlg.tune.content)
            self.display_current_tune()
            self.dirty = True

    def _delete_tune(self, *args, **kwargs):

        if self._confirm("Delete Tune", "Really delete %s?" % self._current_tune.title):
            index = self.abc_file.index(self._current_tune)
            
            self.abc_file.remove(self._current_tune)
            self._refresh_title_list()
            
            try:
                self._select_tune_title(self.abc_file[index])
            except IndexError:
                try:
                    self._select_tune_title(self.abc_file[0])
                except IndexError:
                    self.abc_display.clear()

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
        msgBox.setText(message)
        
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
        

    def _playback_start(self, *args, **kwargs):
        self.toggle_play()
        
        if self.paused:
            self.play_pause_btn.setIcon(self.play_icon)
        else:
            self.play_pause_btn.setIcon(self.pause_icon)

    def _playback_restart(self, *args, **kwargs):
        self.restart()
        self.play_pause_btn.setIcon(self.play_icon)
        
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

    def _app_about(self, *args, **kwargs):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("About the ABCenatrix")
        msgBox.setText(about_text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        return msgBox.exec_() == QMessageBox.Ok # 'cause we care?

    def _about_abc(self, *args, **kwargs):
        wb.open("http://abcnotation.com/about#abc")

    def _learn_abc(self, *args, **kwargs):
        wb.open("http://abcnotation.com/learn")

    def _move_tune_up(self, *args, **kwargs):
        tune = self._current_tune
        if self.abc_file.move(self._current_tune, -1):
            self._refresh_title_list()
            self._select_tune_title(tune)
            self.dirty = True

    def _move_tune_down(self, *args, **kwargs):
        tune = self._current_tune
        if self.abc_file.move(self._current_tune, 1):
            self._refresh_title_list()
            self._select_tune_title(tune)
            self.dirty = True        
        
    def closeEvent(self, event):
        if self._confirm_discard_changes():
            event.accept()
        else:
            event.ignore()

    def _scale_changed(self):
        scale = (self.scale_slider.value() / 100.)
        self.midi.scale = scale
        self.scale_lbl.setText("Speed: %s%%" % self.scale_slider.value())

    def _choose_midi_port(self):
        ports = self.midi.ports

        port, ok = QInputDialog.getItem(self,
                                        "Choose MIDI Port",
                                        "Port:",
                                        ports,
                                        ports.index(self.midi.port_name))

        if ok:
            self.settings.set("MIDI port", port)
            self.midi.port_name = port

    def _prompt_export(self, format):
        """Prompt for a file to load"""
        dirname = self.settings.get("Save directory")
            
        filename, accept = QFileDialog.getSaveFileName(
            self,
            "Export Tunebook",
            dirname,    
            "%s files (*.%s" % (format.upper(), format.lower()))

        if not filename.endswith("." + format.lower()):
            filename += "." + format.lower()

        return accept, filename
    
    def _export_pdf(self, *args, **kwargs):
        accept, filename = self._prompt_export("pdf")
        
        tmp_fn = str(uuid4()) + ".ps"
        
        if accept:
            cmd = """%s -O "%s" "%s" """ % (self.settings.get("abcm2ps location"),
                                            tmp_fn,
                                            self.abc_file.filename)
        
            os.system(cmd)
            cmd = ps_to_pdf_cmd % (self.settings.get("gs location"),
                                       filename,
                                       tmp_fn)
            os.system(cmd)
            os.system("""rm "%s" """ % tmp_fn)

    def _export_ps(self, *args, **kwargs):
        accept, filename = self._prompt_export("ps")
        cmd = """%s -O "%s" "%s" """ % (self.settings.get("abcm2ps location"),
                                        filename,
                                        self.abc_file.filename)
        if accept:
            os.system(cmd)
            
