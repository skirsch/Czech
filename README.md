### Abstract
Using gold-standard record level data supplied by the Czech Republic on over 10M citizens who randomly were given either the Pfizer or Moderna vaccine, we can compute a 1 year mortality risk ratio (MRR) between the two vaccines where the 1 year starts at the time of receipt of the shot.

We found that for virtually all ages below 92 years old, the Moderna shots were much more dangerous than the Pfizer shots. The younger the person, the higher the mortality increase. For those under 60 years old, the relative mortality was 50% higher.

This means that, even if the Pfizer vaccine was perfectly safe, the Moderna vaccine is a disaster and should be halted immediately since a 50% absolute increase in mortality is an unacceptable risk tradeoff compared to the absolute risk of dying from COVID.

However, we also know that Pfizer generated more vaccine-supected deaths and more serious adverse events than Moderna (counting only those people with 30 or more new serious adverse events after taking their shots) on an absolute basis (because there were more Pfizer shots administered). This suggests that the *excess* mortality caused by the Pfizer shots (excess over a placebo shot) must be at least half the *relative* mortality increase of Moderna shots.

In short, this gold-standard record-level data enables us to prove, for the first time, that both Pfizer and Moderna shots cause an unacceptable increase in all-cause mortality relative to the risk they are trying to mitigate and so therefore, even if the vaccines were 100% effective, they should never been used because the risk/benefit ratio is >1. The vaccines should be stopped immediately.

Also, the people who promoted these vaccines should admit that they were incapable of finding large safety signals and should not be trusted by the public in the future until those people who made the correct calls on these vaccines are promoted into positions of authority.

We need to end the liability waiver of vaccine manufacturers, we need to populate the outside committees of the FDA and CDC with only people who publicly spoke out against these vaccines, and we need to immediately stop mandating all vaccines worldwide because a mistake like this one calls all previous vaccine safety studies into question. We need to start making data on other vaccines public, just like the Czech Republic did for the COVID vaccine data. Hiding public health data from the public never improves health outcomes.

### The specifics
* We legally obtained over 10M records people in Czech Republic via FOIA.
* The records preserved privacy by using birth year instead of birth date.
* There was one record for each person
* Each record had YOB, DOD (if dead), and, for each COVID vaccination, the vax date,vax batch, vax name, vax code number for up to 7 vaccinations.
* Deaths were not included for 2023 and beyond, limiting the scope of the analysis
* Dose 2 was given starting in 2021 with the greatest number of doses given mid-year
* You had to wait 8 months after dose 2 before getting a booster.
* Pfizer rolled out first in Jan 2021. Moderna rolled out in Feb 2021.
* Vaccines were randomly distributed for those wishing to get vaxxed.
* People were not allowed to select which vaccines they got.
* These are the stats for Dose 2 vaccines given in 2021 along with the total number of deaths until the end of 2022. Note that we compute the deaths later for each age group within 1 year from the shot which is the accurate way to do the mortality rate calculation. So these are just baseline stats. CMR is the crude mortality rate (deaths/doses). If the vaccines are all safe, the CMR numbers should be very similar. CMR deaths per 100,000 persons. Time to die is not factored into this crude estimate, but even without doing that, you can see a HUGE problem.

|Brand | # recipients of Dose 2 in 2021| # of deaths before 2023 | CMR |
|---|---|---|---|
|Pfizer|5,319,895|86,334|1,623|
|Moderna|496,965|16,461|3,312|
|Others|440,266|22,067|5,012 |
|Total| 6,257,126|124,862|1,996|

* The randomization of which vaccine someone got created a perfect real-world randomized clinical trial where we could compute the mortality rates for 1 year after Dose 2 for the two most popular vaccines. 
* We computed the mortality rate ratio (MRR) individually for each birth year. Because Pfizer was the safer vaccine, we treated it as the control (denominator of the ratio)
* We avoided using unvaccinated as controls because people who decide not to be vaccinated generally have higher mortality than those who opt for vaccination.
* Using these records we computed a 1-year mortality rate ratio (MRR) computed as MRR=MR(Moderna) / MR(Pfizer) where the 1 year was measured from the time the person got the shot. This reduce any seasonality bias that would be created with a shorter observation interval. Most people got their dose 2 shots mid-2021.
* Due to the fact we had no death data past 2022, we restricted the dataset to only those people who were given shot #2 in 2021
* To eliminate the rollout differences, we also computed the MRR ignoring Jan and Feb 2021.The results were insignificantly different. We focus on the whole dataset since that gives all other vaccines the edge since priority was given to the sickest people. So the disparity of MR between vaccines is worse than our calculation (i.e., our calculation is the most conservative estimate)
* MMR increased as age decreased as shown here which shows the 5 year rolling average MRR. So 90 means those aged 90 to 94. MRR = the mortality rate of Moderna/mortality rate of Pfizer

|age|MRR|
|---|---|
|90|1.21|
|80|1.21|
|70|1.47|
|60|1.54|
|50|1.67|

* Below age 50, there were too few total deaths to make accurate comparisons between vaccine types
* We also did a time-series cohort analysis for those getting dose 2 which showed that mortality rate increased monotonically for around 35 weeks after the shot before leveling off, but there was also a near doubling in mortality starting immediately after the shots: a t=0, the MR of Moderna was nearly double that of Pfizer.

* Indepdent validation of the same effect:
    * VAERS found similar ratio
    * Fraiman found similar ratio
    * Amount of active ingredient is in similar ratio

### Estimating the MRR of Pfizer vaccine relative to a saline shot based on severe vaccine injury reports of Pfizer vs. Moderna
A good proxy for relative excess mortality is the number of very severe vaccine injuries relative to the number of shots given.

For example, if Pfizer was completely safe, 100% of the vaccine injury reports I received would have been from Moderna. But Pfizer out numbered Moderna 2:1. That means it wasn't anywhere close to being a placebo.

I did a survey of severe vaccine injuries in mid-2022 with over 1,000 responses. The last vaccine taken was Pfizer:Moderna with 2:1 odds. [This has been in public view since that time](https://airtable.com/apphnJcLy0a9DJWhp/shr5NYfxwjBQ9IaaO). I don't know what the distribution was for the people who reported, so I can't compute any ratios for them. 

So that means our conservative assumption that Pfizer was safe is mistken.

VAERS and V-safe data confirm this. Pfizer showed up extensively.

The MRR depends on age with the smallest harms in the elderly which explains why total ACM didn't skyrocket. 

But it does suggest that the harms from both vaccines were comparable (within a factor of 2). 

So if there was a conservative 4:1 distribution of doses, it means that Pfizer's excess deaths are at least half as many as Moderna since otherwise we can't get to a 2:1 ratio of injury reports. 

So this suggests the true MRR vs. placebo vaccine for the COVID vaccines were something like in this table where the MRR is expressed relative to a saline vaccine instead of the Pfizer vaccine as in the previous table.

|age|Pfizer MRR|Moderna MRR|
|---|---|---|
|90|1.10|1.32|
|80|1.10|1.32|
|70|1.23|1.81|
|60|1.27|1.96|
|50|1.33|2.22|

Which means both vaccines were dangerous.

### Implications of this work
   * Even if the Pfizer vaccine is 100% safe, the Moderna vaccine is a disaster and should be immediately pulled worlwide. Every honest member of the medical community should demand this in every country.
   * The Pfizer vaccine isn't safe either. 
   * The FDA, CDC, WHO and medical community needs to publicly admit that they ALL completely missed this huge safety signal that was sitting in plain sight the whole time. This is a huge failure that cost well over 10M lives. It took me only 2 days of analysis work to discover this safety signal once someone told me where I can find the data.
   * There needs to be a call by lawmakers worldwide to make public health data public for the COVID vaccines and other vaccines.
   * We need to have a serious debate on vaccination in general especially the link between vaccines and autism. Why was there never an internal investigation at the CDC when they realized scientists studying this issue were ordered to destroy the evidence linking vaccines and autism?
   * The mainstream press needs to apologize for ignoring scientists who spoke out against the safety of the COVID vaccines. 
   * We can also prove that the Pfizer vaccine was not safe either. This is obvious by looking at the vaccine injury report rates from the Pfizer vaccine which are off the charts. You don't have to look beyond v-safe for this. But I have over 1,000 vaccine injury reports I've collected and if the Pfizer vaccine was safe, all the injuries would be from Moderna. This is not the case. It's not the case in VAERS either.
   * This is a collosal fuck up by the FDA, CDC, NIH, Congress, mainstream media, mainstream medical community, and health authorities worldwide. We need accountability.
   * The vaccine injured should be compensated for their injuries by the drug companies.
   * We need to REVOKE the liability protection for vaccine manufacturers.
   * All states should immediately STOP REQUIRING ALL VACCINES to attend school until such time there is a definitive clinical trial showing vaccinated kids are healthier. Thus far, all studies of the vaxxed vs. unvaxxed 
   * RFK Jr was right the whole time. He should be our next President. He will clean up the mess created by Presidents Biden and Trump.
   * Both Trump and Biden should apologize publicly for the deaths and harm they have caused.
   * Health authorities worldwide need to be held accountable for not looking at their own safety data.
   * The CEOs/Presidents of every company, organization, school, or university that required these shots at any time should either publicly apologize for their mistakes or be fired by their board of directors.
   * The world should start listening to the advice from people who were censored and stop listening to those who never questioned the safety of the COVID vaccine. The latter people are extremely dangerous.
   * What allowed this to happen is the "stay in your lane" mentality of the medical community. If I asked most people to look my work, they'd refuse because it isn't in their strike zone and they'd feel unqualified to evaluate it. But the people who where it is in their strike zone will find a way to dismiss it because it doesn't fit with their belief system that has been drummed into them from the start of med school that vaccines are the safest of all interventions and the CDC and FDA would let us know if there were any safety signals at all.  As a result, any evidence showing harms will be dismissed.
   * Anecdotes were the most immediate and powerful tip off. Never before in my life have I known so many people who were injured or killed by a vaccine. 
   * Once this work is validated by others, any "scientists" who try to attack this analysis without showing a clear flaw, should earn the disrespect of their peers.
   * It would be really nice if someone (or some government) stepped up and provided funding for VSRF so we can continue our work to tell the truth and expose the fraud.


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


### Doing the data analysis
To get the repo including the 50M source data file:
```
git clone https://github.com/skirsch/Czech
```
To generate all the MR stats and time series files:
```
cd code
make
``` 

The build time for all files is about 1 hour and 20 minutes.

To start over from scratch:
```
make clean
```

### Spreadsheets to analyze the time series data and the 1 year mortality data
In the [analysis directory](analysis) are spreadsheets where you can dump the data you generated to verify the results.

The spreadsheets are pre-populated with the data, so you can either re-paste the data or verify the numbers there are what you generated.

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

### Ack
guy who got data
CZ team who wrote the papers
clare craig
norman fenton
fraiman on confounders
paul marik
pierre kory, 
aseem malhotra
andrew briden: fraiman paper



### Negative acknowledgments
**Sir Ian Diamond, head of the UK ONS**  
for ignoring the requests of UK MPs to do a more thorough analysis of the data

**Te Whatu Ora**  
for pressing criminal charges against Barry Young who was just doing his job to protect the people of New Zealand

Santa Clara Department of public health
CDC for refusing to talk to me about any data
FDA for refusing to engage on this data
Former FDA Commissioner Janet Woodcock for blocking me
LinkedIn for giving me a lifetime
Wikipedia for giving me a lifetime ban
Medium for giving me a lifetime ban
The OLD Twitter for giving me two lifetime bans
### References
fraiman
link on from Google doc on randomized
CZ paper on vax vs unvaxxed