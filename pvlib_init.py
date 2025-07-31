import pvlib 
import pandas as pd
from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import matplotlib.pyplot as plt
import streamlit as st

@st.cache_data
def get_parameters(_breedtegraad=52.2215, _lengtegraad=6.8937, _tijdzone='Europe/Amsterdam', _hoogte=42, _type_paneel="Jinko_Solar_Co___Ltd_JKM410M_72HL_V",_type_omvormer="ABB__PVI_3_0_OUTD_S_US__208V_", _montage_type='open_rack_glass_polymer'):
    location = Location(latitude=_breedtegraad, longitude=_lengtegraad, tz=_tijdzone, altitude=_hoogte) #hoogte gebouw moet er eigenlijk nog bij maar is bijna verwaarloosbaar. 

    sandia_modules = pvlib.pvsystem.retrieve_sam('CECMod')  # Retrieve the CEC module database
    st.write("Modules:", sandia_modules.keys())
    cec_inverters = pvlib.pvsystem.retrieve_sam('CECInverter')  # Retrieve the CEC inverter database

    module = sandia_modules[_type_paneel]  # Example module

    inverter = cec_inverters[_type_omvormer]  # Example inverter

    temperature_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm'][_montage_type]
    print(location)
    return location, module, inverter, temperature_parameters

@st.cache_data
def Initialize_Systeem(_location, _module, _inverter, _temperature_parameters, _hellingshoek=45, _azimuth=180, _panelen_per_reeks=1, _reeksen_per_omvormer=1,_start_date='2021-01-01', _end_date='2021-12-31'):
    
        
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
    
    st.pyplot(plt.gcf())  # Show the plot in Streamlit
    
    
    return model_chain
