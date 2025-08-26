import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from copy import deepcopy
import matplotlib.image as mpimg
class PlotManager:
    @st.cache_data
    def plot_belastingduurkromme(_self, _verbruiken: list[float]):
        punten = PlotManager._bereken_belastingduurkromme(_verbruiken)
        BASE_DIR = os.path.dirname(__file__)

        # pad naar het logo
        logo_path = os.path.join(BASE_DIR, "LO-Bind-FC-RGB.png")

        logo = mpimg.imread(logo_path)
        
        
        
        if not punten:
            st.warning("Geen data om te plotten.")
            return
        duur, belasting = zip(*punten)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        ax.plot(duur, belasting, marker='o', label="Belastingduurkromme")
        ax.set_xlabel('Duur (%)')
        ax.set_ylabel('Belasting (verbruik)')
        ax.set_title('Belastingduurkromme')
        ax.grid(True)
        ax.legend()
        logo_ax = fig.add_axes([0.72, 0.65, 0.18, 0.18], anchor='NE', zorder=1)
        logo_ax.imshow(logo)
        logo_ax.axis('off')
        st.pyplot(fig)

    def _bereken_belastingduurkromme(verbruiken):
        n = len(verbruiken)
        if n == 0:
            return []
        gesorteerd = sorted(verbruiken, reverse=True)
        resultaat = []
        for i, waarde in enumerate(gesorteerd):
            duur = i / n * 100
            resultaat.append((duur, waarde))
        return resultaat
    
    
    def plot_energiebalans_dag(_self, _verbruik: pd.DataFrame, _opbrengst: pd.DataFrame, _max_afname, _max_teruglevering, _positief='positief', _accu_vermogen=0, _toon_verbruik=True, _toon_opbrengst=True, _toon_saldo=False, _toon_saldo_beperkt=True, _toon_limieten=True, _toon_limiet_overschrijdingen=False):
        if _positief == 'positief':
            pos = 1
        else: 
            pos = -1
        
        if _accu_vermogen > 0:
            accu = _accu_vermogen
        else: 
            accu = 0
        logo = mpimg.imread("C:\\Users\\LuukTijhaar(bind)\\vscode\\init_project\\src\\init_project\\LO-Bind-FC-RGB.png")
        min_len = min(len(_verbruik), len(_opbrengst))
        verbruik = _verbruik.iloc[:min_len]
        opbrengst = _opbrengst.iloc[:min_len]
        tijdstappen = verbruik.index[:min_len]
        verbruik_s = verbruik
        opbrengst_s = opbrengst
        saldo = -opbrengst + verbruik_s
        saldo_beperkt = saldo.copy()
        saldo_beperkt[saldo < 0] = saldo[saldo < 0].clip(lower=-_max_teruglevering)
        saldo_beperkt[saldo > 0] = saldo[saldo > 0].clip(upper=_max_afname)
        totaal_saldo = saldo_beperkt.sum()*0.25
        accu_toestand = deepcopy(saldo)
        accu_toestand[0] = 0
        """if accu != 0:
            for i in range(min_len):
                if saldo[i] > _max_afname:
                    accu_toestand[i] = accu_toestand[i-1] + saldo[i] - _max_afname

                elif saldo[i] < -_max_teruglevering:
                    accu_toestand[i] = accu_toestand[i-1] + saldo[i] + _max_teruglevering

                else:
                    saldo[i] -= min(saldo[i], _max_afname)"""
        overmatige_afname = saldo[saldo > _max_afname]
        overmatige_afname = overmatige_afname - _max_afname
        
        overmatige_teruglevering = saldo[saldo < -_max_teruglevering]
        overmatige_teruglevering = overmatige_teruglevering + _max_teruglevering

        toon_verbruik = _toon_verbruik
        toon_opbrengst = _toon_opbrengst
        toon_saldo = _toon_saldo
        toon_saldo_beperkt = _toon_saldo_beperkt
        toon_limieten = _toon_limieten
        toon_limiet_overschrijdingen = _toon_limiet_overschrijdingen

        

        fig, ax = plt.subplots(figsize=(10, 6))
        if toon_verbruik:
            ax.plot(tijdstappen, verbruik_s, label='Verbruik', color='red')
        if toon_opbrengst:
            ax.plot(tijdstappen, pos*opbrengst_s, label='Opbrengst', color='green')
        if toon_saldo_beperkt:
            ax.plot(tijdstappen, saldo_beperkt, label='Saldo (beperkt)', color='blue')
        if toon_saldo:
            ax.plot(tijdstappen, saldo, label='Saldo', color='orange')
        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        if toon_limieten:
            ax.axhline(_max_afname, color='red', linewidth=0.8, linestyle=':', label='Max afname')
            ax.axhline(pos*_max_teruglevering, color='purple', linewidth=0.8, linestyle=':', label='Max teruglevering')
        if toon_limiet_overschrijdingen:
            ax.fill_between(tijdstappen, saldo, saldo_beperkt, where=(np.array(saldo) > np.array(saldo_beperkt)), color='yellow', alpha=0.5, label='Limiet overschreden afname')
            ax.fill_between(tijdstappen, saldo, saldo_beperkt, where=(np.array(saldo) < np.array(saldo_beperkt)), color='orange', alpha=0.5, label='Limiet overschreden teruglevering')
        ax.set_xlabel('Tijdstap')
        ax.set_ylabel('Energie')
        ax.set_title(f'Energiebalans dag (totaal saldo: {totaal_saldo:.2f} kWh)')
        ax.legend()
        ax.grid(True)
        logo_ax = fig.add_axes([0.8, 0.08, 0.18, 0.18], anchor='NE', zorder=1)
        logo_ax.imshow(logo)
        logo_ax.axis('off')
        fig.tight_layout()
        st.pyplot(fig)
        st.markdown(f"""
                <p style="font-size:18px;">
                <h1>Overschrijding afname: {overmatige_afname.sum() * 0.25:.2f} kWh </h1><br>
                <h1>Overschrijding teruglevering: {overmatige_teruglevering.sum() * 0.25:.2f} kWh </h1>
                </p>
                """, unsafe_allow_html=True)
    @st.cache_data
    def plot_dagbalans_jaar(_self, _verbruik_jaar: pd.DataFrame, _opbrengst_jaar: pd.DataFrame, _max_afname, _max_teruglevering):
        opbrengst_jaar = _opbrengst_jaar
        verbruik_jaar = _verbruik_jaar

        verbruik_jaar.index = pd.to_datetime(verbruik_jaar)
        opbrengst_jaar.index = pd.to_datetime(opbrengst_jaar)
        st.write(f"Aantal datapunten {len(verbruik_jaar)} verbruik, {len(opbrengst_jaar)} opbrengst, vorm: {verbruik_jaar.head()}")
        dagen = sorted(set(verbruik_jaar.index.normalize()) & set(opbrengst_jaar.index.normalize()))
        st.write(f"Vorm dagen: {dagen[:5]}... ({len(dagen)} totaal)")
        dagresultaten = []
        st.write(f"Aantal dagen met data: {len(dagen)}")
        for dag in dagen:
            v_dag = verbruik_jaar[verbruik_jaar.index.normalize() == dag]
            o_dag = opbrengst_jaar[opbrengst_jaar.index.normalize() == dag]
            min_len = min(len(v_dag), len(o_dag))
            if min_len == 0:
                continue
            v_dag = v_dag.iloc[:min_len]
            o_dag = o_dag.iloc[:min_len]
            verbruik_s = v_dag.sum(axis=1) if isinstance(v_dag, pd.DataFrame) else v_dag
            # Tel alle kolommen van opbrengst bij elkaar op tot één Series
            if isinstance(o_dag, pd.DataFrame):
                opbrengst_s = o_dag.sum(axis=1)
            else:
                opbrengst_s = o_dag
            saldo = opbrengst_s - verbruik_s
            saldo_beperkt = saldo.copy()
            """saldo_beperkt[saldo < 0] = saldo[saldo < 0].clip(lower=-max_afname)
            saldo_beperkt[saldo > 0] = saldo[saldo > 0].clip(upper=max_teruglevering)"""
            dagresultaten.append({
                'dag': dag,
                'verbruik': verbruik_s.sum(),
                'opbrengst': opbrengst_s.sum(),
                'saldo': saldo_beperkt.sum()
            })

        if not dagresultaten:
            st.warning("Geen overlappende dagen met data gevonden.")
            return
        st.write(f"📅 Aantal dagen met data: {len(dagresultaten)}, voorbeeld data: {dagresultaten}")
        df_dagbalans = pd.DataFrame(dagresultaten).set_index('dag')
        show_verbruik = st.checkbox("Toon verbruik", value=True, key="jaar_verbruik")
        show_opbrengst = st.checkbox("Toon opbrengst", value=True, key="jaar_opbrengst")
        show_saldo = st.checkbox("Toon saldo", value=True, key="jaar_saldo")

        fig, ax = plt.subplots(figsize=(12, 6))
        if show_verbruik:
            ax.plot(df_dagbalans.index, df_dagbalans['verbruik'], label='Totaal verbruik per dag', color='red')
        if show_opbrengst:
            ax.plot(df_dagbalans.index, df_dagbalans['opbrengst'], label='Totaal opbrengst per dag', color='green')
        if show_saldo:
            ax.plot(df_dagbalans.index, df_dagbalans['saldo'], label='Dagbalans (beperkt)', color='blue')
        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax.set_xlabel('Datum')
        ax.set_ylabel('Energie')
        ax.set_title('Dagelijkse energiebalans over het jaar')
        ax.legend()
        ax.grid(True)
        fig.tight_layout()
        st.pyplot(fig)

   
    def plot_reeksen_en_verschil(_self, _opbrengst: pd.Series, _verbruik: pd.Series, _titel="Opbrengst vs Verbruik", show_opbrengst=True, show_verbruik=True, show_verschil=True, _max_afname=0, _max_teruglevering=0):
        opbrengst = _opbrengst
        verbruik = _verbruik
        titel = _titel
        logo = mpimg.imread("C:\\Users\\LuukTijhaar(bind)\\vscode\\init_project\\src\\init_project\\LO-Bind-FC-RGB.png")
        max_afname = _max_afname
        max_teruglevering = _max_teruglevering
        min_len = min(len(opbrengst), len(verbruik))
        opbrengst = opbrengst.iloc[:min_len]
        verbruik = verbruik.iloc[:min_len]
        #st.write(f"Aantal datapunten: {len(opbrengst)} opbrengst, {len(verbruik)} verbruik")
        #st.write(opbrengst.head())
        index = opbrengst.index
        verschil = -opbrengst[:min_len] + verbruik[:min_len]       
        
        #st.write(verbruik.head(),verbruik.shape,opbrengst.head(),opbrengst.shape)#verschil.head(),verschil.shape)


        fig, ax = plt.subplots(figsize=(12, 6))
        if show_opbrengst:
            ax.plot(index, -opbrengst, label="Opbrengst", color="green")
        if show_verbruik:
            ax.plot(index, verbruik, label="Verbruik", color="red")
        if show_verschil:
            ax.plot(index, verschil, label="Verschil (Verbruik - Opbrengst)", color="blue")
        ax.axhline(max_afname, color='red', linewidth=0.8, linestyle='-', label='Max afname')
        ax.axhline(-max_teruglevering, color='purple', linewidth=0.8, linestyle='-', label='Max teruglevering')
        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax.set_xlabel("Tijd")
        ax.set_ylabel("Energie (kW)")
        ax.set_title(titel)
        ax.legend()
        ax.grid(True)
        logo_ax = fig.add_axes([0.8, 0.08, 0.18, 0.18], anchor='NE', zorder=1)
        logo_ax.imshow(logo)
        logo_ax.axis('off')
        fig.tight_layout()
        st.pyplot(fig)