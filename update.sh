#!/bin/sh
git pull && \
./market-stuff.py EX6-AO LSC4-P && \
scp id_list.js market.css *.html sound_market:
