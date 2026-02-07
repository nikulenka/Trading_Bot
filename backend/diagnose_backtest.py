import pandas as pd
import os
import sys

# Add src to path
sys.path.append(os.path.abspath('src'))

from core.indicators import Indicators
from core.strategy import SignalAggregator
from core.backtest import Backtester

def test():
    try:
        # Load data (use 4h)
        data_path = '../data/BTCUSDT_4h.csv'
        if not os.path.exists(data_path):
            print(f"File not found: {data_path}")
            return
            
        df = pd.read_csv(data_path, index_col='timestamp', parse_dates=True)
        print("Data loaded.")
        
        # Indicators
        ind = Indicators(df)
        df = ind.add_all_indicators()
        print("Indicators added.")
        
        # Strategy
        agg = SignalAggregator(df)
        agg.calculate_unum_score()
        print("Strategy calculated.")
        
        # Backtest - Test Asian only
        print("\n--- Testing Asian Session Only ---")
        bt_asian = Backtester(df)
        _, metrics_asian = bt_asian.run_backtest(
            allowed_sessions=['asian']
        )
        print("Asian Metrics:", metrics_asian)
        
        # Backtest - Test all sessions
        print("\n--- Testing All Sessions ---")
        bt_all = Backtester(df)
        _, metrics_all = bt_all.run_backtest(
            allowed_sessions=None
        )
        print("All Metrics:", metrics_all)
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
