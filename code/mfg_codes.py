# vax type and value to record in the MFG column
PFIZER="PF"     # 5586979 got shot 1
MODERNA="MO"    #  526453 got shot 1
ASTRA="AZ"      #  447450 got shot 1
JANN="JA"       #  412314 got shot 1
NOVAVAX="NOVA"  #    5425 got shot 1 but only in 2022 so doesn't appear in Study 2. 14 died. MR of just 258, but there wasn't a full year to die.

OTHER="OTHER"
UNVAX=""  # didn't get a shot for dose 1, 2, or 3 (make sure dropna=false on groupby); will replace blank with blank
PLACEBO="PLACEBO" # unvaccinated so treat as placebo shot on Jan 1, 2022 or whatever date for the comparison

# Define the range of allowable values
R_MFG = [PFIZER, MODERNA, ASTRA, JANN, NOVAVAX, OTHER, UNVAX]
        
MFG_DICT = {'CO01': PFIZER, 'CO02': MODERNA, 'CO08':PFIZER, 'CO09': PFIZER, 'CO15': MODERNA, 'CO16': PFIZER, 
            'CO19': MODERNA, 'CO20': PFIZER, 'CO21':PFIZER, 'CO23':PFIZER,
             'CO03': ASTRA, 'CO04':JANN, 'CO07': NOVAVAX, '': UNVAX, 
             UNVAX: UNVAX, PLACEBO: PLACEBO}

def parse_mfg(mfg):
    if not mfg:
        return UNVAX
    try:
        return MFG_DICT[mfg]
    except:
        return OTHER
    
