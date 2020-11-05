#!/bin/bash

echo -n "Update started at "
date

# Fech new items
mkdir -p backup_items/
cp items backup_items/items_`date +%Y%m%d-%H%M`
./fits-to-items.sh fits | ./market-stuff.py --filter > __new_items
if [ -s __new_items ]; then
    mv __new_items items
else
    echo "Arg couldn't download the items"
    rm __new_items
fi

# Run the stuff
echo "Running market updater" &&
timeout 10m ./market-stuff.py "International Space Station@LSC4-P" && \
echo "Market updater finished"
#scp market.css *.html sound_market:
