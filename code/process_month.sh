#!/bin/bash
# argument is dose number and it will use the .csv file for the dose number
for i in {1..12}; 
do 
	python buckets.py d${1}_$i.csv d${1}_m$i & 
done
