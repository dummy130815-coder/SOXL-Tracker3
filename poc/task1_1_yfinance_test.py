import yfinance as yf
import pandas as pd

def test_yfinance_extended_hours():
    ticker = "SOXL"
    print(f"Fetching data for {ticker}...")
    
    # Fetch 1-minute data for the last 5 days, including pre/post market
    stock = yf.Ticker(ticker)
    df = stock.history(period="5d", interval="1m", prepost=True)
    
    if df.empty:
        print("Failed to fetch data or data is empty.")
        return

    # Convert timezone to EST/EDT for easier verification
    df.index = df.index.tz_convert('America/New_York')
    
    print(f"Total rows fetched: {len(df)}")
    print(f"Data spans from {df.index.min()} to {df.index.max()}")
    
    # Group by hours to see data distribution
    df['hour'] = df.index.hour
    hourly_counts = df.groupby('hour').size()
    
    # Handle potentially missing hours gracefully
    def get_sum(start, end):
        return sum(hourly_counts.get(h, 0) for h in range(start, end+1))
        
    print("\nData points per hour (EST):")
    print("Pre-market (4-9):", get_sum(4, 9))
    print("Regular hours (9-15):", get_sum(9, 15))
    print("After-market (16-19):", get_sum(16, 19))
    
    # Check if there is any data outside normal bounds (Overnight)
    overnight = get_sum(20, 23) + get_sum(0, 3)
    print("Overnight (20-4):", overnight)
    
    print("\nSample Data (First 5 rows):")
    print(df[['Open', 'Close', 'Volume']].head())
    
if __name__ == "__main__":
    test_yfinance_extended_hours()
