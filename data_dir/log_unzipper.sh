#! /bin/bash

for f in ./*.gz 
do 
	gunzip -c "$f" > ./"${f%.*}"
	echo "file processed $f "
done

for i in "$@" ; do
    if [[ $i == "--archive-zips" ]] ; then
        echo "Archiving zips!"
	rm *.gz
        break
    fi
done

