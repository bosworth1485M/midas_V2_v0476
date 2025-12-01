import pandas as pd
import numpy as np
import pandas as pd
import numpy as np
import mplfinance as mpf
import requests
import sys
import os
from dotenv import load_dotenv
from pathlib import Path
from argparse import ArgumentParser

# --- bootstrap: ensure src on path + load .env from project root ---
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
try:
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")
# --- end bootstrap ---


def load_key() -> str:
    k = (os.environ.get("POLYGON_API_KEY") or "")
    k = k.strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set it in .env)", file=sys.stderr)
        sys.exit(1)
    return k


def fetch_polygon_data(ticker, date_str, timespan="minute", multiplier=1, api_key=None):
    date_dt = pd.to_datetime(date_str)
    start_timestamp = int(date_dt.timestamp() * 1000)
    end_timestamp = int((date_dt + pd.Timedelta(days=1)).timestamp() * 1000)

    print(f"Attempting to fetch {ticker} data for {date_str}...")

    if api_key:
        try:
            base_url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_timestamp}/{end_timestamp}"
            params = {"adjusted": "true", "sort": "asc", "limit": 50000}
            headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "midas_v2/1.0"}

            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('resultsCount', 0) > 0:
                df = pd.DataFrame(data['results'])
                df = df.rename(columns={'t': 'Date', 'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'})
                df['Date'] = pd.to_datetime(df['Date'], unit='ms', utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
                df = df.set_index('Date')
                print(f"Polygon Data Loaded: {len(df)} {timespan} bars found.")
                return df
            else:
                print(f"Polygon API returned no results for {ticker} on {date_str}.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Polygon API: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during API processing: {e}")

    # Fallback: mock data
    print("WARNING: Using MOCK DATA because the Polygon API key is missing or invalid.")
    market_open = pd.to_datetime(date_str + ' 09:30:00')
    market_close = pd.to_datetime(date_str + ' 16:00:00')
    if market_open.dayofweek >= 5:
        print("Mock data skipped (weekend detected).")
        return pd.DataFrame()

    date_index = pd.date_range(start=market_open, end=market_close, freq='T')
    date_dt = pd.to_datetime(date_str)
    np.random.seed(date_dt.day * 100)
    price_series = 150 + np.cumsum(np.random.normal(0, 0.5, len(date_index)))

    df = pd.DataFrame({
        'Open': price_series,
        'High': price_series + np.random.uniform(0.1, 0.5, len(date_index)),
        'Low': price_series - np.random.uniform(0.1, 0.5, len(date_index)),
        'Close': price_series + np.random.normal(0, 0.2, len(date_index)),
        'Volume': np.random.randint(100, 5000, len(date_index))
    }, index=date_index)
    df.index.name = 'Date'
    print(f"Mock Data Loaded: {len(df)} minutes of trading data.")
    return df


def calculate_indicators(df, rsi_window=14, bb_window=20, macd_fast=12, macd_slow=26, macd_signal=9, adx_window=14):
    df = df.copy()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']
    df['Cumulative_PV'] = df['PV'].cumsum()
    df['Cumulative_Volume'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cumulative_PV'] / df['Cumulative_Volume']
    df = df.drop(columns=['PV', 'Cumulative_PV', 'Cumulative_Volume'], errors='ignore')

    # Bollinger Bands
    df['BB_SMA'] = df['Close'].rolling(window=bb_window).mean()
    df['BB_STD'] = df['Close'].rolling(window=bb_window).std()
    df['BB_Upper'] = df['BB_SMA'] + (df['BB_STD'] * 2)
    df['BB_Lower'] = df['BB_SMA'] - (df['BB_STD'] * 2)

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=rsi_window - 1, min_periods=rsi_window).mean()
    avg_loss = loss.ewm(com=rsi_window - 1, min_periods=rsi_window).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    df['EMA_Fast'] = df['Close'].ewm(span=macd_fast, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=macd_slow, adjust=False).mean()
    df['MACD_Line'] = df['EMA_Fast'] - df['EMA_Slow']
    df['MACD_Signal'] = df['MACD_Line'].ewm(span=macd_signal, adjust=False).mean()
    df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']

    # ADX/DMI
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['+DM'] = np.where((df['High'] - df['High'].shift(1) > 0) & (df['High'] - df['High'].shift(1) > df['Low'].shift(1) - df['Low']), df['High'] - df['High'].shift(1), 0)
    df['-DM'] = np.where((df['Low'].shift(1) - df['Low'] > 0) & (df['Low'].shift(1) - df['Low'] > df['High'] - df['High'].shift(1)), df['Low'].shift(1) - df['Low'], 0)
    alpha = 1 / adx_window
    df['ATR'] = df['TR'].ewm(alpha=alpha, adjust=False).mean()
    df['+DMI'] = df['+DM'].ewm(alpha=alpha, adjust=False).mean()
    df['-DMI'] = df['-DM'].ewm(alpha=alpha, adjust=False).mean()
    df['+DI'] = (df['+DMI'] / df['ATR']) * 100
    df['+DI'] = df['+DI'].fillna(0)
    df['-DI'] = (df['-DMI'] / df['ATR']) * 100
    df['-DI'] = df['-DI'].fillna(0)
    df['DX'] = (abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])).replace([np.inf, -np.inf], 0).fillna(0) * 100
    df['ADX'] = df['DX'].ewm(alpha=alpha, adjust=False).mean()

    df = df.drop(columns=['H-L', 'H-PC', 'L-PC', 'TR', '+DM', '-DM', 'ATR', '+DMI', '-DMI', 'DX', 'EMA_Fast', 'EMA_Slow'], errors='ignore')

    return df


def plot_intraday_chart(df, ticker, time_range_str, out_path=None):
    """Generates a candlestick chart with indicators. Saves to file and/or displays on screen."""
    if df.empty:
        print("No data to plot.")
        return

    def _safe_make_addplot(ydata, **kwargs):
        try:
            arr = np.asarray(ydata)
        except Exception:
            return None
        if arr.size == 0 or not np.isfinite(arr).any():
            return None
        return mpf.make_addplot(ydata, **kwargs)

    vwap_plot = _safe_make_addplot(df.get('VWAP'), color='orange', linestyle='-')
    bb_plots = [
        _safe_make_addplot(df.get('BB_Upper'), color='gray', linestyle='--'),
        _safe_make_addplot(df.get('BB_Lower'), color='gray', linestyle='--'),
    ]

    rsi_plot = _safe_make_addplot(df.get('RSI'), panel=2, color='purple', ylabel='RSI', ylim=(0, 100))
    rsi_overbought = _safe_make_addplot([70] * len(df), panel=2, color='red', linestyle=':')
    rsi_oversold = _safe_make_addplot([30] * len(df), panel=2, color='green', linestyle=':')

    macd_line_plot = _safe_make_addplot(df.get('MACD_Line'), panel=3, color='blue', ylabel='MACD')
    macd_signal_plot = _safe_make_addplot(df.get('MACD_Signal'), panel=3, color='red', linestyle='--')
    macd_hist_plot = None
    if df.get('MACD_Hist') is not None and not df['MACD_Hist'].dropna().empty:
        colors = ['red' if h < 0 else 'green' for h in df['MACD_Hist'].fillna(0)]
        macd_hist_plot = _safe_make_addplot(df['MACD_Hist'], type='bar', panel=3, color=colors, alpha=0.6)

    adx_plot = _safe_make_addplot(df.get('ADX'), panel=4, color='gold', ylabel='ADX/DMI', ylim=(0, 100))
    plus_di_plot = _safe_make_addplot(df.get('+DI'), panel=4, color='green', linestyle='-')
    minus_di_plot = _safe_make_addplot(df.get('-DI'), panel=4, color='red', linestyle='-')
    adx_threshold = _safe_make_addplot([25] * len(df), panel=4, color='black', linestyle=':')

    apds = []
    for item in ([vwap_plot] + bb_plots + [rsi_plot, rsi_overbought, rsi_oversold,
                                          macd_line_plot, macd_signal_plot, macd_hist_plot,
                                          adx_plot, plus_di_plot, minus_di_plot, adx_threshold]):
        if item is not None:
            apds.append(item)

    # Always generate the figure with returnfig=True so we can both save and display
    # Don't use mplfinance title to avoid clipping issues
    fig, axes = mpf.plot(
        df,
        type='candle',
        style='yahoo',
        ylabel='Price ($)',
        volume=True,
        mav=(10, 30),
        addplot=apds,
        figratio=(12, 8),
        figscale=1.0,
        returnfig=True,
    )

    # Add title using matplotlib's suptitle which is more reliable for display
    import matplotlib.pyplot as plt
    fig.suptitle(f"{ticker} 1-Minute Candles - {time_range_str}\n(SMAs, BB, RSI, MACD, VWAP, ADX)", 
                 fontsize=14, fontweight='bold', y=0.98)

    # Save to file if requested
    if out_path:
        out_path_obj = Path(out_path)
        out_path_obj.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out_path_obj), dpi=100, bbox_inches='tight')
        print(f"Chart saved to {out_path_obj}")

    # Display to screen with proper layout
    fig.subplots_adjust(top=0.93)  # Add top margin for suptitle display
    plt.show()
    plt.close(fig)
    print("\n")


if __name__ == '__main__':
    # Load/validate key (bootstrap already loaded ROOT/.env)
    api_key = load_key()

    # Parse arguments
    parser = ArgumentParser(description="Generate intraday stock charts with technical indicators.")
    parser.add_argument('ticker', help='Stock ticker symbol (e.g., TSLA)')
    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('start_time', help='Start time in HH:MM format')
    parser.add_argument('end_time', help='End time in HH:MM format')
    parser.add_argument('--out', default=None, help='Output file path for saving chart (e.g., out/chart.png). If not specified, chart displays on screen.')
    
    args = parser.parse_args()
    target_ticker = args.ticker.upper()
    target_date = args.date
    start_time_str = args.start_time
    end_time_str = args.end_time
    out_file = args.out

    start_timestamp = f"{target_date} {start_time_str}:00"
    end_timestamp = f"{target_date} {end_time_str}:00"
    time_range_title = f"{target_date} {start_time_str} to {end_time_str}"

    intraday_data_full = fetch_polygon_data(target_ticker, target_date, api_key=api_key)

    if not intraday_data_full.empty:
        try:
            intraday_data = intraday_data_full.loc[start_timestamp:end_timestamp]
        except KeyError as e:
            print(f"Error: Time slicing failed. Check your time format (HH:MM) and ensure the range is valid. Error: {e}")
            sys.exit(1)

        if intraday_data.empty:
            print(f"Error: No data found in the specified range: {start_time_str} to {end_time_str}. Check market hours (9:30-16:00 EST) or date validity.")
            sys.exit(1)

        data_with_indicators = calculate_indicators(intraday_data)
        plot_intraday_chart(data_with_indicators, target_ticker, time_range_title, out_path=out_file)
        print(f"\nSuccessfully generated chart for {target_ticker} from {start_time_str} to {end_time_str}.")
    else:
        print(f"Could not process data for {target_ticker} on {target_date}. Please check the ticker, date, and if your POLYGON_API_KEY is correctly set in your .env file.")
    