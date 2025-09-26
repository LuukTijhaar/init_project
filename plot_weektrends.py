import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from typing import Optional



def _add_day_lines_and_labels(ax, min_len):
    # Voeg verticale lijnen toe bij dagovergangen
    for d in range(1, 7):
        ax.axvline(x=d*96, color='gray', linestyle=':', linewidth=1)
    # Zet daglabels op de x-as
    dagen = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo']
    posities = [i*96 for i in range(7)]
    ax.set_xticks(posities)
    ax.set_xticklabels(dagen)

def plot_weektrends(verbruik: pd.Series, title="Weektrends kwartierdata", max_afname=None, max_teruglevering=None):
    """
    Plot per week een lijn van kwartierverbruik (52 lijnen).
    Toont ook de gemiddelde week als dikke zwarte lijn.
    Optioneel: toon limieten als stippellijn.
    """
    # Zorg dat index datetime is
    verbruik = verbruik.copy()
    verbruik.index = pd.to_datetime(verbruik.index)

    # Groepeer per weeknummer
    weekgroepen = verbruik.groupby(verbruik.index.isocalendar().week)

    fig, ax = plt.subplots(figsize=(16, 8))
    min_len = min(len(week.reset_index(drop=True)) for _, week in weekgroepen)
    weekdata_arr = []
    for weeknr, weekdata in weekgroepen:
        # Reset index zodat x-as 0..len-1 is (kwartiernummer binnen week)
        weekdata = weekdata.reset_index(drop=True)
        weekdata_arr.append(weekdata.values[:min_len])
        ax.plot(weekdata.values[:min_len], label=f"Week {weeknr}", alpha=0.5)
    # Gemiddelde week als dikke zwarte lijn
    mean_week = pd.DataFrame(weekdata_arr).mean(axis=0)
    ax.plot(mean_week, label="Gemiddelde week", color="black", linewidth=3, zorder=10)
    # Limieten als stippellijn
    if max_afname is not None:
        ax.axhline(max_afname, color="orange", linestyle=":", linewidth=2, label="Afnamelimiet")
    if max_teruglevering is not None:
        ax.axhline(-max_teruglevering, color="purple", linestyle=":", linewidth=2, label="Terugleverlimiet")
    ax.set_xlabel("Kwartiernummer binnen week (0=maandag 00:00)")
    ax.set_ylabel("Verbruik (kW)")
    ax.set_title(title)
    ax.grid(True)
    ax.legend(ncol=4, fontsize=8, loc='upper right', frameon=False)
    _add_day_lines_and_labels(ax, min_len)
    plt.tight_layout()
    
    st.pyplot(fig)

def plot_weektrends_summary(verbruik: pd.Series, title="Gemiddelde, max en min week (kwartierdata)", max_afname=None, max_teruglevering=None):
    """
    Plot de gemiddelde week, de week met hoogste totaalverbruik en de week met laagste totaalverbruik.
    Toont ook de som van de min/max week onder de grafiek.
    """
    verbruik = verbruik.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    weekgroepen = verbruik.groupby(verbruik.index.isocalendar().week)
    weekdata_list = [week.reset_index(drop=True) for _, week in weekgroepen]
    week_lengths = [len(w) for w in weekdata_list]
    min_len = min(week_lengths)
    weekdata_arr = [w.iloc[:min_len].values for w in weekdata_list]
    weekdata_arr = pd.DataFrame(weekdata_arr)  # shape: (n_weeks, min_len)

    mean_week = weekdata_arr.mean(axis=0)
    max_idx = weekdata_arr.sum(axis=1).idxmax()
    max_week = weekdata_arr.iloc[max_idx]
    min_idx = weekdata_arr.sum(axis=1).idxmin()
    min_week = weekdata_arr.iloc[min_idx]

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(mean_week, label="Gemiddelde week", color="blue", linewidth=2)
    ax.plot(max_week, label="Max week", color="red", linestyle="--", alpha=0.7)
    ax.plot(min_week, label="Min week", color="green", linestyle="--", alpha=0.7)
    # Limieten als stippellijn
    if max_afname is not None:
        ax.axhline(max_afname, color="orange", linestyle=":", linewidth=2, label="Afnamelimiet")
    if max_teruglevering is not None:
        ax.axhline(-max_teruglevering, color="purple", linestyle=":", linewidth=2, label="Terugleverlimiet")
    ax.set_xlabel("Kwartiernummer binnen week (0=maandag 00:00)")
    ax.set_ylabel("Verbruik (kW)")
    ax.set_title(title)
    ax.grid(True)
    ax.legend(fontsize=12)
    _add_day_lines_and_labels(ax, min_len)
    plt.tight_layout()
    st.pyplot(fig)

    # Toon de sommen onder de grafiek
    st.info(
        f"Som gemiddelde week: {mean_week.sum():.2f} kWh\n"
        f"Som max week: {max_week.sum():.2f} kWh\n"
        f"Som min week: {min_week.sum():.2f} kWh"
    )

def plot_weektrends_per_quartile_stats(verbruik: pd.Series, title="Gemiddelde, max en min per kwartier van de week", max_afname=None, max_teruglevering=None):
    """
    Plot per kwartier van de week het gemiddelde, de max en de min over alle weken.
    """
    verbruik = verbruik.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    weekgroepen = verbruik.groupby(verbruik.index.isocalendar().week)
    weekdata_list = [week.reset_index(drop=True) for _, week in weekgroepen]
    week_lengths = [len(w) for w in weekdata_list]
    min_len = min(week_lengths)
    weekdata_arr = [w.iloc[:min_len].values for w in weekdata_list]
    weekdata_arr = pd.DataFrame(weekdata_arr)  # shape: (n_weeks, min_len)

    mean_per_quartile = weekdata_arr.mean(axis=0)
    max_per_quartile = weekdata_arr.max(axis=0)
    min_per_quartile = weekdata_arr.min(axis=0)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(mean_per_quartile, label="Gemiddelde", color="blue", linewidth=2)
    ax.plot(max_per_quartile, label="Max", color="red", linestyle="--", alpha=0.7)
    ax.plot(min_per_quartile, label="Min", color="green", linestyle="--", alpha=0.7)
    # Limieten als stippellijn
    if max_afname is not None:
        ax.axhline(max_afname, color="orange", linestyle=":", linewidth=2, label="Afnamelimiet")
    if max_teruglevering is not None:
        ax.axhline(-max_teruglevering, color="purple", linestyle=":", linewidth=2, label="Terugleverlimiet")
    ax.set_xlabel("Kwartiernummer binnen week (0=maandag 00:00)")
    ax.set_ylabel("Verbruik (kW)")
    ax.set_title(title)
    ax.grid(True)
    ax.legend(fontsize=12)
    _add_day_lines_and_labels(ax, min_len)
    plt.tight_layout()
    st.pyplot(fig)

def plot_accu_week_simulatie(verbruik: pd.Series, opbrengst: pd.Series, accu_capaciteit: float, max_afname: float, max_teruglevering: float, title="Accu simulatie week"):
    """
    Simuleer en plot een week met hoog verbruik en lage opbrengst, inclusief accuvermogen.
    Toont ook het tekort als verbruik > afnamelimiet en accu leeg is.
    """
    # Zorg dat indexen gelijk en datetime zijn
    verbruik = verbruik.copy()
    opbrengst = opbrengst.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    opbrengst.index = pd.to_datetime(opbrengst.index)
    min_len = min(len(verbruik), len(opbrengst))
    verbruik = verbruik.iloc[:min_len]
    opbrengst = opbrengst.iloc[:min_len]

    # Zoek week met hoogste totaalverbruik en relatief lage opbrengst
    weekgroepen = verbruik.groupby(verbruik.index.isocalendar().week)
    weekdata_list = []
    weekopbrengst_list = []
    weeknr_list = []
    for (weeknr, weekdata), (_, weekopbrengst) in zip(weekgroepen, opbrengst.groupby(opbrengst.index.isocalendar().week)):
        weekdata = weekdata.reset_index(drop=True)
        weekopbrengst = weekopbrengst.reset_index(drop=True)
        weekdata_list.append(weekdata)
        weekopbrengst_list.append(weekopbrengst)
        weeknr_list.append(weeknr)
    # Selecteer week met hoogste verbruik / laagste opbrengst
    scores = [vd.sum() - vo.sum() for vd, vo in zip(weekdata_list, weekopbrengst_list)]
    idx = max(range(len(scores)), key=lambda i: scores[i])
    v = weekdata_list[idx]
    o = weekopbrengst_list[idx]
    weeknr = weeknr_list[idx]
    n = len(v)

    # Simuleer accuvermogen per kwartier + tekort
    accu = [0.0] * n
    tekort = [0.0] * n
    accuv = 0.0
    for i in range(n):
        overschot = o[i] - v[i]
        # Laad accu met overschot (max teruglevering)
        if overschot > 0:
            laad = min(overschot, max_teruglevering, accu_capaciteit - accuv)
            accuv += laad * 0.25  # kwartier naar kWh
        # Ontlaad accu als verbruik > max_afname
        elif v[i] > max_afname:
            nodig = v[i] - max_afname
            ontlaad = min(nodig, accuv / 0.25)
            accuv -= ontlaad * 0.25
            # Tekort als accu leeg is
            if ontlaad < nodig:
                tekort[i] = (nodig - ontlaad) * 0.25  # kWh tekort dit kwartier
        # Accu mag niet negatief/te vol
        accuv = max(0.0, min(accuv, accu_capaciteit))
        accu[i] = accuv

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(v.values, label="Verbruik", color="red")
    ax.plot(o.values, label="Opbrengst", color="green")
    ax.plot(accu, label="Accuvermogen (kWh)", color="blue", linewidth=2)
    ax.plot(tekort, label="Tekort (kWh)", color="black", linestyle=":", linewidth=2)
    # Limieten als stippellijn
    ax.axhline(max_afname, color="orange", linestyle=":", linewidth=2, label="Afnamelimiet")
    ax.set_xlabel("Kwartiernummer binnen week (0=maandag 00:00)")
    ax.set_ylabel("Vermogen / Energie")
    ax.set_title(f"{title} (week {weeknr})")
    ax.grid(True)
    _add_day_lines_and_labels(ax, n)
    ax.legend(fontsize=12)
    plt.tight_layout()
    st.pyplot(fig)
    st.info(
        f"Week {weeknr}: totaal verbruik {v.sum():.2f} kWh, totaal opbrengst {o.sum():.2f} kWh, "
        f"max acculading {max(accu):.2f} kWh, totaal tekort {sum(tekort):.2f} kWh"
    )

def plot_accu_week_simulatie_select(verbruik: pd.Series, opbrengst: pd.Series, accu_capaciteit: float, max_afname: float, max_teruglevering: float, title="Accu simulatie week"):
    """
    Streamlit interface om een week te kiezen voor de accu-simulatie.
    Toont ook welke week het hoogste verbruik heeft en welke week het meest gemiddeld is.
    """
    verbruik = verbruik.copy()
    opbrengst = opbrengst.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    opbrengst.index = pd.to_datetime(opbrengst.index)
    min_len = min(len(verbruik), len(opbrengst))
    verbruik = verbruik.iloc[:min_len]
    opbrengst = opbrengst.iloc[:min_len]

    # Groepeer per week
    weekgroepen_v = list(verbruik.groupby(verbruik.index.isocalendar().week))
    weekgroepen_o = list(opbrengst.groupby(opbrengst.index.isocalendar().week))
    weeknrs = [wnr for wnr, _ in weekgroepen_v]
    weekdata_list = [week.reset_index(drop=True) for _, week in weekgroepen_v]
    weekopbrengst_list = [week.reset_index(drop=True) for _, week in weekgroepen_o]

    # Bepaal week met hoogste verbruik en meest gemiddelde week
    weekverbruik_sommen = [w.sum() for w in weekdata_list]
    max_idx = int(pd.Series(weekverbruik_sommen).idxmax())
    mean_val = pd.Series(weekverbruik_sommen).mean()
    mean_idx = int((pd.Series(weekverbruik_sommen) - mean_val).abs().idxmin())

    st.markdown(f"**Week met hoogste verbruik:** {weeknrs[max_idx]} (totaal: {weekverbruik_sommen[max_idx]:.2f} kWh)")
    st.markdown(f"**Week met gemiddeld verbruik:** {weeknrs[mean_idx]} (totaal: {weekverbruik_sommen[mean_idx]:.2f} kWh)")

    # Streamlit weekkeuze
    gekozen_weeknr = st.number_input("Kies weeknummer voor simulatie", min_value=int(min(weeknrs)), max_value=int(max(weeknrs)), value=int(weeknrs[mean_idx]), step=1)
    if gekozen_weeknr in weeknrs:
        idx = weeknrs.index(gekozen_weeknr)
    else:
        idx = mean_idx  # fallback

    v = weekdata_list[idx]
    o = weekopbrengst_list[idx]
    n = len(v)

    # Simuleer accuvermogen per kwartier + tekort
    accu = [0.0] * n
    tekort = [0.0] * n
    accuv = 0.0
    for i in range(n):
        overschot = o[i] - v[i]
        # Laad accu met overschot (max teruglevering)
        if overschot > 0:
            laad = min(overschot, max_teruglevering, accu_capaciteit - accuv)
            accuv += laad * 0.25  # kwartier naar kWh
        # Ontlaad accu als verbruik > max_afname
        elif v[i] > max_afname:
            nodig = v[i] - max_afname
            ontlaad = min(nodig, accuv / 0.25)
            accuv -= ontlaad * 0.25
            # Tekort als accu leeg is
            if ontlaad < nodig:
                tekort[i] = (nodig - ontlaad) * 0.25  # kWh tekort dit kwartier
        # Accu mag niet negatief/te vol
        accuv = max(0.0, min(accuv, accu_capaciteit))
        accu[i] = accuv

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(v.values, label="Verbruik", color="red")
    ax.plot(o.values, label="Opbrengst", color="green")
    ax.plot(accu, label="Accuvermogen (kWh)", color="blue", linewidth=2)
    ax.plot(tekort, label="Tekort (kWh)", color="black", linestyle=":", linewidth=2)
    ax.axhline(max_afname, color="orange", linestyle=":", linewidth=2, label="Afnamelimiet")
    ax.set_xlabel("Kwartiernummer binnen week (0=maandag 00:00)")
    ax.set_ylabel("Vermogen / Energie")
    ax.set_title(f"{title} (week {weeknrs[idx]})")
    ax.grid(True)
    _add_day_lines_and_labels(ax, n)
    ax.legend(fontsize=12)
    plt.tight_layout()
    st.pyplot(fig)
    st.info(
        f"Week {weeknrs[idx]}: totaal verbruik {v.sum():.2f} kWh, totaal opbrengst {o.sum():.2f} kWh, "
        f"max acculading {max(accu):.2f} kWh, totaal tekort {sum(tekort):.2f} kWh"
    )

def accu_stand_calculator(verbruik: pd.Series, opbrengst: pd.Series, accu_capaciteit: float, peak_shaven=False, pv_zelf_consumption=False, state_of_charge=False, var_tarieven=False, min_vermogen_accu=20, grenswaarde=50, max_laden = 5):
    """
    Simuleer de accu-stand over een periode gegeven een startwaarde.
    Toont ook het tekort als verbruik > afnamelimiet en accu leeg is.
    """
    # Zorg dat indexen gelijk en datetime zijn
    verbruik = verbruik.copy()
    opbrengst = opbrengst.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    opbrengst.index = pd.to_datetime(opbrengst.index)
    min_len = min(len(verbruik), len(opbrengst))
    verbruik = verbruik.iloc[:min_len]
    opbrengst = opbrengst.iloc[:min_len]

    n = len(verbruik)

    # Simuleer accuvermogen per kwartier + tekort
    # Rekenregels voor verschillende strategieën; 
    # pv zelf_consumptie; wannneer pv zelfconsumptie het doel is eerst eigen gebruik simuleren en daarna pas laden met overschot, 's nachts ontladen. 
    # peak shaven; wanneer piekafname het doel is eerst ontladen bij verbruik boven grenswaarde, daarna pas laden met overschot grenswaarde moet zvm gehaald worden op pieken op te vangen. 
    # var_tarieven; wanneer variabele tarieven het doel is, ontladen bij hoge tarieven en laden bij lage tarieven.
    # 's nachts wordt de stand van de accu gecheckt en opgeladen tot een bepaald punt (bijv. 6 uur 's ochtends) om de ochtendpiek op te vangen. 
    for kwartier in verbruik: 
        a = 0


def instellingen_accu(peak_shave="uit", pv_zelf_consumption="uit", state_of_charge="uit", var_tarieven="uit", grenswaarde_ontladen=50, accu_capaciteit=100, max_laden_uit_net=0):
    """
    Hulpfunctie accu module om te bepalen hoe de accu zich gedraagt over de dag.
    """
    if max_laden_uit_net == 0:
        max_laden_uit_net = False
    if peak_shave == "aan":
        peak_shaven = grenswaarde_ontladen

def peak_shave(grenswaarde_ontladen:int, grenswaarde_opladen:int):
        """We gaan het zo aanpakken, we checken eerst of peak shaven aan staat, deze bepaalt het minimale vermogen wat in de accu mag zitten. Pv-zelfconsumptie betekent gewoon dat ze niet terugleveren en gewoon overschotten opsparen en later gebruiken. 
        State of charge betekent dat we 's nachts de stand van de accu checken en opladen tot een bepaald punt (bijv. 6 uur 's ochtends) om de ochtendpiek op te vangen, deze is relatief duur. Combineren kan door eerst peak shaven te doen, daarna pv zelfconsumptie en dan state of charge. 
        State of charge zit pv_zelfconsumptie ook niet echt in de weg."""
        accu_stand = 0
        afnamelimiet = 5
        verbruik = 10
        opbrengst = 0
        if accu_stand < grenswaarde_ontladen:
            # Accu opladen tot grenswaarde
            max_laden = afnamelimiet-(verbruik-opbrengst)
            if max_laden > 0:
                laden = min(max_laden, grenswaarde_opladen)
            else: 
                laden = 0
            accu_stand = accu_stand + laden
        elif accu_stand > grenswaarde_ontladen:
            # Accu ontladen bij verbruik boven grenswaarde
            
            accu_stand = accu_stand - (verbruik-opbrengst)