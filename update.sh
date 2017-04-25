#!/bin/bash
echo -n "Update started at "
date
echo "Running market updater" &&
timeout 10m ./market-stuff.py "Dern's House of Pancakes@J134407" && \
echo "Market updater finished" &&
scp market.css *.html sound_market:
