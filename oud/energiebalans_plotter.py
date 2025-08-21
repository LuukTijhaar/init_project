import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import pandas as pd

def plot_energiebalans_dag(verbruik: pd.DataFrame, opbrengst: pd.DataFrame, max_afname, max_teruglevering):
    """
    Plot de energiebalans op een dag: verbruik, opbrengst, en saldo (met max afname/teruglevering).
    Toont het totale dag-saldo in de grafiek.

    :param verbruik: pd.DataFrame met verbruikswaarden per tijdstap (één kolom)
    :param opbrengst: pd.DataFrame met opbrengstwaarden per tijdstap (één kolom)
    :param max_afname: maximale afname uit het net (positief getal)
    :param max_teruglevering: maximale teruglevering aan het net (positief getal)
    """
    dag = pd.to_datetime(dag, format="%d-%m-%Y").date()
    dag_df = df[f"{dag} 00:00": f"{dag} 23:45"]
    dag_verbruik = verbruik[f"{dag} 00:00": f"{dag} 23:45"]

    if verbruik.shape != opbrengst.shape:
        raise ValueError("verbruik en opbrengst moeten dezelfde vorm hebben")
    # Maak beide even lang (minimale lengte)
    min_len = min(len(verbruik), len(opbrengst))
    verbruik = verbruik.iloc[:min_len, :]
    opbrengst = opbrengst.iloc[:min_len, :]
    tijdstappen = verbruik.index[:min_len]
    verbruik_s = verbruik.iloc[:, 0]
    opbrengst_s = opbrengst.iloc[:, 0]
    
    saldo = opbrengst_s - verbruik_s
    saldo_beperkt = saldo.copy()
    saldo_beperkt[saldo < 0] = saldo[saldo < 0].clip(lower=-max_afname)
    saldo_beperkt[saldo > 0] = saldo[saldo > 0].clip(upper=max_teruglevering)
    totaal_saldo = saldo_beperkt.sum()

    plt.figure(figsize=(10, 6))
    plt.plot(tijdstappen, verbruik_s, label='Verbruik', color='red')
    plt.plot(tijdstappen, opbrengst_s, label='Opbrengst', color='green')
    plt.plot(tijdstappen, saldo_beperkt, label='Saldo (beperkt)', color='blue')
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.axhline(-max_afname, color='grey', linewidth=0.8, linestyle=':', label='Max afname')
    plt.axhline(max_teruglevering, color='orange', linewidth=0.8, linestyle=':', label='Max teruglevering')
    plt.xlabel('Tijdstap')
    plt.ylabel('Energie')
    plt.title(f'Energiebalans dag (totaal saldo: {totaal_saldo:.2f})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.ylabel('Energie')
    plt.title(f'Energiebalans dag (totaal saldo: {totaal_saldo:.2f})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    st.pyplot(plt)

def plot_energiebalans_jaar_per_dag(verbruik_jaar: pd.DataFrame, opbrengst_jaar: pd.DataFrame, max_afname, max_teruglevering):
    """
    Splitst jaardata (met datetime-index) naar dagdata en plot voor elke dag de energiebalans.
    :param verbruik_jaar: pd.DataFrame met verbruikswaarden, datetime-index
    :param opbrengst_jaar: pd.DataFrame met opbrengstwaarden, datetime-index
    :param max_afname: maximale afname uit het net (positief getal)
    :param max_teruglevering: maximale teruglevering aan het net (positief getal)
    """
    # Zorg dat indexen datetime zijn
    verbruik_jaar = verbruik_jaar.copy()
    opbrengst_jaar = opbrengst_jaar.copy()
    verbruik_jaar.index = pd.to_datetime(verbruik_jaar.index)
    opbrengst_jaar.index = pd.to_datetime(opbrengst_jaar.index)
    # Neem alleen overlappende dagen
    dagen = sorted(set(verbruik_jaar.index.normalize()) & set(opbrengst_jaar.index.normalize()))
    for dag in dagen:
        v_dag = verbruik_jaar[verbruik_jaar.index.normalize() == dag]
        o_dag = opbrengst_jaar[opbrengst_jaar.index.normalize() == dag]
        min_len = min(len(v_dag), len(o_dag))
        if min_len == 0:
            continue
        v_dag = v_dag.iloc[:min_len, :]
        o_dag = o_dag.iloc[:min_len, :]
        tijdstappen = v_dag.index[:min_len]
        verbruik_s = v_dag.iloc[:, 0]
        opbrengst_s = o_dag.iloc[:, 0]
        saldo = opbrengst_s - verbruik_s
        saldo_beperkt = saldo.copy()
        saldo_beperkt[saldo < 0] = saldo[saldo < 0].clip(lower=-max_afname)
        saldo_beperkt[saldo > 0] = saldo[saldo > 0].clip(upper=max_teruglevering)
        totaal_saldo = saldo_beperkt.sum()
        plt.figure(figsize=(10, 6))
        plt.plot(tijdstappen, verbruik_s, label='Verbruik', color='red')
        plt.plot(tijdstappen, opbrengst_s, label='Opbrengst', color='green')
        plt.plot(tijdstappen, saldo_beperkt, label='Saldo (beperkt)', color='blue')
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.axhline(-max_afname, color='grey', linewidth=0.8, linestyle=':', label='Max afname')
        plt.axhline(max_teruglevering, color='orange', linewidth=0.8, linestyle=':', label='Max teruglevering')
        plt.xlabel('Tijdstap')
        plt.ylabel('Energie')
        plt.title(f'Energiebalans {dag.date()} (totaal saldo: {totaal_saldo:.2f})')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

def plot_dagbalans_jaar(verbruik_jaar: pd.DataFrame, opbrengst_jaar: pd.DataFrame, max_afname, max_teruglevering):
    """
    Berekent per dag de energiebalans (totaal verbruik, totaal opbrengst, totaal saldo met max afname/teruglevering)
    en plot deze dagbalansen als tijdreeks.

    :param verbruik_jaar: pd.DataFrame met verbruikswaarden, datetime-index
    :param opbrengst_jaar: pd.DataFrame met opbrengstwaarden, datetime-index
    :param max_afname: maximale afname uit het net (positief getal)
    :param max_teruglevering: maximale teruglevering aan het net (positief getal)
    """
    # Zorg dat indexen datetime zijn
    verbruik_jaar = verbruik_jaar.copy()
    opbrengst_jaar = opbrengst_jaar.copy()
    verbruik_jaar.index = pd.to_datetime(verbruik_jaar.index)
    opbrengst_jaar.index = pd.to_datetime(opbrengst_jaar.index)
    dagen = sorted(set(verbruik_jaar.index.normalize()) & set(opbrengst_jaar.index.normalize()))
    dagresultaten = []
    for dag in dagen:
        v_dag = verbruik_jaar[verbruik_jaar.index.normalize() == dag]
        o_dag = opbrengst_jaar[opbrengst_jaar.index.normalize() == dag]
        min_len = min(len(v_dag), len(o_dag))
        if min_len == 0:
            continue
        v_dag = v_dag.iloc[:min_len, :]
        o_dag = o_dag.iloc[:min_len, :]
        verbruik_s = v_dag.iloc[:, 0]
        # Controleer aantal kolommen in opbrengst
        if o_dag.shape[1] == 1:
            opbrengst_s = o_dag.iloc[:, 0]
            saldo = opbrengst_s - verbruik_s
            saldo_beperkt = saldo.copy()
            saldo_beperkt[saldo < 0] = saldo[saldo < 0].clip(lower=-max_afname)
            saldo_beperkt[saldo > 0] = saldo[saldo > 0].clip(upper=max_teruglevering)
            dagresultaten.append({
                'dag': dag,
                'verbruik': verbruik_s.sum(),
                'opbrengst': opbrengst_s.sum(),
                'saldo': saldo_beperkt.sum()
            })
        elif o_dag.shape[1] == 2:
            opbrengst1 = o_dag.iloc[:, 0]
            opbrengst2 = o_dag.iloc[:, 1]
            saldo1 = opbrengst1 - verbruik_s
            saldo2 = opbrengst2 - verbruik_s
            saldo1_beperkt = saldo1.copy()
            saldo2_beperkt = saldo2.copy()
            saldo1_beperkt[saldo1 < 0] = saldo1[saldo1 < 0].clip(lower=-max_afname)
            saldo1_beperkt[saldo1 > 0] = saldo1[saldo1 > 0].clip(upper=max_teruglevering)
            saldo2_beperkt[saldo2 < 0] = saldo2[saldo2 < 0].clip(lower=-max_afname)
            saldo2_beperkt[saldo2 > 0] = saldo2[saldo2 > 0].clip(upper=max_teruglevering)
            dagresultaten.append({
                'dag': dag,
                'verbruik': verbruik_s.sum(),
                'opbrengst1': opbrengst1.sum(),
                'opbrengst2': opbrengst2.sum(),
                'saldo1': saldo1_beperkt.sum(),
                'saldo2': saldo2_beperkt.sum()
            })
        else:
            raise ValueError("Opbrengst mag maximaal 2 kolommen bevatten.")

    if not dagresultaten:
        print("Geen overlappende dagen met data gevonden.")
        return

    df_dagbalans = pd.DataFrame(dagresultaten).set_index('dag')
    plt.figure(figsize=(12, 6))
    plt.plot(df_dagbalans.index, df_dagbalans['verbruik'], label='Totaal verbruik per dag', color='red')
    if 'opbrengst1' in df_dagbalans.columns and 'opbrengst2' in df_dagbalans.columns:
        plt.plot(df_dagbalans.index, df_dagbalans['opbrengst1'], label='Totaal opbrengst 1 per dag', color='green')
        plt.plot(df_dagbalans.index, df_dagbalans['opbrengst2'], label='Totaal opbrengst 2 per dag', color='orange')
        plt.plot(df_dagbalans.index, df_dagbalans['saldo1'], label='Dagbalans 1 (beperkt)', color='blue')
        plt.plot(df_dagbalans.index, df_dagbalans['saldo2'], label='Dagbalans 2 (beperkt)', color='purple')
    else:
        plt.plot(df_dagbalans.index, df_dagbalans['opbrengst'], label='Totaal opbrengst per dag', color='green')
        plt.plot(df_dagbalans.index, df_dagbalans['saldo'], label='Dagbalans (beperkt)', color='blue')
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.xlabel('Datum')
    plt.ylabel('Energie')
    plt.title('Dagelijkse energiebalans over het jaar')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def interactieve_energiebalans_plots(verbruik_jaar: pd.DataFrame, opbrengst_jaar: pd.DataFrame, max_afname, max_teruglevering):
    """
    Toon interactieve checkboxes om te kiezen welke energiebalans-plots getoond worden.
    """
    try:
        from ipywidgets import Checkbox, HBox, VBox, Output, interactive
        from IPython.display import display, clear_output
    except ImportError:
        print("ipywidgets en IPython zijn nodig voor interactieve plots.")
        return

    cb_dagbalans = Checkbox(value=True, description='Dagbalans jaar')
    cb_profielen = Checkbox(value=False, description='Dagprofielen (alle dagen)')
    output = Output()

    def update_plots(*args):
        with output:
            clear_output(wait=True)
            if cb_dagbalans.value:
                plot_dagbalans_jaar(verbruik_jaar, opbrengst_jaar, max_afname, max_teruglevering)
            if cb_profielen.value:
                plot_energiebalans_jaar_per_dag(verbruik_jaar, opbrengst_jaar, max_afname, max_teruglevering)

    cb_dagbalans.observe(update_plots, 'value')
    cb_profielen.observe(update_plots, 'value')

    display(VBox([HBox([cb_dagbalans, cb_profielen]), output]))
    update_plots()

def plot_reeksen_en_verschil(opbrengst: pd.Series, verbruik: pd.Series, titel="Opbrengst vs Verbruik"):
    """
    Plot twee reeksen (opbrengst en verbruik) en hun verschil.

    :param opbrengst: pandas Series (of DataFrame-kolom) met opbrengst
    :param verbruik: pandas Series (of DataFrame-kolom) met verbruik
    :param titel: optioneel, titel van de plot
    """
    # Zorg dat de indexen gelijk zijn
    min_len = min(len(opbrengst), len(verbruik))
    opbrengst = opbrengst.iloc[:min_len]
    verbruik = verbruik.iloc[:min_len]
    index = opbrengst.index

    verschil = opbrengst - verbruik

    plt.figure(figsize=(12, 6))
    plt.plot(index, opbrengst, label="Opbrengst", color="green")
    plt.plot(index, verbruik, label="Verbruik", color="red")
    plt.plot(index, verschil, label="Verschil (Opbrengst - Verbruik)", color="blue")
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.xlabel("Tijd  (kwartieren)")
    plt.ylabel("Energie (kW)")
    plt.title(titel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    st.pyplot(plt)

def plot_max_kwartierverbruik_heatmap(verbruik: pd.Series, limiet: float):
    """
    Plot een heatmap van het hoogste kwartierverbruik per dag als percentage van het limiet.

    :param verbruik: pandas Series met datetime-index (kwartierwaarden)
    :param limiet: float, limietwaarde voor verbruik
    """
    # Zorg dat index datetime is
    verbruik = verbruik.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    # Groepeer per dag en neem het maximum per dag
    max_per_dag = verbruik.groupby(verbruik.index.normalize()).max()
    # Bereken percentage van limiet
    perc_per_dag = (max_per_dag / limiet) * 100

    # Zet om naar DataFrame met kolom 'percentage'
    df = pd.DataFrame({'percentage': perc_per_dag})
    df['dag'] = df.index

    # Maak een matrix voor heatmap: rijen=weken, kolommen=weekdagen
    df['week'] = df['dag'].dt.isocalendar().week
    df['weekday'] = df['dag'].dt.weekday
    pivot = df.pivot(index='week', columns='weekday', values='percentage')

    fig, ax = plt.subplots(figsize=(10, 5))
    c = ax.imshow(pivot, aspect='auto', cmap='YlOrRd', vmin=0, vmax=100)
    ax.set_xlabel('Weekdag (0=ma, 6=zo)')
    ax.set_ylabel('Weeknummer')
    ax.set_title('Max kwartierverbruik per dag (% van limiet)')
    plt.colorbar(c, ax=ax, label='% van limiet')
    ax.set_xticks(range(7))
    ax.set_xticklabels(['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'])
    plt.tight_layout()
    st.pyplot(fig)