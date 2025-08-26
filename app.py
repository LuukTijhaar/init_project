import streamlit as st
import pandas as pd
from plot_manager import PlotManager
from pvlib_init import Initialize_Systeem, get_parameters
import time 
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import io 
import os 
#from dotenv import load_dotenv

st.set_page_config(page_title="Energie Analyse (Nieuw)", layout="wide")



BASE_DIR = os.path.dirname(__file__)

# pad naar het logo
logo_path = os.path.join(BASE_DIR, "LO-Bind-FC-RGB.png")

logo = mpimg.imread(logo_path)

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
    type_omvormer = st.selectbox("Type omvormer", options=["Enphase", "SolarEdge", "Fronius"], index=0)
    type_paneel = st.selectbox("Type paneel", options=["Monokristallijn", "Polykristallijn", "Dunne film"], index=0)

    
    
    aantal_jaar = st.number_input("Aantal jaren voor voorspelling", min_value=1, max_value=2, value=1)
    
    begin_datum = st.date_input("Startdatum", value=pd.to_datetime('2023-01-01'))
    
    zonnedata_pos_neg = st.selectbox("Zonnedata positief of negatief", options=["positief", "negatief"], index=0)
    weer_scenario = st.selectbox("Weer scenario", options=["goed_weer", "slecht_weer", "bewolkt", "wisselvallig"], index=0)
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

@st.cache_resource
def laad_dataframes(file, index_col=0, parse_dates=True): 
    """Laad excel bestanden en retourneer de dataframes."""
    if file is not None: 
        df = pd.read_excel(file, index_col=index_col, parse_dates=parse_dates)
        return df 
    return None

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
            location, module, inverter, temperature_parameters = get_parameters(_breedtegraad=breedtegraad, _lengtegraad=lengtegraad, _tijdzone="Europe/Amsterdam", _hoogte=42)
            
            df_opbrengst1 = Initialize_Systeem(
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
            
            st.write(df_opbrengst1.results.ac['2021-01-01 00:15:00+01:00':'2021-01-02 00:15:00+01:00'])
            
            df_opbrengst2 = Initialize_Systeem(
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

            st.write(f"opbrengst over een jaar totaal: {df_opbrengst.sum()/4000}, zijde 1: {df_opbrengst1.results.ac.sum()/4000}, zijde 2: {df_opbrengst2.results.ac.sum()/4000}")
            
            #st.pyplot(plt.gcf())  # Show the plot in Streamlit
            "df_opbrengst = bereken_opbrengst(aantal_jaren=aantal_jaar, breedtegraad=breedtegraad, lengtegraad=lengtegraad, hellingshoek1=Hellingshoek1, hellingshoek2=Hellingshoek2, orientatie1=orientatie1, orientatie2=orientatie2, wp1=WP1, wp2=WP2,begin_dag=begin_datum,zonnedata_pos=zonnedata_pos_neg,rendement=rendement).bereken_kwartieropbrengst()"
        st.write("Duur:", time.time() - start)
    else: 
        df_opbrengst = laad_dataframes(uploaded_opbrengst, index_col=0, parse_dates=True)
    df_verbruik = laad_dataframes(uploaded_verbruik, index_col=0, parse_dates=True)
    
    st.success("✅ Data succesvol geladen!")
    st.markdown('<div class="section-header">Voorbeeld verbruik</div>', unsafe_allow_html=True)
    st.dataframe(df_verbruik, use_container_width=True)
    st.markdown('<div class="section-header">Voorbeeld opbrengst</div>', unsafe_allow_html=True)
    st.dataframe(df_opbrengst, use_container_width=True)

    st.markdown('<div class="section-header">2. Selecteer kolommen verbruik en opbrengst</div>', unsafe_allow_html=True)
    
    data_verbruik = st.text_input("Kolom verbruiksdata:", value="Verbruik")
    
    data_verbruik = df_verbruik[data_verbruik]
    data_verbruik = data_verbruik.iloc[:35040]*0.25  # Voorbeeld: neem de eerste 35.178 rijen en naar kW
    data_verbruik.index = pd.to_datetime(df_verbruik.iloc[:35040, 0])
    if uploaded_opbrengst != "Processor":
        data_opbrengst = st.text_input("Kolom opbrengstdata:", value="Verbruik")
        data_opbrengst = df_opbrengst[data_opbrengst]
        data_opbrengst = data_opbrengst.iloc[:35040]  # Voorbeeld: neem de eerste 35.178 rijen
    else:
        data_opbrengst = df_opbrengst
        data_opbrengst = data_opbrengst.iloc[:35040]
    data_opbrengst.index = pd.to_datetime(df_verbruik.iloc[:35040, 0])
    #st.dataframe(data_verbruik.head(), use_container_width=True)
    #st.dataframe(data_opbrengst.head(), use_container_width=True)
    #st.write(type(data_verbruik), type(data_opbrengst))
    st.markdown('<div class="section-header">3. Analyse & Visualisatie</div>', unsafe_allow_html=True)
    plotter = PlotManager()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Belastingduurkromme", 
        "Energiebalans dag", 
        "Dagbalans jaar", 
        "Opbrengst vs Verbruik",
        "Max kwartierverbruik heatmap"
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
            logo_ax = fig.add_axes([0.8, 0.08, 0.18, 0.18], anchor='NE', zorder=1)
            logo_ax.imshow(logo)
            logo_ax.axis('off')
            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            st.pyplot(fig)

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
            """
            Plot een heatmap van het hoogste (verbruik - opbrengst) per dag als percentage van max_afname.
            Geeft ook aan hoe vaak het limiet wordt overschreden.
            """
            from matplotlib.colors import LinearSegmentedColormap
            import seaborn as sns

            # Zorg dat indexen datetime zijn
            verbruik = verbruik.copy()
            opbrengst = opbrengst.copy()
            verbruik.index = pd.to_datetime(verbruik.index)
            opbrengst.index = pd.to_datetime(opbrengst.index)

            # Zorg dat series even lang zijn
            min_len = min(len(verbruik), len(opbrengst))
            verbruik = verbruik.iloc[:min_len]
            opbrengst = opbrengst.iloc[:min_len]

            # Verschil per kwartier
            verschil = verbruik - opbrengst

            # Per dag: hoogste kwartierwaarde (piek) van verschil
            piek_per_dag = verschil.resample('D').max()

            # Zet om naar percentage van max_afname
            perc_per_dag = (piek_per_dag / max_afname) * 100

            # Statistiek: aantal dagen limiet overschreden
            overschrijdingen = (piek_per_dag > max_afname).sum()
            totaal_dagen = piek_per_dag.shape[0]

            # Maak DataFrame met dag en maand
            df = pd.DataFrame({'percentage': perc_per_dag})
            df['dag'] = df.index.day
            df['maand'] = df.index.month_name()

            # Pivot: rijen = maand, kolommen = dag
            pivot = df.pivot_table(index="maand", columns="dag", values="percentage", aggfunc="mean")

            # Maanden in logische volgorde
            maanden_volgorde = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            pivot = pivot.reindex(maanden_volgorde)

            colors = [
                (0.0, 'green'),
                (0.8, 'yellow'),
                (1.0, 'red'),
            ]

            custom_cmap = LinearSegmentedColormap.from_list("green_yellow_red", colors)

            fig, ax = plt.subplots(figsize=(16, 8))
            sns.heatmap(pivot, annot=True, fmt=".1f", cmap=custom_cmap, vmin=0, vmax=100,
                        linewidths=0.5, linecolor='gray', ax=ax)

            ax.set_title("Max kwartierverbruik per dag (% van max afname)", fontsize=16)
            ax.set_xlabel("Dag van de maand")
            ax.set_ylabel("Maand")
            plt.tight_layout()
            logo_ax = fig.add_axes([0.8, -0.10, 0.18, 0.18], anchor='NE', zorder=1)
            logo_ax.imshow(logo)
            logo_ax.axis('off')
            # Hoogste dag
            max_perc = perc_per_dag.max()
            max_dag = perc_per_dag.idxmax()
            st.pyplot(fig)
            st.write(f"📅 **Dag met hoogste piek:** {max_dag.date()} met {max_perc:.2f}% van max afname")
            st.write(f"🚨 **Aantal dagen limiet overschreden:** {overschrijdingen} van {totaal_dagen} dagen ({overschrijdingen/totaal_dagen:.1%})")

        plot_max_dagpiek_heatmap(data_verbruik, data_opbrengst, max_afname)


    df = pd.DataFrame({
        "Verbruik (kW)": data_verbruik,
        "Opbrengst (kW)": data_opbrengst})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer: 
        df.to_excel(writer, index=True, sheet_name="Kwartierdata Resultaten")
        writer.close()
        processed_data = output.getvalue()
    st.info("Download hier je resultaten als Excel-bestand.")
    st.download_button(
    label="📥 Download resultaten als Excel",
    data=processed_data,
    file_name="kwartierdata_resultaten.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

else:
    st.warning("Upload zowel verbruik als opbrengst kwartierdata-bestanden om te starten.")

st.markdown("---")
st.info("Gebruik de tabs om verschillende analyses en visualisaties te bekijken.")