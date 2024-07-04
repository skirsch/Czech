### About this repository
Only one country in the world has made publicly available record level data on COVID vaccine statistics: yhe Czech Republic (CR) aka Czechia.

All other countries use "privacy" as the excuse for not publishing record level data on vaccines given.

The way CR preserves privacy is brain dead simple: They only publish the YEAR of birth for a person. Everything else is an exact date.

This has everything we need to determine whether the COVID vaccines are safe.

### The CR source data  

The CR source [data can be downloaded here](https://github.com/PalackyUniversity/uzis-data-analysis/tree/main).

It was first made available on Github on Mar 29, 2024.

### Scripts to analyze the data
You can find these in the scripts directory. 


| Script            | Purpose                                                 |
| -------------------- | ---------------------------------------------------------- | 
| buckets.py     | Detailed time series cohort analysis | 
| convert.py | Converts the CR data to form used by buckets.py                                                       | 
| count_deaths.py          | Counts deaths for 1 year after vaccine was given for each age group                                                       | 
| count_months.py  | Counts # of doses given each month                               | 
| death_rates.py |    ? |
| extract_dose.sh | ? |
| extract_month.sh | ?|
| process_month.sh | ? |

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


### What is really going on here

### What the analysis reveals

### Attacks on the data, methods, or interpretation
