market-site
===========

Requirements
------------
* Needs python3
* You can get the Eve database dump from here: http://pozniak.pl/dbdump/ - ody110-sqlite3-v1.db.bz2 is the file you want

How to run
----------
update_data.sh - generates the data and html files.
update.sh - wraps update_data.sh with a git pull command and then scps the output into the cloud.
resort.sh - resorts the items file
