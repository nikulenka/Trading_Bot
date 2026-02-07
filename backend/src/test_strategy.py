
import sys
import os
import pandas as pd


# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.indicators import Indicators
from src.core.strategy import SignalAggregator

def test_strategy():
    # Load 4h and 1h data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_4h_path = os.path.join(base_dir, 'data', 'BTCUSDT_4h.csv')
    data_1h_path = os.path.join(base_dir, 'data', 'BTCUSDT_1h.csv')
    
    if not os.path.exists(data_4h_path):
        print(f"Error: {data_4h_path} not found.")
        return

    df_4h = pd.read_csv(data_4h_path, index_col='timestamp', parse_dates=True)
    df_1h = pd.read_csv(data_1h_path, index_col='timestamp', parse_dates=True) if os.path.exists(data_1h_path) else None
    
    # Calculate Indicators
    print("Calculating indicators for 4h...")
    indicators_4h = Indicators(df_4h)
    df_4h = indicators_4h.add_all_indicators()
    
    if df_1h is not None:
        print("Calculating indicators for 1h...")
        indicators_1h = Indicators(df_1h)
        df_1h = indicators_1h.add_all_indicators()
    
    # Calculate Strategy
    print("Calculating Unum Score with MTC...")
    other_dfs = {'1h': df_1h} if df_1h is not None else {}
    strategy = SignalAggregator(df_4h, other_dfs=other_dfs)
    scores = strategy.calculate_unum_score()
    
    print(f"Market State: {strategy.state.value}")
    print("\nScore Distribution:")
    print(scores.describe())
    
    print("\nLast 10 Candles (with MTC):")
    cols = ['close', 'unum_score', 'sig_ma', 'sig_macd', 'ADX']
    print(df_4h[cols].tail(10))

if __name__ == "__main__":
    test_strategy()
