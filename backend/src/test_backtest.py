import pandas as pd
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.indicators import Indicators
from src.core.strategy import SignalAggregator
from src.core.backtest import Backtester

def test_backtest():
    # Load 4h data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', 'BTCUSDT_4h.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    print("Loading data...")
    df = pd.read_csv(data_path, index_col='timestamp', parse_dates=True)
    
    # Calculate Indicators
    print("Calculating indicators...")
    indicators = Indicators(df)
    df = indicators.add_all_indicators()
    
    # Calculate Strategy
    print("Calculating Unum Score...")
    strategy = SignalAggregator(df)
    strategy.calculate_unum_score()
    
    # Run Backtest
    print("Running Backtest...")
    bt = Backtester(df)
    results_df, metrics = bt.run_vectorized_backtest(long_threshold=0.6, short_threshold=-0.6)
    
    print("\n=== BACKTEST RESULTS (BTCUSDT 4H) ===")
    for k, v in metrics.items():
        print(f"{k.replace('_', ' ').title()}: {v}")
    
    print("\nEquity Curve Sample (Last 10):")
    print(results_df[['close', 'unum_score', 'equity_curve']].tail(10))

if __name__ == "__main__":
    test_backtest()
