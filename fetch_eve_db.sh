#!/bin/sh
wget -qO- https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2 | bzcat > eve-dump.db
