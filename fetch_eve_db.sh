#!/bin/sh
mv eve-dump.db eve-dump.old.db
wget -qO- https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2 | bzcat > eve-dump.db
