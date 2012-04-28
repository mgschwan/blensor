#!/bin/bash

CFG="source/tools/uncrustify.cfg"

if [ ! -f $CFG ]
then
	echo "Run this from the blender source directory: " $CFG " not found, aborting"
	exit 0
fi


for fn in "$@"
do
	# without this, the script simply undoes whitespace changes.
	uncrustify -c $CFG --no-backup --replace "$fn"
 
	cp "$fn" "$fn.NEW"
	svn revert "$fn" 1> /dev/null
 
	diff "$fn" "$fn.NEW" -u --ignore-trailing-space --ignore-blank-lines > "$fn.DIFF"
 
	patch -p0 < "$fn.DIFF" 1> /dev/null
 
	rm "$fn.NEW"
	rm "$fn.DIFF"
done
