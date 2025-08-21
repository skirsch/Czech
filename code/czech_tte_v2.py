#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
czech_tte_v2.py — Fair day-0 treatment-policy TTE with anchored and windowed HRs.

To run:
python czech_tte_v2.py --baseline ./tte_inputs/baseline.csv --vax ./tte_inputs/vax.csv --events ./tte_inputs/events.csv --t0 2021-06-14 --t1 2022-06-14 --age-min 60 --age-max 89 --covars age,sex,prior_infection --alpha 1.5 --age-bands 60-69,70-79,80-89 --outdir ./results_v2

This script builds a fair day-0 treatment-policy time-to-event (TTE) analysis for the Czech COVID-19 vaccination dataset.

Adds:
- Anchored ACM HR = HR_ACM / HR_nonCOVID (delta-method CI).
- Anchored COVID HR (layman-NPH) = HR_COVID / (HR_nonCOVID ** alpha), default alpha=1.5.
- Windowed Cox HRs for 0–30, 31–90, 91–180, 181–365 days, with anchored versions.
- Optional age-band splits within the selected [age_min, age_max].
- Outputs windows_report.csv with all estimates and prints a concise summary.

Primary design remains day-0, treatment-policy, common [t0, t1].

Dependencies:
  pandas, numpy, matplotlib, lifelines, scikit-learn
"""

import argparse, os, math, warnings
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lifelines import CoxPHFitter
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ----------------------- Utils -----------------------
def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")

def clip_weights(w, lower=0.05, upper=20.0):
    w = np.asarray(w, dtype=float)
    return np.clip(w, lower, upper)

# ----------------------- I/O -------------------------
def load_inputs(baseline_path, vax_path, events_path):
    b = pd.read_csv(baseline_path)
    v = pd.read_csv(vax_path)
    e = pd.read_csv(events_path)
    # Normalize dates
    for c in ["prior_infection_date"]:
        if c in b.columns:
            b[c] = pd.to_datetime(b[c], errors="coerce").dt.normalize()
    v["vax_date"] = pd.to_datetime(v["vax_date"], errors="coerce").dt.normalize()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce").dt.normalize()
    return b, v, e

# ------------------- Cohort build --------------------
def build_analysis_cohorts(baseline, vax, events, t0: datetime, t1: datetime, age_min=None, age_max=None):
    df = baseline.copy()
    if age_min is not None: df = df[df["age"] >= age_min]
    if age_max is not None: df = df[df["age"] <= age_max]
    df = df.drop_duplicates(subset=["person_id"])

    first_dose = vax.sort_values(["person_id","dose_number"]).drop_duplicates("person_id", keep="first")
    first_dose = first_dose[["person_id","vax_date"]].rename(columns={"vax_date":"first_dose_date"})
    df = df.merge(first_dose, on="person_id", how="left")
    df["vaccinated_at_t0"] = ((df["first_dose_date"].notna()) & (df["first_dose_date"] <= pd.Timestamp(t0))).astype(int)

    ev = events[events["event_type"].isin(["death_covid","death_noncovid","death_acm","emigration"])].copy()
    available_types = set(ev["event_type"].unique())
    
    # derive ACM if needed
    if "death_acm" in available_types:
        acm = ev[ev["event_type"]=="death_acm"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_acm_date")
        df = df.merge(acm, left_on="person_id", right_index=True, how="left")
    else:
        # Try to derive from covid + noncovid if both exist
        if "death_covid" in available_types and "death_noncovid" in available_types:
            covid = ev[ev["event_type"]=="death_covid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_covid_date")
            nonc  = ev[ev["event_type"]=="death_noncovid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_noncovid_date")
            acm = pd.concat([covid, nonc], axis=1)
            acm["death_acm_date"] = acm.min(axis=1)
            df = df.merge(acm, left_on="person_id", right_index=True, how="left")
        else:
            # No ACM data available
            df["death_acm_date"] = pd.NaT
    
    # ALWAYS merge cause dates if present, regardless of ACM availability
    if "death_covid" in available_types:
        if "death_covid_date" not in df.columns:  # Only merge if not already created above
            covid = ev[ev["event_type"]=="death_covid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_covid_date")
            df = df.merge(covid, left_on="person_id", right_index=True, how="left")
    else:
        df["death_covid_date"] = pd.NaT
        
    if "death_noncovid" in available_types:
        if "death_noncovid_date" not in df.columns:  # Only merge if not already created above
            nonc  = ev[ev["event_type"]=="death_noncovid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_noncovid_date")
            df = df.merge(nonc, left_on="person_id", right_index=True, how="left")
    else:
        df["death_noncovid_date"] = pd.NaT

    if "emigration" in available_types:
        emi = ev[ev["event_type"]=="emigration"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("emigration_date")
        df = df.merge(emi, left_on="person_id", right_index=True, how="left")
    else:
        df["emigration_date"] = pd.NaT

    df["t0"] = pd.Timestamp(t0); df["t1"] = pd.Timestamp(t1)
    df["end_of_fu"] = df[["death_acm_date","emigration_date"]].min(axis=1)
    df["end_of_fu"] = df["end_of_fu"].fillna(df["t1"])
    df["end_of_fu"] = df[["end_of_fu","t1"]].min(axis=1)

    df["time"] = (df["end_of_fu"] - df["t0"]).dt.days.clip(lower=0)
    df["event_acm"] = ((df["death_acm_date"].notna()) & (df["death_acm_date"] <= df["end_of_fu"])).astype(int)
    df["event_covid"] = ((df["death_covid_date"].notna()) & (df["death_covid_date"] <= df["end_of_fu"])).astype(int)
    df["event_noncovid"] = ((df["death_noncovid_date"].notna()) & (df["death_noncovid_date"] <= df["end_of_fu"])).astype(int)
    return df

# ---------------- Propensity + IPTW ------------------
def build_propensity_and_weights(df, covars: List[str], treat_col="vaccinated_at_t0", stabilize=True, clip=(0.05, 20.0), outdir=None):
    X = df[covars].copy()
    y = df[treat_col].astype(int).values
    num_cols = [c for c in covars if np.issubdtype(X[c].dtype, np.number)]
    cat_cols = [c for c in covars if c not in num_cols]
    pre = ColumnTransformer([("num", StandardScaler(), num_cols),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)])
    model = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=200))])
    model.fit(X, y)
    ps = model.predict_proba(X)[:,1]
    auc = roc_auc_score(y, ps) if len(np.unique(y)) > 1 else np.nan
    eps = 1e-6; ps = np.clip(ps, eps, 1-eps)
    p_treated = y.mean()
    if stabilize:
        w = np.where(y==1, p_treated/ps, (1-p_treated)/(1-ps))
    else:
        w = np.where(y==1, 1/ps, 1/(1-ps))
    w = clip_weights(w, clip[0], clip[1])
    df_out = df.copy()
    df_out["pscore"] = ps; df_out["iptw"] = w
    # Overlap histogram
    if outdir:
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(6,4), dpi=150)
        plt.hist(df_out.loc[y==1,"pscore"], bins=30, alpha=0.5, label="vaccinated_at_t0=1", density=True)
        plt.hist(df_out.loc[y==0,"pscore"], bins=30, alpha=0.5, label="vaccinated_at_t0=0", density=True)
        plt.xlabel("Propensity score"); plt.ylabel("Density"); plt.title(f"Propensity overlap (AUC={auc:.3f})")
        plt.legend(); plt.tight_layout()
        plt.savefig(os.path.join(outdir, "overlap_ps.png")); plt.close(fig)
    return df_out, auc

# ---------------- Cox helpers -----------------------
def cox_hr(df, duration_col, event_col, weight_col, adjust_cols: Optional[List[str]]=None):
    data = df.copy()
    data["treat"] = data["vaccinated_at_t0"].astype(int)
    cols = ["treat"] + (adjust_cols or [])
    use = data[[duration_col, event_col] + cols + ([weight_col] if weight_col else [])].dropna()
    if use.empty or use[event_col].sum() == 0:
        return np.nan, (np.nan, np.nan), np.nan
    
    # Handle categorical variables by encoding them
    categorical_cols = []
    for col in cols:
        if col in use.columns and not np.issubdtype(use[col].dtype, np.number):
            categorical_cols.append(col)
    
    if categorical_cols:
        # Convert categorical variables to dummy variables
        use = pd.get_dummies(use, columns=categorical_cols, drop_first=True, dtype=float)
        # Update treat column name if it was encoded
        treat_cols = [c for c in use.columns if c.startswith('treat')]
        if treat_cols and 'treat' not in use.columns:
            # Find the treatment column after dummy encoding
            for c in treat_cols:
                if use[c].sum() > 0:  # Use the non-zero dummy variable
                    treat_col = c
                    break
        else:
            treat_col = "treat"
    else:
        treat_col = "treat"
    
    cph = CoxPHFitter()
    cph.fit(use, duration_col=duration_col, event_col=event_col, weights_col=weight_col, robust=False)
    
    if treat_col not in cph.params_.index:
        return np.nan, (np.nan, np.nan), np.nan
        
    beta = cph.params_[treat_col]; se = cph.standard_errors_[treat_col]
    hr = math.exp(beta); lcl = math.exp(beta - 1.96*se); ucl = math.exp(beta + 1.96*se)
    return hr, (lcl, ucl), se

def window_restrict(df, start_day:int, end_day:int):
    """Return new duration/event columns for a window [start_day, end_day]."""
    start = df["t0"] + pd.to_timedelta(start_day, unit="D")
    end   = df["t0"] + pd.to_timedelta(end_day, unit="D")
    at_risk_end = df[["end_of_fu", "t1"]].min(axis=1)
    # duration in window
    dur = (np.minimum(at_risk_end, end) - np.maximum(df["t0"] + pd.to_timedelta(0, "D"), start)).dt.days
    dur = np.clip(dur, 0, None)
    # events in window by cause
    ev_acm = ((df["death_acm_date"].notna()) & (df["death_acm_date"] >= start) & (df["death_acm_date"] <= np.minimum(at_risk_end, end))).astype(int)
    ev_covid = ((df["death_covid_date"].notna()) & (df["death_covid_date"] >= start) & (df["death_covid_date"] <= np.minimum(at_risk_end, end))).astype(int)
    ev_noncovid = ((df["death_noncovid_date"].notna()) & (df["death_noncovid_date"] >= start) & (df["death_noncovid_date"] <= np.minimum(at_risk_end, end))).astype(int)
    return dur, ev_acm, ev_covid, ev_noncovid

# ---------------- Main ------------------------------
def main():
    ap = argparse.ArgumentParser(description="Fair day-0 TTE with anchored + windowed HRs")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--vax", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--t0", required=True)
    ap.add_argument("--t1", required=True)
    ap.add_argument("--age-min", type=int, default=None)
    ap.add_argument("--age-max", type=int, default=None)
    ap.add_argument("--covars", type=str, default="age,sex,prior_infection")
    ap.add_argument("--alpha", type=float, default=1.5, help="Exponent for layman-NPH anchoring")
    ap.add_argument("--age-bands", type=str, default="", help="Comma-separated bands like 60-69,70-79")
    ap.add_argument("--outdir", type=str, default="results_v2")
    ap.add_argument("--clip-low", type=float, default=0.05)
    ap.add_argument("--clip-high", type=float, default=20.0)
    ap.add_argument("--windows", type=str, default="0-30,31-90,91-180,181-365")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    t0 = parse_date(args.t0); t1 = parse_date(args.t1)
    covars = [c.strip() for c in args.covars.split(",") if c.strip()]
    bands = []
    if args.age_bands.strip():
        for tok in args.age_bands.split(","):
            lo, hi = tok.split("-"); bands.append((int(lo), int(hi)))
    else:
        bands = [(args.age_min, args.age_max)]

    # Load
    b, v, e = load_inputs(args.baseline, args.vax, args.events)

    # Prepare output table
    rows = []
    print("=== TTE v2 anchored/windowed ===")
    print(f"alpha={args.alpha}  windows={args.windows}  covars={covars}")

    for (amin, amax) in bands:
        label = f"{amin}-{amax}" if amin is not None and amax is not None else "all"
        print(f"\n[Age band {label}] Building cohorts...")
        df = build_analysis_cohorts(b, v, e, t0, t1, amin, amax)

        # Propensity + IPTW
        covars2 = [c for c in covars if c in df.columns]
        if "prior_infection_date" in df.columns and "prior_infection" in covars2:
            df["prior_infection"] = ((df["prior_infection_date"].notna()) & (df["prior_infection_date"] < pd.Timestamp(t0))).astype(int)
        dfw, auc = build_propensity_and_weights(df, covars=covars2, clip=(args.clip_low, args.clip_high), outdir=args.outdir)

        # Full-period HRs
        hr_acm, (l_acm, u_acm), se_acm = cox_hr(dfw, "time", "event_acm", "iptw", covars2)
        hr_nc,  (l_nc,  u_nc),  se_nc  = cox_hr(dfw, "time", "event_noncovid", "iptw", covars2)
        hr_cvd, (l_cvd, u_cvd), se_cvd = cox_hr(dfw, "time", "event_covid", "iptw", covars2)

        # Anchored (delta method; assume independence as heuristic)
        def anchor_ci(hr_num, se_num, hr_den, se_den, power=1.0):
            if any([np.isnan(x) for x in [hr_num, se_num, hr_den, se_den]]): return (np.nan, np.nan, np.nan)
            lnH = math.log(hr_num) - power*math.log(hr_den)
            se  = math.sqrt(se_num**2 + (power**2)*(se_den**2))
            return math.exp(lnH), math.exp(lnH - 1.96*se), math.exp(lnH + 1.96*se)

        anch_acm, anch_acm_l, anch_acm_u = anchor_ci(hr_acm, se_acm, hr_nc, se_nc, power=1.0)
        anch_cvd, anch_cvd_l, anch_cvd_u = anchor_ci(hr_cvd, se_cvd, hr_nc, se_nc, power=args.alpha)

        print(f"AUC={auc:.3f} | HRs: ACM={hr_acm:.3f} [{l_acm:.3f},{u_acm:.3f}]  nonCOVID={hr_nc:.3f} [{l_nc:.3f},{u_nc:.3f}]  COVID={hr_cvd:.3f} [{l_cvd:.3f},{u_cvd:.3f}]")
        print(f"Anchored: ACM={anch_acm:.3f} [{anch_acm_l:.3f},{anch_acm_u:.3f}]  COVID (alpha={args.alpha})={anch_cvd:.3f} [{anch_cvd_l:.3f},{anch_cvd_u:.3f}]")

        rows.append(dict(age_band=label, window="full",
                         hr_acm=hr_acm, lcl_acm=l_acm, ucl_acm=u_acm,
                         hr_noncovid=hr_nc, lcl_noncovid=l_nc, ucl_noncovid=u_nc,
                         hr_covid=hr_cvd, lcl_covid=l_cvd, ucl_covid=u_cvd,
                         anchored_acm=anch_acm, lcl_anchored_acm=anch_acm_l, ucl_anchored_acm=anch_acm_u,
                         anchored_covid=anch_cvd, lcl_anchored_covid=anch_cvd_l, ucl_anchored_covid=anch_cvd_u,
                         auc=auc))

        # Windowed
        win_specs = []
        for w in args.windows.split(","):
            w = w.strip()
            lo, hi = w.split("-"); win_specs.append((int(lo), int(hi), w))

        for lo, hi, wlabel in win_specs:
            dur, evA, evC, evN = window_restrict(dfw, lo, hi)
            tmp = dfw.copy()
            tmp["time_w"] = dur
            tmp["ev_acm_w"] = evA
            tmp["ev_covid_w"] = evC
            tmp["ev_noncovid_w"] = evN
            # Drop rows with zero time in the window
            tmp = tmp[tmp["time_w"] > 0]

            hA, (lA, uA), seA = cox_hr(tmp, "time_w", "ev_acm_w", "iptw", covars2)
            hN, (lN, uN), seN = cox_hr(tmp, "time_w", "ev_noncovid_w", "iptw", covars2)
            hC, (lC, uC), seC = cox_hr(tmp, "time_w", "ev_covid_w", "iptw", covars2)

            aA, aAl, aAu = anchor_ci(hA, seA, hN, seN, power=1.0)
            aC, aCl, aCu = anchor_ci(hC, seC, hN, seN, power=args.alpha)

            print(f"[{wlabel}]  HRs: ACM={hA:.3f} [{lA:.3f},{uA:.3f}]  nonCOVID={hN:.3f} [{lN:.3f},{uN:.3f}]  COVID={hC:.3f} [{lC:.3f},{uC:.3f}]  | Anchored ACM={aA:.3f}  COVID={aC:.3f}")
            rows.append(dict(age_band=label, window=wlabel,
                             hr_acm=hA, lcl_acm=lA, ucl_acm=uA,
                             hr_noncovid=hN, lcl_noncovid=lN, ucl_noncovid=uN,
                             hr_covid=hC, lcl_covid=lC, ucl_covid=uC,
                             anchored_acm=aA, lcl_anchored_acm=aAl, ucl_anchored_acm=aAu,
                             anchored_covid=aC, lcl_anchored_covid=aCl, ucl_anchored_covid=aCu,
                             auc=auc))

    out_csv = os.path.join(args.outdir, "windows_report.csv")
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nWritten: {out_csv}")

if __name__ == "__main__":
    main()
