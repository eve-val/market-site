#!/bin/sh
git pull && \
./update_data.sh && \
scp id_list.js market.css vlgd-r.html orvolle.html 9guy.html poller.html sound_market:
