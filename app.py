import streamlit as st
import pandas as pd
from plot_manager import PlotManager
from plot_weektrends import plot_weektrends, plot_weektrends_summary, plot_weektrends_per_quartile_stats, plot_accu_week_simulatie, plot_accu_week_simulatie_select
from pvlib_init import Initialize_Systeem1, Initialize_Systeem2, get_parameters
from ml_clustering import cluster_typical_profiles
import time 
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import io 
import os 
import gc
from functools import lru_cache
#from dotenv import load_dotenv

st.set_page_config(page_title="Energie Analyse (Nieuw)", layout="wide")
import psutil, tracemalloc
proc = psutil.Process(os.getpid())

if "trace_on" not in st.session_state:
    tracemalloc.start()
    st.session_state.trace_on = True

cur, peak = tracemalloc.get_traced_memory()
st.sidebar.write(f"RAM process: {proc.memory_info().rss/1e6:.1f} MB")
st.sidebar.write(f"tracemalloc current/peak: {cur/1e6:.1f} / {peak/1e6:.1f} MB")

LIGHT_RSS_MB = 900  # Adjust based on observed "light" memory usage in MB

def rss_mb():
    return psutil.Process(os.getpid()).memory_info().rss / 1e6

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


from pathlib import Path

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "LO-Bind-FC-RGB.png"

@st.cache_data(show_spinner=False)
def load_logo_bytes(path: str | Path) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None

logo_bytes = load_logo_bytes(LOGO_PATH)
if logo_bytes:
    st.image(logo_bytes, width=140)
else:
    st.caption("Logo niet gevonden (LO-Bind-FC-RGB.png).")


PV_MODULETYPES = {
    "Topsun_TS_S400SA1": 400,
    "Heliene_96M400": 400,
    "LG_Electronics_Inc__LG400N2W_V5": 400,
    "Grape_Solar_GS_S_420_KR3": 420,
    "Sunpreme_Inc__SNPM_HxB_420": 420,
    "Topsun_TS_M420JA1": 420,
    "SunPower_SPR_E20_440_COM": 440,
    "Solaria_Corporation_Solaria_PowerXT_440C_PD": 440,
    "Heliene_96P440": 440,
    "ENN_Solar_Energy_EST_460": 460,
    "Sunpower_SPR_X21_460_COM": 460,
    "SunPower_SPR_X22_475_COM": 475,
    "Sunpower_SPR_X22_480_COM": 480,
    "Miasole_FLEX_03_480W": 480,
    "First_Solar__Inc__FS_497": 497,
    "Miasole_FLEX_03_500W": 500,
    "Sunpreme_Inc__SNPM_GxB_500": 500
}


st.markdown("""
<style>
    .main-title {font-size:2.5rem;font-weight:700;margin-bottom:0.5em;}
    .section-header {font-size:1.3rem;font-weight:600;margin-top:2em;margin-bottom:0.5em;}
    .stButton>button {width: 100%; font-size: 1.1rem;}
    .stDataFrame {margin-bottom: 1em;}
    .block-container {padding-top: 2rem;}
    .stSidebar {background-color: #f8f9fa;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🔋 Energie Analyse Dashboard</div>', unsafe_allow_html=True)
st.markdown("""
<div style="margin-bottom: 1em;">
    <b>Upload, analyseer, visualiseer en download je kwartierdata-resultaten.</b>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Instellingen")
    if st.button("Verwijder cache geheugen", key="reset_settings"):
        st.cache_data.clear()
        st.success("Cache geheugen is gewist. Herlaad de pagina om opnieuw te beginnen.")
    max_afname = st.number_input("Max afname (kW) (positief getal)", min_value=0.0, value=10.0)
    max_teruglevering = st.number_input("Max teruglevering (kW)(positief getal)", min_value=0.0, value=10.0)
    vermogen_omvormer = st.number_input("Vermogen omvormer (kW)", min_value=0.0, value=2.0)
    type_omvormer = "Enphase" #st.selectbox("Type omvormer", options=["Enphase", "SolarEdge", "Fronius"], index=0)
    type_paneel = st.selectbox("Type paneel", options=PV_MODULETYPES, index=0)
    #vermogen_paneel = st.selectbox("Vermogen paneel (Wp)", options=[300, 350, 400, 450, 500], index=3)
    
    
    aantal_jaar = st.number_input("Aantal jaren voor voorspelling", min_value=1, max_value=2, value=1)
    
    begin_datum = st.date_input("Startdatum", value=pd.to_datetime('2023-01-01'))
    
    zonnedata_pos_neg = st.selectbox("Zonnedata positief of negatief", options=["positief", "negatief"], index=0)
    weer_scenario = "goed weer" #st.selectbox("Weer scenario", options=["goed_weer", "slecht_weer", "bewolkt", "wisselvallig"], index=0)
    st.title("Paneel orientatie 1")
    orientatie1 = st.number_input("Orientatie kant 1, zuid=0, west=90, noord=180, oost=270 etc.", min_value=0, max_value=360, value=90, step=1)
    Hellingshoek1 = st.selectbox("Hellingshoek 1", options=[0, 15, 45, 90], index=2, label_visibility="collapsed")
    Panelen_per_reeks1 = st.number_input("Panelen per reeks", min_value=1, value=1)
    Reeksen1 = st.number_input("Aantal reeksen", min_value=1, value=1)
    Reeksen_per_omvormer1 = st.number_input("Reeksen per omvormer", min_value=1, value=1)
    #WP1 = st.number_input("Watt Pieks 1", min_value=100, value=450)
    st.title("Paneel orientatie 2")
    orientatie2 = st.number_input("Orientatie kant 2, zuid=0, west=90, noord=180, oost=270 etc.", min_value=0, max_value=360, value=90, step=1)
    Hellingshoek2 = st.selectbox("Hellingshoek 2", options=[0, 15, 45, 90], index=3, label_visibility="collapsed")
    Panelen_per_reeks2 = st.number_input("Panelen per reeks", min_value=0, value=0)
    Reeksen2 = st.number_input("Aantal reeksen", min_value=0, value=0)
    Reeksen_per_omvormer2 = st.number_input("Reeksen per omvormer", min_value=0, value=1)
    #WP2 = st.number_input("Watt Pieks 2", value=0)
    st.title("Locatie")
    breedtegraad = st.number_input("Breedtegraad", value=52.13)
    lengtegraad = st.number_input("Lengtegraad", value=6.54)   
st.markdown('<div class="section-header">1. Upload je kwartierdata</div>', unsafe_allow_html=True)

uploaded_verbruik = st.file_uploader("Upload verbruik kwartierdata (excel, index=datetime)", type=["xlsx"], key="verbruik")

data_type = st.selectbox("Type opbrengst data", options=["Aanleveren", "Berekenen"], index=0)
if data_type == "Berekenen":
    uploaded_opbrengst = "Processor"
else:
    uploaded_opbrengst = st.file_uploader("Upload opbrengst kwartierdata (excel, index=datetime)", type=["xlsx"], key="opbrengst")

df_verbruik = None
df_opbrengst = None

def dedup_quarterly_series(s: pd.Series, how: str = "mean") -> pd.Series:
    # 1) datetime-index maken en NaT weg
    idx = pd.to_datetime(s.index, errors="coerce")
    s = pd.Series(pd.to_numeric(s.values, errors="coerce"), index=idx, name=s.name)
    s = s[~s.index.isna()]
    # 2) op exact 15-minuten bakken
    s.index = s.index.floor("15min")
    # 3) dubbelen samenvoegen (DST/dubbele rijen)
    if how == "sum":
        s = s.groupby(s.index).sum()
    else:
        s = s.groupby(s.index).mean()
    return s.sort_index().astype("float32")

def align_to_common_15min_grid(v: pd.Series, o: pd.Series) -> tuple[pd.Series, pd.Series]:
    v = dedup_quarterly_series(v, how="mean")  # verbruik evt. "sum" als je dat beter vindt
    o = dedup_quarterly_series(o, how="mean")
    # gemeenschappelijke periode
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


if uploaded_verbruik and uploaded_opbrengst:
    if uploaded_opbrengst == "Processor":
        start = time.time()
        with st.spinner("Berekenen kwartierdata..."):
            plt.clf()
            location, module, inverter, temperature_parameters = get_parameters(_breedtegraad=breedtegraad, _lengtegraad=lengtegraad, _tijdzone="Europe/Amsterdam", _hoogte=42, _type_paneel=type_paneel)
            
            df_opbrengst1 = Initialize_Systeem1(
                _location=location, 
                _module=module, 
                _inverter=inverter, 
                _temperature_parameters=temperature_parameters, 
                _hellingshoek=Hellingshoek1, 
                _azimuth=orientatie1, 
                _panelen_per_reeks=Panelen_per_reeks1, 
                _reeksen_per_omvormer=Reeksen_per_omvormer1, 
                _start_date=begin_datum, 
                _end_date=begin_datum + pd.DateOffset(years=1))
            
            
            
            df_opbrengst2 = Initialize_Systeem2(
                _location = location, 
                _module = module, 
                _inverter = inverter, 
                _temperature_parameters = temperature_parameters, 
                _hellingshoek=Hellingshoek2, 
                _azimuth=orientatie2, 
                _panelen_per_reeks=Panelen_per_reeks2, 
                _reeksen_per_omvormer=Reeksen_per_omvormer2, 
                _start_date=begin_datum, 
                _end_date=begin_datum + pd.DateOffset(years=1))
            
            #st.write(df_opbrengst2.results.ac.head())
            df_opbrengst = df_opbrengst1.results.ac*Reeksen1 + df_opbrengst2.results.ac*Reeksen2
            
            #st.write(df_opbrengst.head())
            #plt.clf()
            #df_opbrengst.plot(figsize=(16, 9), title='AC Power Output')

            st.write(f"opbrengst over een jaar totaal: {df_opbrengst.sum()/4} kWh, zijde 1: {df_opbrengst1.results.ac.sum()/4*Reeksen1} kWh, zijde 2: {df_opbrengst2.results.ac.sum()/4*Reeksen2} kWh")
            
            #st.pyplot(plt.gcf())  # Show the plot in Streamlit
            
        st.write("Duur:", time.time() - start)
    else: 
        df_opbrengst = read_excel_smart(uploaded_opbrengst, index_col=0, parse_dates=True)
    df_verbruik = read_excel_smart(uploaded_verbruik, index_col=0, parse_dates=True)
    
    st.success("✅ Data succesvol geladen!")
    light_mode = rss_mb() > LIGHT_RSS_MB
    n_show = 500 if light_mode else 1500
    st.caption("Voorbeeld verbruik")
    st.dataframe(df_verbruik.head(n_show), use_container_width=True)
    st.caption("Voorbeeld opbrengst")
    st.dataframe(df_opbrengst.head(n_show), use_container_width=True)

    st.markdown('<div class="section-header">2. Selecteer kolommen verbruik en opbrengst</div>', unsafe_allow_html=True)

    N = 35040  # max 1 jaar kwartierdata

    # --- Verbruik ---
    col_verbruik = st.text_input("Kolom verbruiksdata:", value="Verbruik")
    s_v = pd.to_numeric(df_verbruik[col_verbruik].iloc[:N], errors="coerce").astype("float32") * 4.0  # behoud jouw *4

    # --- Opbrengst ---
    if data_type == "Berekenen":  # df_opbrengst komt uit je PV-processor
        if isinstance(df_opbrengst, pd.DataFrame):
            raw_o = df_opbrengst.iloc[:, 0]
        else:
            raw_o = df_opbrengst
        s_o = pd.to_numeric(raw_o.iloc[:N], errors="coerce").astype("float32")
    else:  # upload
        default_col = df_opbrengst.columns[0] if isinstance(df_opbrengst, pd.DataFrame) else None
        col_opbrengst = st.text_input("Kolom opbrengstdata:", value=default_col or "Opbrengst")
        if isinstance(df_opbrengst, pd.DataFrame):
            raw_o = df_opbrengst[col_opbrengst]
        else:
            raw_o = df_opbrengst
        s_o = pd.to_numeric(raw_o.iloc[:N], errors="coerce").astype("float32")

    # --- Uitlijnen op 15-min grid zonder tijdzones ---
    data_verbruik, data_opbrengst = align_to_common_15min_grid(s_v, s_o)

    # RAM-vriendelijke preview
    st.caption("Voorbeeld verbruik (eerste 500 rijen)")
    st.dataframe(data_verbruik.head(500).to_frame(name=col_verbruik), use_container_width=True)
    st.caption("Voorbeeld opbrengst (eerste 500 rijen)")
    st.dataframe(data_opbrengst.head(500).to_frame(name="Opbrengst"), use_container_width=True)

    st.markdown('<div class="section-header">3. Analyse & Visualisatie</div>', unsafe_allow_html=True)

    plotter = PlotManager()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Belastingduurkromme", 
        "Energiebalans dag", 
        "Dagbalans jaar", 
        "Opbrengst vs Verbruik",
        "Max kwartierverbruik heatmap",
        "Weekoverzicht",
        "Accu module"
    ])

    with tab1:
        st.markdown("#### Belastingduurkromme (op basis van verbruik)")
        plotter.plot_belastingduurkromme(data_verbruik)
       
    with tab2:
        st.markdown("#### Energiebalans op een dag")
        dag = st.date_input("Kies een dag", value=data_verbruik.index[0].date())
        st.write(f"🔍 Gekozen dag: {dag}")

        # Zet 'dag' om naar pd.Timestamp (essentieel)
        dag = pd.to_datetime(dag)

        # Mask aanmaken
        mask_v = data_verbruik.index.normalize() == dag
        mask_o = data_opbrengst.index.normalize() == dag
        
        # Filter de Series
        verbruik_op_dag = data_verbruik[mask_v]
        opbrengst_op_dag = data_opbrengst[mask_o]
        
        toon_verbruik = st.checkbox("Toon verbruik", value=True, key="dag_verbruik")
        toon_opbrengst = st.checkbox("Toon opbrengst", value=True, key="dag_opbrengst")
        toon_saldo = st.checkbox("Toon saldo", value=False, key="dag_saldo")
        toon_saldo_beperkt = st.checkbox("Toon saldo (beperkt)", value=True, key="dag_saldo_beperkt")
        toon_limieten = st.checkbox("Toon limieten", value=True, key="dag_limieten")
        toon_limiet_overschrijdingen = st.checkbox("Toon limiet overschrijdingen", value=False, key="dag_limiet_overschrijdingen")


        if mask_v.sum() > 0 and mask_o.sum() > 0:
            plotter.plot_energiebalans_dag(data_verbruik[mask_v], data_opbrengst[mask_o], max_afname, max_teruglevering, _positief=zonnedata_pos_neg, _toon_verbruik=toon_verbruik, _toon_opbrengst=toon_opbrengst, _toon_saldo=toon_saldo, _toon_saldo_beperkt=toon_saldo_beperkt, _toon_limieten=toon_limieten, _toon_limiet_overschrijdingen=toon_limiet_overschrijdingen)
        else:
            st.info("Geen data voor deze dag.")

        clusters = st.number_input("Aantal clusters voor verbruiksprofielen", min_value=2, max_value=10, value=4, key="aantal_clusters")
        cluster_typical_profiles(data_verbruik, n_clusters=clusters, use_weekend=True)

    with tab3:
        st.markdown("#### Dagbalans over gehele periode")
        def plot_dagtotalen_en_verschil(verbruik: pd.Series, opbrengst: pd.Series):
            """
            Plot per dag de som van verbruik, opbrengst en het verschil (opbrengst - verbruik).
            """
            # Zorg dat indexen datetime zijn
            verbruik = verbruik.copy()
            opbrengst = opbrengst.copy()
            verbruik.index = pd.to_datetime(verbruik.index)
            opbrengst.index = pd.to_datetime(opbrengst.index)
            # Resample per dag
            verbruik_per_dag = verbruik.resample('D').sum()
            opbrengst_per_dag = opbrengst.resample('D').sum()
            verschil_per_dag = -opbrengst_per_dag + verbruik_per_dag
            totaal_verbruik = verbruik_per_dag.sum()*0.25
            totaal_opbrengst = opbrengst_per_dag.sum()*0.25
            st.markdown(f"""
            <p style="font-size:18px;">
            <h1>Totaal verbruik: {totaal_verbruik:.2f} kWh</h1>
            <h1>Totaal opbrengst: {totaal_opbrengst:.2f} kWh</h1>
            <h1>Verschil (verbruik - opbrengst): {-totaal_opbrengst + totaal_verbruik:.2f} kWh</h1>
            </p>""", unsafe_allow_html=True)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(verbruik_per_dag.index, verbruik_per_dag, label="Verbruik per dag", color="red")
            ax.plot(opbrengst_per_dag.index, -opbrengst_per_dag, label="Opbrengst per dag", color="green")
            ax.plot(verschil_per_dag.index, verschil_per_dag, label="Verschil (opbrengst - verbruik)", color="blue")
            ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
            ax.set_xlabel("Datum")
            ax.set_ylabel("Energie (som per dag)")
            ax.set_title("Dagtotalen verbruik, opbrengst en verschil")

            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig); gc.collect()

        plot_dagtotalen_en_verschil(data_verbruik, data_opbrengst)

    with tab4:
        st.markdown("#### Opbrengst vs Verbruik (kies kolommen)")
        #kolom_v = st.selectbox("Kies verbruikskolom", df_verbruik.columns)
        #kolom_o = st.selectbox("Kies opbrengstkolom", df_opbrengst.columns)
        show_opbrengst = st.checkbox("Toon opbrengst", value=True, key="reeksen_opbrengst")
        show_verbruik = st.checkbox("Toon verbruik", value=True, key="reeksen_verbruik")
        show_verschil = st.checkbox("Toon verschil", value=True, key="reeksen_verschil")
        plotter.plot_reeksen_en_verschil(_verbruik=data_verbruik, _opbrengst=data_opbrengst, show_opbrengst=show_opbrengst, show_verbruik=show_verbruik, show_verschil=show_verschil, _max_afname=max_afname, _max_teruglevering=max_teruglevering)

    with tab5:
        st.markdown("#### Heatmap: Max kwartierverbruik per dag (% van limiet)")
        def plot_max_dagpiek_heatmap(verbruik: pd.Series, opbrengst: pd.Series, max_afname: float):
            verbruik = verbruik.astype("float32")
            opbrengst = opbrengst.astype("float32")
            min_len = min(len(verbruik), len(opbrengst))
            verbruik = verbruik.iloc[:min_len]
            opbrengst = opbrengst.iloc[:min_len]

            verschil = (verbruik - opbrengst)
            piek_per_dag = verschil.resample("D").max()
            perc_per_dag = (piek_per_dag / max_afname) * 100.0

            df = pd.DataFrame({"perc": perc_per_dag})
            df["day"] = df.index.day
            df["month"] = df.index.month
            pivot = df.pivot_table(index="month", columns="day", values="perc", aggfunc="mean")

            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=100)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels([pd.Timestamp(year=2000, month=m, day=1).strftime("%B") for m in pivot.index])
            ax.set_xticks(range(pivot.shape[1]))
            ax.set_xticklabels(pivot.columns)
            ax.set_xlabel("Day of month")
            ax.set_ylabel("Month")
            ax.set_title("Max kwartierverbruik per dag (% van max afname)")
            fig.colorbar(im, ax=ax, label="% van limiet")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig); gc.collect()

            overschrijdingen = (piek_per_dag > max_afname).sum()
            totaal_dagen = piek_per_dag.shape[0]
            st.write(
                f"📅 Hoogste piek: {perc_per_dag.idxmax().date()} – {perc_per_dag.max():.1f}% "
                f"| 🚨 Overschrijdingen: {overschrijdingen}/{totaal_dagen} ({overschrijdingen/totaal_dagen:.1%})"
            )


        plot_max_dagpiek_heatmap(data_verbruik, data_opbrengst, max_afname)

    with tab6:
        st.markdown("#### Weekoverzicht")
        plot_weektrends(data_verbruik, title="Weektrends verbruik kwartierdata")
        
        plot_weektrends_summary(data_verbruik, title="Gemiddelde, max en min week verbruik (kwartierdata)")
        plot_weektrends_per_quartile_stats(data_verbruik, title="Gemiddelde, max en min per kwartier van de week")

    with tab7:
        st.markdown("#### Accu module")
        with st.expander("Toelichting accu module"): 
            capaciteit = st.number_input("Accu capaciteit (kWh)", min_value=1.0, value=10.0)
            
            peak_shaven = st.checkbox("Peak shaven? (accu gebruiken om pieken te dempen)", value=True, key="peak_shaven")
            pv_zelf_consumptie = st.checkbox("PV zelf consumptie? (accu gebruiken om pv opbrengst op te slaan en 's nachts te ontladen)", value=True, key="pv_zelf_consumptie")
            state_of_charge = st.checkbox("State of Charge gebruiken? (Gebruik state of charge om 's nachts te laden uit net om ochtendpiek op te vangen)", value=False, key="state_of_charge")
            var_tarieven = st.checkbox("Variabele tarieven? (Gebruik variabele tarieven om accu te laden als stroom goedkoop is)", value=False, key="var_tarieven")
            if state_of_charge is True:
                st.slider("Minimale state of charge (%)", min_value=0, max_value=100, value=40, key="min_soc")
                st.number_input("Maximale laadsnelheid (kW)", min_value=0.0, value=2.0, key="max_charge_rate")
            if st.button("📈 Simuleer accu (week)"):
                plot_accu_week_simulatie(...)
                plot_accu_week_simulatie_select(...)
        
        

    df_out = pd.DataFrame({"Verbruik (kW)": data_verbruik, "Opbrengst (kW)": data_opbrengst})
    csv_bytes = df_out.to_csv(index=True).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv_bytes, file_name="kwartierdata_resultaten.csv", mime="text/csv")

    # Alleen als je per se Excel wilt:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_out.to_excel(writer, sheet_name="Resultaten")
    excel_bytes = output.getvalue()
    st.download_button("📥 Download Excel", data=excel_bytes,
                    file_name="kwartierdata_resultaten.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    del df_out, csv_bytes, excel_bytes, output
    gc.collect()


else:
    st.warning("Upload zowel verbruik als opbrengst kwartierdata-bestanden om te starten.")

st.markdown("---")
st.info("Gebruik de tabs om verschillende analyses en visualisaties te bekijken.")