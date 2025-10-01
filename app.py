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
import ctypes
from functools import lru_cache
import numpy as np
from pathlib import Path
import seaborn as sns
from plots import plot_dag_en_maand, plot_max_dagpiek_heatmap
from utils import read_excel_smart, align_to_common_15min_grid, angle_picker, tilt_picker, PV_MODULETYPES

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
    
    def hard_cleanup(preserve_keys=("trace_on",)):
        # 1) Session state leegmaken (maar behoud wat nodig is)
        for k in list(st.session_state.keys()):
            if k not in preserve_keys:
                del st.session_state[k]

        # 2) Matplotlib volledig sluiten en caches legen
        try:
            plt.close('all')
            from matplotlib import font_manager as fm
            fm._rebuild()  # kleine cache reset
        except Exception:
            pass

        # 3) Streamlit caches legen
        st.cache_data.clear()
        st.cache_resource.clear()

        # 4) Lokale grote variabelen/globals opruimen
        g = globals()
        for name in list(g.keys()):
            if name.startswith(("df_", "data_", "s_", "fig", "ax", "output", "excel_bytes", "csv_bytes")):
                g.pop(name, None)

        # 5) GC + heap trim (geeft RAM terug aan OS op Linux)
        gc.collect()
        try:
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception:
            pass

    with st.sidebar:
        if st.button("🧹 Hard cleanup (RAM vrijmaken)"):
            hard_cleanup()
            st.success("Geheugen opgeschoond.")
            st.experimental_rerun()

    max_afname = st.number_input("Max afname (kW) (positief getal)", min_value=0.0, value=70.0)
    max_teruglevering = st.number_input("Max teruglevering (kW)(positief getal)", min_value=0.0, value=20.0)
    vermogen_omvormer = st.number_input("Vermogen omvormer (kW)", min_value=0.0, value=2.0)
    type_omvormer = "Enphase" #st.selectbox("Type omvormer", options=["Enphase", "SolarEdge", "Fronius"], index=0)
    type_paneel = st.selectbox("Vermogen paneel", options=[400, 420, 440, 460, 475, 480, 500], index=0)
    #vermogen_paneel = st.selectbox("Vermogen paneel (Wp)", options=[300, 350, 400, 450, 500], index=3)
    
    
    aantal_jaar = 1 #st.number_input("Aantal jaren voor voorspelling", min_value=1, max_value=2, value=1)
    
    begin_datum = st.date_input("Startdatum", value=pd.to_datetime('2023-01-01'))
    
    zonnedata_pos_neg = "positief"
    weer_scenario = "goed weer" #st.selectbox("Weer scenario", options=["goed_weer", "slecht_weer", "bewolkt", "wisselvallig"], index=0)
    st.title("Paneel orientatie 1")
    orientatie1 = angle_picker("Oriëntatie (°)", default=90, key="ori1") - 180
    Hellingshoek1 = tilt_picker("Hellingshoek 1 (°)", key="tilt1")
    Panelen_per_reeks1 = st.number_input("Panelen per reeks", min_value=1, value=1)
    Reeksen1 = st.number_input("Aantal reeksen", min_value=1, value=1)
    Reeksen_per_omvormer1 = st.number_input("Reeksen per omvormer", min_value=1, value=1)
    #WP1 = st.number_input("Watt Pieks 1", min_value=100, value=450)
    st.title("Paneel orientatie 2")
    orientatie2 = angle_picker("Oriëntatie (°)", default=270, key="ori2") - 180
    Hellingshoek2 = tilt_picker("Hellingshoek 2 (°)", default=13, key="tilt2")
    Panelen_per_reeks2 = st.number_input("Panelen per reeks", min_value=0, value=0)
    Reeksen2 = st.number_input("Aantal reeksen", min_value=0, value=0)
    Reeksen_per_omvormer2 = st.number_input("Reeksen per omvormer", min_value=0, value=1)
    #WP2 = st.number_input("Watt Pieks 2", value=0)
    st.title("Locatie")
    breedtegraad = st.number_input("Breedtegraad", value=52.13)
    lengtegraad = st.number_input("Lengtegraad", value=6.54)
    POWER_TO_TYPES = {}
    for module, vermogen in PV_MODULETYPES.items():
        POWER_TO_TYPES.setdefault(vermogen, []).append(module) 
    type_paneel =POWER_TO_TYPES[type_paneel]  
st.markdown('<div class="section-header">1. Upload je kwartierdata</div>', unsafe_allow_html=True)

uploaded_verbruik = st.file_uploader("Upload verbruik kwartierdata (excel, index=datetime)", type=["xlsx"], key="verbruik")
data_type = st.selectbox("Type opbrengst data", options=["Aanleveren", "Berekenen"], index=0)
if data_type == "Berekenen":
    uploaded_opbrengst = "Processor"
else:
    uploaded_opbrengst = st.file_uploader("Upload opbrengst kwartierdata (excel, index=datetime)", type=["xlsx"], key="opbrengst")

df_verbruik = None
df_opbrengst = None

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
                _end_date=begin_datum + pd.DateOffset(years=1)) * 0.65
           
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
                _end_date=begin_datum + pd.DateOffset(years=1)) * 0.65
            
            df_opbrengst = (df_opbrengst1*Reeksen1 + df_opbrengst2*Reeksen2) 

            st.write(f"opbrengst over een jaar totaal: {df_opbrengst.sum()/4} kWh, zijde 1: {df_opbrengst1.sum()/4*Reeksen1} kWh, zijde 2: {df_opbrengst2.sum()/4*Reeksen2} kWh")
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

    col_verbruik = st.text_input("Kolom verbruiksdata:", value="Verbruik")
    if data_type == "Berekenen":
        default_col = None
    else:
        default_col = df_opbrengst.columns[0] if isinstance(df_opbrengst, pd.DataFrame) else None
    col_opbrengst = st.text_input("Kolom opbrengstdata:", value=default_col or "Opbrengst")

    # Begin direct met verwerken en visualiseren, geen button meer
    N = 35040  # max 1 jaar kwartierdata

    # --- Verbruik ---
    s_v = pd.to_numeric(df_verbruik[col_verbruik].iloc[:N], errors="coerce").astype("float32") * 4.0

    # --- Opbrengst ---
    if data_type == "Berekenen":
        if isinstance(df_opbrengst, pd.DataFrame):
            raw_o = df_opbrengst.iloc[:, 0]
        else:
            raw_o = df_opbrengst
        s_o = pd.to_numeric(raw_o.iloc[:N], errors="coerce").astype("float32")
    else:
        if isinstance(df_opbrengst, pd.DataFrame):
            raw_o = df_opbrengst[col_opbrengst]
        else:
            raw_o = df_opbrengst
        s_o = pd.to_numeric(raw_o.iloc[:N], errors="coerce").astype("float32")

    data_verbruik, data_opbrengst = align_to_common_15min_grid(s_v, s_o)

    st.caption("Voorbeeld verbruik (eerste 500 rijen)")
    st.dataframe(data_verbruik.head(500).to_frame(name=col_verbruik), use_container_width=True)
    st.caption("Voorbeeld opbrengst (eerste 500 rijen)")
    st.dataframe(data_opbrengst.head(500).to_frame(name="Opbrengst"), use_container_width=True)

    st.markdown('<div class="section-header">3. Analyse & Visualisatie</div>', unsafe_allow_html=True)

    plotter = PlotManager()

    # Nieuwe tabvolgorde
    tab3, tab6, tab7, tab4, tab5, tab2, tab1 = st.tabs([
        "Dagbalans jaar",        # 1
        "Weekoverzicht",         # 2
        "Typische Dagprofielen", # 3
        "Heatmap",               # 4
        "Energiebalans dag",     # 5
        "Opbrengst vs Verbruik", # 6
        "Belastingduurkromme",   # 7
    ])

    # 1. Dagbalans jaar
    with tab3:
        st.markdown("#### Dagbalans over gehele periode")

        

        # AANROEP
        plot_dag_en_maand(data_verbruik, data_opbrengst)
        st.markdown("""
        **Toelichting:**
        - Daglijnen: verbruik (boven 0), opbrengst (onder 0) en verschil (verbruik - opbrengst)
        - Maandstaven: verbruik, opbrengst en overschot (alleen positieve delen van opbrengst - verbruik per kwartier)
        - Alle waarden in kWh (kwartierdata in kW * 0,25)
        """)

    # 2. Weekoverzicht
    with tab6:
        st.markdown("#### Weekoverzicht")
        plot_weektrends(data_verbruik, title="Weektrends verbruik kwartierdata")
        
        plot_weektrends_summary(data_verbruik, title="Gemiddelde, max en min week verbruik (kwartierdata)")
        plot_weektrends_per_quartile_stats(data_verbruik, title="Gemiddelde, max en min per kwartier van de week")

    # 3. Typische Dagprofielen
    with tab7:
        st.markdown("#### Typische Dagprofielen")
        clusters = st.number_input("Aantal clusters voor verbruiksprofielen", min_value=2, max_value=10, value=4, key="aantal_clusters_typische_dag")
        cluster_typical_profiles(data_verbruik, n_clusters=clusters, use_weekend=True)

    # 4. Heatmap
    with tab4:
        st.markdown("#### Heatmap: Max kwartierverbruik per dag (% van limiet)")
        grootste_overschrijding_dag = None
        

        grootste_overschrijding_dag = plot_max_dagpiek_heatmap(data_verbruik, data_opbrengst, max_afname)

    # 5. Energiebalans dag
    with tab5:
        st.markdown("#### Energiebalans op een dag")
        # Gebruik de dag met grootste overschrijding als default
        default_dag = grootste_overschrijding_dag if grootste_overschrijding_dag is not None else data_verbruik.index[0].date()
        dag = st.date_input("Kies een dag", value=default_dag)
        st.write(f"🔍 Gekozen dag: {dag}")

        dag = pd.to_datetime(dag)
        mask_v = data_verbruik.index.normalize() == dag
        mask_o = data_opbrengst.index.normalize() == dag
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

    # 6. Opbrengst vs Verbruik
    with tab2:
        st.markdown("#### Opbrengst vs Verbruik (kies kolommen)")
        show_opbrengst = st.checkbox("Toon opbrengst", value=True, key="reeksen_opbrengst")
        show_verbruik = st.checkbox("Toon verbruik", value=True, key="reeksen_verbruik")
        show_verschil = st.checkbox("Toon verschil", value=True, key="reeksen_verschil")
        plotter.plot_reeksen_en_verschil(_verbruik=data_verbruik, _opbrengst=data_opbrengst, show_opbrengst=show_opbrengst, show_verbruik=show_verbruik, show_verschil=show_verschil, _max_afname=max_afname, _max_teruglevering=max_teruglevering)

    # 7. Belastingduurkromme
    with tab1:
        st.markdown("#### Belastingduurkromme (op basis van verbruik)")
        plotter.plot_belastingduurkromme(data_verbruik)
        

    try:
        df_out = pd.DataFrame({"Verbruik (kWh)": data_verbruik/4, "Opbrengst (kWh)": data_opbrengst/4})
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
    except Exception as e:
        st.error(f"Fout bij aanmaken downloadbestanden: {e}")
    del df_out, csv_bytes, excel_bytes, output
    gc.collect()


else:
    st.warning("Upload zowel verbruik als opbrengst kwartierdata-bestanden om te starten.")

st.markdown("---")
st.info("Gebruik de tabs om verschillende analyses en visualisaties te bekijken.")