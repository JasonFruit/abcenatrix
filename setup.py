import os
from setuptools import setup

# Utility function to read the README file.  Used for the
# long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to
# put a raw string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "abcviewer",
    version = "0.1.0",
    author = "Jason R. Fruit",
    author_email = "jasonfruit@gmail.com",
    description = "A viewer for tunebooks in ABC musical notation.",
    license = "MIT",
    keywords = "ABC music viewer",
    url = "http://jasonfruit.com/abcviewer.html",
    scripts=["abcviewer",],
    packages=['abcv',],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Multimedia",
        "License :: OSI Approved :: MIT License",
    ],
)
