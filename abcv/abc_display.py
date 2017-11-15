# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import os
import tempfile
from uuid import uuid4

# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *
from abcv.scrollable_svg import ScrollableSvgWidget, fits

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

        width, height = self.size().toTuple()

        self.svg = ScrollableSvgWidget(height, width, fit_style=fits.FIT_WIDTH)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Light)
        self.scroll_area.setWidget(self.svg)

        self.layout.addWidget(self.scroll_area, stretch=1.0)

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

    def resizeEvent(self, *args, **kwargs):
        self.svg.visible_width, self.svg.visible_height = self.size().toTuple()
        self.refresh()
        
    @property
    def fit_style(self):
        return self.svg.fit_style

    @fit_style.setter
    def fit_style(self, new_value):
        self.svg.fit_style = new_value
        
    @property
    def tune(self):
        return self._tune

    @tune.setter
    def tune(self, new_val):
        self._tune = new_val
        self.refresh()

    def show_or_hide_pages(self):
        for wid in [self.page_back_button,
                    self.page_forward_button,
                    self.page_label]:
            if self.pages > 1:
                wid.show()
            else:
                wid.hide()
                
    def refresh(self):
        self._svg_fn = _make_tmp_fn()
        self.pages = self._tune.write_svg(self._svg_fn, page=self.page)
        self.show_or_hide_pages()
        self.svg.load(self._svg_fn)
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

if __name__ == "__main__":
    from tunebook import *
    abc = """X:1
T:The Bonnie Lass o' Bon-Accord
T: From Logie Collection
M:4/4
L:1/16
Q:1/4=64
Z: Jason R. Fruit <JasonFruit@gmail.com>
K:A
!f!E2 | A3B {AB}c3B .A2.A,2C2E2 | !2!A{BA}G!<(!(A!3!f) ec{c}B!<)!A !>(!{A}B4-B3!>)!c | A3B {AB}c3B .A2.C2.E2.=G2 |
(FDFA) (GE!1!G!3!B) !2!A4-A2 :| (3("heroic"efg) | (!>!a3!tenuto!c) (d2f2) .e2.A2 !0!a2(!4!gf) | .e2.A2 (fe)(dc) {c}B4-B2 (3(!<(!ef!<)!g) |
a3c d2f2 e2A2 a2 "plaintive"=G2 | (FDFA) (GEGB) A4-A2 (3(efg) | (a3!tenuto!c) (d2f2) .e2.A2 a2(gf) |
.e2.A2 {Ag}(fe)(dc) {c}B4-B3c | (A,CEA !4!.c3)!3!.B .A2.C2.E2.=G2 | (FDFA) (GE!1!G!3!B) A4-A2 ||
"VAR"!p!E2 | {AB}(AGAB) {AB}(cBAG) .A (A,B,C DEFG) | (AGAf) (ec{c}BA) ({A}B4!tenuto!B3c) | !f!(AGAB) cBAG .A (A,B,!1!C DEF!0!=G) |
(FDFA) GEGB A4-A2 :| (3!<(!(ef!<)!g) | !>!!>(!a.g.f.e .d.!>)!c.B.A eAcA !>!a(GA).B | cAeA aedc {c}(B4 !tenuto!B2) (3(!<(!ef!<)!g) |
.a.g.f.e .d.c.B.A eAcA !0!a(GA=G) | (FDFA) (GEGB) A4 A2 (3(efg | !>(!a).g.f.!>)!e .d.c.B.A eAcA a2(gf)
eG(Aa) (fe)(dc) {c}B4-B3c | (A,CEA "_7 down"c!4!e!4!!0!a)(g "_9 up"aecA G!4!AE=G) | ("_rall."FDF!2!A G!4!f)(!3!!fermata!eG) {G}"_3rd Corde"A4-A2 ||
K:Aminor
!p!"_sadly""^Minor."E2 | A3B {AB}c3B A2A,2C2E2 | (A^GAB cAdc) (B4!tenuto!B2)E2 | A3Bc3B "^2nd"A2c2d2f2 & x8 A2C2D2F2 |
({ef}ed"^3rd Corde"ef) (e2^G2) A4-A2 & ({EF}EDEF) (EDCB,) A,4-A,2 :| (3(e^f^g) | (a3=g)(.=f2.e2) .f2.e2.d2.c2 | (cBAB cAdc) B4-B2 (3(e^f^g) |
%page2
a3"""
    tune = tune_from_abc(abc)
    qa = QApplication([])
    app = AbcDisplay(tune=tune)
    app.showMaximized()
    qa.exec_()

        

