# code written by chatgpt, modified by me
# have to read in the files into dataframes.

import pandas as pd
import numpy as np
from scipy.stats import fisher_exact

# US 2000 Standard Population (scaled to sum to 100,000)
us_standard_population_scaled = {
    "0-4": 6914,
    "5-9": 7255,
    "10-14": 7303,
    "15-19": 7217,
    "20-24": 6649,
    "25-29": 6453,
    "30-34": 7104,
    "35-39": 8075,
    "40-44": 8185,
    "45-49": 7212,
    "50-54": 6272,
    "55-59": 4846,
    "60-64": 3880,
    "65-69": 3427,
    "70-74": 3177,
    "75-79": 2700,
    "80-84": 1784,
    "85-89": 974,
    "90-94": 420,
    "95-99": 130,
    "100+": 26
}

# Load the CSV files for Dose 1, Dose 2, and Dose 3
dose_1_file_path = '/mnt/data/vax_5.csv'
dose_2_file_path = '/mnt/data/vax_6.csv'
dose_3_file_path = '/mnt/data/vax_7.csv'

dose_1_data = pd.read_csv(dose_1_file_path)
dose_2_data = pd.read_csv(dose_2_file_path)
dose_3_data = pd.read_csv(dose_3_file_path)

# Function to process each dose dataset with 2021 restriction, case normalization, and calculate odds ratio + CI
def process_dose_data(dose_name, data, brand_column, date_column, deaths_column):
    # Restrict data to vaccinations in 2021
    data = data[data[date_column].str.contains('2021', na=False)]
    
    # Remove rows with missing values in the brand column
    data = data.dropna(subset=[brand_column])
    
    # Normalize brand names and filter for Comirnaty (Pfizer) and Spikevax (Moderna)
    pfizer_data = data[data[brand_column].str.lower().str.startswith('comirnaty')]
    moderna_data = data[data[brand_column].str.lower().str.startswith('spikevax')]

    # Group by age and sum shots and deaths
    pfizer_grouped = pfizer_data.groupby('age').agg(
        shots_total=('shots', 'sum'),
        deaths_total=(deaths_column, 'sum')
    ).reset_index()

    moderna_grouped = moderna_data.groupby('age').agg(
        shots_total=('shots', 'sum'),
        deaths_total=(deaths_column, 'sum')
    ).reset_index()

    # Add the standard population to both datasets
    pfizer_grouped['standard_population'] = pfizer_grouped['age'].map(us_standard_population_scaled)
    moderna_grouped['standard_population'] = moderna_grouped['age'].map(us_standard_population_scaled)

    # Calculate the weighted MR for each age group
    pfizer_grouped['MR'] = (pfizer_grouped['deaths_total'] / pfizer_grouped['shots_total']) * 100000
    pfizer_grouped['weighted_MR'] = (pfizer_grouped['MR'] * pfizer_grouped['standard_population']) / 100000

    moderna_grouped['MR'] = (moderna_grouped['deaths_total'] / moderna_grouped['shots_total']) * 100000
    moderna_grouped['weighted_MR'] = (moderna_grouped['MR'] * moderna_grouped['standard_population']) / 100000

    # Calculate ASMR for Pfizer and Moderna
    ASMR_pfizer = pfizer_grouped['weighted_MR'].sum()
    ASMR_moderna = moderna_grouped['weighted_MR'].sum()

    # Calculate odds ratio and confidence intervals
    total_pfizer_shots = pfizer_grouped['shots_total'].sum()
    total_moderna_shots = moderna_grouped['shots_total'].sum()
    
    total_pfizer_deaths = pfizer_grouped['deaths_total'].sum()
    total_moderna_deaths = moderna_grouped['deaths_total'].sum()
    
    # Number of people who survived (shots minus deaths)
    pfizer_alive = total_pfizer_shots - total_pfizer_deaths
    moderna_alive = total_moderna_shots - total_moderna_deaths
    
    # Construct Fisher matrix and calculate odds ratio
    fisher_matrix = [[pfizer_alive, total_pfizer_deaths], [moderna_alive, total_moderna_deaths]]
    oddsratio, p_value = fisher_exact(fisher_matrix)
    
    # Calculate 95% Confidence Interval for Odds Ratio
    log_or = np.log(oddsratio)
    se_log_or = np.sqrt((1 / pfizer_alive) + (1 / total_pfizer_deaths) + (1 / moderna_alive) + (1 / total_moderna_deaths))
    ci_95_lower = np.exp(log_or - 1.96 * se_log_or)
    ci_95_upper = np.exp(log_or + 1.96 * se_log_or)

    # Return the results in a dictionary
    return {
        'dose_name': dose_name,
        'pfizer_grouped': pfizer_grouped,
        'moderna_grouped': moderna_grouped,
        'ASMR_pfizer': ASMR_pfizer,
        'ASMR_moderna': ASMR_moderna,
        'odds_ratio': oddsratio,
        'ci_95_lower': ci_95_lower,
        'ci_95_upper': ci_95_upper
    }

# Process Dose 1, 2, and 3 data, restricting to 2021 and handling brand variations
dose_1_results = process_dose_data('Dose 1', dose_1_data, 'brand_1', 'date_1', 'deaths_within_365d_d1')
dose_2_results = process_dose_data('Dose 2', dose_2_data, 'brand_2', 'date_2', 'deaths_within_365d_d2')
dose_3_results = process_dose_data('Dose 3', dose_3_data, 'brand_3', 'date_3', 'deaths_within_365d_d3')

# Prepare Excel output with updated restrictions
with pd.ExcelWriter("/mnt/data/vaccine_dose_analysis_2021_with_odds_ratios.xlsx") as writer:
    # Write each dose's results to separate sheets
    dose_1_results['pfizer_grouped'].to_excel(writer, sheet_name='Dose 1 Pfizer', index=False)
    dose_1_results['moderna_grouped'].to_excel(writer, sheet_name='Dose 1 Moderna', index=False)

    dose_2_results['pfizer_grouped'].to_excel(writer, sheet_name='Dose 2 Pfizer', index=False)
    dose_2_results['moderna_grouped'].to_excel(writer, sheet_name='Dose 2 Moderna', index=False)

    dose_3_results['pfizer_grouped'].to_excel(writer, sheet_name='Dose 3 Pfizer', index=False)
    dose_3_results['moderna_grouped'].to_excel(writer, sheet_name='Dose 3 Moderna', index=False)

    # Summary sheet including odds ratios and confidence intervals
    summary_data = {
        'Dose': ['Dose 1', 'Dose 2', 'Dose 3'],
        'ASMR Pfizer': [dose_1_results['ASMR_pfizer'], dose_2_results['ASMR_pfizer'], dose_3_results['ASMR_pfizer']],
        'ASMR Moderna': [dose_1_results['ASMR_moderna'], dose_2_results['ASMR_moderna'], dose_3_results['ASMR_moderna']],
        'Odds Ratio': [dose_1_results['odds_ratio'], dose_2_results['odds_ratio'], dose_3_results['odds_ratio']],
        '95% CI Lower': [dose_1_results['ci_95_lower'], dose_2_results['ci_95_lower'], dose_3_results['ci_95_lower']],
        '95% CI Upper': [dose_1_results['ci_95_upper'], dose_2_results['ci_95_upper'], dose_3_results['ci_95_upper']]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

# Provide the download link for the generated Excel file
"/mnt/data/vaccine_dose_analysis_2021_with_odds_ratios.xlsx"
