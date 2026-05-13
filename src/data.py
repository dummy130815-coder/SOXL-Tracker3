import yfinance as yf
import pandas as pd
import pytz
from tvDatafeed import TvDatafeed, Interval

def fetch_soxl_data(period="5d", interval="5m"):
    """
    SOXLの全セッション（通常・時間外・オーバーナイト）を取得し、統合する関数。
    """
    # 1. yfinanceから通常・時間外データを取得
    ticker = "SOXL"
    stock = yf.Ticker(ticker)
    df_yf = stock.history(period=period, interval=interval, prepost=True)
    
    if df_yf.empty:
        return df_yf
        
    # 米東部時間(EST/EDT)に変換してセッション判定
    eastern = pytz.timezone('US/Eastern')
    df_yf.index = df_yf.index.tz_convert(eastern)
    
    df_yf['Session'] = 'Unknown'
    hours = df_yf.index.hour
    minutes = df_yf.index.minute
    time_float = hours + minutes / 60.0
    
    pre_mask = (time_float >= 4.0) & (time_float < 9.5)
    reg_mask = (time_float >= 9.5) & (time_float < 16.0)
    aft_mask = (time_float >= 16.0) & (time_float < 20.0)
    
    df_yf.loc[pre_mask, 'Session'] = 'Pre-market'
    df_yf.loc[reg_mask, 'Session'] = 'Regular'
    df_yf.loc[aft_mask, 'Session'] = 'After-market'
    
    # 2. TradingView (BOATS) からオーバーナイトデータを取得
    try:
        # インターバルのマッピング
        tv_interval_map = {
            "1m": Interval.in_1_minute,
            "2m": Interval.in_3_minute, # TVに2mはないので3mで代用
            "5m": Interval.in_5_minute,
            "15m": Interval.in_15_minute,
            "30m": Interval.in_30_minute,
            "60m": Interval.in_1_hour,
            "1h": Interval.in_1_hour,
            "1d": Interval.in_daily
        }
        tv_interval = tv_interval_map.get(interval, Interval.in_5_minute)
        
        # 期間に応じた取得件数の目安
        period_days_map = {"1d": 1, "5d": 5, "10d": 10, "1mo": 30, "3mo": 90}
        days = period_days_map.get(period, 5)
        
        # 余裕を持ってバー数を設定
        if interval == "1m": n_bars = days * 1440
        elif interval == "5m": n_bars = days * 288
        elif interval == "1h" or interval == "60m": n_bars = days * 24
        else: n_bars = 1000
        
        tv = TvDatafeed()
        df_tv = tv.get_hist(symbol='SOXL', exchange='BOATS', interval=tv_interval, n_bars=n_bars)
        
        if df_tv is not None and not df_tv.empty:
            # TVデータのインデックスをJSTからUTC経由で変換（TVのnologinは通常ローカル時系列を返すが、ここでは一旦JSTと仮定）
            # もしUTCで返ってくる場合は tz_localize('UTC').tz_convert(eastern) になる
            # PoCの結果、システム時間(JST)と一致していたため、JSTとしてlocalize
            jst = pytz.timezone('Asia/Tokyo')
            df_tv.index = df_tv.index.tz_localize(jst).tz_convert(eastern)
            
            # 必要なカラムをyfinanceに合わせる
            df_tv = df_tv[['open', 'high', 'low', 'close', 'volume']].copy()
            df_tv.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df_tv['Session'] = 'Overnight'
            
            # yfinanceデータの開始時刻に合わせてフィルタリング（範囲を統一）
            start_time = df_yf.index.min()
            df_tv = df_tv[df_tv.index >= start_time]
            
            # yfinanceデータと統合
            combined_df = pd.concat([df_yf, df_tv])
            # インデックスの重複を除去し、時間順にソート
            df = combined_df[~combined_df.index.duplicated(keep='first')].sort_index()
        else:
            df = df_yf
    except Exception as e:
        print(f"TradingView data fetch failed: {e}")
        df = df_yf

    # 最終的にJSTに変換して返す
    jst = pytz.timezone('Asia/Tokyo')
    df.index = df.index.tz_convert(jst)
    df['Datetime'] = df.index
    
    return df
