#!/bin/bash
# Usage: ./extract_vax_year <filename> <year>
# Example: ./extract_vax_year foo.csv 2021
file=$1
year=$2
cmd="\$4 ~ /$year$/ {print \$0}"
awk -F, "$cmd" $file