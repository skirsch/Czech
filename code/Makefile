# generate all the analysis files
# the last file is the time series analysis so we make everything depend on the previous step

# target name: files that must be generated before this can run
datadir=../data
source_file=$(datadir)/CR_records.csv
compressed_source_file=$source_file.xz
record_file=$(datadir)/records.csv # in buckets.py format
records21_file=$(datadir)/records21.csv
dose2_21_file=$datadir/dose2_21.csv
pfizer_stats=$datadir/moderna_stats.csv
moderna_stats=$datadir/moderna_stats.csv

time_series=$datadir/d2_month_dose_week_decade.txt

# only really need the second file, but require the first to make sure everything is built before time series which is the last to build
all: $(moderna_stats) $(dose_21_file)
	python buckets.py $(dose2_21_file)

objects = foo.o bar.o all.o
all: $(objects)
	$(CC) $^ -o all

# Syntax - targets ...: target-pattern: prereq-patterns ...
# In the case of the first target, foo.o, the target-pattern matches foo.o and sets the "stem" to be "foo".
# It then replaces the '%' in prereq-patterns with that stem
$(objects): %.o: %.c
	$(CC) -c $^ -o $@

all.c:
	echo "int main() { return 0; }" > all.c

# Note: all.c does not use this rule because Make prioritizes more specific matches when there is more than one match.
%.c:
	touch $@

clean:
	rm -f *.c *.o all


#!/bin/bash
# This is the master script to generate all data files from the source file
# Just one line:
#         cd code; ./analyze.sh



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
```
python buckets.py dose2.csv dose2
python count_months.py dose2.csv
```