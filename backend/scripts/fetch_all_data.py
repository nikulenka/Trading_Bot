
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import DataLoader

async def main():
    timeframes = ['1h', '2h', '4h']
    for tf in timeframes:
        print(f"Fetching/Verifying data for {tf}...")
        loader = DataLoader(timeframe=tf)
        df = await loader.fetch_data(years=4)
        if not df.empty:
            loader.save_data(df)
            print(f"[{tf}] Saved {len(df)} rows.")
        else:
            print(f"[{tf}] No data found.")

if __name__ == "__main__":
    asyncio.run(main())
