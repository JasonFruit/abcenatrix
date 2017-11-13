import os
from setuptools import setup
import codecs

# Utility function to read the README file.  Used for the
# long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to
# put a raw string in below ...
def read(fname):
    return codecs.open(os.path.join(os.path.dirname(__file__), fname), "r", "utf-8").read()

# installing PySide on Linux using pip is usually a failure, adds
# preinstallation dependencies of its own, and would unduly limit
# Python versions we could use, so don't even try
if os.name == "posix":
    requirements = ["pygame", "mido"]
else:
    requirements = ["pyside", "pygame", "mido"]
    
setup(
    name = "abcenatrix",
    version = "0.3.13",
    author = "Jason R. Fruit",
    author_email = "jasonfruit@gmail.com",
    description = "A viewer, player, and editor for tunebooks in ABC musical notation.",
    license = "MIT",
    keywords = "ABC music viewer player editor",
    url = "http://jasonfruit.com/abcenatrix.html",
    scripts=["abcenatrix",],
    data_files=[("/usr/share/applications", ["abcenatrix.desktop"]),
                ("/usr/share/pixmaps", ["abcenatrix.png"])],
    install_requires=requirements,
    packages=['abcv',],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Multimedia",
        "License :: OSI Approved :: MIT License",
    ],
)
