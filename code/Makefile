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

# complete when we have all the time series analyses and MR stats files
all: $(time_series_pfizer) $(time_series_moderna) $(pfizer_stats) $(moderna_stats) $(full_matrix)
	@echo "All done!"

# computes 4 different studies: shot1 given in 2021, shot2 given in 2021, shot3 given in 2021, unvaxxed in 2021
# This is the ultimate indicator of what is going on. Four states for each dose.
# Takes 46 minutes to run.
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

$(source_file): $(compressed_source_file)
	@echo "Expanding source data file..."
	@xz  -dk $(compressed_source_file) # decompress and keep original file

# convert CR format (1 record per person) to buckets format (1 record per shot)
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

	