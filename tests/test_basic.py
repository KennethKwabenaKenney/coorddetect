import pandas as pd
from coorddetect import detect_xyz

def test_xyz_detection():
    df = pd.DataFrame({
        "A": [1, 2, 3],
        "X_coord": [100, 200, 300],
        "Y_coord": [400, 500, 600],
        "Z_coord": [10, 20, 30],
    })

    xyz, meta = detect_xyz(df)

    assert xyz.shape[1] == 3
    assert meta["confidence"] > 0.5
    
    
    