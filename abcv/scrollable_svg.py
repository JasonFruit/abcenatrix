# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtSvg import QSvgWidget

class Fits(object):
    def __init__(self):
        self.FIT_ALL = 1
        self.FIT_WIDTH = 2
        self.FIT_HEIGHT = 3

fits = Fits()

class ScrollableSvgWidget(QSvgWidget):
    def __init__(self,
                 visible_height,
                 visible_width,
                 fit_style=fits.FIT_ALL):
        QSvgWidget.__init__(self)
        self.fit_style = fit_style
        self.visible_height = visible_height
        self.visible_width = visible_width

    def clear(self):
        self.load(bytes("", "utf-8"))

    def paintEvent(self, paint_event):
        painter = QPainter(self)
        
        default_width, default_height = self.renderer().defaultSize().toTuple()
        widget_width = self.visible_width

        left = 0
        top = 0

        if self.fit_style == fits.FIT_ALL or self.fit_style == fits.FIT_HEIGHT:
            scale_by = self.visible_height / default_height
            new_width = default_width * scale_by
            new_size = QSize(widget_width, self.visible_height)
            self.resize(new_size)
            self.renderer().render(painter,
                                   QRect(left,
                                         top,
                                         new_width,
                                         self.visible_height))
            
        elif self.fit_style == fits.FIT_WIDTH:
            scale_by = widget_width / default_width
            new_height = default_height * scale_by
            new_size = QSize(widget_width, new_height)
            self.resize(new_size)
            self.renderer().render(painter,
                                   QRect(left,
                                         top,
                                         widget_width,
                                         new_height))
