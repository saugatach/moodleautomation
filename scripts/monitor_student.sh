#!/bin/bash

student=`cat ../data/studentid.csv | grep $1 `
if [ -z "$student" ]; then
	echo "Student not found"
	exit
fi

cat data/studentid.csv | grep $1

#| cut -d',' -f1
