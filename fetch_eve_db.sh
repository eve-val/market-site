#!/bin/sh
wget -qO- http://pozniak.pl/dbdump/rub110-sqlite3-v1.db.bz2 | bzcat > eve-dump.db
