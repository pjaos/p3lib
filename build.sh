#!/bin/sh
rm -rf doc
doxygen
python3 -m pip install --upgrade build
python3 -m build