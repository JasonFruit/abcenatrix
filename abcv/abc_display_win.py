# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import os
import tempfile
from uuid import uuid4

# Import the core and GUI elements of Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKit import *
# from PySide.QtCore import *
# from PySide.QtGui import *
# from PySide.QtWebKit import *
from abcv.scrollable_svg import fits

def _make_tmp_fn():
    tempdir = tempfile.gettempdir()
    return os.path.join(tempdir, "%s.svg" % uuid4())

class AbcDisplay(QWidget):
    def __init__(self, tune=None, parent=None, fit=fits.FIT_ALL):
        QWidget.__init__(self, parent=parent)

        
        self.pages = 1
        self.page = 1
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        width, height = self.size().width(), self.size().height()

        self.svg = QWebView()

        self.layout.addWidget(self.svg, stretch=1.0)

        self.button_hbox = QHBoxLayout()
        self.layout.addLayout(self.button_hbox, stretch=0.0)

        self.button_hbox.addStretch()

        self.page_back_button = QPushButton("<")
        self.page_back_button.clicked.connect(self.prev_page)
        self.page_label = QLabel(str(self.page))
        self.page_forward_button = QPushButton(">")
        self.page_forward_button.clicked.connect(self.next_page)

        self.button_hbox.addWidget(self.page_back_button, stretch=0.0)
        self.button_hbox.addWidget(self.page_label, stretch=0.2)
        self.button_hbox.addWidget(self.page_forward_button, stretch=0.0)

        self.button_hbox.addStretch()

        self.show_or_hide_pages()

        if tune:
            self.tune = tune
        else:
            self._tune = None

        self.fit_style = fit

    @property
    def tune(self):
        return self._tune

    @tune.setter
    def tune(self, new_val):
        self._tune = new_val
        self.refresh()

    @property
    def fit_style(self):
        return self._fit_style

    @fit_style.setter
    def fit_style(self, new_val):
        self._fit_style = new_val

        if self._fit_style == fits.FIT_WIDTH:
            self.svg.setZoomFactor(self.svg.width() / (8.5 * 72.0) * 0.75)
        else:
            self.svg.setZoomFactor(self.svg.height() / (11.5 * 72.0) * 0.75)
            
    def show_or_hide_pages(self):
        for wid in [self.page_back_button,
                    self.page_forward_button,
                    self.page_label]:
            if self.pages > 1:
                wid.show()
            else:
                wid.hide()

    def _load_svg(self, fn):
        svg_bs = open(fn, "rb").read()
        self.svg.setContent(svg_bs, "image/svg+xml")
                
    def refresh(self):
        if self._tune:
            self._svg_fn = _make_tmp_fn()
            self.pages = self._tune.write_svg(self._svg_fn, page=self.page)
            self.show_or_hide_pages()
            self._load_svg(self._svg_fn)
            self.show_page_num()

    def show_page_num(self):
        self.page_label.setText("%s of %s" % (self.page, self.pages))

    def next_page(self, *args, **kwargs):
        if self.page < self.pages:
            self.page += 1
            self.refresh()

    def prev_page(self, *args, **kwargs):
        if self.page > 1:
            self.page -= 1
            self.refresh()

    def clear(self):
        self.svg.setContent("")
