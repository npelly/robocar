#!/bin/bash

# recurse all directories
# but whitelist only *.py and main.cpp
# and only copy directories that have something
# DEBUG: use --dry-run

#TARGET=pi.local
TARGET=euler.local

rsync -vr --prune-empty-dirs --include "*/" --include="*.py" --include "*.js" --include "*.html" --include "main.cpp" --exclude "*" \
    ~/code/robocar/ pi@$TARGET:~/code/robocar
