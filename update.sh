#!/bin/sh
git pull && ./market-stuff.py Hemin > hemin.html && ./market-stuff.py Utopia > utopia.html && ./market-stuff.py --poller > id_list.js && scp id_list.js hemin.html utopia.html poller.html sound_market:
