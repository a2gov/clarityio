import pytest
import pandas as pd
import numpy as np
from clarityio import scale_raw_to_aqi

def test_scale_raw_values():
    assert scale_raw_to_aqi('pm2.5_24hr', 18.84) == 69.14676806083651
    assert scale_raw_to_aqi('nitrogen_dioxide_1hr', 300) == 138.64864864864865

def test_scale_pandas_series():
    data = pd.Series([5, 9, 30, 60])
    expected = pd.Series([27.777778, 50.0, 89.939163, 154.154506], dtype='float64')
    result = scale_raw_to_aqi('pm2.5_24hr', data)
    pd.testing.assert_series_equal(result, expected)

def test_missing_inputs():
    assert np.isnan(scale_raw_to_aqi('sulfur_dioxide_1hr', None))
    assert np.isnan(scale_raw_to_aqi('ozone_8hr', np.nan))

def test_invalid_pollutant_name():
    with pytest.raises(ValueError, match="Unknown pollutant: invalid_pollutant"):
        scale_raw_to_aqi('invalid_pollutant', 999)

def test_negative_raw_value():
    with pytest.raises(ValueError, match="Negative pollutant values are invalid."):
        assert scale_raw_to_aqi('carbon_monoxide_8hr', -0.010) == 0

def test_raw_value_exceeding_scale():
    with pytest.warns(UserWarning, match="Pollutant value 99999 is off the scale for pm10_24hr, returning maximum scaled value of 500."):
        assert scale_raw_to_aqi('pm10_24hr', 99999) == 500