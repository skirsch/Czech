#!/bin/bash
# extract vaccine maker records for Dose 2
# argument is 1 for Pfizer or 2 for Moderna

awk -F,  '$3=='$1 male.csv female.csv >d$1.csv
 
