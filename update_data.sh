#!/bin/sh
./market-stuff.py Hemin > hemin.html && \
./market-stuff.py Utopia > utopia.html && \
./market-stuff.py Orvolle > orvolle.html && \
./market-stuff.py 9GYL-O > 9guy.html && \
./market-stuff.py --poller > id_list.js
