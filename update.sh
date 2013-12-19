#!/bin/sh
git pull && \
./market-stuff.py VLGD-R Orvolle 9GYL-O LSC4-P && \
scp id_list.js market.css *.html sound_market:
