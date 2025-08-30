#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# KCOR_analysis_KCOR.py
# Extends your KCOR_analysis to add weekly KCOR (Dose>0 vs Dose=0) with 95% CIs
# for EACH birth_year, per sheet. It detrends the log-rate ratio anchored to 2023 (flat)
# and lets you set N weeks offset after enrollment and horizon length.
#
# Usage:
#   python KCOR_analysis_KCOR.py <input_excel> [output_excel] [N_weeks_offset] [horizon_weeks]
# Example:
#   python KCOR_analysis_KCOR.py KCOR_output.xlsx KCOR_with_ASMR_byDose_KCOR.xlsx 72 52
# 
# Default behavior: Wait 72 weeks after enrollment, then analyze 52 weeks of data.
# Detrending uses 2023 data if available, otherwise weeks 52-104 of analysis period to avoid normalizing early safety signals.

import sys, math
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

# ==================== CONFIG ====================

CZECH_REFERENCE_POP = {
    1900: 13, 1905: 23, 1910: 32, 1915: 45,
    1920: 1068, 1925: 9202, 1930: 35006, 1935: 72997,
    1940: 150323, 1945: 246393, 1950: 297251, 1955: 299766,
    1960: 313501, 1965: 335185, 1970: 415319, 1975: 456701,
    1980: 375605, 1985: 357674, 1990: 338424, 1995: 256900,
    2000: 251049, 2005: 287094, 2010: 275837, 2015: 238952,
    2020: 84722,
}
PT_STD = float(sum(CZECH_REFERENCE_POP.values()))
BUCKETS = sorted(CZECH_REFERENCE_POP.keys())
ALPHA = 0.05
Z = 1.959963984540054

COL_DATE = "DateDied"
COL_BY   = "YearOfBirth"
COL_ALV  = "Alive"
COL_DED  = "Dead"
COL_DOSE = "Dose"

FORCE_FLAT_ANCHOR_2023 = True   # flatten ratio over 2023
DEFAULT_N_WEEKS_OFFSET = 72     # Wait 72 weeks after enrollment before starting analysis
DEFAULT_HORIZON_WEEKS  = 52     # Analyze 52 weeks of data

# ==================== HELPERS ====================

def sheetname_to_enroll_date(s: str):
    try:
        parts = s.replace("-", "_").split("_")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            iso_year = int(parts[0]); iso_week = int(parts[1])
            return date.fromisocalendar(iso_year, iso_week, 1)
    except Exception:
        pass
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def rate_ci_poisson(D, PT, alpha=ALPHA):
    D = float(D); PT = float(PT)
    if PT <= 0 or np.isnan(D) or np.isnan(PT):
        return (np.nan, np.nan)
    if D == 0:
        return (0.0, -math.log(alpha) / PT)
    try:
        from scipy.stats import chi2
        lo = 0.5 * chi2.ppf(alpha / 2.0, 2.0 * D) / PT
        hi = 0.5 * chi2.ppf(1.0 - alpha / 2.0, 2.0 * (D + 1.0)) / PT
        return (lo, hi)
    except Exception:
        r = D / PT
        se_log = 1.0 / math.sqrt(D)
        return (math.exp(math.log(r) - Z * se_log), math.exp(math.log(r) + Z * se_log))

# ==================== CORE (CMR / ASMR) ====================

def compute_base_tables(df, sheet):
    df = df.copy()
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
    df["birth_year"] = pd.to_numeric(df[COL_BY], errors="coerce").astype("Int64")
    df["deaths"] = pd.to_numeric(df[COL_DED], errors="coerce").fillna(0.0).astype(float)
    df["Dose"] = pd.to_numeric(df[COL_DOSE], errors="coerce").fillna(0).astype(int)
    df["person_time"] = pd.to_numeric(df[COL_ALV], errors="coerce").fillna(0.0).astype(float) + 0.5 * df["deaths"]

    enroll_date = sheetname_to_enroll_date(sheet)
    if enroll_date is not None:
        df = df[df[COL_DATE].dt.date >= enroll_date]

    agg = df.groupby([COL_DATE, "birth_year", "Dose"], as_index=False).agg(
        deaths=("deaths", "sum"),
        person_time=("person_time", "sum"),
    ).sort_values(["Dose", "birth_year", COL_DATE])

    # CMR
    agg["CMR"] = agg["deaths"] / agg["person_time"]
    ci = agg.apply(lambda r: rate_ci_poisson(r["deaths"], r["person_time"]), axis=1, result_type="expand")
    agg["CMR_LCL"], agg["CMR_UCL"] = ci[0], ci[1]

    # Cumulative
    agg["cum_deaths"] = agg.groupby(["birth_year","Dose"])["deaths"].cumsum()
    agg["cum_person_time"] = agg.groupby(["birth_year","Dose"])["person_time"].cumsum()
    agg["CUM_CMR"] = agg["cum_deaths"] / agg["cum_person_time"]
    cum_ci = agg.apply(lambda r: rate_ci_poisson(r["cum_deaths"], r["cum_person_time"]), axis=1, result_type="expand")
    agg["CUM_CMR_LCL"], agg["CUM_CMR_UCL"] = cum_ci[0], cum_ci[1]

    return agg, enroll_date

# ==================== KCOR (weekly, with CIs) ====================

def detrended_kcor_by_birthyear(out_df, birth_year, enroll_date, N_weeks_offset, horizon_weeks):
    results = {}
    base = out_df.loc[(out_df["birth_year"]==birth_year)].copy()
    if base.empty: return results
    base["DateDied"] = pd.to_datetime(base["DateDied"], errors="coerce")
    base["rate"] = base["deaths"] / base["person_time"]

    if (base["Dose"]==0).sum()==0: return results

    for dose_treat in sorted([d for d in base["Dose"].unique() if d!=0]):
        sub = base[base["Dose"].isin([0, dose_treat])].copy()
        piv_r = sub.pivot_table(index="DateDied", columns="Dose", values="rate", aggfunc="sum").sort_index()
        piv_d = sub.pivot_table(index="DateDied", columns="Dose", values="deaths", aggfunc="sum").sort_index()
        piv_pt= sub.pivot_table(index="DateDied", columns="Dose", values="person_time", aggfunc="sum").sort_index()

        if piv_r.empty: continue

        # analysis window
        if enroll_date is None:
            analysis_start = pd.Timestamp(piv_r.index.min())
        else:
            analysis_start = pd.Timestamp(enroll_date) + pd.Timedelta(weeks=N_weeks_offset)
        analysis_end = analysis_start + pd.Timedelta(weeks=horizon_weeks) - pd.Timedelta(days=1)

        # baseline anchor - use post-enrollment detrending period
        # Add small epsilon to avoid log(0) and division by 0
        epsilon = 1e-10
        rate_treat = np.maximum(piv_r[dose_treat], epsilon)
        rate_ref = np.maximum(piv_r[0], epsilon)
        y = np.log(rate_treat / rate_ref)
        t = np.arange(1, len(y)+1)
        
        # First try 2023 data if available
        anchor_mask = (piv_r.index >= pd.Timestamp("2023-01-01")) & (piv_r.index <= pd.Timestamp("2023-12-31"))
        
        # If no 2023 data, use the specified detrending period (starting at analysis_start + 52 weeks)
        if not anchor_mask.any():
            detrend_start = analysis_start + pd.Timedelta(weeks=52)  # Start detrending 52 weeks into analysis period
            detrend_end = detrend_start + pd.Timedelta(weeks=52) - pd.Timedelta(days=1)  # Use 52 weeks for detrending
            anchor_mask = (piv_r.index >= detrend_start) & (piv_r.index <= detrend_end)
            
            # Error out if insufficient data for detrending in the specified period
            if not anchor_mask.any():
                raise ValueError(f"Insufficient data for detrending birth_year={birth_year}, dose_treat={dose_treat}. "
                               f"Need data from {detrend_start.date()} to {detrend_end.date()}")

        if anchor_mask.any():
            if FORCE_FLAT_ANCHOR_2023:
                yhat = np.repeat(y[anchor_mask].mean(), len(y))
            else:
                X = np.vstack([np.ones(len(t)), t]).T
                beta = np.linalg.pinv(X[anchor_mask]) @ y[anchor_mask].values
                yhat = X @ beta
        else:
            raise ValueError(f"No valid detrending data available for birth_year={birth_year}, dose_treat={dose_treat}")

        log_rr_det = y.values - yhat
        rr_det = np.exp(log_rr_det)

        wt = np.minimum(piv_pt[dose_treat].fillna(0), piv_pt[0].fillna(0)).values
        var_week = np.where((piv_d[dose_treat]>0) & (piv_d[0]>0),
                            1.0/np.maximum(piv_d[dose_treat].values, 1e-10) + 1.0/np.maximum(piv_d[0].values, 1e-10),
                            np.nan)

        mask_analysis = (piv_r.index >= analysis_start) & (piv_r.index <= analysis_end)
        lw = log_rr_det.copy(); ww = wt.copy(); vw = var_week.copy()
        lw[~mask_analysis] = 0.0; ww[~mask_analysis] = 0.0; vw[~mask_analysis] = 0.0

        cum_w = np.cumsum(ww)
        cum_num = np.cumsum(lw * ww)
        cum_var_num = np.cumsum((ww**2) * vw)

        # Use numpy's errstate to suppress all division warnings
        with np.errstate(divide='ignore', invalid='ignore'):
            valid_mask = (cum_w > 0) & np.isfinite(cum_w) & np.isfinite(cum_num)
            log_kcor = np.where(valid_mask, cum_num / cum_w, np.nan)
            
            valid_var_mask = (cum_w > 0) & np.isfinite(cum_w) & np.isfinite(cum_var_num)
            var_log_kcor = np.where(valid_var_mask, cum_var_num / (cum_w**2), np.nan)
        se_log_kcor = np.sqrt(var_log_kcor)
        KCOR = np.exp(log_kcor)
        KCOR_LCL = np.exp(log_kcor - Z*se_log_kcor)
        KCOR_UCL = np.exp(log_kcor + Z*se_log_kcor)

        df_out = pd.DataFrame({
            "DateDied": piv_r.index,
            "birth_year": birth_year,
            "Dose_treat": dose_treat,
            "Dose_ref": 0,
            "KCOR": KCOR,
            "KCOR_LCL": KCOR_LCL,
            "KCOR_UCL": KCOR_UCL,
            "log_RR_detrended": log_rr_det,
            "RR_detrended": rr_det,
            "weight": wt,
            "in_analysis": mask_analysis
        })
        results[dose_treat] = df_out

    return results

# ==================== PIPELINE ====================

def process_book(inp_path: str, out_path: str, N_weeks_offset=DEFAULT_N_WEEKS_OFFSET, horizon_weeks=DEFAULT_HORIZON_WEEKS):
    xls = pd.ExcelFile(inp_path)
    writer = pd.ExcelWriter(out_path, engine="xlsxwriter")

    for sheet in xls.sheet_names:
        df = pd.read_excel(inp_path, sheet_name=sheet)
        out, enroll_date = compute_base_tables(df, sheet)
        out.to_excel(writer, sheet_name=sheet[:31], index=False)

        years = sorted([int(y) for y in out["birth_year"].dropna().unique() if int(y) > 0])
        for by in years:
            kcor_tables = detrended_kcor_by_birthyear(out, by, enroll_date, N_weeks_offset, horizon_weeks)
            for dose_treat, df_k in kcor_tables.items():
                df_k2 = df_k.copy()
                df_k2["DateDied"] = pd.to_datetime(df_k2["DateDied"], errors="coerce").dt.strftime("%Y-%m-%d")
                name = f"{sheet[:18]}_BY{by}_D{dose_treat}v0_KCOR"
                df_k2.to_excel(writer, sheet_name=name[:31], index=False)

    writer.close()
    print(f"Wrote output to: {out_path}")

# ==================== CLI ====================

def main():
    if len(sys.argv) < 2:
        print("Usage: python KCOR_analysis_KCOR.py <input_excel> [output_excel] [N_weeks_offset] [horizon_weeks]")
        sys.exit(1)
    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("KCOR_with_ASMR_byDose_KCOR.xlsx")
    N_weeks = int(sys.argv[3]) if len(sys.argv) >= 4 else DEFAULT_N_WEEKS_OFFSET
    horizon = int(sys.argv[4]) if len(sys.argv) >= 5 else DEFAULT_HORIZON_WEEKS
    process_book(str(inp), str(outp), N_weeks, horizon)

if __name__ == "__main__":
    main()
