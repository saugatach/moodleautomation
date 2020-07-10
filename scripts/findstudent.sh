#!/bin/bash

student=`cat ../data/studentid.csv | grep $1`
if [ -z "$student" ]; then
	echo "Student not found"
	exit
fi

for stuid in `cat ../data/studentid.csv | grep $1 | cut -d ',' -f1 | uniq`
do
	cat ../data/studentid.csv | grep $stuid | cut -d ',' -f2 | uniq
	cat ../data/courseid.csv | grep $stuid | cut -d ',' -f2 | cut -d '.' -f 3-
	echo "---------------------------"
done

#cat data/studentid.csv | grep $1 | head -n 1 | cut -d ',' -f2
#stuid=`cat data/studentid.csv | grep $1 | head -n 1 | cut -d ',' -f1`
#cat data/courseid.csv | grep $stuid | cut -d ',' -f2


