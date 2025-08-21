# Czech Epidemiological Data Analysis - AI Agent Instructions

## Project Overview
This repository analyzes Czech COVID-19 vaccination and mortality data using record-level data from over 10M citizens. The project uses two main analytical approaches:
- **KCOR Analysis**: Dose group enrollment analysis with Excel output by enrollment dates
- **Survival Analysis**: Time-to-event Cox proportional hazards models for mortality risk

## Key Data Conventions

### Date Formats & Parsing
- **ISO Week Format**: Dates like "2021-24" represent ISO week 24 of 2021
- **Parsing Pattern**: Use `pd.to_datetime(date_str + '-1', format='%G-%V-%u')` to convert ISO weeks
- **Date Storage**: Convert all dates to `datetime.date` objects for consistency
- **Missing Dates**: Use `pd.NaT` or `None` for missing date values

### Missing Value Conventions
- **YearOfBirth**: Use `-1` for missing birth years (int type)
- **Date Fields**: Use `pd.NaT` or leave as NaN
- **Categorical Fields**: Use `'NONE'` string for missing categories when grouping

### Birth Year Parsing
- **Range Format**: Handle "1920-1924" format by extracting first 4 characters: `int(str(value)[:4])`
- **Single Digit**: Values with length 1 should return -1 (missing)
- **Validation**: Ensure years are between 1900 and current year

## Core Analysis Patterns

### KCOR.py Dose Group Assignment
```python
# Vectorized dose group assignment (preferred over .apply())
for i, enroll_date in enumerate(enrollment_dates):
    mask = (dose_dates <= enroll_date) & dose_dates.notna()
    dose_groups = np.where(mask, i, dose_groups)

# YearOfBirth parsing function
def parse_year(value):
    if len(str(value)) == 1: return -1
    return int(str(value)[:4])
```

### Excel Output Structure
- **Multi-sheet**: One sheet per enrollment date (ISO week format as sheet name)
- **Index Columns**: `YearOfBirth`, `DateOfDeath`, `Gender`
- **Dose Columns**: `dose_0` through `dose_6` (counts per dose group)
- **Summary Column**: `Count` (total across all dose groups)

### Survival Analysis (czech_tte.py)
- **Cox Models**: Always encode categorical variables before fitting
```python
# Handle categorical variables before Cox regression
if categorical_cols:
    data = pd.get_dummies(data, columns=categorical_cols, drop_first=True, dtype=float)
```
- **IPTW Weighting**: Use `weights_col="iptw"` for inverse probability weighting
- **Performance**: Use `robust=False` during development, `robust=True` for final analysis

## Performance Optimization Patterns

### Vectorization Over Iteration
```python
# PREFERRED: Vectorized operations
dose_mask = (dose_dates <= pd.Timestamp(enroll_date))
dose_group = dose_mask.apply(lambda row: row[::-1].idxmax() if row.any() else None, axis=1)

# AVOID: Row-wise .apply() with complex logic
# df.apply(lambda row: expensive_function(row), axis=1)
```

### Memory Management
- Process enrollment dates sequentially, don't load all data into memory
- Use appropriate data types (int32 for counts, float32 for rates when precision allows)
- Drop intermediate DataFrames when no longer needed

### Cox Model Performance
- **Development**: Set `robust=False` for faster iteration
- **Production**: Use `robust=True` for proper variance estimation with weights
- **Sample Reduction**: Use `.sample(frac=0.1)` for testing with large datasets

## Common Data Processing Patterns

### Death Analysis Time Windows
```python
# Standard time thresholds for mortality analysis
thresholds = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660, 690, 720, 750]

# Death within threshold calculation
for threshold in thresholds:
    data[f'death_within_{threshold}d_d{dose}'] = data[f'days_until_death_from_d{dose}'] <= threshold
```

### Grouping and Aggregation
```python
# Standard grouping pattern for mortality analysis
group_cols = ['YearOfBirth', 'DateOfDeath', 'Gender']
summary = df.groupby(group_cols, dropna=False)[value_cols].sum().reset_index()
```

## File Naming and Output Conventions

### Analysis Output Files
- **KCOR Results**: `KCOR.main.csv` (main output), multi-sheet Excel by enrollment date
- **Survival Analysis**: Results in `--outdir` with `summary.txt`, KM plots (PNG), Cox results
- **Time Series**: `vax_*.csv` files for different grouping strategies

### Input Data Format
- **Czech Records**: `CR_records.csv.xz` (compressed source data)
- **Survival Inputs**: Separate CSV files for `baseline`, `vax`, `events`

## Critical Command Patterns

### Make Commands
```bash
# Full analysis pipeline
make

# KCOR analysis only
make kcor

# Time series analysis
make analysis
```

### Survival Analysis Command
```bash
python czech_tte.py --baseline ./tte_inputs/baseline.csv --vax ./tte_inputs/vax.csv --events ./tte_inputs/events.csv --t0 2021-06-14 --t1 2022-06-14 --age-min 60 --age-max 89 --covars age,sex,prior_infection --outdir ./results
```

## Error Prevention Guidelines

### Date Parsing Errors
- Always add `+ '-1'` suffix to ISO week strings before parsing
- Use `format='%G-%V-%u'` for ISO week parsing (not standard `%Y-%U-%u`)
- Wrap date parsing in try-except blocks for robust error handling

### Cox Model Errors
- **Categorical Variables**: Always convert string categories to dummy variables
- **Missing Values**: Drop rows with NaN in critical columns before Cox fitting
- **Convergence**: Check for perfect separation in binary outcomes

### Memory/Performance Issues
- **Large DataFrames**: Process in chunks or use vectorized operations
- **Excel Output**: Use `xlsxwriter` engine for better performance with large sheets
- **Cox Models**: Consider sampling for exploratory analysis before full runs

## Data Quality Checks

### Always Validate
- Check for date consistency (death date >= vaccination date)
- Verify dose sequences are logical (dose 2 > dose 1 date)
- Validate age ranges are reasonable (typically 18-100 years)
- Check for duplicate person IDs in analysis cohorts

### Debug Output Patterns
```python
print(f"Processing enrollment date {enroll_str} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total records: {len(df)}")
print(f"Deaths in cohort: {df['event_acm'].sum()}")
print(f"Follow-up person-days: {df['time'].sum()}")
```

## Statistical Analysis Standards

### Mortality Rate Calculations
- **Crude Mortality Rate (CMR)**: Deaths per 100,000 person-years
- **Age-Standardized Mortality Rate (ASMR)**: Use US 2000 standard population
- **Hazard Ratios**: Report with 95% confidence intervals
- **Risk Ratios**: Kaplan-Meier survival at specific time points (e.g., 365 days)

### Model Assumptions
- Cox models assume proportional hazards - check with Schoenfeld residuals if needed
- IPTW assumes no unmeasured confounding - validate with negative controls
- Missing data should be handled explicitly (not ignored)
