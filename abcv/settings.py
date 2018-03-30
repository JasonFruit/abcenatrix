import os
import codecs
import json

class Settings(object):
    def __init__(self, filename):
        self._filename = filename

        # create settings file if it doesn't exist
        if not os.path.exists(self._filename):
            self._settings = _default_settings
            self._save()
        else:
            self._load()
            
    def _load(self):
        # load the settings file
        with codecs.open(self._filename, "r", "utf-8") as f:
            self._settings = json.load(f)

    def _save(self):
        with codecs.open(self._filename, "w", "utf-8") as f:
            json.dump(self._settings, f)

    def get(self, name):
        try:
            return self._settings[name]
        except KeyError:
            return None

    def set(self, name, value):
        self._settings[name] = value
        self._save()
