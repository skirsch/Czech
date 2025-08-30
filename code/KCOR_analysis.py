#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# KCOR_analysis.py
# Analyze the KCOR_output.xlsx file produced by KCOR.py to compute ASMR (age-standardized mortality rates)
# using Method B (direct standardization) with Czech 5-year age distribution as weights.  
# The ASMR is computed per Dose group, with confidence intervals, and added as rows with birth_year = 0.
# The output is saved to KCOR_with_ASMR_byDose.xlsx (configurable via CLI).
# Usage: python KCOR_analysis.py <input_excel> [output_excel]
# Example: python KCOR_analysis.py KCOR_output.xlsx KCOR_with_ASMR_byDose.xlsx
# Requires: pandas, numpy, scipy (for exact Poisson CIs)
# to run: cd code;make KCOR_analysis

import sys, math
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

# ==================== CONFIG ====================

# Standard population weights (5-year starts)
CZECH_REFERENCE_POP = {
    1900: 13, 1905: 23, 1910: 32, 1915: 45,
    1920: 1068, 1925: 9202, 1930: 35006, 1935: 72997,
    1940: 150323, 1945: 246393, 1950: 297251, 1955: 299766,
    1960: 313501, 1965: 335185, 1970: 415319, 1975: 456701,
    1980: 375605, 1985: 357674, 1990: 338424, 1995: 256900,
    2000: 251049, 2005: 287094, 2010: 275837, 2015: 238952,
    2020: 84722,
}
PT_STD = float(sum(CZECH_REFERENCE_POP.values()))      # constant standard person-time per week
BUCKETS = sorted(CZECH_REFERENCE_POP.keys())
ALPHA = 0.05
Z = 1.959963984540054                                  # ~97.5th percentile (two-sided 95%)

# Input schema from your workbook
COL_DATE = "DateDied"
COL_BY   = "YearOfBirth"
COL_ALV  = "Alive"
COL_DED  = "Dead"
COL_DOSE = "Dose"      # will be kept as a grouping key
# (Sex is ignored on purpose to pool counts.)

# ==================== HELPERS ====================

def sheetname_to_enroll_date(s: str):
    """Parse sheet names like '2021_13' (ISO year_week) -> Monday date, else try direct date parse."""
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

def to_bucket_start(y):
    if pd.isna(y): return np.nan
    y = int(y)
    if y < BUCKETS[0]: return BUCKETS[0]
    if y > BUCKETS[-1] + 4: return BUCKETS[-1]
    return y - ((y - BUCKETS[0]) % 5)

def rate_ci_poisson(D, PT, alpha=ALPHA):
    """95% CI for rate = D/PT. Exact gamma via chi-square if SciPy is available; otherwise log-rate approx."""
    D = float(D); PT = float(PT)
    if PT <= 0 or np.isnan(D) or np.isnan(PT):
        return (np.nan, np.nan)
    if D == 0:
        return (0.0, -math.log(alpha) / PT)  # exact upper bound at zero deaths
    try:
        from scipy.stats import chi2
        lo = 0.5 * chi2.ppf(alpha / 2.0, 2.0 * D) / PT
        hi = 0.5 * chi2.ppf(1.0 - alpha / 2.0, 2.0 * (D + 1.0)) / PT
        return (lo, hi)
    except Exception:
        r = D / PT
        se_log = 1.0 / math.sqrt(D)
        return (math.exp(math.log(r) - Z * se_log), math.exp(math.log(r) + Z * se_log))

# ==================== CORE ====================

def process_book(inp_path: str, out_path: str):
    xls = pd.ExcelFile(inp_path)
    writer = pd.ExcelWriter(out_path, engine="xlsxwriter")

    for sheet in xls.sheet_names:
        df = pd.read_excel(inp_path, sheet_name=sheet)

        # --- Coerce & derive ---
        df = df.copy()
        df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
        df["birth_year"] = pd.to_numeric(df[COL_BY], errors="coerce").astype("Int64")
        df["deaths"] = pd.to_numeric(df[COL_DED], errors="coerce").fillna(0.0).astype(float)
        df["Dose"] = pd.to_numeric(df[COL_DOSE], errors="coerce").fillna(0).astype(int)
        # Person-time per row: mid-interval approximation
        df["person_time"] = pd.to_numeric(df[COL_ALV], errors="coerce").fillna(0.0).astype(float) + 0.5 * df["deaths"]

        # Filter to on/after enrollment date parsed from sheet name
        enroll_date = sheetname_to_enroll_date(sheet)
        if enroll_date is not None:
            df = df[df[COL_DATE].dt.date >= enroll_date]

        # --- Aggregate across Sex, keep Dose as a stratum ---
        agg = df.groupby([COL_DATE, "birth_year", "Dose"], as_index=False).agg(
            deaths=("deaths", "sum"),
            person_time=("person_time", "sum"),
        ).sort_values(["Dose", "birth_year", COL_DATE])

        # --- CMR & CIs per row (per 100K person-years) ---
        agg["CMR"] = (agg["deaths"] / agg["person_time"]) * 52 * 1e5  # Convert to per 100K person-years
        ci = agg.apply(lambda r: rate_ci_poisson(r["deaths"], r["person_time"]), axis=1, result_type="expand")
        # Scale confidence intervals to per 100K person-years
        agg["CMR_LCL"], agg["CMR_UCL"] = ci[0] * 52 * 1e5, ci[1] * 52 * 1e5

        # --- Cumulative by (birth_year, Dose) (per 100K person-years) ---
        agg["cum_deaths"] = agg.groupby(["birth_year","Dose"])["deaths"].cumsum()
        agg["cum_person_time"] = agg.groupby(["birth_year","Dose"])["person_time"].cumsum()
        agg["CUM_CMR"] = (agg["cum_deaths"] / agg["cum_person_time"]) * 52 * 1e5  # Convert to per 100K person-years
        cum_ci = agg.apply(lambda r: rate_ci_poisson(r["cum_deaths"], r["cum_person_time"]), axis=1, result_type="expand")
        # Scale cumulative confidence intervals to per 100K person-years
        agg["CUM_CMR_LCL"], agg["CUM_CMR_UCL"] = cum_ci[0] * 52 * 1e5, cum_ci[1] * 52 * 1e5

        # ---------- ASMR rows per Dose (birth_year = 0), Method B ----------
        tmp = agg.copy()
        tmp["bucket"] = tmp["birth_year"].apply(to_bucket_start)
        tmp = tmp[~tmp["bucket"].isna()]  # exclude unknown birth years from ASMR

        weights = pd.DataFrame({"bucket": list(CZECH_REFERENCE_POP.keys()),
                                "w": list(CZECH_REFERENCE_POP.values())})

        # Bucket totals per (date, dose)
        by_bucket = tmp.groupby([COL_DATE, "Dose", "bucket"], as_index=False).agg(
            deaths=("deaths", "sum"),
            person_time=("person_time", "sum"),
        )
        by_bucket["rate"] = by_bucket["deaths"] / by_bucket["person_time"]
        merged = by_bucket.merge(weights, on="bucket", how="left")

        # Weekly ASMR per (date, dose) with delta-method CI; plus standardized deaths (Method B)
        asmr_rows = []
        for (dt, dose), sub_all in merged.groupby([COL_DATE, "Dose"]):
            sub = sub_all[sub_all["person_time"] > 0]
            if sub.empty:
                asmr_rows.append((dt, dose, np.nan, np.nan, np.nan, np.nan, 0.0))
                continue
            W = sub["w"].sum()
            ASMR = (sub["w"] * sub["rate"]).sum() / W
            # delta method: Var(ASMR) ≈ sum ((w_i/W)^2 * D_i / PT_i^2)
            var = ((sub["w"]/W)**2 * (sub["deaths"] / (sub["person_time"]**2).replace(0,np.nan))).sum()
            var = float(var) if np.isfinite(var) else np.nan
            if np.isfinite(var) and var >= 0:
                se = math.sqrt(var)
                lo = max(0.0, ASMR - Z * se)
                hi = ASMR + Z * se
            else:
                lo = hi = np.nan
            # Convert ASMR to per 100K person-years
            ASMR_per_100k = ASMR * 52 * 1e5 if np.isfinite(ASMR) else np.nan
            lo_per_100k = lo * 52 * 1e5 if np.isfinite(lo) else np.nan
            hi_per_100k = hi * 52 * 1e5 if np.isfinite(hi) else np.nan
            asmr_rows.append((dt, dose, ASMR_per_100k, lo_per_100k, hi_per_100k))

        asmr_df = pd.DataFrame(asmr_rows, columns=[COL_DATE, "Dose", "ASMR", "ASMR_LCL", "ASMR_UCL"]).sort_values(["Dose", COL_DATE])
        # Calculate cumulative ASMR directly from weekly rates
        asmr_df["week_index"] = asmr_df.groupby("Dose").cumcount() + 1
        asmr_df["ASMR_cum_CMR"] = asmr_df.groupby("Dose")["ASMR"].expanding().mean().reset_index(level=0, drop=True)

        # CIs for cumulative ASMR via cumulative bucket totals (per Dose)
        by_bucket = by_bucket.sort_values([ "Dose", COL_DATE, "bucket"])
        by_bucket["cum_deaths"] = by_bucket.groupby(["Dose","bucket"])["deaths"].cumsum()
        by_bucket["cum_pt"]     = by_bucket.groupby(["Dose","bucket"])["person_time"].cumsum()
        by_bucket["cum_rate"]   = by_bucket["cum_deaths"] / by_bucket["cum_pt"]
        merged_cum = by_bucket.merge(weights, on="bucket", how="left")

        cum_ci_rows = []
        for (dt, dose), sub_all in merged_cum.groupby([COL_DATE, "Dose"]):
            sub = sub_all[sub_all["cum_pt"] > 0]
            if sub.empty:
                cum_ci_rows.append((dt, dose, np.nan, np.nan))
            else:
                W = sub["w"].sum()
                ASMR_cum = (sub["w"] * sub["cum_rate"]).sum() / W
                var = ((sub["w"]/W)**2 * (sub["cum_deaths"] / (sub["cum_pt"]**2).replace(0,np.nan))).sum()
                var = float(var) if np.isfinite(var) else np.nan
                if np.isfinite(var) and var >= 0:
                    se = math.sqrt(var)
                    lo = max(0.0, ASMR_cum - Z * se)
                    hi = ASMR_cum + Z * se
                    # Convert to per 100K person-years
                    lo_per_100k = lo * 52 * 1e5
                    hi_per_100k = hi * 52 * 1e5
                else:
                    lo_per_100k = hi_per_100k = np.nan
                cum_ci_rows.append((dt, dose, lo_per_100k, hi_per_100k))

        cum_ci_df = pd.DataFrame(cum_ci_rows, columns=[COL_DATE, "Dose", "ASMR_cum_LCL", "ASMR_cum_UCL"])
        asmr_out = asmr_df.merge(cum_ci_df, on=[COL_DATE, "Dose"], how="left")

        # Final ASMR rows (birth_year == 0), per Dose
        asmr_rows_final = pd.DataFrame({
            COL_DATE:  asmr_out[COL_DATE],
            "birth_year": 0,
            "Dose": asmr_out["Dose"],
            "deaths": np.nan,
            "person_time": np.nan,
            "CMR": asmr_out["ASMR"],
            "CMR_LCL": asmr_out["ASMR_LCL"],
            "CMR_UCL": asmr_out["ASMR_UCL"],
            "CUM_CMR": asmr_out["ASMR_cum_CMR"],
            "CUM_CMR_LCL": asmr_out["ASMR_cum_LCL"],
            "CUM_CMR_UCL": asmr_out["ASMR_cum_UCL"],
        })

        # Concatenate and save
        out = pd.concat([agg, asmr_rows_final], ignore_index=True, sort=False)
        out = out.sort_values(["Dose", "birth_year", COL_DATE])

        # Format date column to remove timestamp (keep only date part)
        out[COL_DATE] = pd.to_datetime(out[COL_DATE]).dt.date

        cols = [
            COL_DATE, "Dose", "birth_year", "deaths", "person_time",
            "CMR", "CMR_LCL", "CMR_UCL",
            "CUM_CMR", "CUM_CMR_LCL", "CUM_CMR_UCL",
            "cum_deaths", "cum_person_time",
        ]
        out = out[[c for c in cols if c in out.columns]]
        out.to_excel(writer, sheet_name=sheet[:31], index=False)

    writer.close()
    print(f"Wrote output to: {out_path}")

# ==================== CLI ====================

def main():
    if len(sys.argv) < 2:
        print("Usage: python KCOR_analysis.py <input_excel> [output_excel]")
        print("Example: python KCOR_analysis.py KCOR_output.xlsx KCOR_with_ASMR_byDose.xlsx")
        sys.exit(1)
    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("../analysis/KCOR_analysis.xlsx")
    process_book(str(inp), str(outp))

if __name__ == "__main__":
    main()
