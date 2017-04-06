#!/bin/sh
echo -n "Update started at "
date
echo "Running market updater" &&
timeout 10m ./market-stuff.py I-CUVX 14YI-D YZ-LQL && \
echo "Market updater finished" &&
scp market.css *.html sound_market:
