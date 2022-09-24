#!/bin/bash

cd $(dirname $0)
source ./bin/activate

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
timeout 10m ./market-stuff.py "Rens" && \
echo "Market updater finished" && \
cp market.css Rens.html Rens.json public/* /srv/of-sound-mind.com/market
