# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

from PySide.QtCore import *
from PySide.QtGui import *
from abcv.tunebook import information_fields

_good_chars = "abcdefghijklmnopqrstuvwxyz "

def _only_good_chars(s):
    return "".join([c for c in s.lower()
                    if c in _good_chars]).strip()

def _clean_patterns(pat):
    return _only_good_chars(pat).split(" ")

class FilterItem(object):
    def __init__(self, key, pattern):
        self.key = key
        self.patterns = _clean_patterns(pattern)
    def match(self, tune):
        
        if self.key == "*":
            value = _only_good_chars(tune.content)
        else:
            try:
                value = _only_good_chars(" ".join(tune[self.key]))
            except KeyError:
                value = ""
                
        results = [(pattern in value)
                   for pattern in self.patterns]
        
        return not (False in results)

class Filter(list):
    def __init__(self):
        list.__init__(self)

    def apply(self, list_widget):
        self.clear(list_widget)

        for filter in self:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if not filter.match(item.tune):
                        item.setHidden(True)

    def clear(self, list_widget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setHidden(False)

    def __repr__(self):
        return " and \n".join(["%s: %s" % (item.key, " ".join(item.patterns))
                               for item in self])

        

class FilterDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent)
        self.setMinimumSize(QSize(600, 400))
        self.setModal(True)

        self.filter = Filter()
        
        self.set_up()

    def set_up(self):

        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.vbox.addWidget(QLabel("Show only tunes where:"), stretch=0)

        self.filter_dsc_label = QLabel("")
        self.filter_dsc_label.setMinimumSize(QSize(600, 250))
        self.vbox.addWidget(self.filter_dsc_label, stretch=1)

        self.new_filter_hbox = QHBoxLayout()
        self.vbox.addLayout(self.new_filter_hbox, stretch=0)
        
        self.field_list = QComboBox()

        self.field_list.addItem("Entire tune")

        for dsc in sorted([information_fields[k] for k in information_fields.keys()]):
            self.field_list.addItem(dsc)

        self.new_filter_hbox.addWidget(self.field_list, stretch=0)

        self.pattern_input = QLineEdit()
        self.new_filter_hbox.addWidget(self.pattern_input, stretch=1)

        self.add_filter_btn = QPushButton("&Add to filter")
        self.add_filter_btn.clicked.connect(self._add_to_filter)
        
        self.new_filter_hbox.addWidget(self.add_filter_btn, stretch=0)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.vbox.addWidget(self.buttons)

    def _add_to_filter(self, *args, **kwargs):
        print(self.field_list.currentText())
        
        key = "*"
        
        for k in information_fields.keys():
            if information_fields[k] == self.field_list.currentText():
                key = k

        self.filter.append(FilterItem(key, self.pattern_input.text()))

        self.filter_dsc_label.setText(repr(self.filter))







if __name__ == "__main__":
    qt_app = QApplication([])
    app = FilterDialog()
    accepted = app.exec_()
    if accepted:
        print(accepted, app.filter)
        exit()
    else:
        exit()
    qt_app.exec_()

