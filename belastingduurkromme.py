from typing import List, Tuple
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
def bereken_belastingduurkromme(verbruiken: pd.DataFrame) -> List[Tuple[float, float]]:
    """
    Bereken de belastingduurkromme op basis van een lijst met verbruikswaarden.
    Geeft een lijst van (duur, belasting)-paren terug, waarbij duur het percentage van de tijd is
    dat het verbruik wordt overschreden.

    :param verbruiken: Lijst met verbruikswaarden (bijv. per uur of kwartier)
    :return: Lijst van tuples (duur in %, belasting)
    """

    n = len(verbruiken)
    
    if n == 0:
        st.write("Geen verbruikswaarden beschikbaar.")
        return []

    gesorteerd = sorted(verbruiken, reverse=True)
    resultaat = []
    for i, waarde in enumerate(gesorteerd):
        duur = i / n * 100  # 0% bij hoogste belasting, 100% bij laagste
        resultaat.append((duur, waarde))
        
    return resultaat


def plot_belastingduurkromme(verbruiken_df):
    """
    Plot de belastingduurkromme op basis van een DataFrame met verbruikswaarden.
    """
    # Zet kolom om naar lijst met waarden
    verbruiken_lijst = verbruiken_df.squeeze().tolist()
    punten = bereken_belastingduurkromme(verbruiken_lijst)

    if not punten:
        st.write("Geen data om te plotten.")
        return

    duur, belasting = zip(*punten)
    plt.figure(figsize=(8, 5))
    plt.plot(duur, belasting, marker='o')
    plt.xlabel('Duur (%)')
    plt.ylabel('Belasting (verbruik)')
    plt.title('Belastingduurkromme')
    plt.grid(True)
    st.pyplot(plt)