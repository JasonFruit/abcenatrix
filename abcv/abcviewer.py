import os, sys
import codecs
from uuid import uuid4
from abcv.tunebook import AbcTune, AbcTunebook, information_fields
from abcv.scrollable_svg import ScrollableSvgWidget, fits
from abcv.tune_editor import AbcTuneEditor

from PySide.QtCore import *
from PySide.QtGui import *

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

class AbcViewer(QMainWindow):
    def __init__(self, settings, filename=None):
        QMainWindow.__init__(self)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__),
                                              "/usr/share/pixmaps/abcviewer.png")))

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
        
        self.title_list = QListWidget()
        self.title_list.currentItemChanged.connect(self._on_index_change)
        self.tunebook_hbox.addWidget(self.title_list, stretch=0) # fixed width

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
            
    def _setUpMenus(self):
        # top-level menus
        self.file_menu = self.menuBar().addMenu("Tune&book")
        self.view_menu = self.menuBar().addMenu("Vie&w")
        self.tune_menu = self.menuBar().addMenu("&Tune")
        
        # open and save go in the file menu
        self.file_open = QAction("&Open", self)
        self.file_open.setShortcut("Ctrl+O")
        self.file_open.setStatusTip("Open a tunebook")
        self.file_open.triggered.connect(self._prompt_load)

        self.file_save = QAction("&Save", self)
        self.file_save.setShortcut("Ctrl+S")
        self.file_save.setStatusTip("Save the tunebook")
        self.file_save.triggered.connect(self._save_tunebook)

        self.file_menu.addAction(self.file_open)
        self.file_menu.addAction(self.file_save)

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
        self.tune_add_to_new_book.setStatusTip("Create a new ABC file with only this tune")
        self.tune_add_to_new_book.triggered.connect(self._add_tune_to_new_tunebook)

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
        dirname = self.settings.get("Open directory")
            
        filename, accept = QFileDialog.getOpenFileName(self,
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

    def _save_tunebook(self, *args, **kwargs):
        self._save()
        
    def _save(self, filename=None):
        if not filename:
            filename = self.abc_file.filename
        print(filename)
        self.abc_file.write(filename)

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
        self.tmp_svg = "/tmp/%s.svg" % uuid4()
        self._current_tune.write_svg(self.tmp_svg)
        self.abc_display.load(self.tmp_svg)

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

    def _delete_tune(self, *args, **kwargs):

        if self._confirm("", "Really delete %s?" % self._current_tune.title):
            self.abc_file.remove(self._current_tune)

            self.title_list.clear()

            for tune in self.abc_file:
                self.title_list.addItem(TuneListItem(tune))

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

    def _confirm(self, title, message):
        msgBox = QMessageBox(self)
        msgBox.setText(title)
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Ok)
        return msgBox.exec_() == QMessageBox.Ok

    def _tune_info(self):
        tune = self._current_tune
        show_tune_info(tune, self)
        

    def resizeEvent(self, *args, **kwargs):
        """resize the ABC display to match the new window size"""
        self.abc_display.visible_width, self.abc_display.visible_height = self.scroll_area.size().toTuple()

