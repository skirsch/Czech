#!/usr/bin/env python3
"""
prepare_czech_tte_inputs.py — Build baseline.csv, vax.csv, events.csv for czech_tte.py from the Czech raw CSV,
and emit a validation report (precheck.txt / precheck.csv).

Key features:
- Mirrors KCOR.py date handling (ISO week -> Monday) and field names.
- Uses DateOfDeath as ACM; Date_COVID_death as COVID-coded.
- Optional t0 for cohorting in the report; if provided, we compute vaccinated_at_t0 and early-window deaths.

Outputs (in --outdir):
- baseline.csv, vax.csv, events.csv
- precheck.txt: human-readable summary
- precheck.csv: machine-readable cohort metrics by vaccinated_at_t0 (0/1)

Usage:
    cd code; python czech_tte_prepare_inputs.py --input ../data/vax_24.csv --outdir ./tte_inputs --t0 2021-06-14
"""

import argparse
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

def iso_week_to_date(iso_week_str):
    """Convert 'YYYY-WW' (or 'YYYYWW') to Monday date of that ISO week. Pass through YYYY-MM-DD if present."""
    if pd.isna(iso_week_str):
        return pd.NaT
    s = str(iso_week_str).strip()
    if not s:
        return pd.NaT
    # If looks like a full date, try parse
    if len(s) >= 8 and s.count('-') >= 2:
        d = pd.to_datetime(s, errors='coerce')
        return d.normalize() if pd.notna(d) else pd.NaT
    # Normalize ISO-week formats
    s = s.replace('W','').replace(' ', '')
    if '-' not in s and len(s) >= 6:
        s = f"{s[:4]}-{s[4:6]}"
    try:
        d = pd.to_datetime(s + '-1', format='%G-%V-%u', errors='coerce')
        return d.normalize() if pd.notna(d) else pd.NaT
    except Exception:
        return pd.NaT

def parse_year(y):
    y_str = str(y)
    if len(y_str) < 4:
        return np.nan
    try:
        year = int(y_str[:4])
        if 1900 <= year <= datetime.now().year:
            return year
    except Exception:
        pass
    return np.nan

def qstats(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return dict(mean=np.nan, sd=np.nan, p25=np.nan, p50=np.nan, p75=np.nan)
    return dict(
        mean=float(np.mean(x)),
        sd=float(np.std(x, ddof=1)) if x.size > 1 else 0.0,
        p25=float(np.nanpercentile(x, 25)),
        p50=float(np.nanpercentile(x, 50)),
        p75=float(np.nanpercentile(x, 75)),
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Path to Czech raw CSV (same file KCOR.py uses)')
    ap.add_argument('--outdir', required=True, help='Output directory for baseline.csv, vax.csv, events.csv')
    ap.add_argument('--t0', required=False, default=None, help='t0 date (YYYY-MM-DD) to compute age at t0 and cohort report (optional)')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load raw
    df = pd.read_csv(args.input, low_memory=False)

    # If columns match KCOR schema length, rename to English
    english_cols = [
        'ID', 'Infection', 'Gender', 'YearOfBirth', 'DateOfPositiveTest', 'DateOfResult', 'Recovered', 'Date_COVID_death',
        'Symptom', 'TestType', 'Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose',
        'Date_FifthDose', 'Date_SixthDose', 'Date_SeventhDose', 'VaccineCode_FirstDose', 'VaccineCode_SecondDose',
        'VaccineCode_ThirdDose', 'VaccineCode_FourthDose', 'VaccineCode_FifthDose', 'VaccineCode_SixthDose',
        'VaccineCode_SeventhDose', 'PrimaryCauseHospCOVID', 'bin_Hospitalization', 'min_Hospitalization',
        'days_Hospitalization', 'max_Hospitalization', 'bin_ICU', 'min_ICU', 'days_ICU', 'max_ICU', 'bin_StandardWard',
        'min_StandardWard', 'days_StandardWard', 'max_StandardWard', 'bin_Oxygen', 'min_Oxygen', 'days_Oxygen',
        'max_Oxygen', 'bin_HFNO', 'min_HFNO', 'days_HFNO', 'max_HFNO', 'bin_MechanicalVentilation_ECMO',
        'min_MechanicalVentilation_ECMO', 'days_MechanicalVentilation_ECMO', 'max_MechanicalVentilation_ECMO',
        'Mutation', 'DateOfDeath', 'Long_COVID', 'DCCI'
    ]
    if len(df.columns) == len(english_cols):
        df.columns = english_cols

    # Convert all Date* columns via ISO-week logic
    date_cols = [c for c in df.columns if c.startswith('Date')]
    for c in date_cols:
        df[c] = df[c].apply(iso_week_to_date)

    # Keep Infection <= 1 to avoid multiple-episode duplicates
    if 'Infection' in df.columns:
        df = df[(df['Infection'].fillna(0).astype(float) <= 1)]

    # Sex map
    sex_map = {'M': 'M', 'F': 'F', 'Male': 'M', 'Female': 'F', 'm': 'M', 'f': 'F', 1: 'M', 2: 'F'}
    sex = df['Gender'].map(sex_map).fillna(df['Gender'].astype(str).str.upper().str[0])

    # Age at t0 (preferred); if missing, fallback to 2022-01-01
    if args.t0:
        t0 = pd.to_datetime(args.t0).normalize()
        ref_year = t0.year
    else:
        t0 = None
        ref_year = 2022
    yob = df['YearOfBirth'].apply(parse_year)
    age = (ref_year - yob).astype('float')
    age = age.where(np.isfinite(age), np.nan)

    # Prior infection earliest
    earliest_inf = df[['ID','DateOfPositiveTest']].dropna().groupby('ID').DateOfPositiveTest.min()

    # ----- Build outputs -----
    baseline = pd.DataFrame({'person_id': df['ID'], 'sex': sex, 'age': age}).drop_duplicates('person_id')
    baseline = baseline.merge(earliest_inf.rename('prior_infection_date'), left_on='person_id', right_index=True, how='left')

    # Vaccinations long
    dose_cols = [
        ('Date_FirstDose','VaccineCode_FirstDose',1),
        ('Date_SecondDose','VaccineCode_SecondDose',2),
        ('Date_ThirdDose','VaccineCode_ThirdDose',3),
        ('Date_FourthDose','VaccineCode_FourthDose',4),
        ('Date_FifthDose','VaccineCode_FifthDose',5),
        ('Date_SixthDose','VaccineCode_SixthDose',6),
        ('Date_SeventhDose','VaccineCode_SeventhDose',7),
    ]
    vax_rows = []
    for date_col, brand_col, dnum in dose_cols:
        if date_col in df.columns:
            sub = df[['ID', date_col]].copy()
            sub = sub.rename(columns={'ID':'person_id', date_col:'vax_date'})
            if brand_col in df.columns:
                sub['brand'] = df[brand_col].values
            else:
                sub['brand'] = np.nan
            sub = sub[~sub['vax_date'].isna()]
            sub['dose_number'] = dnum
            vax_rows.append(sub[['person_id','dose_number','vax_date','brand']])
    vax = pd.concat(vax_rows, axis=0, ignore_index=True) if vax_rows else pd.DataFrame(columns=['person_id','dose_number','vax_date','brand'])

    # Events (death_covid / death_noncovid)
    ev_rows = []
    if 'Date_COVID_death' in df.columns:
        covid = df[['ID','Date_COVID_death']].dropna().rename(columns={'ID':'person_id','Date_COVID_death':'event_date'})
        covid['event_type'] = 'death_covid'
        ev_rows.append(covid[['person_id','event_date','event_type']])
    if 'DateOfDeath' in df.columns:
        tmp = df[['ID','DateOfDeath','Date_COVID_death']].rename(columns={'ID':'person_id'})
        noncov = tmp[(~tmp['DateOfDeath'].isna()) & (tmp['Date_COVID_death'].isna())][['person_id','DateOfDeath']]
        noncov = noncov.rename(columns={'DateOfDeath':'event_date'})
        noncov['event_type'] = 'death_noncovid'
        ev_rows.append(noncov[['person_id','event_date','event_type']])
    events = pd.concat(ev_rows, axis=0, ignore_index=True) if ev_rows else pd.DataFrame(columns=['person_id','event_date','event_type'])

    # Save
    outdir = args.outdir
    baseline_path = os.path.join(outdir, 'baseline.csv')
    vax_path = os.path.join(outdir, 'vax.csv')
    events_path = os.path.join(outdir, 'events.csv')
    baseline.to_csv(baseline_path, index=False, date_format='%Y-%m-%d')
    vax.to_csv(vax_path, index=False, date_format='%Y-%m-%d')
    events.to_csv(events_path, index=False, date_format='%Y-%m-%d')

    print(f"Written: {baseline_path}  (N={len(baseline)})")
    print(f"Written: {vax_path}       (rows={len(vax)})")
    print(f"Written: {events_path}    (rows={len(events)})")

    # ----- Validation report (if t0 provided) -----
    precheck_txt = os.path.join(outdir, 'precheck.txt')
    precheck_csv = os.path.join(outdir, 'precheck.csv')

    lines = []
    rows = []

    lines.append("=== Precheck report ===")
    if t0 is None:
        lines.append("No --t0 provided; cohort-at-t0 and early-window checks skipped.")
        with open(precheck_txt, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"Written: {precheck_txt}")
        sys.exit(0)

    lines.append(f"t0: {t0.date()}")
    # First dose per person
    first_dose = vax.sort_values(['person_id','dose_number']).groupby('person_id').vax_date.min()
    merged = baseline.merge(first_dose.rename('first_dose_date'), left_on='person_id', right_index=True, how='left')

    merged['vaccinated_at_t0'] = ((~merged['first_dose_date'].isna()) & (merged['first_dose_date'] <= t0)).astype(int)
    merged['prior_inf_at_t0'] = ((~merged['prior_infection_date'].isna()) & (merged['prior_infection_date'] < t0)).astype(int)

    # Derive ACM death date
    ev_covid = events[events['event_type']=='death_covid'][['person_id','event_date']].rename(columns={'event_date':'death_covid_date'})
    ev_nonc  = events[events['event_type']=='death_noncovid'][['person_id','event_date']].rename(columns={'event_date':'death_noncovid_date'})
    acm = merged[['person_id']].copy()
    acm = acm.merge(ev_covid, on='person_id', how='left').merge(ev_nonc, on='person_id', how='left')
    acm['death_acm_date'] = acm[['death_covid_date','death_noncovid_date']].min(axis=1)

    merged = merged.merge(acm[['person_id','death_covid_date','death_noncovid_date','death_acm_date']], on='person_id', how='left')

    # Early windows relative to t0
    def in_window(date_series, start, end):
        return (date_series.notna()) & (date_series >= start) & (date_series <= end)

    win14 = (t0, t0 + pd.Timedelta(days=14))
    win180 = (t0, t0 + pd.Timedelta(days=180))

    merged['acm_0_14'] = in_window(merged['death_acm_date'], *win14).astype(int)
    merged['covid_0_14'] = in_window(merged['death_covid_date'], *win14).astype(int)
    merged['noncovid_0_14'] = in_window(merged['death_noncovid_date'], *win14).astype(int)

    merged['noncovid_0_180'] = in_window(merged['death_noncovid_date'], *win180).astype(int)

    # Group summaries
    total = len(merged)
    n_vax = int((merged['vaccinated_at_t0']==1).sum())
    n_unv = int((merged['vaccinated_at_t0']==0).sum())
    lines.append(f"N total: {total} | vaccinated_at_t0=1: {n_vax} ({n_vax/total:.1%}), =0: {n_unv} ({n_unv/total:.1%})")

    for g in [0,1]:
        sub = merged[merged['vaccinated_at_t0']==g]
        ages = qstats(sub['age'])
        sex_counts = sub['sex'].fillna('U').value_counts(dropna=False).to_dict()
        pi_counts = sub['prior_inf_at_t0'].value_counts().to_dict()
        acm14 = int(sub['acm_0_14'].sum())
        cov14 = int(sub['covid_0_14'].sum())
        ncv14 = int(sub['noncovid_0_14'].sum())
        ncv180 = int(sub['noncovid_0_180'].sum())

        rate14 = (acm14 / len(sub) * 1e5) if len(sub)>0 else np.nan  # per 100k in first 14d
        rate180_ncv = (ncv180 / len(sub) * 1e5) if len(sub)>0 else np.nan

        lines.append(f"\nGroup vaccinated_at_t0={g}")
        lines.append(f"  N={len(sub)} | age mean={ages['mean']:.2f}, sd={ages['sd']:.2f}, median={ages['p50']:.2f} (IQR {ages['p25']:.2f}-{ages['p75']:.2f})")
        lines.append(f"  sex counts: {sex_counts}")
        lines.append(f"  prior infection at t0: {pi_counts.get(1,0)} yes / {pi_counts.get(0,0)} no")
        lines.append(f"  deaths 0–14d: ACM={acm14}, COVID={cov14}, non-COVID={ncv14} (rate per 100k={rate14:.2f})")
        lines.append(f"  non-COVID deaths 0–180d: {ncv180} (rate per 100k={rate180_ncv:.2f})")

        rows.append({
            'vaccinated_at_t0': g,
            'N': len(sub),
            'age_mean': ages['mean'],
            'age_sd': ages['sd'],
            'age_p25': ages['p25'],
            'age_p50': ages['p50'],
            'age_p75': ages['p75'],
            'sex_M': sex_counts.get('M', 0),
            'sex_F': sex_counts.get('F', 0),
            'sex_other': sum(v for k,v in sex_counts.items() if k not in ['M','F']),
            'prior_inf_yes': pi_counts.get(1,0),
            'prior_inf_no': pi_counts.get(0,0),
            'acm_0_14': acm14,
            'covid_0_14': cov14,
            'noncovid_0_14': ncv14,
            'noncovid_0_180': ncv180,
            'rate_per100k_acm_0_14': rate14,
            'rate_per100k_noncovid_0_180': rate180_ncv
        })

    with open(precheck_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    pd.DataFrame(rows).to_csv(precheck_csv, index=False)

    print(f"Written: {precheck_txt}")
    print(f"Written: {precheck_csv}")

if __name__ == '__main__':
    main()
