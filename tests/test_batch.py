from spheroidkit.io.batch import parse_well_from_filename, build_dose_series, PlateResult, WellResult

def test_well_parsing():
    assert parse_well_from_filename("img_A01.tif") == "A01"
    assert parse_well_from_filename("scan-H12-d3.png") == "H12"
    assert parse_well_from_filename("plate_b2.jpg") == "B02"
    assert parse_well_from_filename("noWELLhere.tif") is None

def test_dose_series_normalises_to_control():
    plate = PlateResult(wells=[
        WellResult("A01","p",metrics={"area":1000},concentration=0,group="control"),
        WellResult("A02","p",metrics={"area":1000},concentration=0,group="control"),
        WellResult("B01","p",metrics={"area":500}, concentration=1.0,group="t"),
        WellResult("C01","p",metrics={"area":250}, concentration=10.0,group="t"),
    ])
    s = build_dose_series(plate, metric="area")
    assert s["concentrations"] == [1.0, 10.0]
    assert abs(s["responses"][0] - 50.0) < 1e-6   # 500/1000
    assert abs(s["responses"][1] - 25.0) < 1e-6   # 250/1000

def test_requires_controls():
    plate = PlateResult(wells=[
        WellResult("B01","p",metrics={"area":500},concentration=1.0,group="t")])
    try:
        build_dose_series(plate); assert False
    except ValueError:
        pass

print("running batch tests...")
test_well_parsing()
test_dose_series_normalises_to_control()
test_requires_controls()
print("all batch tests passed")
