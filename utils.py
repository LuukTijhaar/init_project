import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import gc

def mem_optimize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # downcast numeriek
    for c in df.select_dtypes(include="float").columns:
        df[c] = pd.to_numeric(df[c], downcast="float")
    for c in df.select_dtypes(include="int").columns:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    # strings -> category als dat loont
    for c in df.select_dtypes(include="object").columns:
        u = df[c].nunique(dropna=False)
        if u < 0.5 * len(df):
            df[c] = df[c].astype("category")
    return df

@st.cache_data(show_spinner=False, ttl=3600, max_entries=6)
def read_excel_smart(file, index_col=0, parse_dates=True) -> pd.DataFrame: 
    df = pd.read_excel(file, index_col=index_col, parse_dates=parse_dates,
        engine="openpyxl", engine_kwargs={"data_only": True})
    if parse_dates and not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index, errors="coerce")
    return mem_optimize_df(df)

def as_float32_series(s: pd.Series) -> pd.Series: 
    s = pd.Series(pd.to_numeric(s, errors="coerce"), index=s.index, name=s.name)
    return s.astype("float32")

def dedup_quarterly_series(s: pd.Series, how: str = "mean") -> pd.Series:
    """
    Zorg dat een Series een nette 15-minuten tijdreeks wordt:
    - index naar datetime
    - tz-info weg
    - indices naar 15 min afronden
    - dubbelen samenvoegen (mean of sum)
    """
    idx = pd.to_datetime(s.index, errors="coerce")
    s = pd.Series(pd.to_numeric(getattr(s, "values", s), errors="coerce"), index=idx, name=getattr(s, "name", None))
    s = s[~s.index.isna()]

    # verwijder timezone
    if isinstance(s.index, pd.DatetimeIndex) and s.index.tz is not None:
        s.index = s.index.tz_convert("UTC").tz_localize(None)

    # floor naar 15 min
    ns = s.index.asi8
    step = 900_000_000_000  # 15 minuten in ns
    floored = (ns // step) * step
    s.index = pd.to_datetime(floored)

    # dubbelen samenvoegen
    if how == "sum":
        s = s.groupby(s.index).sum()
    else:
        s = s.groupby(s.index).mean()

    return s.sort_index().astype("float32")

def align_to_common_15min_grid(v: pd.Series, o: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Zet verbruik (v) en opbrengst (o) op dezelfde 15-minuten grid
    en snijdt bij tot de overlappende periode.
    """
    v = dedup_quarterly_series(v, how="mean")
    o = dedup_quarterly_series(o, how="mean")

    start = max(v.index.min(), o.index.min())
    end   = min(v.index.max(), o.index.max())
    if pd.isna(start) or pd.isna(end) or start >= end:
        aligned = pd.DataFrame({"v": v, "o": o}).dropna()
        return aligned["v"].astype("float32"), aligned["o"].astype("float32")

    grid = pd.date_range(start=start, end=end, freq="15min")
    v = v.reindex(grid)
    o = o.reindex(grid)

    aligned = pd.DataFrame({"v": v, "o": o}).dropna()
    return aligned["v"].astype("float32"), aligned["o"].astype("float32")

def angle_picker(label: str, default: int = 90, key: str | None = None):
    # quick presets
    cols = st.columns(4)
    preset = None
    with cols[0]:
        if st.button("N (0°)", key=f"{key}_N"): preset = 0
    with cols[1]:
        if st.button("E (90°)", key=f"{key}_O"): preset = 90
    with cols[2]:
        if st.button("S (180°)", key=f"{key}_Z"): preset = 180
    with cols[3]:
        if st.button("W (270°)", key=f"{key}_W"): preset = 270

    # slider
    if preset is None:
        angle = st.slider(label, min_value=0, max_value=359, value=default, step=1, key=key)
    else:
        # force slider to preset by using a separate key store
        st.session_state[f"{key}_val"] = preset
        angle = st.slider(label, min_value=0, max_value=359, value=preset, step=1, key=key)

    # dial (polar plot)
    theta = np.deg2rad(angle)  # 0° = richting oosten op polar; we draaien labels mee
    fig = plt.figure(figsize=(3.8, 3.8))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location('N')   # 0° boven (Noord)
    ax.set_theta_direction(-1)        # klokwijzerzin
    ax.set_rticks([])                 # geen r-ringen
    ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels(["N", "O", "Z", "W"])
    ax.plot([0, theta], [0, 1], linewidth=3)  # pijl
    ax.scatter([theta], [1], s=60)
    ax.set_title(f"{angle}°", pad=12)

    st.pyplot(fig)
    plt.close(fig); del fig; gc.collect()

    return angle

def tilt_picker(label: str = "Hellingshoek (°)", default: int = 13, key: str | None = None) -> int:
    # Nummer input in plaats van slider
    angle = st.number_input(label, min_value=0, max_value=90, value=default, step=1, key=key)

    # --- Semicircle dial (0–90°) ---
    fig = plt.figure(figsize=(3.8, 3.0))
    ax = fig.add_subplot(121, projection='polar')
    ax.set_theta_zero_location('E')   # 0° naar rechts = horizontaal
    ax.set_theta_direction(1)
    ax.set_thetamin(0); ax.set_thetamax(90)
    ax.set_rticks([]); ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 15, 30, 45, 60, 75, 90]))
    ax.set_xticklabels([f"{d}°" for d in [0,15,30,45,60,75,90]])
    theta = np.deg2rad(angle)
    ax.plot([0, theta], [0, 1], linewidth=3)
    ax.scatter([theta], [1], s=60)
    ax.set_title(f"Helling: {angle}°", pad=10)

    # --- Simple side view panel ---
    ax2 = fig.add_subplot(122)
    ax2.set_aspect("equal")
    L, W = 1.2, 0.7  # schematisch paneel
    rect = np.array([[-L/2,-W/2],[ L/2,-W/2],[ L/2, W/2],[-L/2, W/2],[-L/2,-W/2]])
    rad = np.deg2rad(angle)
    R = np.array([[np.cos(rad), -np.sin(rad)],[np.sin(rad), np.cos(rad)]])
    rect_rot = (rect @ R.T) + np.array([0, 0.35])
    ax2.plot(rect_rot[:,0], rect_rot[:,1], linewidth=2)
    ax2.plot([-1.0, 1.0], [0, 0], linestyle="--", linewidth=1)  # grondlijn
    ax2.set_xlim(-1.1, 1.1); ax2.set_ylim(-0.15, 1.2)
    ax2.set_xticks([]); ax2.set_yticks([])
    ax2.set_title("Zijaanzicht")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig); del fig; gc.collect()
    return angle

PV_MODULETYPES = {
    "Topsun_TS_S400SA1": 400,
    "Grape_Solar_GS_S_420_KR3": 420,
    "SunPower_SPR_E20_440_COM": 440,
    "ENN_Solar_Energy_EST_460": 460,
    "SunPower_SPR_X22_475_COM": 475,
    "Sunpower_SPR_X22_480_COM": 480,
    "Sunpreme_Inc__SNPM_GxB_500": 500
}