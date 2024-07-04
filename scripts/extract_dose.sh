#!/bin/bash
awk -F,  '$3=='$1 male.csv female.csv >d$1.csv
 
