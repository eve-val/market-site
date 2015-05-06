#!/bin/sh
echo -n "Update started at "
date
echo "Running market updater" &&
timeout 10m ./market-stuff.py I-CUVX && \
echo "Market updater finished" &&
scp id_list.js market.css *.html sound_market:
