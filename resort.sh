#!/bin/sh
TMPFILE=`tempfile`
LANG=C sort items > $TMPFILE && mv $TMPFILE items
