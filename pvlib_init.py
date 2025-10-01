import pvlib 
import pandas as pd
from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS as TMP
import matplotlib.pyplot as plt
import streamlit as st



# @st.cache_data
def get_parameters(
    _type_paneel,
    _breedtegraad=52.2215, _lengtegraad=6.8937,
    _tijdzone='Europe/Amsterdam', _hoogte=42,
    _type_omvormer="ABB__PVI_3_0_OUTD_S_US__208V_",
    _montage_type='open_rack_glass_polymer'
):
    # 1) locatie
    location = Location(latitude=_breedtegraad, longitude=_lengtegraad, tz=_tijdzone, altitude=_hoogte)

    # 2) CEC databases
    cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')       # modules (kolommen)
    cec_inverters = pvlib.pvsystem.retrieve_sam('CECInverter')# inverters (rijen)

    # 3) normaliseer paneelkeuze → string
    if isinstance(_type_paneel, (list, tuple)):
        paneel_key = str(_type_paneel[0])
    else:
        paneel_key = str(_type_paneel)

    # 4) harde check: exacte key in CEC?
    if paneel_key not in cec_modules.columns:
        # probeer kleine normalisatie (underscores/spaties/case)
        lower_map = {c.lower(): c for c in cec_modules.columns}
        norm = re.sub(r'[\s\-]+', '_', paneel_key.strip())
        paneel_key_try = lower_map.get(paneel_key.lower()) or lower_map.get(norm.lower())
        if paneel_key_try is None:
            # laatste redmiddel: fuzzy
            import difflib
            match = difflib.get_close_matches(paneel_key, cec_modules.columns, n=1, cutoff=0.8)
            if match:
                paneel_key = match[0]
            else:
                raise KeyError(
                    f"Paneel '{_type_paneel}' niet gevonden in CEC database. "
                    f"Probeer een exacte CEC-naam of gebruik PVWatts fallback."
                )
        else:
            paneel_key = paneel_key_try

    # 5) haal de moduleparameters op als Series (GEEN DataFrame!)
    module_series = cec_modules[paneel_key]
    if isinstance(module_series, pd.DataFrame):
        # dit gebeurt als je per ongeluk meerdere kolommen hebt geselecteerd
        raise ValueError("Er werden meerdere modulekolommen geselecteerd; verwacht één exact matchende CEC-module.")

    # 6) inverter (dict)
    inverter = cec_inverters[_type_omvormer]

    # 7) temperatuurmodel
    temperature_parameters = TMP['sapm'][_montage_type]

    return location, module_series, inverter, temperature_parameters


def Initialize_Systeem1(
    _location, _module, _inverter, _temperature_parameters,
    _hellingshoek=45, _azimuth=180,
    _panelen_per_reeks=1, _reeksen_per_omvormer=1,
    _start_date='2021-01-01', _end_date='2021-12-31'
):
    # PVSystem met CEC-module (Series) en CEC-inverter (dict/Series)
    system = PVSystem(
        module_parameters=_module,
        inverter_parameters=_inverter,
        surface_tilt=_hellingshoek,
        surface_azimuth=_azimuth,
        temperature_model_parameters=_temperature_parameters,
        modules_per_string=_panelen_per_reeks,
        strings_per_inverter=_reeksen_per_omvormer,
    )

    # zet dc_model expliciet op 'cec' om gedoe te voorkomen
    model_chain = ModelChain(system, _location, aoi_model="no_loss", dc_model="cec")

    # tijdreeks + clearsky
    times = pd.date_range(start=_start_date, end=_end_date, freq='15min', tz=_location.tz)
    clear_sky = _location.get_clearsky(times)

    model_chain.run_model(weather=clear_sky)
    model_chain.results.ac = model_chain.results.ac / 1000  # naar kW
    # model_chain.results.ac.plot(figsize=(16,9), title='AC Power Output')
    return model_chain.results.ac


def Initialize_Systeem2(_location, _module, _inverter, _temperature_parameters, _hellingshoek=45, _azimuth=180, _panelen_per_reeks=1, _reeksen_per_omvormer=1,_start_date='2021-01-01', _end_date='2021-12-31'):
    
        
    system = PVSystem(
        module_parameters=_module, inverter_parameters=_inverter,   
        surface_tilt=_hellingshoek,  # tilt angle of the modules
        surface_azimuth=_azimuth,  # azimuth angle of the modules
        temperature_model_parameters=_temperature_parameters,
        modules_per_string=_panelen_per_reeks,
        strings_per_inverter=_reeksen_per_omvormer,
    )

    model_chain = ModelChain(system, _location, aoi_model="no_loss")

    times = pd.date_range(start=_start_date, end=_end_date, freq='15min', tz=_location.tz)

    clear_sky = _location.get_clearsky(times)

    #clear_sky.plot(figsize=(16,9))

    model_chain.run_model(weather=clear_sky)
    model_chain.results.ac = model_chain.results.ac  / 1000  # Convert to kW if needed
    model_chain.results.ac.plot(figsize=(16,9), title='AC Power Output')
    
    #st.pyplot(plt.gcf())  # Show the plot in Streamlit
    
    
    return model_chain.results.ac