
import ccxt.async_support as ccxt
import pandas as pd
import asyncio
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

class DataLoader:
    def __init__(self, exchange_id='binance', symbol='BTC/USDT', timeframe='4h'):
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True})
        os.makedirs(DATA_DIR, exist_ok=True)


    async def fetch_data(self, limit=1000, since=None, years=4):
        """
        Fetch OHLCV data from exchange with pagination.
        """
        try:
            # Calculate start time if 'since' is not provided
            if since is None:
                since = self.exchange.milliseconds() - (years * 365 * 24 * 60 * 60 * 1000)
            
            all_ohlcv = []
            current_since = since
            now = self.exchange.milliseconds()
            
            logger.info(f"Fetching {self.timeframe} data for {self.symbol} starting from {datetime.fromtimestamp(current_since/1000)}...")
            
            while current_since < now:
                ohlcv = await self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=current_since, limit=limit)
                if not ohlcv:
                    break
                
                all_ohlcv.extend(ohlcv)
                current_since = ohlcv[-1][0] + 1 # Move to next timestamp
                
                # Rate limit sleep (basic)
                await asyncio.sleep(self.exchange.rateLimit / 1000)
                
                if len(ohlcv) < limit: # Reached end of data
                    break

            if not all_ohlcv:
                logger.warning("No data returned from exchange.")
                return pd.DataFrame()

            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Remove duplicates just in case
            df = df[~df.index.duplicated(keep='first')]
            
            logger.info(f"Fetched {len(df)} rows for {self.timeframe}.")
            return df
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()
        finally:
            await self.exchange.close()

    def save_data(self, df: pd.DataFrame, filename: str = None):
        if filename is None:
            filename = f"{self.symbol.replace('/', '')}_{self.timeframe}.csv"
        filepath = os.path.join(DATA_DIR, filename)
        df.to_csv(filepath)
        logger.info(f"Data saved to {filepath}")

async def main():
    timeframes = ['4h', '2h', '1h']
    for tf in timeframes:
        loader = DataLoader(timeframe=tf)
        df = await loader.fetch_data(years=4)
        if not df.empty:
            loader.save_data(df)
            print(f"[{tf}] Head: {df.index[0]}, Tail: {df.index[-1]}, Count: {len(df)}")

if __name__ == "__main__":
    asyncio.run(main())
