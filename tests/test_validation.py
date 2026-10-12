import numpy as np
from spheroidkit.analysis.validation import agreement, dice_iou, concordance_ccc

def test_perfect_agreement():
    x = [100,200,300,400]
    a = agreement(x, x)
    assert abs(a.pearson_r - 1.0) < 1e-9
    assert abs(a.ccc - 1.0) < 1e-9
    assert abs(a.bias) < 1e-9

def test_dice_identical_masks():
    m = np.zeros((50,50), bool); m[10:40,10:40] = True
    d, i = dice_iou(m, m)
    assert abs(d-1.0) < 1e-9 and abs(i-1.0) < 1e-9

def test_dice_disjoint():
    a = np.zeros((50,50), bool); a[0:10,0:10]=True
    b = np.zeros((50,50), bool); b[40:50,40:50]=True
    d, i = dice_iou(a,b)
    assert d == 0.0 and i == 0.0

print("running validation tests...")
test_perfect_agreement(); test_dice_identical_masks(); test_dice_disjoint()
print("all validation tests passed")
