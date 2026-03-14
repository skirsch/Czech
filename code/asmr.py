import math
import pandas as pd
from datetime import date, datetime

# --- US 2000 Standard Million (19 groups); sums to 1_000_000 ---
US2000_STD_MILLION = {
    "<1": 13818,
    "1-4": 55317,
    "5-9": 72533,
    "10-14": 73032,
    "15-19": 72169,
    "20-24": 66478,
    "25-29": 64529,
    "30-34": 71044,
    "35-39": 80762,
    "40-44": 81851,
    "45-49": 72118,
    "50-54": 62716,
    "55-59": 48454,
    "60-64": 38793,
    "65-69": 34264,
    "70-74": 31773,
    "75-79": 26999,
    "80-84": 17842,
    "85+": 15508,
}

AGE_BINS = [
    ("<1",   0,   0),    # age == 0 years (~<1)
    ("1-4",  1,   4),
    ("5-9",  5,   9),
    ("10-14",10, 14),
    ("15-19",15, 19),
    ("20-24",20, 24),
    ("25-29",25, 29),
    ("30-34",30, 34),
    ("35-39",35, 39),
    ("40-44",40, 44),
    ("45-49",45, 49),
    ("50-54",50, 54),
    ("55-59",55, 59),
    ("60-64",60, 64),
    ("65-69",65, 69),
    ("70-74",70, 74),
    ("75-79",75, 79),
    ("80-84",80, 84),
    ("85+",  85, 200),   # cap at 200
]

def age_to_group(age_years: int) -> str:
    """Map integer age to US2000 19-group label."""
    if pd.isna(age_years):
        return None
    age = int(age_years)
    for label, a0, a1 in AGE_BINS:
        if a0 <= age <= a1:
            return label
    return None

def _coerce_week(x):
    """Return a datetime.date for the week key (datetime64, str, or date)."""
    if isinstance(x, pd.Timestamp):
        return x.date()
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return pd.to_datetime(x).date()

def _approx_age_from_born(week_d: date, born_year: int) -> int:
    """
    Approx age in whole years at week_d when only a birth YEAR is known.
    Uses July 1st as mid-year proxy.
    """
    if pd.isna(born_year):
        return None
    dob_proxy = date(int(born_year), 7, 1)
    return max(0, int((week_d - dob_proxy).days // 365.2425))

def _age_from_dob(week_d: date, dob: date) -> int:
    """Exact age in whole years at week_d from a full date of birth."""
    if pd.isna(dob):
        return None
    dob = pd.to_datetime(dob).date()
    years = week_d.year - dob.year - ((week_d.month, week_d.day) < (dob.month, dob.day))
    return max(0, years)

def _weights_df(min_age=None, max_age=None) -> pd.DataFrame:
    """
    Return weights dataframe filtered to [min_age, max_age] (inclusive) if provided,
    re-normalized so weights sum to 1.0.
    """
    dfw = pd.DataFrame(
        [{"age_group": k, "w": v} for k, v in US2000_STD_MILLION.items()]
    )
    # Attach bin ranges to filter by age if needed
    bounds = pd.DataFrame(
        [{"age_group": lab, "a0": a0, "a1": a1} for (lab, a0, a1) in AGE_BINS]
    )
    dfw = dfw.merge(bounds, on="age_group", how="left")

    if min_age is not None:
        dfw = dfw[dfw["a1"] >= int(min_age)]
    if max_age is not None:
        dfw = dfw[dfw["a0"] <= int(max_age)]

    # Re-normalize to sum to 1.0
    total = dfw["w"].sum()
    if total == 0:
        raise ValueError("Selected age range produced empty weight set.")
    dfw["w_norm"] = dfw["w"] / float(total)
    return dfw[["age_group", "w_norm"]].reset_index(drop=True)

def compute_asmr(
    df: pd.DataFrame,
    week_col: str = "week",
    group_col: str = None,      # e.g., "cohort" or "vax_group"; can be None for overall
    deaths_col: str = "deaths",
    pop_col: str = "pop",
    # supply exactly ONE of age_col, dob_col, born_col
    age_col: str = None,        # integer age in years
    dob_col: str = None,        # full date of birth
    born_col: str = None,       # birth year (int)
    min_age: int = None,        # e.g., 40 to do 40+
    max_age: int = None,
    annualize: bool = False,    # if True, multiply weekly rate by 52.1775
    return_components: bool = False,  # if True, also return age-specific rates
) -> pd.DataFrame:
    """
    Compute weekly direct age-standardized mortality rate per 100k using US2000 weights.

    Input df must contain one row per (week, person/age bin) with counts, OR an already
    aggregated dataset by (week, age, group). Provide enough info to determine age_group.

    Returns a DataFrame with columns:
        [group_col], week_col, ASMR_per100k_week (and ASMR_per100k_annual if annualize)
    """
    if sum(x is not None for x in (age_col, dob_col, born_col)) != 1:
        raise ValueError("Specify exactly one of age_col, dob_col, or born_col.")

    # Ensure week is date
    df = df.copy()
    df[week_col] = df[week_col].apply(_coerce_week)

    # Derive age in whole years
    if age_col:
        df["_age"] = df[age_col].astype("Int64")
    elif dob_col:
        df["_age"] = df.apply(lambda r: _age_from_dob(r[week_col], r[dob_col]), axis=1)
    else:  # born_col
        df["_age"] = df.apply(lambda r: _approx_age_from_born(r[week_col], int(r[born_col])), axis=1)

    # Map to 19-group label
    df["_age_group"] = df["_age"].apply(age_to_group)

    # Aggregate to (week, group, age_group)
    gb_cols = [week_col, "_age_group"]
    if group_col:
        gb_cols.insert(1, group_col)

    agg = (
        df.groupby(gb_cols, dropna=False)[[deaths_col, pop_col]]
        .sum(min_count=1)
        .reset_index()
    )

    # Build weights for selected age range and join
    w = _weights_df(min_age=min_age, max_age=max_age)  # age_group, w_norm

    # Ensure every group/week has all age groups (fill missing with 0)
    # Create a cartesian frame over existing (week, group) x all age groups
    keys = agg[[c for c in gb_cols if c != "_age_group"]].drop_duplicates()
    keys["key"] = 1
    wg = w.copy()
    wg["key"] = 1
    frame = keys.merge(wg, on="key").drop(columns=["key"])

    frame = frame.merge(agg, on=gb_cols, how="left")
    frame[deaths_col] = frame[deaths_col].fillna(0.0)
    frame[pop_col] = frame[pop_col].fillna(0.0)

    # Age-specific weekly rates
    frame["rate"] = frame.apply(
        lambda r: (r[deaths_col] / r[pop_col]) if r[pop_col] > 0 else 0.0, axis=1
    )

    # Direct standardization: sum(w * r)
    grouped = frame.groupby([c for c in gb_cols if c != "_age_group"], dropna=False)
    out = grouped.apply(lambda g: (g["w_norm"] * g["rate"]).sum()).reset_index(name="ASMR_weekly")

    # Per 100k scaling
    out["ASMR_per100k_week"] = out["ASMR_weekly"] * 100_000.0
    if annualize:
        out["ASMR_per100k_annual"] = out["ASMR_per100k_week"] * 52.1775

    # Optional: return age-specific components for QA
    if return_components:
        frame["rate_per100k_week"] = frame["rate"] * 100_000.0
        return out, frame

    return out

# ------------------------
# Example usage (assumes df has columns: week, born, group, deaths, pop)
# df = pd.read_csv("your_weekly_counts.csv")
# asmr = compute_asmr(
#     df,
#     week_col="week",
#     group_col="group",          # or None
#     deaths_col="deaths",
#     pop_col="pop",
#     born_col="born",            # OR set age_col="age" if you have integer ages
#     min_age=None, max_age=None, # or set min_age=40 for 40+
#     annualize=False,
# )
# # Pivot for plotting:
# asmr_pivot = asmr.pivot(index="week", columns="group", values="ASMR_per100k_week").sort_index()
