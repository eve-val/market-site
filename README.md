market-site
===========

Requirements
------------
* Needs python3
* You can get the Eve database dump from here: http://pozniak.pl/dbdump/ - You want the file for the latest version of eve in sqlite3 format. See below for a script that automates this.

How to run
----------
* update_data.sh - generates the data and html files.
* update.sh - wraps update_data.sh with a git pull command and then scps the output into the cloud.
* resort.sh - resorts the items file.
* fetch_eve_db.sh - fetches the Eve database dump and uncompresses it to the location expected by the other tools.
