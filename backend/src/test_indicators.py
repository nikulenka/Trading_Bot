
import sys
import os
import pandas as pd
# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.indicators import Indicators

def test_indicators():
    # Load 4h data
    # Path: backend/src/test_indicators.py -> backend/src -> backend -> Traging_Bot -> data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', 'BTCUSDT_4h.csv')
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path, index_col='timestamp', parse_dates=True)
    print(f"Loaded {len(df)} rows.")

    indicators = Indicators(df)
    df_with_ind = indicators.add_all_indicators()

    # Check for NaN values at the end (should be filled usually, except specifically where lookback is needed)
    print("Columns:", df_with_ind.columns)
    print("Last row:\n", df_with_ind.tail(1).T)
    
    # Check specific logic
    if 'SMA_20' in df_with_ind.columns:
        print("SMA_20 calculation successful.")
    else:
        print("SMA_20 missing.")

if __name__ == "__main__":
    test_indicators()
