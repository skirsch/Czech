#!/bin/bash
# This is the master script to generate all data files from the source file
# Just one line:
#         cd code; ./analyze.sh

datadir=../data
source_file=$datadir/CR_records.csv
compressed_source_file=$source_file.xz
record_file=$datadir/records.csv # in buckets.py format
records21_file=$datadir/records21.csv
dose2_21_file=$datadir/dose2_21.csv

if [[ ! -f $source_file ]]; then
    echo "expanding source data file..."
    xz  -dk $compressed_source_file # decompress and keep original file
fi

if [[ ! -f $record_file ]]; then
    echo "converting to buckets.py format..."
    # convert CR format (1 record per person) to buckets format (1 record per shot)
    python convert.py $source_file >$record_file  
fi

if [[ ! -f $records21_file ]]; then
    echo "extracting shots given in 2021"
    # get only those vaccinated in 2021 to allow 1 year to die
    ./extract_vax_year.sh $record_file 2021 >$records21_file 
fi

if [[ ! -f $dose2_21_file ]]; then
    echo "extracting shots dose 2"
    ./extract_dose.sh $records21_file 2 >$dose2_21_file       # get dose 2 data
fi

echo "extracting Pfizer shots..."
./extract_vax_code.sh $dose2_21_file   1 >$datadir/pfizer.csv    # get Pfizer shots
echo "extracting Moderna shots..."
./extract_vax_code.sh $dose2_21_file   2 >$datadir/moderna.csv   # get Moderna shots

echo "Now doing mortality analysis"
# now generate the MR for each birth year for each manufacturer
for mfg in "pfizer" "moderna" 
do
   echo "for $mfg..."
   python count_deaths.py $datadir/$mfg.csv >$datadir/${mfg}_counts.csv
done
echo "I'm done. And Pfizer and Moderna are finished after you analyze the output."