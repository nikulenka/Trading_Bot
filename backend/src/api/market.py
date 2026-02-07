
from fastapi import APIRouter, HTTPException
import pandas as pd
import os
from ..core.indicators import Indicators
from ..core.strategy import SignalAggregator

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
        strategy = SignalAggregator(df)
        strategy.calculate_unum_score()
        
        # Limit to last 500 candles for performance
        df_recent = df.tail(500).reset_index()
        
        # Determine signals for chart plotting
        # Convert Timestamp to string for JSON serialization
        results = df_recent.to_dict(orient='records')
        
        # Process data to handle NaN values (replace with None for JSON)
        clean_results = []
        for row in results:
            clean_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
            clean_row['timestamp'] = getattr(row['timestamp'], 'isoformat', lambda: str(row['timestamp']))()
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
        indicators = Indicators(df)
        df = indicators.add_all_indicators()
        strategy = SignalAggregator(df)
        strategy.calculate_unum_score()
        
        latest = df.iloc[-1]
        
        return {
            "timestamp": latest.name.isoformat(),
            "unum_score": float(latest['unum_score']),
            "close": float(latest['close']),
            "rsi": float(latest['RSI']),
            "macd": float(latest['MACD']),
            "obv_trend": "Bullish" if latest['OBV'] > df['OBV'].rolling(20).mean().iloc[-1] else "Bearish"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
