import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.cluster import KMeans
import gc

@st.cache_data
def cluster_typical_profiles(verbruik: pd.Series, n_clusters=7, use_weekend=True, random_state=42):
    """
    Voer clustering uit op dagelijkse verbruiksprofielen (96 kwartieren per dag).
    Optioneel: voeg weekend/weekdag als feature toe.
    Toont typische profielen en clusterverdeling.
    """
    # Zorg dat index datetime is
    verbruik = verbruik.copy()
    verbruik.index = pd.to_datetime(verbruik.index)
    # Maak matrix: elke rij = 1 dag, 96 kolommen = kwartieren
    df = verbruik.groupby(verbruik.index.date).apply(lambda x: x.values[:96])
    df = pd.DataFrame(df.tolist(), index=df.index)
    # Filter incomplete dagen
    df = df[df.apply(lambda r: len(r.dropna())==96, axis=1)]
    X = np.stack(df.values)
    # Voeg weekend/weekdag toe als feature
    if use_weekend:
        is_weekend = pd.Series(df.index).apply(lambda d: pd.Timestamp(d).weekday() >= 5).astype(int).values
        X = np.hstack([X, is_weekend.reshape(-1, 1)])
    # Clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    labels = kmeans.fit_predict(X)
    # Plot typische profielen
    fig, ax = plt.subplots(figsize=(16, 8))
    for i in range(n_clusters):
        mean_profile = kmeans.cluster_centers_[i][:96]
        ax.plot(mean_profile, label=f"Cluster {i+1}")
    ax.set_xlabel("Kwartier van de dag (0=00:00)")
    ax.set_ylabel("Gemiddeld verbruik (kW)")
    ax.set_title("Typische dagelijkse verbruiksprofielen (clusters)")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)  # Sluit de figuur om geheugen vrij te maken
    gc.collect()
    # Clusterverdeling
    unique, counts = np.unique(labels, return_counts=True)
    cluster_counts = {int(k)+1: int(v) for k, v in zip(unique, counts)}  # cast keys & values
    st.write("Aantal dagen per cluster:", cluster_counts)

    # Optioneel: toon clusterlabel per dag
    df_result = pd.DataFrame({
        "datum": df.index.astype(str),      # naar string voor JSON-veiligheid
        "cluster": (labels + 1).astype(int), # labels naar Python int
        "weekdag?": pd.Series(df.index).apply(lambda d: pd.Timestamp(d).weekday() >= 5).astype(int).values
    })
    st.dataframe(df_result)
