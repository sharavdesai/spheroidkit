from spheroidkit.analysis.growth import TimePoint, build_growth_curve

def test_baseline_anchors_to_first():
    pts = [TimePoint(24, 800000), TimePoint(72, 1200000)]
    gc = build_growth_curve(pts, baseline="first")
    assert abs(gc.fold_change[0] - 1.0) < 1e-6
    assert abs(gc.fold_change[1] - 1.5) < 1e-6

def test_unsorted_input_is_sorted():
    pts = [TimePoint(120, 1280000), TimePoint(24, 820000), TimePoint(72, 1010000)]
    gc = build_growth_curve(pts)
    assert list(gc.times_h) == [24, 72, 120]

def test_growth_rate_positive_for_growth():
    pts = [TimePoint(24, 800000), TimePoint(168, 1600000)]
    gc = build_growth_curve(pts)
    assert gc.specific_growth_rate > 0
    assert gc.doubling_time_h > 0

print("running growth tests...")
test_baseline_anchors_to_first()
test_unsorted_input_is_sorted()
test_growth_rate_positive_for_growth()
print("all growth tests passed")
