import os
import codecs
import tempfile
from copy import deepcopy

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
    def write_svg(self, filename):
        """Write an SVG file of the first page of the tune to the specified
filename"""

        # write the tune to a temp file
        with tempfile.NamedTemporaryFile() as f:
            f.write(bytes(self.content, "utf-8"))
            f.flush()

            # convert to an SVG; abcm2ps adds 001 to the base filename
            os.system(
                "abcm2ps -v -O %(filename)s %(tmpfile)s" %
                {"filename": filename,
                 "tmpfile": f.name})
            
            # move the whatnot001.svg file to whatnot.svg
            os.system(
                "mv %s %s" % (filename.replace(".svg", "001.svg"), filename))
        

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
    def __init__(self, filename):
        list.__init__(self)
        self.filename = filename
        self._load()
        
    def _load(self, encoding="utf-8"):
        """load the tunebook filename"""
        
        tune = None

        # try to load the file with each encoding from _encodings in turn
        try:
            with codecs.open(self.filename, "r", encoding) as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                next_encoding = _encodings[_encodings.index(encoding) + 1]
            except IndexError: # you ran out of encodings, you poor sod
                raise LoadError("Unable to determine file encoding. Tried: " + ", ".join(_encodings))
            
            self._load(next_encoding)
            return None

        
        for line in lines:
            # ignore blank lines
            if line.strip() == "":
                pass
            # save the tune and start a new one for each xref number
            elif line.strip().startswith("X:"):
                # tune is None if you haven't started one before
                if tune:
                    self.append(tune)
                tune = AbcTune(int(line.replace("X:", "").strip()))
            # T: is the title; store the first and ignore the rest
            elif line.strip().startswith("T:"):
                if tune.title == "":
                    tune.title = line.replace("T:", "").strip()
            # anything of the pattern ?: ... is a top-level property,
            # at least for our inexact purposes
            elif len(line.strip()) > 1 and line.strip()[1] == ":":
                try:
                    tune[line.strip()[0]].append(line.strip()[2:].strip())
                except KeyError:
                    tune[line.strip()[0]] = [line.strip()[2:].strip()]
                except:
                    pass

            # if there's a tune, and the line isn't blank, add it to
            # the tune (there's no tune until we reach the first X:
            if tune != None and line.strip() != "":
                tune.content += line

        # there's probably one last tune to add
        if tune:
            self.append(tune)

    def titles(self):
        """Return a sorted list of tune titles"""
        return sorted([tune.title for tune in self])
