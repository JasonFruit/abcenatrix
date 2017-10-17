import os
import codecs
import tempfile

class AbcTune(dict):
    def __init__(self, xref):
        dict.__init__(self)
        self.xref = xref
        self.title = ""
        self.content = ""
    def write_svg(self, filename):
        with tempfile.NamedTemporaryFile() as f:
            f.write(bytes(self.content, "utf-8"))
            f.flush()
            os.system(
                "abcm2ps -v -O %(filename)s %(tmpfile)s" %
                {"filename": filename,
                 "tmpfile": f.name})
            # srsly? 001?
            os.system(
                "mv %s %s" % (filename.replace(".svg", "001.svg"), filename))
        
class AbcTunebook(list):
    def __init__(self, filename):
        list.__init__(self)
        self.filename = filename
        self._load()
    def _load(self):
        with codecs.open(self.filename, "r", "utf-8") as f:

            tune = None

            lines = f.readlines()
            
            for line in lines:
                if line.strip() == "":
                    pass
                elif line.strip().startswith("X:"):
                    if tune:
                        self.append(tune)
                    tune = AbcTune(int(line.replace("X:", "").strip()))
                elif line.strip().startswith("T:"):
                    if tune.title == "":
                        tune.title = line.replace("T:", "").strip()
                elif len(line.strip()) > 1 and line.strip()[1] == ":":
                    try:
                        tune[line.strip()[0]].append(line.strip()[2:].strip())
                    except KeyError:
                        tune[line.strip()[0]] = [line.strip()[2:].strip()]
                    except:
                        pass
                        
                if tune != None and line.strip() != "":
                    tune.content += line

        if tune:
            self.append(tune)

    def titles(self):
        return sorted([tune.title for tune in self])


if __name__ == "__main__":
    abc_file = AbcTunebook("/home/jason/Downloads/Kohlers.abc")
    abc_file[12].write_svg("out.svg")
    
