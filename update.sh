#!/bin/sh
git pull && \
./update_data.sh && \
scp id_list.js market.css hemin.html utopia.html orvolle.html 9guy.html poller.html sound_market:
