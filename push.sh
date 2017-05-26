#!/bin/bash

# recurse all directories
# but whitelist only *.py and main.cpp
# and only copy directories that have something
# DEBUG: use --dry-run

rsync -vr --prune-empty-dirs --include "*/" --include="*.py" --include "main.cpp" --exclude "*" \
    ~/code/robocar/ pi@pi.local:~/code/robocar
