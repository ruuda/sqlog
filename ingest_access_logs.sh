#! /bin/bash

for f in `ls -tU ./data_dir/*.log*`
do
	echo "In file: $f"
	./sqlog.py --format COMBINED log.sqlite < $f
done
