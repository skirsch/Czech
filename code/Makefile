# generate all the analysis files
# the last file is the time series analysis so we make everything depend on the previous step

# target name: files that must be generated before this can run
datadir=../data
source_file=$(datadir)/CR_records.csv
compressed_source_file=$(source_file).xz
record_file=$(datadir)/records.csv # in buckets.py format
records21_file=$(datadir)/records21.csv
dose2_21_file=$(datadir)/dose2_21.csv
pfizer_dose2_21_file=$(datadir)/pfizer_dose2_21.csv
moderna_dose2_21_file=$(datadir)/moderna_dose2_21.csv
pfizer_stats=$(datadir)/pfizer_stats.csv
moderna_stats=$(datadir)/moderna_stats.csv
# just one of the time series output files
time_series_pfizer=$(datadir)/ts_pfizer_d2_month_dose_week_decade.txt 
time_series_moderna=$(datadir)/ts_moderna_d2_month_dose_week_decade.txt 
time_series_files=$(datadir)/ts_*
full_matrix=$(datadir)/full_matrix.csv
time_series_all_files=$(datadir)/ts_all_month_dose_week_decade.txt 

# vax_N.csv files; just need to list the last one because the program remakes all of them
# so if the last one is there, we should be good to go
vax_files=$(datadir)/vax_1.csv $(datadir)/vax_2.csv $(datadir)/vax_3.csv $(datadir)/vax_4.csv $(datadir)/vax_5.csv $(datadir)/vax_6.csv $(datadir)/vax_7.csv

# comorbidities csv downloaded from website
com_source=$(datadir)/ockovani-profese.csv
comorbidity=$(datadir)/comorbidity.csv


# complete when we have built the time series, 1 year death rates, and the more detailed 1-year mortality analysis
# vax target will meke the vax1.csv, etc files
all: time-series death-rates analysis time-series-all comorbidity vax
	@echo "All done!"

download:
	@wget -O - https://github.com/skirsch/Czech/raw/main/data/CR_records.csv.xz?download= >$(compressed_source_file)
.PHONY: download

# this target makes a time series from the FULL dataset, rather than from a restricted dataset 
# that just looks at those given dose 2 in 2021. So this is the traditional time series showing
# all the transitions.
time-series-all: $(time_series_all_files)

$(time_series_all_files): $(record_file)
	@echo "Time series analysis for all records"
	@python buckets.py $(record_file) $(datadir)/ts_all


# these are the ultimate csv files suitable for pivot table analysis
vax: $(vax_files)

$(vax_files): $(source_file)
	@echo "Making all the vax_N.csv files from the Czech source file"
	@python vax.py


comorbidity:	$(comorbidity)

# make the comorbidities.xls file
$(comorbidity): $(com_source)
	@python comorbidity.py

$(com_source):
	@echo "Downloading 3.8G file from Czech Republic"
	@wget -O $(com_source) https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-profese.csv 


# analysis computes 4 different studies: shot1 given in 2021, shot2 given in 2021, shot3 given in 2021, unvaxxed in 2021
# This is the ultimate indicator of what is going on. Four states for each dose.
# Takes 46 minutes to run.

analysis: $(full_matrix)

# time series will convert the records file to buckets.py and then create the time series
# files for Pfizer and Moderna that can be analyzed in the spreadsheets

time-series:  $(time_series_pfizer) $(time_series_moderna) 

death-rates: $(pfizer_stats) $(moderna_stats)

$(full_matrix): $(source_file)
	@echo "Computing the full matrix analysis buckets from original source file"
	@python full_matrix.py $(source_file) >$(full_matrix)

# compute time series for Pfizer dose 2 given in 2021
$(time_series_pfizer): $(pfizer_dose2_21_file)
	@echo "Time series analysis for Pfizer"
	@python buckets.py $(pfizer_dose2_21_file) $(datadir)/ts_pfizer_d2
	
# compute time series for moderna dose 2 given in 2021
$(time_series_moderna): $(moderna_dose2_21_file)
	@echo "Time series analysis for moderna"
	@python buckets.py $(moderna_dose2_21_file) $(datadir)/ts_moderna_d2


# friendly target name for uncompressing data
# sudo apt install xz-utils if you don't have xz
uncompress: $(source_file)

# expansion step is done by calling xz directly
$(source_file): $(compressed_source_file)
	@echo "Expanding source data file..."
	@xz  -dk $(compressed_source_file) # decompress and keep original file

# convert CR format (1 record per person) to buckets format (1 record per shot)
# including the uvaccinated records!
$(record_file):	$(source_file)
	@echo "Converting to buckets.py format..."
	@python convert.py $(source_file) >$(record_file)  

# get only those vaccinated in 2021 to allow 1 year to die
$(records21_file): $(record_file)
	@echo "Extracting shots given in 2021"
	@./extract_vax_year.sh $(record_file) 2021 >$(records21_file)

$(dose2_21_file): $(records21_file)
	@echo "Extracting dose 2 from the shots given in 2021 file"
	@./extract_dose.sh $(records21_file) 2 >$(dose2_21_file)

# pfizer for dose 2 is vax code=1
$(pfizer_dose2_21_file): $(dose2_21_file)
	@echo "Extracting pfizer doses for d2 in 2021"
	@./extract_vax_code.sh $(dose2_21_file) 1 >$(pfizer_dose2_21_file) 

# Moderna for dose 2 is vax code=2
$(moderna_dose2_21_file): $(dose2_21_file)
	@echo "Extracting moderna doses for d2 in 2021"
	@./extract_vax_code.sh $(dose2_21_file) 2 >$(moderna_dose2_21_file) 

# note the death_rates.py takes an optional argument for month to start at (defaults at 1 which is Jan)
# I ran this with the second positional optional parameter of 3 and got essentially the same result
# to prove that the effect was not caused by startup differences.
# This is the most CONSERVATIVE way to do the calculation (with the default start month) because
# if anything, it will disadvantage Pfizer and make Moderna look safer.

$(pfizer_stats): $(pfizer_dose2_21_file)
	@echo "Computing MR for 1 year from shot #2 given in 2021 for Pfizer by age (vax code 1)"
	@python death_rates.py  $(pfizer_dose2_21_file) >$(pfizer_stats)    

$(moderna_stats): $(moderna_dose2_21_file)
	@echo "computing MR for 1 year from shot #2 given in 2021 for moderna by age (vax code 2)"
	@python death_rates.py  $(moderna_dose2_21_file) >$(moderna_stats) 

# remove all files except for the compressed source file we started with
clean:
	@rm -f $(source_file) $(record_file) $(records21_file) $(dose2_21_file) $(pfizer_dose2_21_file) $(moderna_dose2_21_file)
	@rm -f $(pfizer_stats) $(moderna_stats) $(time_series_files) $(full_matrix)

	