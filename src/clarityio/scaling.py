import warnings
import pandas as pd
import numpy as np

def scale_raw_to_aqi(pollutant, value):
    """
    Scale a raw pollutant value to the Air Quality Index (AQI) of 0-500.

    Parameters:
    pollutant (str): The type of pollutant (e.g., 'PM10', 'PM2.5', 'carbon_monoxide_8hour', etc.)
    value (float or pd.Series): The concentration of the pollutant. Can be a single float value or a Pandas Series of float values.

    Returns:
    float or pd.Series: The scaled AQI value(s). Returns a single float if input is a float, or a Pandas Series if input is a Series.

    Raises:
    ValueError: If the pollutant is unknown.

    Warnings:
    UserWarning: If the pollutant value is off the scale.

    Sources for cutoffs:
    https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf for cutoffs,
    though PM2.5 changed in 2024: https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf

    """
    
    cutoffs = {
    'pm10_24hr': [
        (54, 0, 50, 0),
        (154, 55, 100, 51),
        (254, 155, 150, 101),
        (354, 255, 200, 151),
        (424, 355, 300, 201),
        (604, 425, 500, 301),
    ],
    'pm2.5_24hr': [
        (9, 0, 50, 0),
        (35.4, 9.1, 100, 51),
        (55.4, 35.5, 150, 101),
        (125.4, 55.5, 200, 151),
        (225.4, 125.5, 300, 201),
        (500, 225.5, 500, 301)
    ],
    'carbon_monoxide_8hr': [
        (4.4, 0, 50, 0),
        (9.4, 4.5, 100, 51),
        (12.4, 9.5, 150, 101),
        (15.4, 12.5, 200, 151),
        (30.4, 15.5, 300, 201),
        (50.4, 30.5, 500, 301)
    ],
    # TODO: EPA says '24 hours' for the higher two levels of this pollutant, how to incorporate that?
    'sulfur_dioxide_1hr': [
        (35, 0, 50, 0),
        (75, 36, 100, 51),
        (185, 76, 150, 101),
        (304, 186, 200, 151),
        (604, 305, 300, 201),
        (1004, 605, 500, 301)
    ],
    'nitrogen_dioxide_1hr': [
        (53, 0, 50, 0),
        (100, 54, 100, 51),
        (360, 101, 150, 101),
        (649, 361, 200, 151),
        (1249, 650, 300, 201),
        (2049, 1250, 500, 301)
    ],
    'ozone_1hr': [
      # Lower two tiers are not provided by EPA
        (0.164, 0.125, 150, 101),
        (0.204, 0.165, 200, 151),
        (0.404, 0.205, 300, 201),
        (0.604, 0.405, 500, 301)
    ],
    'ozone_8hr': [
        (0.054, 0, 50, 0),
        (0.070, 0.055, 100, 51),
        (0.085, 0.071, 150, 101),
        (0.105, 0.086, 200, 151),
        (0.200, 0.106, 300, 201)
      # Top tier not provided by EPA
    ]
    }
    if isinstance(value, pd.Series):
        return value.apply(lambda x: scale_raw_to_aqi(pollutant, x))
    if value is None or np.isnan(value):
        return np.nan
    elif value < 0:
        raise ValueError("Negative pollutant values are invalid.")
    if pollutant not in cutoffs:
        raise ValueError(f"Unknown pollutant: {pollutant}")
    for cutoff, low, high, base in cutoffs[pollutant]:
        if value <= cutoff:
            return (high - base) / (cutoff - low) * (value - low) + base
    warnings.warn(f"Pollutant value {value} is off the scale for {pollutant}, returning maximum scaled value of {cutoffs[pollutant][-1][2]}.")
    return cutoffs[pollutant][-1][2]