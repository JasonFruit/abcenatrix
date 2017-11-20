# coding=utf-8

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import os
import codecs
import tempfile
from copy import deepcopy
from subprocess import check_output

information_fields = {
    "X": "Reference number",
    "T": "Tune title",
    "C": "Composer",
    "O": "Origin",
    "A": "Author of lyrics",
    "M": "Meter",
    "L": "Unit note length",
    "Q": "Tempo",
    "P": "Parts",
    "R": "Rhythm",
    "Z": "Transcriber",
    "N": "Notes",
    "G": "Group",
    "H": "History",
    "K": "Key"}

tools_dir = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), ".."), "tools"))

def tool_path(tool):
    tp = os.path.join(tools_dir, tool)
    if os.path.exists(tp):
        return tp
    elif os.path.exists(tp + ".exe"):
        return tp + ".exe"
    else:
        return tool

abc2midi = tool_path("abc2midi")
abc2abc = tool_path("abc2abc")
abcm2ps = tool_path("abcm2ps")
        

def tune_from_abc(abc):
    lines = abc.split("\n")
    tune = AbcTune(0)
    tune.content = abc.strip()
    
    for line in lines:
        line = line.strip()
        
        if len(line) > 1 and line[1] == ":": # it's a data field
            key, value = line[0], line[2:].strip()
            
            if key == "X":
                try:
                    tune.xref = int(value)
                except ValueError:
                    tune.xref = None
            elif key == "T":
                if tune.title == "":
                    tune.title = value

            try:
                tune[key].append(value)
            except KeyError:
                tune[key] = [value,]

    return tune
                

class AbcTune(dict):
    """Represents a single tune from an ABC tunebook; a dict whose
contents are the top-level properties of the tune.  Also has:

 - xref:int: the X: value from the original tunebook
 - title:string: the first T: value
 - content:string: a copy of everything from the first X: line to the next tune"""
    def __init__(self, xref):
        dict.__init__(self)
        self.xref = xref
        self.title = ""
        self.content = ""

    def _write_temp_file(self, midi_program=None):
        abc = self.content

        # insert an abc2midi directive for the instrument if needed
        if midi_program != None:
            midi_pos = abc.index("\n", abc.index("\nK:") + 1)
            abc = abc[:midi_pos] + "\n%%%%MIDI program %s\n" % midi_program + abc[midi_pos + 1:]
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            tmp_fn = f.name

            # Python 3 first, then 2
            try:
                f.write(abc.encode("utf-8"), "utf-8")
            except:
                f.write(abc.encode("utf-8"))
            f.flush()

            return f.name
        
    def write_svg(self, filename, page=1):
        """Write an SVG file of the first page of the tune to the specified
        filename, returning the page count"""

        # write the tune to a temp file
        tmp_fn = self._write_temp_file()

        # convert to an SVG; abcm2ps adds 001 to the base filename
        # (and for succeeding pages, 002, 003 …)
        os.system(
            abcm2ps + " -v -O %(filename)s %(tmpfile)s" %
            {"filename": filename,
             "tmpfile": tmp_fn})

        page_str = "{:0>3d}".format(page)
        
        # move the whatnot001.svg file to whatnot.svg
        os.system(
            "cp %s %s" % (filename.replace(".svg", "%s.svg" % page_str), filename))

        pages = 0

        while os.path.exists(
                filename.replace(".svg",
                                 "%s.svg" % "{:0>3d}".format(pages + 1))):
            pages += 1

        return pages

    def write_midi(self, filename, midi_program=None):
        """Write MIDI of the tune to the specified filename"""

        if midi_program == None:
            tmp_fn = self._write_temp_file()
        else:
            tmp_fn = self._write_temp_file(midi_program=midi_program)
            
        # convert to MIDI
        os.system(
            abc2midi + " %(tmpfile)s -o %(filename)s" %
            {"filename": filename,
             "tmpfile": tmp_fn})

    def copy(self):
        """Return a deep copy of the tune; e.g. for modification, leaving the
original unchanged."""
        return deepcopy(self)

    def transpose(self, semitones):
        """Transpose the tune to a new key"""
        self._replace_with_abc2abc_output(["-e",  "-t", str(semitones)])

    def update_from_abc(self, abc):
        other = tune_from_abc(abc)
        self.clear()
        self.title = other.title
        self.xref = other.xref
        self.content = other.content
        for k in other.keys():
            self[k] = other[k]



    def _replace_with_abc2abc_output(self, abc2abc_args):
        tmp_fn = self._write_temp_file()
            
        self.update_from_abc(
            check_output([abc2abc, tmp_fn] + abc2abc_args).decode("utf-8"))
        

# order of encodings to try when opening files, ordered by prevalence
# on the web, emphasizing Western languages
_encodings = ["utf-8",
              "ISO-8859-1",
              "Windows-1251",
              "Windows-1251",
              "ISO-8859-2",
              "ISO-8859-15"]


# if you can't load the file, raise this baby
class LoadError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
# no, seriously, someone has to raise the baby


class AbcTunebook(list):
    """Represents a tunebook file in ABC format; a list of tunes with a
filename and a method to return a sorted list of titles"""
    def __init__(self, filename=None):
        list.__init__(self)
        if filename:
            self.filename = filename
            self._load()
        else:
            self.filename = None

    def _load(self, encoding="utf-8"):
        """load the tunebook filename"""
        
        tune = None

        # try to load the file with each encoding from _encodings in turn
        try:
            with codecs.open(self.filename, "r", encoding) as f:
                abc = f.read()
        except UnicodeDecodeError:
            try:
                next_encoding = _encodings[_encodings.index(encoding) + 1]
            except IndexError: # you ran out of encodings, you poor sod
                raise LoadError("Unable to determine file encoding. Tried: " + ", ".join(_encodings))
            
            self._load(next_encoding)
            return None

        def maybe_add_xref_tag(tune):
            if tune.startswith("X:"):
                return tune
            else:
                return "X:" + tune
            
        tunes = [tune for tune in map(tune_from_abc,
                                      [maybe_add_xref_tag(tune)
                                       for tune in abc.split("\nX:")
                                       if tune.strip()])]

        # trim off extraneous matter before first tune
        if not abc.strip().startswith("X:"):
            tunes = tunes[1:]

        for tune in tunes:
            list.append(self, tune)

    def titles(self):
        """Return a list of tune titles"""
        return [tune.title for tune in self]

    def move(self, item, direction):
        index = self.index(item)

        if direction > 0 and len(self) > index + 1:
            cur, next = self[index], self[index + 1]
            self[index + 1], self[index] = cur, next
        elif direction < 0 and index > 1:
            cur, prev = self[index], self[index - 1]
            self[index - 1], self[index] = cur, prev
            
            
    def renumber(self):
        """Renumber tunes with sequential xrefs"""
        xref = 1
        for tune in self:
            tune.xref = xref
            xref_line = [line for line in tune.content.split("\n")
                         if line.strip().startswith("X:")][0]
            tune.content = tune.content.replace(xref_line,
                                                "X:%s" % xref)
            xref += 1

    def write(self, fn):
        """Save the tunebook to a file"""
        self.renumber() # in case of duplicate xrefs
        with codecs.open(fn, "w", "utf-8") as f:
            f.write("\n\n".join([tune.content
                                 for tune in self]))
        self.filename = fn
            
    def append(self, tune):
        """Add a tune to the tunebook"""
        list.append(self, tune)
        self.renumber() # redo xref numbering to keep unique

    def remove(self, tune):
        """Delete a tune from the tunebook"""
        list.remove(self, tune)
        self.renumber()
