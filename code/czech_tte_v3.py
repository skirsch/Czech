#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
czech_tte_v3.py — Fair day-0 treatment-policy TTE with anchored, windowed HRs, α-fit (layman-NPH),
and a --fast mode for big datasets.

Adds vs v2:
- Periodic HR table and log–log α-fit (regress log HR_COVID on log HR_nonCOVID).
- Fitted-α anchored COVID HR alongside fixed-α anchoring (alpha from --alpha or estimated).
- Optional scatter plot of log HRs with fitted line (matplotlib only; no seaborn).
- Per-age-band CSVs: alpha_weekly_<band>.csv, alpha_fit_<band>.csv (+ optional PNG).
- Consolidated alpha_summary.csv across age bands.
- windows_report.csv includes `anchored_covid_fit*` columns when --alpha-fit is used.
- --fast mode: robust=False, ties='breslow', float32 design matrix for Cox fits (applies to full, windowed, and α-fit).
- NEW: --alpha-step (default 28 days) and --alpha-min-weeks with fallback α* from full-period HRs.

Usage (Windows one line):
  python .\czech_tte_v3.py --baseline .\tte_inputs\baseline.csv --vax .\tte_inputs\vax.csv --events .\tte_inputs\events.csv --t0 2021-06-14 --t1 2022-06-14 --age-min 60 --age-max 89 --covars age,sex,prior_infection --alpha 1.5 --alpha-fit --alpha-step 28 --alpha-min-weeks 3 --plot-alpha --age-bands 60-69,70-79,80-89 --outdir .\results_v3 --fast

Dependencies:
  pandas, numpy, matplotlib, lifelines, scikit-learn
  (Optional) statsmodels for weighted least squares; falls back to numpy if absent.
"""

import argparse, os, math, warnings
from typing import List, Optional
import numpy as np
import pandas as pd
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lifelines import CoxPHFitter
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score

try:
    import statsmodels.api as sm  # optional for WLS
except Exception:
    sm = None

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
        if "death_covid" in available_types and "death_noncovid" in available_types:
            covid = ev[ev["event_type"]=="death_covid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_covid_date")
            nonc  = ev[ev["event_type"]=="death_noncovid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_noncovid_date")
            acm = pd.concat([covid, nonc], axis=1)
            acm["death_acm_date"] = acm.min(axis=1)
            df = df.merge(acm, left_on="person_id", right_index=True, how="left")
        else:
            df["death_acm_date"] = pd.NaT

    # ALWAYS merge cause dates if present
    if "death_covid" in available_types:
        if "death_covid_date" not in df.columns:
            covid = ev[ev["event_type"]=="death_covid"][["person_id","event_date"]].groupby("person_id").event_date.min().rename("death_covid_date")
            df = df.merge(covid, left_on="person_id", right_index=True, how="left")
    else:
        df["death_covid_date"] = pd.NaT

    if "death_noncovid" in available_types:
        if "death_noncovid_date" not in df.columns:
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
        fig = plt.figure(figsize=(6,4), dpi=150)
        plt.hist(df_out.loc[y==1,"pscore"], bins=30, alpha=0.5, label="vaccinated_at_t0=1", density=True)
        plt.hist(df_out.loc[y==0,"pscore"], bins=30, alpha=0.5, label="vaccinated_at_t0=0", density=True)
        plt.xlabel("Propensity score"); plt.ylabel("Density"); plt.title(f"Propensity overlap (AUC={auc:.3f})")
        plt.legend(); plt.tight_layout()
        plt.savefig(os.path.join(outdir, "overlap_ps.png")); plt.close(fig)
    return df_out, auc

# ---------------- Cox helpers -----------------------
def cox_hr(df, duration_col, event_col, weight_col, adjust_cols: Optional[List[str]]=None,
           robust=True, ties="efron", as_float32=False):
    data = df.copy()
    data["treat"] = data["vaccinated_at_t0"].astype(int)
    cols = ["treat"] + (adjust_cols or [])
    use = data[[duration_col, event_col] + cols + ([weight_col] if weight_col else [])].dropna()
    if use.empty or use[event_col].sum() == 0:
        return np.nan, (np.nan, np.nan), np.nan

    # one-hot any categoricals in adjusters
    categorical_cols = []
    for col in cols:
        if col in use.columns and not np.issubdtype(use[col].dtype, np.number):
            categorical_cols.append(col)
    if categorical_cols:
        use = pd.get_dummies(use, columns=categorical_cols, drop_first=True, dtype=float)

    # float32 for speed (optional)
    if as_float32:
        for c in use.columns:
            if c not in [duration_col, event_col] and use[c].dtype.kind in "fc":
                use[c] = use[c].astype("float32")

    treat_col = "treat" if "treat" in use.columns else [c for c in use.columns if c.startswith("treat")][0]

    cph = CoxPHFitter()
    cph.fit(use, duration_col=duration_col, event_col=event_col, weights_col=weight_col, robust=robust)

    if treat_col not in cph.params_.index:
        return np.nan, (np.nan, np.nan), np.nan

    beta = cph.params_[treat_col]; se = cph.standard_errors_[treat_col]
    
    # Protect against overflow in exp calculations
    try:
        hr = math.exp(beta)
        lcl = math.exp(beta - 1.96*se) 
        ucl = math.exp(beta + 1.96*se)
    except OverflowError:
        # If overflow, return NaN values
        return np.nan, (np.nan, np.nan), np.nan
    
    return hr, (lcl, ucl), se

def window_restrict(df, start_day:int, end_day:int):
    """Return new duration/event columns for a window [start_day, end_day] inclusive."""
    start = df["t0"] + pd.to_timedelta(start_day, unit="D")
    end   = df["t0"] + pd.to_timedelta(end_day, unit="D")
    at_risk_end = df[["end_of_fu", "t1"]].min(axis=1)
    # duration in window
    dur = (np.minimum(at_risk_end, end) - np.maximum(df["t0"], start)).dt.days
    dur = np.clip(dur, 0, None)
    # events in window by cause
    ev_acm = ((df["death_acm_date"].notna()) & (df["death_acm_date"] >= start) & (df["death_acm_date"] <= np.minimum(at_risk_end, end))).astype(int)
    ev_covid = ((df["death_covid_date"].notna()) & (df["death_covid_date"] >= start) & (df["death_covid_date"] <= np.minimum(at_risk_end, end))).astype(int)
    ev_noncovid = ((df["death_noncovid_date"].notna()) & (df["death_noncovid_date"] >= start) & (df["death_noncovid_date"] <= np.minimum(at_risk_end, end))).astype(int)
    return dur, ev_acm, ev_covid, ev_noncovid

# ----------- Periodic table + α-fit helpers ----------
def weekly_hr_table(dfw, covars2, max_day=365, step=7, fast=False):
    """Return periodic HRs for non-COVID and COVID outcomes using IPTW-weighted Cox within each window [lo, hi]."""
    rows = []
    rflag = (not fast)
    ties = "breslow" if fast else "efron"
    af32 = fast
    for lo in range(0, max_day, step):
        hi = min(max_day-1, lo + step - 1)  # inclusive window e.g., 0-27, 28-55, ...
        dur, evA, evC, evN = window_restrict(dfw, lo, hi)
        tmp = dfw.copy()
        tmp["time_w"] = dur
        tmp["ev_noncovid_w"] = evN
        tmp["ev_covid_w"] = evC
        tmp = tmp[tmp["time_w"] > 0]
        hN, (_, _), seN = cox_hr(tmp, "time_w", "ev_noncovid_w", "iptw", covars2,
                                 robust=rflag, ties=ties, as_float32=af32)
        hC, (_, _), seC = cox_hr(tmp, "time_w", "ev_covid_w", "iptw", covars2,
                                 robust=rflag, ties=ties, as_float32=af32)
        nN = int(tmp["ev_noncovid_w"].sum()); nC = int(tmp["ev_covid_w"].sum())
        rows.append(dict(week_start=lo, week_end=hi, hr_noncovid=hN, se_noncovid=seN, n_noncovid=nN,
                         hr_covid=hC, se_covid=seC, n_covid=nC))
    return pd.DataFrame(rows)

def fit_alpha_from_weekly(tab):
    """Fit log(HR_covid) = intercept + alpha * log(HR_noncovid) via WLS if statsmodels available, else unweighted OLS."""
    t = tab.dropna(subset=["hr_noncovid","hr_covid"]).copy()
    t = t[(t["hr_noncovid"]>0) & (t["hr_covid"]>0) & (t["n_noncovid"]>0)]
    if len(t) < 3:
        return dict(alpha=np.nan, alpha_lcl=np.nan, alpha_ucl=np.nan, intercept=np.nan, r2=np.nan, weeks=len(t))
    x = np.log(t["hr_noncovid"].values)
    y = np.log(t["hr_covid"].values)
    w = (t["n_covid"].fillna(0) + t["n_noncovid"]).clip(lower=1).values
    if sm is not None:
        X = np.column_stack([np.ones_like(x), x])
        model = sm.WLS(y, X, weights=w)
        res = model.fit()
        alpha = float(res.params[1]); alpha_se = float(res.bse[1])
        alpha_l = alpha - 1.96*alpha_se; alpha_u = alpha + 1.96*alpha_se
        intercept = float(res.params[0]); r2 = float(res.rsquared)
    else:
        p = np.polyfit(x, y, 1)
        alpha = float(p[0]); intercept = float(p[1])
        alpha_l = np.nan; alpha_u = np.nan; r2 = np.nan
    return dict(alpha=alpha, alpha_lcl=alpha_l, alpha_ucl=alpha_u, intercept=intercept, r2=r2, weeks=len(t))

# ---------------- Main ------------------------------
def main():
    ap = argparse.ArgumentParser(description="Fair day-0 TTE with anchored + windowed HRs + alpha-fit")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--vax", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--t0", required=True)
    ap.add_argument("--t1", required=True)
    ap.add_argument("--age-min", type=int, default=None)
    ap.add_argument("--age-max", type=int, default=None)
    ap.add_argument("--covars", type=str, default="age,sex,prior_infection")
    ap.add_argument("--alpha", type=float, default=1.5, help="Exponent for layman-NPH anchoring of COVID HR (used when --alpha-fit is not set)")
    ap.add_argument("--alpha-fit", action="store_true", help="Estimate alpha via log–log regression per age band")
    ap.add_argument("--alpha-step", type=int, default=28, help="Window size (days) for alpha regression (default 28)")
    ap.add_argument("--alpha-min-weeks", type=int, default=3, help="Min usable windows required to trust weekly alpha")
    ap.add_argument("--plot-alpha", action="store_true", help="Save scatter plot of log HRs with fitted line per age band")
    ap.add_argument("--age-bands", type=str, default="", help="Comma-separated bands like 60-69,70-79")
    ap.add_argument("--outdir", type=str, default="results_v3")
    ap.add_argument("--clip-low", type=float, default=0.05)
    ap.add_argument("--clip-high", type=float, default=20.0)
    ap.add_argument("--windows", type=str, default="0-30,31-90,91-180,181-365")
    ap.add_argument("--fast", action="store_true",
                    help="Speed mode: robust=False, ties='breslow', float32 design matrix for Cox fits (also used for α-fit windows)")
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

    # Prepare output tables
    rows = []
    alpha_rows = []
    print("=== TTE v3 anchored/windowed + alpha-fit ===")
    print(f"alpha(default)={args.alpha}  windows={args.windows}  covars={covars}  fast={args.fast}")

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
        hr_acm, (l_acm, u_acm), se_acm = cox_hr(
            dfw, "time", "event_acm", "iptw", covars2,
            robust=not args.fast, ties=("breslow" if args.fast else "efron"), as_float32=args.fast
        )
        hr_nc,  (l_nc,  u_nc),  se_nc  = cox_hr(
            dfw, "time", "event_noncovid", "iptw", covars2,
            robust=not args.fast, ties=("breslow" if args.fast else "efron"), as_float32=args.fast
        )
        hr_cvd, (l_cvd, u_cvd), se_cvd = cox_hr(
            dfw, "time", "event_covid", "iptw", covars2,
            robust=not args.fast, ties=("breslow" if args.fast else "efron"), as_float32=args.fast
        )

        # Anchor helper (delta-method; α treated as fixed)
        def anchor_ci(hr_num, se_num, hr_den, se_den, power=1.0):
            if any([np.isnan(x) for x in [hr_num, se_num, hr_den, se_den]]): return (np.nan, np.nan, np.nan)
            lnH = math.log(hr_num) - power*math.log(hr_den)
            se  = math.sqrt(se_num**2 + (power**2)*(se_den**2))
            return math.exp(lnH), math.exp(lnH - 1.96*se), math.exp(lnH + 1.96*se)

        # Default (fixed-α) anchoring
        anch_acm, anch_acm_l, anch_acm_u = anchor_ci(hr_acm, se_acm, hr_nc, se_nc, power=1.0)
        anch_cvd, anch_cvd_l, anch_cvd_u = anchor_ci(hr_cvd, se_cvd, hr_nc, se_nc, power=args.alpha)

        # Periodic HRs for α-fit (using alpha-step; honors --fast)
        weekly = weekly_hr_table(dfw, covars2, max_day=365, step=args.alpha_step, fast=args.fast)
        alpha_est = (fit_alpha_from_weekly(weekly) if args.alpha_fit
                     else dict(alpha=np.nan, alpha_lcl=np.nan, alpha_ucl=np.nan, intercept=np.nan, r2=np.nan, weeks=len(weekly)))

        # Choose alpha_star: weekly if usable; else full-period fallback; else default
        alpha_star = None
        if args.alpha_fit and not np.isnan(alpha_est.get("alpha", np.nan)) and alpha_est.get("weeks", 0) >= args.alpha_min_weeks:
            alpha_star = alpha_est["alpha"]
        elif args.alpha_fit and (hr_cvd > 0) and (hr_nc > 0):
            alpha_star = math.log(hr_cvd) / math.log(hr_nc)
            print(f"alpha_fit fallback: using full-period α*={alpha_star:.3f} (weekly not usable)")
        else:
            alpha_star = args.alpha

        # Anchored COVID using fitted/selected α
        anch_cvd_fit, anch_cvd_fit_l, anch_cvd_fit_u = anchor_ci(hr_cvd, se_cvd, hr_nc, se_nc, power=alpha_star)

        print(f"AUC={auc:.3f} | HRs: ACM={hr_acm:.3f} [{l_acm:.3f},{u_acm:.3f}]  nonCOVID={hr_nc:.3f} [{l_nc:.3f},{u_nc:.3f}]  COVID={hr_cvd:.3f} [{l_cvd:.3f},{u_cvd:.3f}]")
        print(f"Anchored: ACM={anch_acm:.3f} [{anch_acm_l:.3f},{anch_acm_u:.3f}]  COVID(fixed α={args.alpha})={anch_cvd:.3f} [{anch_cvd_l:.3f},{anch_cvd_u:.3f}]")
        if args.alpha_fit:
            print(f"alpha_fit: α={alpha_star:.3f} (raw est={alpha_est.get('alpha', np.nan):.3f}, 95%CI=[{alpha_est.get('alpha_lcl', np.nan):.3f},{alpha_est.get('alpha_ucl', np.nan):.3f}], intercept={alpha_est.get('intercept', np.nan):.3f}, R2={alpha_est.get('r2', np.nan):.3f}, windows={alpha_est.get('weeks', 0)})")
            print(f"Anchored COVID(fitted α)={anch_cvd_fit:.3f} [{anch_cvd_fit_l:.3f},{anch_cvd_fit_u:.3f}]")

        # Save weekly + alpha fit artifacts
        weekly_path = os.path.join(args.outdir, f"alpha_weekly_{label}.csv")
        weekly.to_csv(weekly_path, index=False)
        alpha_fit_path = os.path.join(args.outdir, f"alpha_fit_{label}.csv")
        pd.DataFrame([dict(age_band=label, **alpha_est)]).to_csv(alpha_fit_path, index=False)

        # Optional plot
        if args.plot_alpha:
            t = weekly.dropna(subset=["hr_noncovid","hr_covid"]).copy()
            t = t[(t["hr_noncovid"]>0) & (t["hr_covid"]>0)]
            fig = plt.figure(figsize=(5,4), dpi=150)
            x = np.log(t["hr_noncovid"].values); y = np.log(t["hr_covid"].values)
            plt.scatter(x, y)
            if len(t) >= 2:
                if sm is not None and not np.isnan(alpha_star):
                    xx = np.linspace(x.min(), x.max(), 100)
                    bb = alpha_est.get("intercept", 0.0)
                    if np.isnan(bb): bb = 0.0
                    yy = bb + alpha_star*xx
                else:
                    p = np.polyfit(x, y, 1)
                    xx = np.linspace(x.min(), x.max(), 100); yy = p[1] + p[0]*xx
                plt.plot(xx, yy)
            plt.xlabel("log HR non-COVID"); plt.ylabel("log HR COVID")
            plt.title(f"log–log fit α (age {label})")
            plt.tight_layout(); plt.savefig(os.path.join(args.outdir, f"alpha_fit_{label}.png")); plt.close(fig)

        # Store full-period row
        rows.append(dict(age_band=label, window="full",
                         hr_acm=hr_acm, lcl_acm=l_acm, ucl_acm=u_acm,
                         hr_noncovid=hr_nc, lcl_noncovid=l_nc, ucl_noncovid=u_nc,
                         hr_covid=hr_cvd, lcl_covid=l_cvd, ucl_covid=u_cvd,
                         anchored_acm=anch_acm, lcl_anchored_acm=anch_acm_l, ucl_anchored_acm=anch_acm_u,
                         anchored_covid=anch_cvd, lcl_anchored_covid=anch_cvd_l, ucl_anchored_covid=anch_cvd_u,
                         anchored_covid_fit=anch_cvd_fit, lcl_anchored_covid_fit=anch_cvd_fit_l, ucl_anchored_covid_fit=anch_cvd_fit_u,
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

            hA, (lA, uA), seA = cox_hr(tmp, "time_w", "ev_acm_w", "iptw", covars2,
                                       robust=not args.fast, ties=("breslow" if args.fast else "efron"), as_float32=args.fast)
            hN, (lN, uN), seN = cox_hr(tmp, "time_w", "ev_noncovid_w", "iptw", covars2,
                                       robust=not args.fast, ties=("breslow" if args.fast else "efron"), as_float32=args.fast)
            hC, (lC, uC), seC = cox_hr(tmp, "time_w", "ev_covid_w", "iptw", covars2,
                                       robust=not args.fast, ties=("breslow" if args.fast else "efron"), as_float32=args.fast)

            # Anchors
            aA, aAl, aAu = anchor_ci(hA, seA, hN, seN, power=1.0)
            aC, aCl, aCu = anchor_ci(hC, seC, hN, seN, power=args.alpha)

            # Fitted-α anchor using alpha_star
            aC_fit, aC_fit_l, aC_fit_u = anchor_ci(hC, seC, hN, seN, power=alpha_star)

            print(f"[{wlabel}]  HRs: ACM={hA:.3f} [{lA:.3f},{uA:.3f}]  nonCOVID={hN:.3f} [{lN:.3f},{uN:.3f}]  COVID={hC:.3f} [{lC:.3f},{uC:.3f}]  | Anchored ACM={aA:.3f}  COVID={aC:.3f}  COVID(fit α)={aC_fit:.3f}")

            rows.append(dict(age_band=label, window=wlabel,
                             hr_acm=hA, lcl_acm=lA, ucl_acm=uA,
                             hr_noncovid=hN, lcl_noncovid=lN, ucl_noncovid=uN,
                             hr_covid=hC, lcl_covid=lC, ucl_covid=uC,
                             anchored_acm=aA, lcl_anchored_acm=aAl, ucl_anchored_acm=aAu,
                             anchored_covid=aC, lcl_anchored_covid=aCl, ucl_anchored_covid=aCu,
                             anchored_covid_fit=aC_fit, lcl_anchored_covid_fit=aC_fit_l, ucl_anchored_covid_fit=aC_fit_u,
                             auc=auc))

        # Alpha summary row
        alpha_rows.append(dict(age_band=label, alpha=alpha_star,
                               alpha_raw=alpha_est.get("alpha", np.nan),
                               alpha_lcl=alpha_est.get("alpha_lcl", np.nan),
                               alpha_ucl=alpha_est.get("alpha_ucl", np.nan),
                               intercept=alpha_est.get("intercept", np.nan),
                               r2=alpha_est.get("r2", np.nan),
                               windows=alpha_est.get("weeks", np.nan)))

    out_csv = os.path.join(args.outdir, "windows_report.csv")
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nWritten: {out_csv}")

    # alpha summary index
    alpha_summary_csv = os.path.join(args.outdir, "alpha_summary.csv")
    pd.DataFrame(alpha_rows).to_csv(alpha_summary_csv, index=False)
    print(f"Written: {alpha_summary_csv}")

if __name__ == "__main__":
    main()
