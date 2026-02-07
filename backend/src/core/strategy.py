
import pandas as pd
import numpy as np
from .indicators import Indicators

class SignalAggregator:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        # Weights based on "Mid-term" stability focus
        self.weights = {
            'trend': 0.40,
            'volume_levels': 0.40,
            'momentum': 0.20
        }
        
        # Sub-weights within categories
        self.sub_weights = {
            'trend': {
                'ma_alignment': 0.5, # 20% total
                'macd': 0.25,        # 10% total
                'aroon': 0.25        # 10% total
            },
            'volume_levels': {
                'fib_interaction': 0.4, # 16% total
                'obv_trend': 0.4,       # 16% total
                'atr_volatility': 0.2   # 8% total
            },
            'momentum': {
                'rsi': 0.5,          # 10% total
                'stoch': 0.25,       # 5% total
                'cci': 0.25          # 5% total
            }
        }

    def align_signals(self):
        """
        Calculates raw signals (-1, 0, 1) for each component.
        """
        # 1. Trend Signals
        self.df['sig_ma'] = self._calc_ma_signal()
        self.df['sig_macd'] = self._calc_macd_signal()
        self.df['sig_aroon'] = self._calc_aroon_signal()
        
        # 2. Volume & Levels
        self.df['sig_fib'] = self._calc_fib_signal()
        self.df['sig_obv'] = self._calc_obv_signal()
        self.df['sig_atr'] = self._calc_atr_signal() # Mostly likely a filter (0 or 1)
        
        # 3. Momentum
        self.df['sig_rsi'] = self._calc_rsi_signal()
        self.df['sig_stoch'] = self._calc_stoch_signal()
        self.df['sig_cci'] = self._calc_cci_signal()

    def calculate_unum_score(self):
        """
        Aggregates signals into a final 'Unum' score (-1.0 to +1.0).
        """
        self.align_signals()
        
        # Trend Score
        trend_score = (
            self.df['sig_ma'] * self.sub_weights['trend']['ma_alignment'] +
            self.df['sig_macd'] * self.sub_weights['trend']['macd'] +
            self.df['sig_aroon'] * self.sub_weights['trend']['aroon']
        )
        
        # Volume/Levels Score
        vol_score = (
            self.df['sig_fib'] * self.sub_weights['volume_levels']['fib_interaction'] +
            self.df['sig_obv'] * self.sub_weights['volume_levels']['obv_trend'] +
            self.df['sig_atr'] * self.sub_weights['volume_levels']['atr_volatility']
        )
        
        # Momentum Score
        mom_score = (
            self.df['sig_rsi'] * self.sub_weights['momentum']['rsi'] +
            self.df['sig_stoch'] * self.sub_weights['momentum']['stoch'] +
            self.df['sig_cci'] * self.sub_weights['momentum']['cci']
        )
        
        # Final Weighted Sum
        self.df['unum_score'] = (
            trend_score * self.weights['trend'] +
            vol_score * self.weights['volume_levels'] +
            mom_score * self.weights['momentum']
        )
        
        return self.df['unum_score']

    # --- Signal Calculation Helpers ---

    def _calc_ma_signal(self):
        # Bullish: Price > EMA_20 > EMA_50 > EMA_200
        # Bearish: Price < EMA_20 < EMA_50 < EMA_200
        # Using vectorized comparison
        c1 = (self.df['close'] > self.df['EMA_20']) & (self.df['EMA_20'] > self.df['EMA_50'])
        c2 = (self.df['close'] < self.df['EMA_20']) & (self.df['EMA_20'] < self.df['EMA_50'])
        return np.where(c1, 1, np.where(c2, -1, 0))

    def _calc_macd_signal(self):
        # Bullish: MACD Line > Signal Line (Histogram > 0)
        # Bearish: MACD Line < Signal Line
        return np.where(self.df['MACD_Hist'] > 0, 1, -1)

    def _calc_aroon_signal(self):
        # Bullish: Aroon Up > Aroon Down 
        return np.where(self.df['Aroon_Up'] > self.df['Aroon_Down'], 1, -1)

    def _calc_fib_signal(self):
        # Logic: If price bounces off a Fibonacci level?
        # For MVP: Check if price is above 0.5 Retracement (Bullish Zone) vs below (Bearish Zone) 
        # relative to the Roll_Max/Min range.
        mid_point = self.df['Fib_500']
        return np.where(self.df['close'] > mid_point, 1, -1)

    def _calc_obv_signal(self):
        # Logic: OBV Rising? Comparing to OBV SMA(20)
        obv_sma = self.df['OBV'].rolling(20).mean()
        return np.where(self.df['OBV'] > obv_sma, 1, -1)

    def _calc_atr_signal(self):
        # ATR is non-directional. Used here as a filter?
        # For now, return 0 (neutral) to not bias direction, 
        # OR implementation: Low volatility = 0, High volatility = 1 (trend confirmation).
        # Let's keep it neutral for now or use it to reduce position size (not implemented here).
        return np.zeros(len(self.df)) 

    def _calc_rsi_signal(self):
        # Bullish: 40 < RSI < 70 (Uptrend zone)
        # Bearish: 30 < RSI < 60 (Downtrend zone)
        # Overbought (>70) -> Potential reversal (-0.5?) or strong trend (1?)
        # For trend following: > 50 is bullish
        return np.where(self.df['RSI'] > 50, 1, -1)

    def _calc_stoch_signal(self):
        # Bullish: K > D
        return np.where(self.df['Stoch_K'] > self.df['Stoch_D'], 1, -1)

    def _calc_cci_signal(self):
        # Bullish: CCI > 0
        return np.where(self.df['CCI'] > 0, 1, -1)
