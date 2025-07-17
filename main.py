import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for matplotlib
import matplotlib.pyplot as plt
from kwartierdata_processor import KwartierdataProcessor, plot_opbrengst_per_dag, plot_opbrengst_jaar, normaliseer_data, read_data, kwartierdata_naar_dagdata, maak_heatmap_verbruik, plot_opbrengst_dag
from belastingduurkromme import plot_belastingduurkromme
from zonnepanelen_scenarios import get_zonnepanelen_scenario_profiel
from energiebalans_plotter import plot_dagbalans_jaar, plot_reeksen_en_verschil

st.set_page_config(page_title="Energie Analyse", layout="wide")

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
    <b>Analyseer, visualiseer en download je kwartierdata-resultaten eenvoudig.</b>
</div>
""", unsafe_allow_html=True)

def show_home():
    st.title("Welkom bij het Zonne-energie Dashboard")
    st.write("Dit dashboard helpt je bij het analyseren van zonne-energie data en het maken van voorspellingen.")
    st.write("Gebruik de navigatie aan de zijkant om door de verschillende pagina's te bladeren.")
    st.write("uitleg van het dashboard & mogelijke errors")

def Data_analyse_bestaande_data():
    st.title("Data Analyse Bestaande Data")
    st.write("Upload je zonne-energie data in CSV of Excel formaat om deze te analyseren.")
    st.write("Zorg ervoor dat de data een tijdstempel bevat en de opbrengst per kwartier is vastgelegd.")
    if uploaded_file := st.file_uploader("Upload je data van het verbruik", type=["xlsx", "csv"]):
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

    if uploaded_file := st.file_uploader("Upload je data van de opbrengst", type=["xlsx", "csv"]):
        if uploaded_file.name.endswith('.xlsx'):
            opbrengst_df = pd.read_excel(uploaded_file)
        else:
            opbrengst_df = pd.read_csv(uploaded_file)
    
    st.write("Data preview:")
    st.dataframe(df.head())
    st.dataframe(opbrengst_df.head())
    verbruik_data = st.text_input("Kolom verbruiksdata:")
    oprbrengst_data = st.text_input("Kolom opbrengstdata:")
    st.write("Data informatie:")
    
    if verbruik_data is not None and oprbrengst_data is not None:
        data_verbruik = df[verbruik_data] # Selecteer de opgegeven kolom
        data_opbrengst = df[oprbrengst_data]
        st.markdown("### 📊 Dagelijkse energiebalans over het jaar")
        

        st.markdown("### 📈 Dagprofielen (per dag)")
        
        plot_reeksen_en_verschil(data_opbrengst,data_verbruik)

def show_voorspelling_en_analyse():
    st.title("Voorspelling en Analyse")
    st.write("Hier kun je voorspellingen maken op basis van de geüploade data.")
    st.write("Gebruik de knoppen aan de zijkant om door de verschillende analyses te navigeren.")
    st.write("Hier komt de voorspelling en analyse pagina")
    st.header("Kies de algemene eigenschappen van de installatie:")
    aantal_jaar = st.number_input("Aantal jaren voor voorspelling", min_value=1, max_value=2, value=1)
    breedtegraad = st.number_input("Breedtegraad", value=52.13)
    lengtegraad = st.number_input("Lengtegraad", value=6.54)   
    begin_datum = st.date_input("Startdatum", value=pd.to_datetime('2023-01-01'))
    plot_dag = st.date_input("Plot dag", value=pd.to_datetime('2023-06-01'))
    afnamelimiet = st.number_input("Afname limiet (kWh)", min_value=0, value=0)
    terugleverlimiet = st.number_input("Teruglever limiet (kWh)", min_value=0, value=0)
    
    zonnedata_pos_neg = st.selectbox("Zonnedata positief of negatief", options=["positief", "negatief"], index=0)
    weer_scenario = st.selectbox("Weer scenario", options=["goed_weer", "slecht_weer", "bewolkt", "wisselvallig"], index=0)
    rendement = st.slider("Rendement (%)", min_value=0, max_value=100, value=95)
    st.write("Kies de oriëntaties en hellingshoeken van de zonnepanelen:")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Paneel orientatie 1")
        orientatie1 = st.selectbox("Orientaties", options=["oost", "west", 'zuid', "noord", "zuidoost", "zuidwest", "noordoost", "noordwest"], index=0, label_visibility="collapsed")
        Hellingshoek1 = st.selectbox("Hellingshoek 1", options=[0, 15, 45, 90], index=2, label_visibility="collapsed")
        WP1 = st.number_input("Watt Pieks 1", min_value=100, value=450)

    with col2:
        st.write("Paneel orientatie 2")
        orientatie2 = st.selectbox("Orientaties", options=["oost", "west", 'zuid', "noord", "zuidoost", "zuidwest", "noordoost", "noordwest"], index=1, label_visibility="collapsed")
        Hellingshoek2 = st.selectbox("Hellingshoek 1", options=[0, 15, 45, 90], index=3, label_visibility="collapsed")
        WP2 = st.number_input("Watt Pieks 2", value=0)
    
    if uploaded_file := st.file_uploader("Upload je data van het verbruik", type=["xlsx", "csv"]):
        if uploaded_file.name.endswith('.xlsx'):
            verbruik_df = read_data(uploaded_file)
        else:
            verbruik_df = pd.read_csv(uploaded_file)

    
    if st.button("Bereken Kwartierdata"):
        Kwartierdata = KwartierdataProcessor(
            aantal_jaren=aantal_jaar,
            breedtegraad=breedtegraad,
            lengtegraad=lengtegraad,
            hellingshoek1=Hellingshoek1,
            hellingshoek2=Hellingshoek2,
            orientatie1=orientatie1,
            orientatie2=orientatie2,
            wp1=WP1,
            wp2=WP2,
            begin_dag=begin_datum,
            dag_grafiek=plot_dag,
            zonnedata_pos=zonnedata_pos_neg,
            rendement=rendement
        ).bereken_kwartieropbrengst()
        
        verbruik = verbruik_df/4 # Normaliseer verbruik naar kwartierdata (4 kwartieren per uur)
        weer_scenario_data = get_zonnepanelen_scenario_profiel(weer_scenario)
        plot_belastingduurkromme(verbruik)
        plot_opbrengst_jaar(Kwartierdata, verbruik)
        plot_opbrengst_per_dag(kwartierdata_naar_dagdata(Kwartierdata), kwartierdata_naar_dagdata(verbruik), terugleverlimiet=terugleverlimiet, afnamelimiet=afnamelimiet)
        maak_heatmap_verbruik(verbruik, limiet=afnamelimiet)
        plot_opbrengst_dag(Kwartierdata, verbruik, plot_dag)
        #dag_opbrengst = kwartierdata_naar_dagdata(Kwartierdata)
        #dag_scenario = dag_opbrengst[]
        #plot_opbrengst_per_dag(kwartierdata_naar_dagdata(Kwartierdata)*weer_scenario_data, kwartierdata_naar_dagdata(verbruik), terugleverlimiet=terugleverlimiet, afnamelimiet=afnamelimiet)
        #plot_energiebalans_dag(verbruik, Kwartierdata, afnamelimiet, terugleverlimiet)
        st.write("Analysis done")
        csv = Kwartierdata.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Download Kwartierdata als CSV",
            data=csv,
            file_name="kwartierdata_resultaten.csv",
            mime="text/csv"
        )
    

st.sidebar.title("Navigatie")
pagina = st.sidebar.selectbox("Kies een pagina", ["Home", "Data Analyse bestaande data", "Voorspelling en analyse"])
if pagina == "Home":
    show_home()
elif pagina == "Data Analyse bestaande data":  
    Data_analyse_bestaande_data()   
elif pagina == "Voorspelling en analyse":
    show_voorspelling_en_analyse()

#Achtergrond data van de berekening
Aantal_jaren = 2
Breedtegraad = 52.13
Lengtegraad = 6.54
Orientaties = 2
Hellingshoek1 = 15
Hellingshoek2 = 0
Orientatie1 = "oost"
Orientatie2 = "west"
WP1 = 2000
WP2 = 1000

