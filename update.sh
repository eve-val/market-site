#!/bin/sh
git pull && ./market-stuff.py > index.html && ./market-stuff.py --poller > id_list.js && scp id_list.js index.html poller.html sound_market:
