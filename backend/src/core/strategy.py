
import pandas as pd
import numpy as np
from .indicators import Indicators

from enum import Enum

class MarketState(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    UNCERTAIN = "uncertain"

class SignalAggregator:
    def __init__(self, df: pd.DataFrame, other_dfs: dict = None, custom_weights: dict = None):
        self.df = df
        self.other_dfs = other_dfs or {} # Expected: {'1h': df, '2h': df}
        self.state = MarketState.UNCERTAIN
        
        # Default Weights
        self.weights = {
            'trend': 0.40,
            'volume_levels': 0.40,
            'momentum': 0.20
        }
        
        # Merge custom weights if provided
        if custom_weights:
            self.weights.update(custom_weights)
            # Ensure they sum to 1? Or just use as is. 
            # We'll normalize if they don't, but for now we expect raw inputs.
        
        # Sub-weights within categories
        self.sub_weights = {
            'trend': {
                'ma_alignment': 0.4, 
                'macd': 0.3,        
                'aroon': 0.3        
            },
            'volume_levels': {
                'fib_interaction': 0.5, 
                'obv_trend': 0.3,       
                'atr_volatility': 0.2   
            },
            'momentum': {
                'rsi': 0.4,          
                'stoch': 0.3,       
                'cci': 0.3          
            }
        }

    def detect_market_state(self):
        """
        Determines if the market is trending or ranging using ADX and MA slope.
        """
        if 'ADX' not in self.df.columns:
            return MarketState.UNCERTAIN

        latest_adx = self.df['ADX'].iloc[-1]
        
        if latest_adx > 25:
            self.state = MarketState.TRENDING
            # In Trending: Priortize Trend and Volume
            self.weights = {'trend': 0.50, 'volume_levels': 0.35, 'momentum': 0.15}
        elif latest_adx < 20:
            self.state = MarketState.RANGING
            # In Ranging: Prioritize Oscillators and Levels
            self.weights = {'trend': 0.20, 'volume_levels': 0.40, 'momentum': 0.40}
        else:
            self.state = MarketState.UNCERTAIN
            self.weights = {'trend': 0.33, 'volume_levels': 0.33, 'momentum': 0.34}
            
        return self.state

    def confirm_signal_mtf(self, score_series):
        """
        Adjusts the score based on confirmation from other timeframes.
        If we have 1h data, check the latest trend on 1h.
        """
        if not self.other_dfs or '1h' not in self.other_dfs:
            return score_series
            
        df1 = self.other_dfs['1h']
        # Simple confirmation: 1h trend direction
        # Bullish if close > EMA_50 on 1h
        ema_50_1h = df1['close'].rolling(50).mean()
        latest_1h_trend = 1 if df1['close'].iloc[-1] > ema_50_1h.iloc[-1] else -1
        
        # If 4h score and 1h trend disagree, dampen the score.
        current_4h_dir = np.sign(score_series.iloc[-1])
        if current_4h_dir != latest_1h_trend:
            # Dampen the last value (and ideally the whole series if we had full alignment, 
            # but for MVP we focus on the current signal)
            score_series.iloc[-1] *= 0.5
                
        return score_series

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

    def calculate_unum_score(self, apply_state_weights=True):
        """
        Aggregates signals into a final 'Unum' score (-1.0 to +1.0).
        """
        if apply_state_weights:
            self.detect_market_state() # Update weights based on current state
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
        raw_score = (
            trend_score * self.weights['trend'] +
            vol_score * self.weights['volume_levels'] +
            mom_score * self.weights['momentum']
        )
        
        # --- PHASE 5: Noise Reduction Filters ---
        
        # 1. Stricter Trend Strength (ADX)
        # If ADX < 22, the trend is too weak. Neutralize or heavily dampen.
        adx_filter = np.where(self.df['ADX'] > 22, 1.0, 0.2)
        
        # 2. Volume Spike Confirmation
        # Check if volume is 20% higher than SMA(20)
        vol_spike = np.where(self.df['volume'] > self.df['VOL_SMA'] * 1.2, 1.0, 0.5)
        
        # 3. Volatility Normalization (refined ATR filter)
        vol_dampener = self.df['sig_atr']
        
        # Combine filters
        score_series = raw_score * adx_filter * vol_spike * vol_dampener
        
        # 4. Signal Persistence (Dampen if signal just flipped)
        # Requirement: Current sign matches previous sign
        prev_score = score_series.shift(1).fillna(0)
        persistence = np.where(np.sign(score_series) == np.sign(prev_score), 1.0, 0.5)
        score_series = score_series * persistence
        
        # Multi-Timeframe Confirmation (MTC)
        self.df['unum_score'] = self.confirm_signal_mtf(score_series)
        
        return self.df['unum_score']

    # --- Signal Calculation Helpers ---

    def _calc_ma_signal(self):
        # Bullish: Price > EMA_20 > EMA_50 > EMA_200
        # Bearish: Price < EMA_20 < EMA_50 < EMA_200
        c1 = (self.df['close'] > self.df['EMA_20']) & (self.df['EMA_20'] > self.df['EMA_50'])
        c2 = (self.df['close'] < self.df['EMA_20']) & (self.df['EMA_20'] < self.df['EMA_50'])
        return np.where(c1, 1, np.where(c2, -1, 0))

    def _calc_macd_signal(self):
        return np.where(self.df['MACD_Hist'] > 0, 1, -1)

    def _calc_aroon_signal(self):
        return np.where(self.df['Aroon_Up'] > self.df['Aroon_Down'], 1, -1)

    def _calc_fib_signal(self):
        """
        Advanced logic: Detect bounces off key Fib levels (0.382, 0.5, 0.618).
        """
        lookback = 3
        # Tolerance: 0.5% of price
        tolerance = self.df['close'] * 0.005
        
        # Bullish bounce: Low within tolerance of level, Close > Level
        fib_levels = ['Fib_382', 'Fib_500', 'Fib_618']
        bull_signal = np.zeros(len(self.df))
        bear_signal = np.zeros(len(self.df))
        
        for level in fib_levels:
            # Price touched level from above and bounced
            touched = (self.df['low'] <= self.df[level] + tolerance) & (self.df['low'] >= self.df[level] - tolerance)
            bounced = (self.df['close'] > self.df[level])
            bull_signal = np.where(touched & bounced, 1, bull_signal)
            
            # Price touched level from below and rejected
            touched_upper = (self.df['high'] >= self.df[level] - tolerance) & (self.df['high'] <= self.df[level] + tolerance)
            rejected = (self.df['close'] < self.df[level])
            bear_signal = np.where(touched_upper & rejected, -1, bear_signal)
            
        # If no bounce, return trend direction relative to middle
        combined = np.where(bull_signal != 0, bull_signal, bear_signal)
        return np.where(combined != 0, combined, np.where(self.df['close'] > self.df['Fib_500'], 0.5, -0.5))

    def _calc_obv_signal(self):
        obv_sma = self.df['OBV'].rolling(20).mean()
        return np.where(self.df['OBV'] > obv_sma, 1, -1)

    def _calc_atr_signal(self):
        """
        Volatility dampener (0.3 to 1.0).
        If ATR is low relative to moving average (50), dampen the score.
        """
        atr_sma = self.df['ATR'].rolling(window=50).mean()
        # Relative Volatility
        rel_vol = self.df['ATR'] / atr_sma
        # Clamp between 0.3 (dead) and 1.0 (active)
        return np.clip(rel_vol, 0.3, 1.0)

    def _calc_rsi_signal(self):
        return np.where(self.df['RSI'] > 50, 1, -1)

    def _calc_stoch_signal(self):
        return np.where(self.df['Stoch_K'] > self.df['Stoch_D'], 1, -1)

    def _calc_cci_signal(self):
        return np.where(self.df['CCI'] > 0, 1, -1)
