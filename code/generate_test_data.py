#!/usr/bin/env python3
"""
Generate test data for KCOR analysis validation

Dose 0: deaths per week starting at 1000, decreasing by factor 0.999 each week
Dose 2: deaths per week starting at 1000, increasing by factor 1.003 each week

This creates a controlled test case where we know exactly what the trends should be.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta

def generate_test_data(weeks=100, start_date=date(2020, 1, 1)):
    """Generate test data with known weekly trends"""
    
    # Create weekly dates
    dates = [start_date + timedelta(weeks=i) for i in range(weeks)]
    
    # Generate deaths per week with known trends
    dose_0_deaths = []
    dose_2_deaths = []
    
    for week in range(weeks):
        # Dose 0: starts at 1000, decreases by factor 0.999 each week
        # Use a more reasonable decay to avoid extremely small numbers
        dose_0_deaths.append(max(1, int(1000 * (0.999 ** week))))
        
        # Dose 2: starts at 1000, increases by factor 1.003 each week  
        # Use a more reasonable growth factor to avoid overflow
        dose_2_deaths.append(max(1, int(1000 * (1.001 ** week))))
    
    # Create realistic population data starting at 1M people per dose group
    # Population decreases over time due to deaths
    dose_0_population = []
    dose_2_population = []
    
    # Start with 1M people in each group
    pop_0 = 1000000
    pop_2 = 1000000
    
    for week in range(weeks):
        dose_0_population.append(pop_0)
        dose_2_population.append(pop_2)
        
        # Update population for next week (subtract deaths)
        pop_0 = max(0, pop_0 - dose_0_deaths[week])
        pop_2 = max(0, pop_2 - dose_2_deaths[week])
    
    # Person-time is the average population over the week
    dose_0_person_time = [pop for pop in dose_0_population]
    dose_2_person_time = [pop for pop in dose_2_population]
    
    # Create DataFrame
    data = []
    for i, (date_val, d0_deaths, d2_deaths, d0_pt, d2_pt) in enumerate(zip(
        dates, dose_0_deaths, dose_2_deaths, dose_0_person_time, dose_2_person_time)):
        
        # Add dose 0 data
        data.append({
            'DateDied': date_val.strftime('%Y-%m-%d'),
            'YearOfBirth': 1940,
            'Alive': d0_pt,  # This is the population at start of week
            'Dead': d0_deaths,
            'Dose': 0
        })
        
        # Add dose 2 data
        data.append({
            'DateDied': date_val.strftime('%Y-%m-%d'),
            'YearOfBirth': 1940,
            'Alive': d2_pt,  # This is the population at start of week
            'Dead': d2_deaths,
            'Dose': 2
        })
    
    df = pd.DataFrame(data)
    
    # Add some random noise to make it more realistic
    np.random.seed(42)  # For reproducible results
    noise_factor = 0.1  # 10% noise
    
    for dose in [0, 2]:
        mask = df['Dose'] == dose
        noise = np.random.normal(1, noise_factor, mask.sum())
        # Apply noise and handle any NaN values
        df.loc[mask, 'Dead'] = np.maximum(0, df.loc[mask, 'Dead'] * noise).fillna(0).astype(int)
        df.loc[mask, 'Alive'] = np.maximum(0, df.loc[mask, 'Alive'] * noise).fillna(0).astype(int)
    
    # Show trend over time
    print("\nTrend analysis:")
    print(f"After 52 weeks: Dose 0 = {1000 * (0.999 ** 52):.1f}, Dose 2 = {1000 * (1.001 ** 52):.1f}")
    print(f"After 104 weeks: Dose 0 = {1000 * (0.999 ** 104):.1f}, Dose 2 = {1000 * (1.001 ** 104):.1f}")
    print(f"After 208 weeks: Dose 0 = {1000 * (0.999 ** 208):.1f}, Dose 2 = {1000 * (1.001 ** 208):.1f}")
    
    # Show population trends
    print("\nPopulation trends:")
    print(f"Starting population: 1,000,000 per dose group")
    print(f"After 52 weeks: Dose 0 = {1000000 - sum(dose_0_deaths[:52]):,}, Dose 2 = {1000000 - sum(dose_2_deaths[:52]):,}")
    print(f"After 104 weeks: Dose 0 = {1000000 - sum(dose_0_deaths[:104]):,}, Dose 2 = {1000000 - sum(dose_2_deaths[:104]):,}")
    print(f"After 208 weeks: Dose 0 = {1000000 - sum(dose_0_deaths[:208]):,}, Dose 2 = {1000000 - sum(dose_2_deaths[:208]):,}")
    
    return df

def main():
    """Generate test data and save to Excel"""
    
    print("Generating test data...")
    print("Dose 0: deaths decreasing by factor 0.999 per week")
    print("Dose 2: deaths increasing by factor 1.001 per week")
    
    # Generate 4 years (208 weeks) of data
    df = generate_test_data(weeks=208)
    
    # Save to Excel
    output_file = '../analysis/KCOR_test_data.xlsx'
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Create a sheet name that matches the expected format (e.g., "2020_01")
        sheet_name = "2020_01"  # This will be parsed as enrollment date 2020-01-06
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Test data saved to: {output_file}")
    print(f"Sheet name: {sheet_name}")
    print(f"Data shape: {df.shape}")
    print(f"Date range: {df['DateDied'].min()} to {df['DateDied'].max()}")
    
    # Show sample of the trends
    print("\nSample trends (first 10 weeks):")
    sample = df[df['Dose'].isin([0, 2])].groupby(['DateDied', 'Dose'])['Dead'].sum().unstack()
    print(sample.head(10))

if __name__ == "__main__":
    main()
