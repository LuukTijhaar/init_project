# Scenario's voor zonnepanelen-opbrengst per dag (kwartier-profiel, waarden tussen 0 en 1)
from typing import Literal

def get_zonnepanelen_scenarios_kwartier():
    """
    Geeft een dict met vier scenario's voor zonnepanelen-opbrengst per dag.
    Elke waarde is een lijst van 96 vermenigvuldigingsfactoren (één per kwartier).
    """
    import numpy as np

    kwartieren = np.arange(96)
    # Zonsopkomst rond 5:30 (kwartier 22), hoogste punt rond 13:00 (kwartier 52), zonsondergang rond 21:30 (kwartier 86)
    def dagprofiel(piek=1.0, breedte=32, start=22, eind=86):
        profiel = np.zeros(96)
        midden = (start + eind) // 2
        sigma = breedte / 2.355  # FWHM naar sigma
        for i in range(start, eind):
            profiel[i] = piek * np.exp(-0.5 * ((i - midden) / sigma) ** 2)
        return profiel

    return {
        "goed_weer": dagprofiel(piek=1.0, breedte=40, start=22, eind=86).tolist(),
        "slecht_weer": (dagprofiel(piek=0.25, breedte=40, start=22, eind=86) * 0.7).tolist(),
        "bewolkt": (dagprofiel(piek=0.35, breedte=60, start=22, eind=86) * 0.9).tolist(),
        "wisselvallig": (
            dagprofiel(piek=0.7, breedte=40, start=22, eind=86) *
            (0.7 + 0.3 * np.sin(kwartieren / 6) + 0.2 * np.random.RandomState(42).randn(96))
        ).clip(0, 1).tolist()
    }

def get_zonnepanelen_scenario_profiel(scenario_naam: Literal['goed_weer', 'slecht_weer', 'bewolkt', 'wisselvallig']):
    """
    Geeft het kwartierprofiel voor de opgegeven scenario-naam.
    :param scenario_naam: 'goed_weer', 'slecht_weer', 'bewolkt', of 'wisselvallig'
    :return: lijst van 96 waarden (vermenigvuldigingsfactoren)
    """
    scenario_dict = get_zonnepanelen_scenarios_kwartier()
    if scenario_naam not in scenario_dict:
        raise ValueError(f"Scenario '{scenario_naam}' niet gevonden. Kies uit: {list(scenario_dict.keys())}")
    return scenario_dict[scenario_naam]
