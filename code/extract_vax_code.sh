#!/bin/bash

# Usage: ./extract_vax_code.sh <source_file> <dose code>
# where dose code 1= Pfizer, 2=Moderna, etc.
# extract records with the vax code from file

awk -F, '$2=='$2 $1
 
