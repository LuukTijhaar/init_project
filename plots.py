import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import gc
import numpy as np

def plot_dag_en_maand(verbruik: pd.Series, opbrengst: pd.Series):
    """
    Maakt:
    - Daglijnen (kWh/dag) voor verbruik, opbrengst (onder 0 voor visuele scheiding) en verschil (verbruik - opbrengst)
    - Maandstaven (kWh/maand) voor verbruik, opbrengst en overschot (max(opbrengst - verbruik, 0) per kwartier)
    Aannames:
    - Input is kwartierwaarden in kW → kWh = kW * 0,25
    """

    # 1) Netjes alignen en naar kWh brengen
    v = verbruik.copy()
    o = opbrengst.copy()
    v.index = pd.to_datetime(v.index)
    o.index = pd.to_datetime(o.index)
    df = pd.concat([v.rename("verbruik_kW"), o.rename("opbrengst_kW")], axis=1).dropna().sort_index()

    # kW per kwartier → kWh per kwartier
    df["verbruik_kWh"]  = df["verbruik_kW"]  * 0.25
    df["opbrengst_kWh"] = df["opbrengst_kW"] * 0.25

    # 2) Dagtotalen
    dag = df[["verbruik_kWh", "opbrengst_kWh"]].resample("D").sum()
    dag["verschil_kWh"] = dag["verbruik_kWh"] - dag["opbrengst_kWh"]

    # 3) Maandtotalen
    # Overschot = alleen positieve delen van (opbrengst - verbruik) per kwartier optellen
    df["overschot_kWh_kwartier"] = (df["opbrengst_kWh"] - df["verbruik_kWh"]).clip(lower=0)
    maand = pd.DataFrame({
        "verbruik_kWh":  df["verbruik_kWh"].resample("M").sum(),
        "opbrengst_kWh": df["opbrengst_kWh"].resample("M").sum(),
        "overschot_kWh": df["overschot_kWh_kwartier"].resample("M").sum(),
    })

    # 4) Totale sommen (kWh)
    totaal_verbruik  = dag["verbruik_kWh"].sum()
    totaal_opbrengst = dag["opbrengst_kWh"].sum()
    totaal_verschil  = totaal_verbruik - totaal_opbrengst

    # 5) Plot: daglijnen (kWh/dag)
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(dag.index, dag["verbruik_kWh"], label="Verbruik per dag (kWh)")
    ax1.plot(dag.index, dag["opbrengst_kWh"], label="Opbrengst per dag (kWh, negatief getekend)")
    ax1.plot(dag.index, dag["verschil_kWh"], label="Verschil (verbruik − opbrengst) per dag (kWh)")
    ax1.axhline(0, linewidth=0.8, linestyle="--")
    ax1.set_xlabel("Datum")
    ax1.set_ylabel("kWh per dag")
    ax1.set_title("Dagtotalen (kWh)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()

    # 6) Plot: maandstaven (kWh/maand) – gegroepeerd
    if not maand.empty:
        x = maand.index
        labels = [d.strftime("%Y-%m") for d in x]
        width = 0.28
        import numpy as np
        idx = np.arange(len(x))

        fig2, ax2 = plt.subplots(figsize=(12, 5))
        ax2.bar(idx - width, maand["verbruik_kWh"].values,  width, label="Verbruik (kWh/maand)")
        ax2.bar(idx,         maand["opbrengst_kWh"].values, width, label="Opbrengst (kWh/maand)")
        ax2.bar(idx + width, maand["overschot_kWh"].values, width, label="Overschot (kWh/maand)")

        ax2.set_xticks(idx)
        ax2.set_xticklabels(labels, rotation=45, ha="right")
        ax2.set_ylabel("kWh per maand")
        ax2.set_title("Maandtotalen: verbruik, opbrengst en overschot (kWh)")
        ax2.legend()
        ax2.grid(True, axis="y", alpha=0.3)
        fig2.tight_layout()

def plot_max_dagpiek_heatmap(verbruik: pd.Series,
                             opbrengst: pd.Series,
                             max_afname: float,
                             logo_bytes=None):
    # --- Validatie & aligneren ---
    if max_afname is None or not np.isfinite(max_afname) or max_afname <= 0:
        raise ValueError("max_afname moet een positief getal > 0 zijn.")

    # Zorg voor datetime index en dezelfde tijdstempels
    verbruik = verbruik.copy()
    opbrengst = opbrengst.copy()
    if not isinstance(verbruik.index, pd.DatetimeIndex):
        verbruik.index = pd.to_datetime(verbruik.index)
    if not isinstance(opbrengst.index, pd.DatetimeIndex):
        opbrengst.index = pd.to_datetime(opbrengst.index)

    # Align op de intersectie van timestamps
    ix = verbruik.index.intersection(opbrengst.index)
    verbruik = verbruik.loc[ix].astype("float32")
    opbrengst = opbrengst.loc[ix].astype("float32")

    if verbruik.empty or opbrengst.empty:
        raise ValueError("Geen overlappende timestamps tussen verbruik en opbrengst.")

    # --- Berekeningen ---
    verschil = verbruik - opbrengst
    # dagmax (kwartierpiek per dag)
    piek_per_dag = verschil.resample("D").max()
    # % van limiet (kan NaN opleveren als dag leeg was)
    perc_per_dag = (piek_per_dag / float(max_afname)) * 100.0
    perc_per_dag = perc_per_dag.replace([np.inf, -np.inf], np.nan)

    # DataFrame voor pivot
    df = pd.DataFrame({"perc": perc_per_dag})
    df["day"] = df.index.day
    df["month"] = df.index.month

    # Pivot: maand x dag
    pivot = df.pivot_table(index="month",
                           columns="day",
                           values="perc",
                           aggfunc="mean",
                           observed=False)
    pivot = pivot.replace([np.inf, -np.inf], np.nan)

    # --- Annotaties als strings (leeg bij NaN) ---
    def _fmt_int_or_empty(x):
        if pd.isna(x):
            return ""
        try:
            return f"{int(round(float(x)))}"
        except Exception:
            return ""

    annot = pivot.applymap(_fmt_int_or_empty)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, annot=annot, fmt="", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={'label': '% van limiet'})
    ax.set_xlabel("Dag van maand")
    ax.set_ylabel("Maand")
    ax.set_title("Max kwartierverbruik per dag (% van max afname)")
    fig.tight_layout(rect=[0, 0.08, 1, 1])

    # Logo onder de plot (optioneel)
    if logo_bytes:
        import matplotlib.offsetbox as offsetbox
        from PIL import Image
        import io as _io
        logo_img = Image.open(_io.BytesIO(logo_bytes))
        ax_logo = fig.add_axes([0.4, 0.01, 0.2, 0.07])
        ax_logo.axis('off')
        ax_logo.imshow(logo_img)

    # Streamlit tonen (als aanwezig), anders laat je de caller het fig zelf gebruiken
    try:
        import streamlit as st
        st.pyplot(fig)
    except Exception:
        pass

    plt.close(fig); gc.collect()

    # --- Resultaat (grootste dag) ---
    if perc_per_dag.dropna().empty:
        grootste_dag = None
    else:
        grootste_dag = perc_per_dag.idxmax().date()

    return grootste_dag