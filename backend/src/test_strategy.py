
import sys
import os
import pandas as pd


# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.indicators import Indicators
from src.core.strategy import SignalAggregator

def test_strategy():
    # Load 4h data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', 'BTCUSDT_4h.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path, index_col='timestamp', parse_dates=True)
    
    # Calculate Indicators
    print("Calculating indicators...")
    indicators = Indicators(df)
    df = indicators.add_all_indicators()
    
    # Calculate Strategy
    print("Calculating Unum Score...")
    strategy = SignalAggregator(df)
    scores = strategy.calculate_unum_score()
    
    print("Score Distribution:")
    print(scores.describe())
    
    print("\nLast 10 Candles:")
    cols = ['close', 'unum_score', 'sig_ma', 'sig_macd', 'OBV', 'RSI']
    print(df[cols].tail(10))

if __name__ == "__main__":
    test_strategy()
