#!/bin/bash

student=`cat ../data/datainput/studentid.csv | grep $1`
if [ -z "$student" ]; then
	echo "Student not found"
	exit
fi

for stuid in `cat ../data/datainput/studentid.csv | grep $1 | cut -d ',' -f1 | uniq`
do
	stuname=`cat ../data/datainput/studentid.csv | grep $stuid | cut -d ',' -f2 | uniq | head -n 1`
	coursename=`cat ../data/datainput/courseid.csv | grep $stuid | cut -d ',' -f2 | cut -d '.' -f 3-`
	gradebook="../data/dataoutput/PHX.20200824.${coursename}.csv"	
	
	echo "Student ID:" $stuid	
	echo $coursename
	cat "$gradebook" | cut -d"," -f1-6 | sed 's/,/ /' | grep "$stuname" | cut -d"," -f1,3-5 | sed 's/,/ | /g'

	echo "------------------------------------------------------------------------"
done

#cat data/studentid.csv | grep $1 | head -n 1 | cut -d ',' -f2
#stuid=`cat data/studentid.csv | grep $1 | head -n 1 | cut -d ',' -f1`
#cat data/courseid.csv | grep $stuid | cut -d ',' -f2


