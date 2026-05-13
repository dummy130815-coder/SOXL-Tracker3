from tvDatafeed import TvDatafeed, Interval
import pandas as pd

def test_boats_data():
    # tvDatafeedの初期化（匿名ログイン）
    tv = TvDatafeed()
    
    print("Fetching BOATS:SOXL from TradingView...")
    # BOATS:SOXL の 5分足を直近100件取得
    df = tv.get_hist(symbol='SOXL', exchange='BOATS', interval=Interval.in_5_minute, n_bars=100)
    
    if df is None or df.empty:
        print("Failed to fetch BOATS data.")
        return
        
    print(f"Fetched {len(df)} rows.")
    # インデックスをプリントして時間帯を確認
    print("\nTail of data:")
    print(df.tail())
    
    # 時間帯の確認（TVデータは通常UTCまたは市場現地時間）
    print(f"\nStart: {df.index.min()}")
    print(f"End:   {df.index.max()}")

if __name__ == "__main__":
    test_boats_data()
