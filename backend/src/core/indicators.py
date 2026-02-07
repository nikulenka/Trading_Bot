
import pandas as pd
try:
    import pandas_ta as ta
except ImportError:
    ta = None
import ta as ta_lib
import numpy as np

class Indicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if not isinstance(self.df.index, pd.DatetimeIndex):
             self.df.index = pd.to_datetime(self.df.index)
        self.df.sort_index(inplace=True)

    def add_all_indicators(self):
        """
        Adds all requested indicators to the dataframe.
        """
        self.add_moving_averages()
        self.add_rsi()
        self.add_stoch()
        self.add_macd()
        self.add_obv()
        self.add_atr()
        self.add_aroon()
        self.add_cci()
        self.add_fibonacci_levels()
        return self.df

    def add_moving_averages(self, periods=[20, 50, 200]):
        """
        Adds SMA and EMA for specified periods.
        """
        for p in periods:
            self.df[f'SMA_{p}'] = ta_lib.trend.SMAIndicator(close=self.df['close'], window=p).sma_indicator()
            self.df[f'EMA_{p}'] = ta_lib.trend.EMAIndicator(close=self.df['close'], window=p).ema_indicator()
            # "MA" usually implies Simple or Weighted. We'll stick to SMA/EMA as primary.

    def add_rsi(self, period=14):
        self.df['RSI'] = ta_lib.momentum.RSIIndicator(close=self.df['close'], window=period).rsi()

    def add_stoch(self, k_window=14, d_window=3):
        stoch = ta_lib.momentum.StochasticOscillator(high=self.df['high'], low=self.df['low'], close=self.df['close'], window=k_window, smooth_window=d_window)
        self.df['Stoch_K'] = stoch.stoch()
        self.df['Stoch_D'] = stoch.stoch_signal()

    def add_macd(self, fast=12, slow=26, sign=9):
        macd = ta_lib.trend.MACD(close=self.df['close'], window_slow=slow, window_fast=fast, window_sign=sign)
        self.df['MACD'] = macd.macd()
        self.df['MACD_Signal'] = macd.macd_signal()
        self.df['MACD_Hist'] = macd.macd_diff()

    def add_obv(self):
        self.df['OBV'] = ta_lib.volume.OnBalanceVolumeIndicator(close=self.df['close'], volume=self.df['volume']).on_balance_volume()

    def add_atr(self, period=14):
        self.df['ATR'] = ta_lib.volatility.AverageTrueRange(high=self.df['high'], low=self.df['low'], close=self.df['close'], window=period).average_true_range()

    def add_aroon(self, period=25):
        aroon = ta_lib.trend.AroonIndicator(high=self.df['high'], low=self.df['low'], window=period)
        self.df['Aroon_Up'] = aroon.aroon_up()
        self.df['Aroon_Down'] = aroon.aroon_down()
        self.df['Aroon_Ind'] = aroon.aroon_indicator()

    def add_cci(self, period=20):
        self.df['CCI'] = ta_lib.trend.CCIIndicator(high=self.df['high'], low=self.df['low'], close=self.df['close'], window=period).cci()

    def add_fibonacci_levels(self, lookback_period=100):
        """
        Calculates Fibonacci levels based on high/low of the lookback period.
        Note: This is a rolling calculation, which might change over time.
        For fixed levels, we need to identify specific swing highs/lows.
        """
        # Rolling Max/Min for dynamic levels
        self.df['Roll_Max'] = self.df['high'].rolling(window=lookback_period).max()
        self.df['Roll_Min'] = self.df['low'].rolling(window=lookback_period).min()
        
        diff = self.df['Roll_Max'] - self.df['Roll_Min']
        
        self.df['Fib_0'] = self.df['Roll_Min']
        self.df['Fib_236'] = self.df['Roll_Min'] + diff * 0.236
        self.df['Fib_382'] = self.df['Roll_Min'] + diff * 0.382
        self.df['Fib_500'] = self.df['Roll_Min'] + diff * 0.5
        self.df['Fib_618'] = self.df['Roll_Min'] + diff * 0.618
        self.df['Fib_786'] = self.df['Roll_Min'] + diff * 0.786
        self.df['Fib_100'] = self.df['Roll_Max']

    def check_fib_interaction(self, tolerance=0.03):
        """
        Analyzes if current price is within tolerance of Fibonacci levels.
        Returns a signal or mask.
        """
        # TODO: Implement logic to detect "touches" or "bounces"
        pass
