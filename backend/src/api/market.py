
from fastapi import APIRouter, HTTPException
import pandas as pd
import os
from ..core.indicators import Indicators
from ..core.strategy import SignalAggregator
from ..core.backtest import Backtester

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")

def load_data(timeframe):
    filename = f"BTCUSDT_{timeframe}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Data for {timeframe} not found")
    
    df = pd.read_csv(filepath, index_col='timestamp', parse_dates=True)
    return df

@router.get("/market-data/{timeframe}")
async def get_market_data(timeframe: str):
    """
    Returns historical data with indicators and Unum score.
    """
    if timeframe not in ['1h', '2h', '4h']:
        raise HTTPException(status_code=400, detail="Invalid timeframe")
    
    try:
        df = load_data(timeframe)
        
        # Calculate Indicators
        indicators = Indicators(df)
        df = indicators.add_all_indicators()
        
        # Calculate Strategy Score
        other_dfs = {}
        if timeframe == '4h':
            # Load 1h for confirmation if available
            try:
                other_dfs['1h'] = load_data('1h')
            except:
                pass
                
        strategy = SignalAggregator(df, other_dfs=other_dfs)
        strategy.calculate_unum_score()
        market_state = strategy.state.value if hasattr(strategy, 'state') else "unknown"
        
        # Limit to last 500 candles for performance
        df_recent = df.tail(500).reset_index()
        
        # Add market state to the latest row
        results = df_recent.to_dict(orient='records')
        
        # Process data to handle NaN values (replace with None for JSON)
        clean_results = []
        for row in results:
            clean_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
            ts = row['timestamp']
            clean_row['timestamp'] = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
            clean_row['market_state'] = market_state
            clean_results.append(clean_row)
            
        return clean_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-signal")
async def get_latest_signal():
    """
    Returns the most recent Unum signal for 4h timeframe.
    """
    try:
        df = load_data('4h')
        other_dfs = {}
        try:
            other_dfs['1h'] = load_data('1h')
        except:
            pass
            
        indicators = Indicators(df)
        df = indicators.add_all_indicators()
        strategy = SignalAggregator(df, other_dfs=other_dfs)
        strategy.calculate_unum_score()
        
        latest = df.iloc[-1]
        
        return {
            "timestamp": latest.name.isoformat(),
            "unum_score": float(latest['unum_score']),
            "close": float(latest['close']),
            "rsi": float(latest['RSI']),
            "macd": float(latest['MACD']),
            "market_state": strategy.state.value,
            "obv_trend": "Bullish" if latest['OBV'] > df['OBV'].rolling(20).mean().iloc[-1] else "Bearish"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest")
async def run_backtest_endpoint(
    trend_w: float = 0.4,
    vol_w: float = 0.4,
    mom_w: float = 0.2,
    long_t: float = 0.6,
    short_t: float = -0.6,
    sl_pct: float = 0.015,
    tp_pct: float = 0.03,
    trailing_sl_pct: float = 0.015,
    skip_weekends: bool = True,
    sessions: str = None # Comma-separated: "asian,european"
):
    try:
        df = load_data("4h")
        indicators = Indicators(df)
        df = indicators.add_all_indicators()
        
        weights = {'trend': trend_w, 'volume_levels': vol_w, 'momentum': mom_w}
        aggregator = SignalAggregator(df, custom_weights=weights)
        aggregator.calculate_unum_score()
        
        allowed_sessions = sessions.split(",") if sessions else None
        
        backtester = Backtester(df)
        results_df, metrics = backtester.run_backtest(
            long_threshold=long_t,
            short_threshold=short_t,
            sl_pct=sl_pct,
            tp_pct=tp_pct,
            trailing_sl_pct=trailing_sl_pct,
            skip_weekends=skip_weekends,
            allowed_sessions=allowed_sessions
        )
        
        chart_data = results_df.tail(500).reset_index()
        chart_data['timestamp'] = chart_data['timestamp'].astype(str)
        
        return {
            "metrics": metrics,
            "chart_data": chart_data.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize")
async def run_optimization_endpoint(
    sl_pct: float = 0.015,
    tp_pct: float = 0.03,
    trailing_sl_pct: float = 0.015,
    skip_weekends: bool = True,
    sessions: str = None
):
    try:
        df_base = load_data("4h")
        indicators = Indicators(df_base)
        df_base = indicators.add_all_indicators()
        
        allowed_sessions = sessions.split(",") if sessions else None
        best_roi = -float('inf')
        best_weights = {}
        
        # Test weight combinations
        test_weights = [
            (0.4, 0.4, 0.2),
            (0.5, 0.3, 0.2),
            (0.3, 0.5, 0.2),
            (0.4, 0.2, 0.4),
            (0.2, 0.4, 0.4)
        ]
        
        for w_t, w_v, w_m in test_weights:
            df_run = df_base.copy()
            weights = {'trend': w_t, 'volume_levels': w_v, 'momentum': w_m}
            aggregator = SignalAggregator(df_run, custom_weights=weights)
            aggregator.calculate_unum_score()
            
            backtester = Backtester(df_run)
            _, metrics = backtester.run_backtest(
                sl_pct=sl_pct,
                tp_pct=tp_pct,
                trailing_sl_pct=trailing_sl_pct,
                skip_weekends=skip_weekends,
                allowed_sessions=allowed_sessions
            )
            
            if metrics['total_return_pct'] > best_roi:
                best_roi = metrics['total_return_pct']
                best_weights = weights
                
        return {
            "best_weights": best_weights,
            "best_roi": best_roi
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
