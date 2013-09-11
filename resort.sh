#!/bin/sh
TMPFILE=`tempfile`
LANG=C sort items | uniq > $TMPFILE && mv $TMPFILE items
