#!/bin/sh

find $1 -type f|xargs cat| sed -r '/^$/d;s/\[([A-Za-z ]+),.*/\1/;s/ x[0-9]+$//;s/, .+//'|sort|uniq
