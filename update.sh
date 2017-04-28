#!/bin/bash

# argument should be a URL to fetch item list from
URL="$1"

echo -n "Update started at "
date

# Fech new items
mkdir -p backup_items/
cp items backup_items/items_`date +%Y%m%d-%H%M`
curl -s $URL | ./market-stuff.py --filter > items

# Run the stuff
echo "Running market updater" &&
timeout 10m ./market-stuff.py "Statio Tranquillitatis@J134407" && \
echo "Market updater finished" &&
scp market.css *.html sound_market:
