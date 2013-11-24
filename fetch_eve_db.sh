#!/bin/sh
wget -qO- http://pozniak.pl/dbdump/rub100-sqlite3-v1.db.bz2 | bzcat > eve-dump.db
