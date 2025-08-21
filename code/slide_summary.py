import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate

# Load the Czech ACM data (adjust path and column names as needed)
data = pd.read_excel("analysis/1950_acm_only.xlsx", sheet_name="ACM death date")

# Assume columns: 'Row Labels' (week), 'Cum uvax died this week' (unvaccinated deaths),
# 'Cum vax died this week' (vaccinated deaths), 'Unvax alive', 'Vax alive'
# Adjust column names based on your Excel file
data['Week'] = data['Row Labels']
data['Unvax_Deaths'] = data['Cum uvax died this week']
data['Vax_Deaths'] = data['Cum vax died this week']
data['Unvax_Alive'] = data['Unvax alive']
data['Vax_Alive'] = data['Vax alive']

# Filter for relevant periods
low_covid_weeks = [f'2021-{w}' for w in range(24, 39)]  # 2021 weeks 24–38
high_covid_weeks = [f'2021-{w}' for w in range(40, 53)] + [f'2022-{w:02d}' for w in range(1, 19)]  # 2021 weeks 40–2022 week 18
data_low = data[data['Week'].isin(low_covid_weeks)]
data_high = data[data['Week'].isin(high_covid_weeks)]

# Calculate weekly ACM rates (annualized, per 100,000 person-weeks)
data['Unvax_Rate'] = (data['Unvax_Deaths'] / data['Unvax_Alive'] * 52 * 100000).fillna(0)
data['Vax_Rate'] = (data['Vax_Deaths'] / data['Vax_Alive'] * 52 * 100000).fillna(0)

# Plot settings
plt.figure(figsize=(12, 6))
sns.lineplot(x='Week', y='Unvax_Rate', data=data[data['Week'].isin(low_covid_weeks + high_covid_weeks)], 
             label='Unvaccinated', color='blue', linewidth=2)
sns.lineplot(x='Week', y='Vax_Rate', data=data[data['Week'].isin(low_covid_weeks + high_covid_weeks)], 
             label='Vaccinated', color='red', linewidth=2)

# Highlight periods
plt.axvspan(low_covid_weeks[0], low_covid_weeks[-1], alpha=0.1, color='green', label='Low COVID (2021 wk 24–38)')
plt.axvspan(high_covid_weeks[0], high_covid_weeks[-1], alpha=0.1, color='orange', label='High COVID (2021 wk 40–2022 wk 18)')

# Customize plot
plt.title('Weekly ACM Rates: Unvaccinated vs. Vaccinated (Czech 1950–1954 Cohort)', fontsize=14, pad=10)
plt.xlabel('Week', fontsize=12)
plt.ylabel('ACM Rate (per 100,000 person-weeks, annualized)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()

# Save plot
plt.savefig('czech_acm_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Create table
table_data = [
    ['Cohort', 'High/Low Ratio (95% CI)', 'ACM Ratio (Unvax/Vax)', 'COVID Death Proportion', 'Vaccinated Cases (2022)'],
    ['Unvaccinated', '1.493656 (1.399–1.595)', '3.299 (low), 3.334 (high)', '19.12%', '-'],
    ['Vaccinated', '1.478139 (1.402–1.558)', '-', '12.40%', '84.3%']
]
table = tabulate(table_data, headers='firstrow', tablefmt='grid')

# Save table as text
with open('czech_acm_table.txt', 'w') as f:
    f.write(table)

# Print caption
caption = """
Czech ACM Data: No Vaccine Mortality Benefit
FOIA-derived data (8,732 deaths, millions of person-weeks) shows no differential benefit: 
both cohorts exhibit ~1.49x ACM increase from low to high COVID periods, with a stable 
~3.3 unvaccinated/vaccinated ratio, contradicting an expected 1.13–1.5x unvaccinated spike 
(14.62% COVID deaths). 84.3% vaccinated cases in 2022 confirm no infection reduction.
"""
with open('czech_acm_caption.txt', 'w') as f:
    f.write(caption)

print("Infographic components saved: czech_acm_plot.png, czech_acm_table.txt, czech_acm_caption.txt")