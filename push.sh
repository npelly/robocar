#!/bin/bash

# recurse all directories
# but whitelist only specific file extensions
# and only copy directories that have something
# DEBUG: use --dry-run

rsync -vr --prune-empty-dirs --include "*/" --include="*.py" --include "*.ini" --include "*.js" --include "*.html" --include "main.cpp" --exclude "*" \
    ~/code/robocar/ pi@$1:~/code/robocar
