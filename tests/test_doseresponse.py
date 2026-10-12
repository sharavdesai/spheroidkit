import numpy as np
from spheroidkit.analysis.doseresponse import (
    fit_dose_response, response_from_growth, curve_points)

def test_recovers_known_ic50():
    conc = np.array([0.01,0.1,0.3,1.0,3.0,10.0,30.0])
    resp = 5 + 95/(1 + 10**((np.log10(conc)-np.log10(2.0))*1.0))
    fit = fit_dose_response(conc, resp, n_boot=200)
    assert 1.5 < fit.ic50 < 2.5          # true IC50 = 2.0
    assert fit.r_squared > 0.99

def test_response_from_growth():
    r = response_from_growth([80,40,10], control_growth=100)
    assert np.allclose(r, [80,40,10])

def test_rejects_nonpositive_conc():
    try:
        fit_dose_response([0,1,2],[100,50,10])
        assert False
    except ValueError:
        pass

def test_curve_points_monotonic_decreasing():
    conc = np.array([0.1,1.0,10.0,100.0])
    resp = np.array([95,60,20,5])
    fit = fit_dose_response(conc, resp, n_boot=100)
    x, y = curve_points(fit)
    assert y[0] > y[-1]                    # inhibition: high at low conc

print("running dose-response tests...")
test_recovers_known_ic50()
test_response_from_growth()
test_rejects_nonpositive_conc()
test_curve_points_monotonic_decreasing()
print("all dose-response tests passed")
