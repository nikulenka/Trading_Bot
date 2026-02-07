import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, df: pd.DataFrame, initial_balance=10000, fee=0.001):
        """
        initial_balance: Starting USD
        fee: 0.1% = 0.001
        """
        self.df = df.copy()
        self.initial_balance = initial_balance
        self.fee = fee
        
    def run_backtest(self, long_threshold=0.6, short_threshold=-0.6, 
                     sl_pct=0.02, tp_pct=0.04, trailing_sl_pct=0.015, 
                     skip_weekends=True, allowed_sessions=None):
        """
        Simulates trading with SL/TP, Trailing Stop, and Session Filtering.
        allowed_sessions: list of session names ['asian', 'european', 'american'] or None (all)
        """
        df = self.df
        df['signal'] = 0
        df['market_returns'] = df['close'].pct_change()
        
        # 1. Identification (UTC)
        # Asian: 00-09, European: 07-16, American: 13-22
        df['hour'] = df.index.hour
        df['is_asian'] = (df['hour'] >= 0) & (df['hour'] < 9)
        df['is_european'] = (df['hour'] >= 7) & (df['hour'] < 16)
        df['is_american'] = (df['hour'] >= 13) & (df['hour'] < 22)
        
        # Calculate session mask
        if allowed_sessions:
            session_mask = pd.Series(False, index=df.index)
            if 'asian' in allowed_sessions: session_mask |= df['is_asian']
            if 'european' in allowed_sessions: session_mask |= df['is_european']
            if 'american' in allowed_sessions: session_mask |= df['is_american']
            df['in_session'] = session_mask
        else:
            df['in_session'] = True

        # Weekend filter (5=Sat, 6=Sun)
        if skip_weekends:
            df['is_weekend'] = df.index.dayofweek >= 5
        else:
            df['is_weekend'] = False

        balance = self.initial_balance
        position = 0 # 1 for Long, -1 for Short, 0 for None
        entry_price = 0
        peak_price = 0
        equity_curve = [] 
        trades_count = 0
        signals = [0] * len(df)
        
        # Pre-calculate for efficiency
        scores = df['unum_score'].values
        prices = df['close'].values
        weekends = df['is_weekend'].values
        in_sessions = df['in_session'].values
        
        for i in range(1, len(df)):
            # Update Equity Curve based on price movement
            curr_equity = balance
            if position == 1:
                curr_equity = (prices[i] / entry_price) * balance * (1 - self.fee)
            elif position == -1:
                curr_equity = (2 - (prices[i] / entry_price)) * balance * (1 - self.fee)
            
            # 1. Exit Logic (SL / TP / Trailing Stop) - Exits are ALWAYS active once in trade
            exit_triggered = False
            if position != 0:
                if position == 1:
                    peak_price = max(peak_price, prices[i])
                    if (prices[i] <= entry_price * (1 - sl_pct)) or \
                       (prices[i] >= entry_price * (1 + tp_pct)) or \
                       (prices[i] <= peak_price * (1 - trailing_sl_pct)):
                        exit_triggered = True
                elif position == -1:
                    peak_price = min(peak_price, prices[i])
                    if (prices[i] >= entry_price * (1 + sl_pct)) or \
                       (prices[i] <= entry_price * (1 - tp_pct)) or \
                       (prices[i] >= peak_price * (1 + trailing_sl_pct)):
                        exit_triggered = True

            if exit_triggered:
                balance = curr_equity * (1 - self.fee)
                position = 0
                trades_count += 1
            
            # 2. Entry Logic (Only if not in position, not weekend, and IN ALLOWED SESSION)
            if position == 0 and not weekends[i] and in_sessions[i]:
                if scores[i] > long_threshold:
                    position = 1
                    entry_price = prices[i]
                    peak_price = prices[i]
                    balance = balance * (1 - self.fee)
                    trades_count += 1
                elif scores[i] < short_threshold:
                    position = -1
                    entry_price = prices[i]
                    peak_price = prices[i]
                    balance = balance * (1 - self.fee)
                    trades_count += 1
            
            equity_curve.append(curr_equity)
            signals[i] = position
            
        df['equity_curve'] = [self.initial_balance] + equity_curve
        df['signal'] = signals
        df['strategy_returns'] = df['equity_curve'].pct_change().fillna(0)
        df['cum_strategy_returns'] = df['equity_curve'] / self.initial_balance
        df['cum_market_returns'] = (1 + df['market_returns'].fillna(0)).cumprod()
        df['trades_count_total'] = trades_count
        
        return self.calculate_metrics(df, trades_count)

    def calculate_metrics(self, df, trades_count=0):
        """
        Calculates performance KPIs.
        """
        total_return = (df['cum_strategy_returns'].iloc[-1] - 1) * 100
        buy_hold_return = (df['cum_market_returns'].iloc[-1] - 1) * 100
        
        # Win Rate (Simplified: bars where we are in position and strategy_returns > 0)
        active_bars = df[df['signal'] != 0]
        win_rate = (active_bars['strategy_returns'] > 0).sum() / len(active_bars) * 100 if len(active_bars) > 0 else 0
        
        # Drawdown
        df['peak'] = df['equity_curve'].cummax()
        df['drawdown'] = (df['equity_curve'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min() * 100
        
        # Sharpe Ratio (Rough estimate using candle frequency)
        # Note: Risk-free rate assumed 0
        returns = df['strategy_returns'].dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 6) if returns.std() != 0 else 0 # Adjust for 4h candles
        
        metrics = {
            "total_return_pct": round(total_return, 2),
            "buy_hold_return_pct": round(buy_hold_return, 2),
            "win_rate_pct": round(win_rate, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "final_balance": round(df['equity_curve'].iloc[-1], 2),
            "total_trades": int(trades_count)
        }
        
        return df, metrics
