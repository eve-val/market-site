#!/bin/bash
echo -n "Update started at "
date
echo "Running market updater" &&
timeout 10m ./market-stuff.py 1021149293700@J134407 && \
echo "Market updater finished" &&
scp market.css *.html sound_market:
