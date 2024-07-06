#!/bin/bash
# Arguments are filename dose_number
# writes to stdout
awk -F, '$3=='$2 $1
 
