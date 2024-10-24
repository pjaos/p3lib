#!/bin/sh

set -e

if [ -d "dist" ]; then
    sudo rm -rf dist
fi

if [ -d "doc" ]; then
    sudo rm -rf doc
fi

pyflakes3 src/p3lib
doxygen
python3 -m pip install --break-system-packages --upgrade build
python3 -m build
cp -rf dist/* dist.done/