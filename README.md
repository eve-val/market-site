market-site
===========

Code to create a simple market summary page.
This is all pretty janky.

Requirements
------------
* Needs python3, sqlite3, and [EsiPy](https://github.com/Kyria/EsiPy)

How to setup
----------
* auth-market.py - Gets an ESI refresh token to use to look up citadel orders; it will output an eve SSO URL - visit it, authenticate, and then enter the code displayed in your browser. Should only need to be run once.
* fetch_eve_db.sh - Fetches the Eve static database dump and uncompresses it to the location expected by the other tools. Needs to be run after EVE updates.
* The market script expects a file named 'items' with a list of items to display. There is a 'demo_items' file that can be copied over.

How to run
----------
* market-script.py 'Citadel Name@SystemName' - Generates SystemName.html containing a market summary a citadel in SystemName using ESI data
* market-script.py SystemName - Generates SystemName.html containing a market summary from the stations in SystemName using eve-central data
* update.sh - Drives the site updating process for my corp

How to work on the front-end
----------------------------
* The front-end is just static content, but it expects that `/market.json` is a valid URL and looks like the file at `public/market.json`. The CSS is compiled from `css/styles.css` by running `npm run build:css:dist`, which will compile it and strip out all unused CSS classes. During development, build the CSS with `npm run build:css`, which skips that last step.
