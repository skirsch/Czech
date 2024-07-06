### About this repository
Only one country in the world has made publicly available record level data on COVID vaccine statistics: the Czech Republic (CR) aka Czechia.

All other countries use "privacy" as the excuse for not publishing record level data on vaccines given.

The way CR preserves privacy is brain dead simple: They only publish the YEAR of birth for a person. Everything else is an exact date.

This has everything we need to determine whether the COVID vaccines are safe.

### The CR source data  

The CR source [data can be downloaded here](https://github.com/PalackyUniversity/uzis-data-analysis/tree/main).

It was first made available on Github on Mar 29, 2024.

The file is compressed and expands to a `.csv` file with header and entries like this:
```
Sex, Year of Birth, Date of Death, Vax1 date, Vax1 batch code, Vax1 Code, Vax1 Name, <repeat these 4 fields for 7 vaccines>
"F",1956,,2021-05-03,"EY3014","CO01","Comirnaty",2021-06-14,"FD0168","CO01","Comirnaty",2021-12-11,"1F1020A","CO01","Com
irnaty",2022-09-29,,"CO08","Comirnaty Original/Omicron BA.1",2023-10-10,"HH0832","CO20","Comirnaty Omicron XBB.1.5.",,,,
,,,,
```


### Scripts to analyze the data
You can find these in the scripts directory. 


| Script            | Purpose                                                 |
| -------------------- | ---------------------------------------------------------- | 
| [buckets.py](./scripts/buckets.py)     | Detailed time series cohort analysis | 
| [convert.py](./scripts/convert.py)| Converts the CR data from .csv to the form used by buckets.py (one line per dose)   | 
| [count_deaths.py](./scripts/count_deaths.py)          | Counts deaths for 1 year after vaccine was given for each age group | 
| [count_months.py](./scripts/count_months.py)  | Counts # of doses given each month  | 
| [death_rates.py](./scripts/death_rates.py) |    ? |
| [extract_dose.sh](./scripts/extract_dose.sh) | ? |
| [extract_month.sh](./scripts/extract_month.sh) | ?|
| [process_month.sh](./scripts/process_month.sh) | ? |
| [extract_vax_code.sh](./scripts/process_month.sh)| Extract records matching a vax code|

### How to use the scripts to generate the mortality rate for one year from shot administration which is the key outcome
Note if you are using windows, you'll need to install something like Git Bash in order to have a shell that works, otherwise 
```
python convert.py CR_records.csv >records.csv  # convert CR format (1 record per person) to buckets format (1 record per shot)
bash extract_dose.sh records.csv 2 >dose2.csv        # get dose 2 data
bash extract_vax_code.sh dose2.csv 1 >pfizer.csv    # get Pfizer shots (vax code 1 for dose 2 vaccines)
extract_vax_type dose2.csv 2 >moderna.csv   # get Moderna shots used in Dose 2 (vax code 2 for dose 2 vaccines)
for mfg in "pfizer" "moderna" do
   python count_deaths.py $mfg.csv >${mfg}_counts.csv
done
```
You now have a pfizer_counts.csv and moderna_counts.csv files which you can analyze in a spreadsheet

### Using the scripts to generate time series cohort analysis files

```
python buckets.py dose2.csv dose2
python count_months.py dose2.csv
```

### Spreadsheets to analyze the time series data and the 1 year mortality data

### The methodology
The vaccination program in CR randomly assigned vaccines to people.

So it was a perfect real world clinical trial.

We compare all people who opted for the shots by comparing the results for each vaccine type.

If the mortality 1 year from the shot was the same for all vaccines, they are likely all safe.

We suspected going into this that Moderna would be MUCH worse than Pfizer since the mRNA dose is 3X higher (30 mcg for Pfizer; 100 mcg for Moderna). 
We had anecdotal reports, we had VAERS data, etc. all showing Moderna was a more dangerous shot.
Use pfizer as control and assume it is perfectly safe. 


Then easy to prove that Moderna has around a 50% or more increase in mortality for all but the very elderly.

### Quick summary

Basically, you can think of Pfizer as the placebo. Then you compare the Moderna mortality rate and you see that for every single age the mortality rate at 1 yr from shot 2 is around 50% more for Moderna. IN The vaccines were randomized. That means even if Pfizer is safe, Moderna is not. And the fact that nobody noticed that Moderna was more deadly, says that the entire system for monitoring safety is completely inadequate. Which then puts Pfizer into the crosshairs as being unsafe as well, which it is since it triggered so many death reports in VAERS among other data. And we have biological plausibility because the dose of mRNA for Moderna was 3.3 times greater than for Pfizer. so it makes sense that the deaths were significantly higher for every single age group

Essentially, by randomizing the vaccine to people in the Czech Republic, they created the perfect clinical trial. And then they published the record level data. This has never been done before. It’s always been kept hidden from public view.

If both vaccines were safe, there should have been less than a 4% difference in ACM for the elderly and a much smaller difference for those under 60 years old. 

Also, we have all these anecdotes of people dying right after the jab, which is unheard of. One of my friends had four of his friends die on the day that they got jabbed. That is statistically impossible if the shots are safe. I should never be able to find a single anecdote like that even if I talked to everyone on earth.

### Why this is a gold standard study data
1. Huge dataset
2. Record level data
3. Government supplied the data
4. Everyone covered in the country, no exclusions
5. Vaccine allocation was randomized. People were not allowed to pick which vaccine they got.
6. Pfizer was offered before Moderna, but we analyzed the data starting 
7. Exact dates for each vaccine and vaccine type. Exact death dates. Date of birth was obfuscated to be year of birth to preserve privacy. So all the important data was exact.

### The limitations
1. No deaths after 2022. This limited our ability to do similar analyses on Dose 3 and beyond.
2. Pfizer was given starting in Jan 2021 whereas Moderna rolled out in Feb. To account for this we analyzed the data for vaccination in CY 2021 vs. March-Dec 2021. There wasn't a material difference in the results.

### The setup
1. We basically had record level data on vaccination dates, types, and date of death if the person died for everyone in CR.
2. So our approach was to use Pfizer as the control and see if the mortality rate for Moderna was different compared to the control
3. The setup was essentially a PERFECT real world vaccine trial because the vaccine maker was randomized. If all the vaccines were safe, the mortality rate as measured over a 12 month period from the time of vaccination would be the same regardless of manufacturer.
4. Both vaccines were rolled out at the same peak month and had similar distribution curves. 



### The experiment
Dose 2 1 year mortality on each birth year

Why dose 2? No deaths in database after Dec 31, 2022 so to get 1 year follow up (to even out seasonality effects), limited to dose 2. Dose 1 would have been better but people could get a dose 2 shot of a different vaccine in 3 weeks. You couldn't get a booster for 8 months but that would be randomized between the groups getting the dose 2 shots so not material. We didn't need to filter these out.

### What we expected to see
If the vaccines were all safe, we'd expect to see nearly zero mortality difference between the two cohorts. This is because the vaccine fundamentally protect people by exposing them to an antigen. So the mechanism of action is nearly identical between both vaccines. 

So if 20% of all deaths are from COVID and one vaccine is "magically" 20% better than another vaccine for reasons nobody can explain, you're looking at most a 4% mortality difference betwen the two vaccines for the elderly and perhaps a 10X smaller difference for younger people (since young people rarely die from COVID). So if you are under 60 years old, any ACM differences should be miniscule and unmeasurable.


But we've been claiming the vaccines increase all-cause mortality with Pfizer being the least deadly per shot, Moderna being about 50% more deadly, and the J&J shot was the deadliest. We've known that from early analysis of the VAERS data: there was a proportionally higher rate of death reports per dose for Moderna vs. Pfizer.

So we expected Moderna would have a higher death rate based on VAERS, other studies looking at the rate of side effects, and anecodetal observations of healthcare professionals who tracked vaccine type of the vaccine injured.  

Around June 2021 when I was analyzing the VAERS data and publishing documents computing the URF of 41 for VAERS, I pointed out that Moderna was significantly more deadly on a deaths per shots given basis. Anyone can verify this from the VAERS data. We can also do a statistical analysis of vaccine injury reports and look at the percentage from Moderna vs. Pfizer in the injury reports compared to doses administered. This should have been a huge red flag. If the vaccines were safe, there shouldn't have been proportionally more Moderna reports.


### Biological plausibility
To make a determination of causality, we have to show biological plausibility.

We have that here in spades.

Moderna was 100mcg of mRNA vs. 30mcg for the Pfizer shot. Moderna was only 50mcg for some cases. So that is a near perfect match to the 50% increase in mortality.

### What we observed

### What is really going on here

### What the analysis reveals

### Attacks on the data, methods, or interpretation
