import os, sys
import codecs
from uuid import uuid4
from tunebook import AbcTune, AbcTunebook
from scrollable_svg import ScrollableSvgWidget, fits

from PySide.QtCore import *
from PySide.QtGui import *

qt_app = QApplication(sys.argv)

class TuneListItem(QListWidgetItem):
    def __init__(self, tune):
        QListWidgetItem.__init__(self, tune.title)
        self.tune = tune

class AbcViewer(QMainWindow):
    def __init__(self, filename=None):
        QMainWindow.__init__(self)

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

        # the tune is in an SVG display widget that changes height
        # based on fit parameters
        self.abc_display = ScrollableSvgWidget(height,
                                               width,
                                               fit_style=fits.FIT_ALL)

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
        self.file_menu = self.menuBar().addMenu("&File")
        self.view_menu = self.menuBar().addMenu("Vie&w")
        self.tune_menu = self.menuBar().addMenu("&Tune")
        
        # open and print go in the file menu
        self.file_open = QAction("&Open", self)
        self.file_open.setShortcut("Ctrl+O")
        self.file_open.setStatusTip("Open an ABC file")
        self.file_open.triggered.connect(self._prompt_load)

        self.file_print = QAction("&Print", self)
        self.file_print.setShortcut("Ctrl+P")
        self.file_print.setStatusTip("Print a tune")
        self.file_print.triggered.connect(self._print)

        self.file_menu.addAction(self.file_open)
        self.file_menu.addAction(self.file_print)

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

        self.tune_transpose = QAction("Transpose", self)
        self.tune_transpose.triggered.connect(self._transpose)

        self.tune_menu.addAction(self.tune_transpose)

    def _fit_width(self, *args, **kwargs):
        self.abc_display.fit_style = fits.FIT_WIDTH
        self.abc_display.repaint()

    def _fit_height(self, *args, **kwargs):
        self.abc_display.fit_style = fits.FIT_HEIGHT
        self.abc_display.repaint()

    def _fit_all(self, *args, **kwargs):
        self.abc_display.fit_style = fits.FIT_ALL
        self.abc_display.repaint()
        
    def _prompt_load(self):
        """Prompt for a file to load"""
        filename = QFileDialog.getOpenFileName(self,
                                               "Open Tunebook",
                                               "~",
                                               "ABC files (*.abc *.abc.txt)")[0]
        self._load(filename)

    def _load(self, filename):
        """Load a new ABC file"""
        self.abc_file = AbcTunebook(filename)
        self.setWindowTitle(self.abc_file.filename)

        self.title_list.clear()
        
        for tune in sorted(self.abc_file, key=lambda t: t.title):
            self.title_list.addItem(TuneListItem(tune))

    def _on_index_change(self, current, previous):
        # try to delete the last temp SVG file
        if self.tmp_svg:
            try:
                os.unlink(self.tmp_svg)
            except:
                pass # oh well

        self._current_tune = current.tune
        self.display_current_tune()

    def display_current_tune(self):
        #export the selected tune as an SVG and display it
        self.tmp_svg = "/tmp/%s.svg" % uuid4()
        self._current_tune.write_svg(self.tmp_svg)
        self.abc_display.load(self.tmp_svg)

    def _print(self, *args, **kwargs):
        # TODO: fit the display to the real page dimensions instead of
        # this approximation
        
        # save the fit for display and change to fit the whole page,
        # which is okay for most printers
        old_fit = self.abc_display.fit_style
        self.abc_display.fit_style = fits.FIT_ALL
        
        printDialog = QPrintDialog(self)

        if printDialog.exec_() == QDialog.Accepted:
            painter = QPainter()
            painter.begin(printDialog.printer())
            self.abc_display.render(painter, QPoint())

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
            self._current_tune = self._current_tune.copy()
            self._current_tune.transpose(steps)
            self.display_current_tune()

    def resizeEvent(self, *args, **kwargs):
        """resize the ABC display to match the new window size"""
        self.abc_display.visible_width, self.abc_display.visible_height = self.scroll_area.size().toTuple()


# if there's a filename passed in as an argument, load it; otherwise
# start empty
try:
    fn = sys.argv[1]
    app = AbcViewer(fn)
except:
    app = AbcViewer()
    
app.showMaximized()

# Run the application's event loop
qt_app.exec_()
