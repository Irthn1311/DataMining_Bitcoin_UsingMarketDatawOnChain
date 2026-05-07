import os
import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timezone


# =========================
# CONFIG
# =========================

START_DATE = "2015-01-01"
END_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OHLCV_FILE = os.path.join(OUTPUT_DIR, "btc_ohlcv_daily.csv")
ONCHAIN_FILE = os.path.join(OUTPUT_DIR, "btc_onchain_daily.csv")
EVENT_FILE = os.path.join(OUTPUT_DIR, "political_events.csv")
MERGED_FILE = os.path.join(OUTPUT_DIR, "btc_merged_event_daily.csv")


# =========================
# DATASET 1: BTC OHLCV
# =========================

def fetch_btc_ohlcv_yfinance(start_date=START_DATE, end_date=END_DATE):
    """
    Fetch Bitcoin OHLCV daily data from Yahoo Finance using yfinance.

    Output columns:
    date, open, high, low, close, adj_close, volume
    """
    print(f"[1/4] Fetching BTC OHLCV from {start_date} to {end_date}...")

    df = yf.download(
        "BTC-USD",
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        raise ValueError("Không lấy được dữ liệu OHLCV từ yfinance.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.reset_index()

    df = df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume"
    })

    df["date"] = pd.to_datetime(df["date"]).dt.date

    expected_cols = ["date", "open", "high", "low", "close", "adj_close", "volume"]
    df = df[expected_cols]

    numeric_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.sort_values("date").reset_index(drop=True)

    df.to_csv(OHLCV_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved: {OHLCV_FILE} | shape = {df.shape}")

    return df


# =========================
# DATASET 2A: COIN METRICS ON-CHAIN
# =========================

def fetch_coinmetrics_asset_metrics(
    start_date=START_DATE,
    end_date=END_DATE,
    metrics=None
):
    """
    Fetch Bitcoin on-chain metrics from Coin Metrics Community API.

    Bản này an toàn:
    - Fetch từng metric riêng.
    - Metric nào bị forbidden / unavailable thì bỏ qua.
    - Sau đó merge các metric fetch được theo date.
    """

    if metrics is None:
        metrics = [
            "PriceUSD",
            "AdrActCnt",
            "TxCnt",
            "HashRate",
            "FeeTotUSD",
            "DiffMean",
            "RevUSD",
            "SplyCur",
            "TxTfrValAdjUSD"
        ]

    rename_map = {
        "PriceUSD": "price_usd",
        "AdrActCnt": "active_addresses",
        "TxCnt": "tx_count",
        "HashRate": "hash_rate",
        "FeeTotUSD": "fee_usd",
        "DiffMean": "difficulty",
        "RevUSD": "miner_revenue_usd",
        "SplyCur": "supply_current",
        "TxTfrValAdjUSD": "transfer_value_adj_usd"
    }

    print(f"[2A] Fetching BTC on-chain metrics from Coin Metrics from {start_date} to {end_date}...")

    base_url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"

    metric_dfs = []
    failed_metrics = []

    for metric in metrics:
        print(f"  - Fetching Coin Metrics metric: {metric}")

        params = {
            "assets": "btc",
            "metrics": metric,
            "frequency": "1d",
            "start_time": start_date,
            "end_time": end_date,
            "page_size": 10000
        }

        all_rows = []
        next_url = base_url

        try:
            while next_url:
                if next_url == base_url:
                    response = requests.get(next_url, params=params, timeout=30)
                else:
                    response = requests.get(next_url, timeout=30)

                if response.status_code != 200:
                    print(f"    Skipped {metric}: HTTP {response.status_code}")
                    print(f"    Response: {response.text[:300]}")
                    failed_metrics.append(metric)
                    all_rows = []
                    break

                payload = response.json()
                rows = payload.get("data", [])
                all_rows.extend(rows)

                next_url = payload.get("next_page_url")
                time.sleep(0.2)

            if not all_rows:
                continue

            df_metric = pd.DataFrame(all_rows)

            if "time" not in df_metric.columns or metric not in df_metric.columns:
                print(f"    Skipped {metric}: response missing expected columns")
                failed_metrics.append(metric)
                continue

            df_metric["date"] = pd.to_datetime(df_metric["time"]).dt.date

            value_col = rename_map.get(metric, metric)
            df_metric = df_metric[["date", metric]].copy()
            df_metric = df_metric.rename(columns={metric: value_col})
            df_metric[value_col] = pd.to_numeric(df_metric[value_col], errors="coerce")

            metric_dfs.append(df_metric)

        except Exception as e:
            print(f"    Skipped {metric}: {e}")
            failed_metrics.append(metric)

    if not metric_dfs:
        raise ValueError("Không fetch được metric on-chain nào từ Coin Metrics.")

    df = metric_dfs[0]
    for df_metric in metric_dfs[1:]:
        df = df.merge(df_metric, on="date", how="outer")

    df = df.sort_values("date").reset_index(drop=True)

    if failed_metrics:
        print("")
        print("Các metric Coin Metrics bị bỏ qua vì không truy cập được hoặc lỗi API:")
        for m in sorted(set(failed_metrics)):
            print(f"  - {m}")

    print(f"Coin Metrics on-chain shape = {df.shape}")
    return df


# =========================
# DATASET 2B: BLOCKCHAIN.COM SUPPLEMENT
# =========================

def fetch_blockchain_chart(
    chart_name,
    start_date=START_DATE,
    end_date=END_DATE,
    timespan="all",
    rolling_average=None
):
    """
    Fetch dữ liệu chart từ Blockchain.com Charts API.

    sampled=false rất quan trọng:
    - Nếu không có sampled=false, Blockchain.com có thể trả dữ liệu bị lấy mẫu thưa.
    - Dữ liệu thưa sẽ gây rất nhiều NaN khi merge với OHLCV daily.
    """

    url = f"https://api.blockchain.info/charts/{chart_name}"

    params = {
        "timespan": timespan,
        "format": "json",
        "sampled": "false"
    }

    if rolling_average:
        params["rollingAverage"] = rolling_average

    try:
        response = requests.get(url, params=params, timeout=60)
    except Exception as e:
        print(f"    Blockchain.com chart skipped {chart_name}: {e}")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"    Blockchain.com chart skipped {chart_name}: HTTP {response.status_code}")
        print(f"    Response: {response.text[:300]}")
        return pd.DataFrame()

    payload = response.json()
    values = payload.get("values", [])

    if not values:
        print(f"    Blockchain.com chart empty: {chart_name}")
        return pd.DataFrame()

    df = pd.DataFrame(values)

    if "x" not in df.columns or "y" not in df.columns:
        print(f"    Blockchain.com chart skipped {chart_name}: missing x/y")
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["x"], unit="s").dt.date
    df[chart_name] = pd.to_numeric(df["y"], errors="coerce")

    df = df[["date", chart_name]]

    start_dt = pd.to_datetime(start_date).date()
    end_dt = pd.to_datetime(end_date).date()

    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)

    print(
        f"    {chart_name}: "
        f"{df['date'].min()} -> {df['date'].max()} | rows = {len(df)}"
    )

    return df

def make_daily_complete(df, value_cols, start_date=START_DATE, end_date=END_DATE):
    """
    Chuẩn hóa dataframe thành dữ liệu daily đầy đủ từ start_date đến end_date.

    Nếu Blockchain.com còn thiếu một vài ngày:
    - Reindex theo ngày.
    - Nội suy theo thời gian.
    - Forward fill / backward fill phần còn thiếu ở đầu/cuối.
    """

    if df.empty:
        return df

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.set_index("date").sort_index()

    full_index = pd.date_range(start=start_date, end=end_date, freq="D")
    df = df.reindex(full_index)

    for col in value_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].interpolate(method="time")
            df[col] = df[col].ffill().bfill()

    df = df.reset_index().rename(columns={"index": "date"})
    df["date"] = df["date"].dt.date

    return df

def fetch_blockchain_onchain_supplement(start_date=START_DATE, end_date=END_DATE):
    """
    Fetch các metric on-chain bổ sung từ Blockchain.com Charts API.

    Dùng để bổ sung:
    - fee_usd
    - difficulty
    - miner_revenue_usd
    - estimated_transaction_volume_usd
    """

    print(f"[2B] Fetching supplementary on-chain metrics from Blockchain.com from {start_date} to {end_date}...")

    chart_map = {
        "transaction-fees-usd": "fee_usd",
        "difficulty": "difficulty",
        "miners-revenue": "miner_revenue_usd",
        "estimated-transaction-volume-usd": "estimated_transaction_volume_usd"
    }

    dfs = []

    for chart_name, output_col in chart_map.items():
        print(f"  - Fetching Blockchain.com chart: {chart_name}")

        df_chart = fetch_blockchain_chart(
            chart_name=chart_name,
            start_date=start_date,
            end_date=end_date,
            timespan="all",
            rolling_average=None
        )

        if df_chart.empty:
            print(f"    Skipped empty chart: {chart_name}")
            continue

        df_chart = df_chart.rename(columns={chart_name: output_col})
        dfs.append(df_chart)

        time.sleep(0.2)

    if not dfs:
        print("Không fetch được metric bổ sung nào từ Blockchain.com.")
        return pd.DataFrame(columns=["date"])

    df = dfs[0]
    for other in dfs[1:]:
        df = df.merge(other, on="date", how="outer")

    df = df.sort_values("date").reset_index(drop=True)

    value_cols = [
        "fee_usd",
        "difficulty",
        "miner_revenue_usd",
        "estimated_transaction_volume_usd"
    ]

    df = make_daily_complete(
        df=df,
        value_cols=value_cols,
        start_date=start_date,
        end_date=end_date
    )

    print(f"Blockchain.com supplement after daily completion shape = {df.shape}")

    print("Blockchain.com supplement missing values:")
    print(df.isna().sum())

    return df


def build_onchain_dataset(start_date=START_DATE, end_date=END_DATE):
    """
    Build Dataset 2:
    - Fetch từ Coin Metrics.
    - Fetch bổ sung từ Blockchain.com.
    - Merge lại thành btc_onchain_daily.csv.
    """

    print("[2/4] Building BTC on-chain dataset...")

    df_cm = fetch_coinmetrics_asset_metrics(start_date=start_date, end_date=end_date)
    df_bc = fetch_blockchain_onchain_supplement(start_date=start_date, end_date=end_date)

    df_cm["date"] = pd.to_datetime(df_cm["date"]).dt.date

    if df_bc.empty:
        df_onchain = df_cm.copy()
    else:
        df_bc["date"] = pd.to_datetime(df_bc["date"]).dt.date

        df_onchain = df_cm.merge(
            df_bc,
            on="date",
            how="outer",
            suffixes=("", "_bc")
        )

        supplement_cols = [
            "fee_usd",
            "difficulty",
            "miner_revenue_usd",
            "estimated_transaction_volume_usd"
        ]

        for col in supplement_cols:
            bc_col = f"{col}_bc"

            if bc_col in df_onchain.columns:
                if col in df_onchain.columns:
                    df_onchain[col] = df_onchain[col].combine_first(df_onchain[bc_col])
                    df_onchain = df_onchain.drop(columns=[bc_col])
                else:
                    df_onchain = df_onchain.rename(columns={bc_col: col})

    df_onchain = df_onchain.sort_values("date").reset_index(drop=True)

    # Ép kiểu số
    for col in df_onchain.columns:
        if col != "date":
            df_onchain[col] = pd.to_numeric(df_onchain[col], errors="coerce")

    df_onchain.to_csv(ONCHAIN_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved: {ONCHAIN_FILE} | shape = {df_onchain.shape}")

    print("")
    print("On-chain columns:")
    for col in df_onchain.columns:
        print(f"- {col}")

    return df_onchain


# =========================
# DATASET 3A: POLITICAL EVENTS
# =========================

def create_political_events_template():
    """
    Tạo file sự kiện chính trị thủ công.

    Lưu ý:
    - Đây là template ban đầu.
    - Bạn nên kiểm tra lại ngày, tên sự kiện và thêm nguồn trước khi đưa vào báo cáo.
    - Có thể thêm cột source nếu muốn trích dẫn rõ.
    """

    print("[3/4] Creating political_events.csv template...")

    events = [
        {
            "date": "2016-06-23",
            "event_name": "Brexit referendum",
            "event_type": "Referendum",
            "region": "United Kingdom / Europe",
            "severity": "Medium"
        },
        {
            "date": "2016-11-08",
            "event_name": "US presidential election 2016",
            "event_type": "Election",
            "region": "United States",
            "severity": "Medium"
        },
        {
            "date": "2020-03-11",
            "event_name": "WHO declares COVID-19 a pandemic",
            "event_type": "Global crisis",
            "region": "Global",
            "severity": "High"
        },
        {
            "date": "2020-11-03",
            "event_name": "US presidential election 2020",
            "event_type": "Election",
            "region": "United States",
            "severity": "Medium"
        },
        {
            "date": "2021-05-19",
            "event_name": "China crypto crackdown market shock",
            "event_type": "Crypto regulation",
            "region": "China",
            "severity": "High"
        },
        {
            "date": "2022-02-24",
            "event_name": "Russia invades Ukraine",
            "event_type": "War/Conflict",
            "region": "Europe",
            "severity": "High"
        },
        {
            "date": "2022-11-11",
            "event_name": "FTX files for bankruptcy",
            "event_type": "Crypto market crisis",
            "region": "Global",
            "severity": "High"
        },
        {
            "date": "2023-03-10",
            "event_name": "Silicon Valley Bank collapse",
            "event_type": "Banking crisis",
            "region": "United States",
            "severity": "High"
        },
        {
            "date": "2023-10-07",
            "event_name": "Israel-Hamas war begins",
            "event_type": "War/Conflict",
            "region": "Middle East",
            "severity": "High"
        },
        {
            "date": "2024-01-10",
            "event_name": "US spot Bitcoin ETF approval",
            "event_type": "Crypto regulation / Finance",
            "region": "United States",
            "severity": "High"
        },
        {
            "date": "2024-04-19",
            "event_name": "Bitcoin halving 2024",
            "event_type": "Crypto protocol event",
            "region": "Global",
            "severity": "High"
        },
        {
            "date": "2024-11-05",
            "event_name": "US presidential election 2024",
            "event_type": "Election",
            "region": "United States",
            "severity": "Medium"
        }
    ]

    df_events = pd.DataFrame(events)
    df_events["date"] = pd.to_datetime(df_events["date"]).dt.date

    if os.path.exists(EVENT_FILE):
        print(f"File đã tồn tại, không ghi đè: {EVENT_FILE}")
        df_events = pd.read_csv(EVENT_FILE)
        df_events["date"] = pd.to_datetime(df_events["date"]).dt.date
    else:
        df_events.to_csv(EVENT_FILE, index=False, encoding="utf-8-sig")
        print(f"Saved: {EVENT_FILE} | shape = {df_events.shape}")

    return df_events


# =========================
# FEATURE ENGINEERING
# =========================

def add_ohlcv_features(df):
    """
    Tạo feature cho Dataset 1.
    """
    df = df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    df["return_1d"] = df["close"].pct_change(fill_method=None)
    df["return_7d"] = df["close"].pct_change(periods=7, fill_method=None)

    df["abs_return_1d"] = df["return_1d"].abs()

    df["volatility_7"] = df["return_1d"].rolling(window=7).std()

    df["volume_change"] = df["volume"].pct_change(fill_method=None)

    df["high_low_range"] = (df["high"] - df["low"]) / df["open"]

    df["ma_7"] = df["close"].rolling(window=7).mean()
    df["ma_30"] = df["close"].rolling(window=30).mean()
    df["ma_ratio"] = df["ma_7"] / df["ma_30"]

    return df


def add_onchain_features(df):
    """
    Tạo feature cho Dataset 2.
    Chỉ tạo pct_change cho những cột thực sự tồn tại.
    """
    df = df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    candidate_cols = [
        "price_usd",
        "active_addresses",
        "tx_count",
        "hash_rate",
        "difficulty",
        "fee_usd",
        "miner_revenue_usd",
        "supply_current",
        "transfer_value_adj_usd",
        "estimated_transaction_volume_usd"
    ]

    for col in candidate_cols:
        if col in df.columns:
            df[f"{col}_change"] = df[col].pct_change(fill_method=None)

    return df


def add_association_flags(df):
    """
    Tạo biến high/low để phục vụ Association Analysis.
    Biến high = 1 nếu giá trị nằm trên phân vị 75%.

    Chỉ tạo flag nếu cột có ít nhất 70% dữ liệu hợp lệ.
    """
    df = df.copy()

    flag_cols = [
        "volume_change",
        "abs_return_1d",
        "volatility_7",
        "high_low_range",
        "active_addresses_change",
        "tx_count_change",
        "fee_usd_change",
        "miner_revenue_usd_change",
        "hash_rate_change",
        "difficulty_change",
        "transfer_value_adj_usd_change",
        "estimated_transaction_volume_usd_change"
    ]

    for col in flag_cols:
        if col in df.columns:
            valid_ratio = df[col].notna().mean()

            if valid_ratio < 0.7:
                print(f"Skipped flag {col}: too many missing values ({valid_ratio:.2%} valid)")
                continue

            threshold = df[col].quantile(0.75)
            df[f"{col}_high"] = (df[col] >= threshold).astype(int)

    return df


def add_event_features(df, df_events, window_sizes=(3, 7, 14)):
    """
    Tạo event features:
    - event_today
    - event_window_3d
    - event_window_7d
    - event_window_14d
    - event_name, event_type, region, severity nếu đúng ngày event
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    df_events = df_events.copy()
    df_events["date"] = pd.to_datetime(df_events["date"])

    df["event_today"] = 0

    for w in window_sizes:
        df[f"event_window_{w}d"] = 0

    event_info = df_events[["date", "event_name", "event_type", "region", "severity"]].copy()

    df = df.merge(event_info, on="date", how="left")

    df["event_today"] = df["event_name"].notna().astype(int)

    for event_date in df_events["date"]:
        for w in window_sizes:
            mask = (
                (df["date"] >= event_date - pd.Timedelta(days=w)) &
                (df["date"] <= event_date + pd.Timedelta(days=w))
            )
            df.loc[mask, f"event_window_{w}d"] = 1

    for col in ["event_name", "event_type", "region", "severity"]:
        if col in df.columns:
            df[col] = df[col].fillna("None")

    df["date"] = df["date"].dt.date

    return df


# =========================
# DATASET 3: MERGE 1 + 2 + EVENTS
# =========================

def build_merged_dataset(df_ohlcv, df_onchain, df_events):
    """
    Gộp OHLCV + on-chain + political events.
    """
    print("[4/4] Building merged Dataset 3...")

    df_ohlcv = add_ohlcv_features(df_ohlcv)
    df_onchain = add_onchain_features(df_onchain)

    df_ohlcv["date"] = pd.to_datetime(df_ohlcv["date"]).dt.date
    df_onchain["date"] = pd.to_datetime(df_onchain["date"]).dt.date

    df = df_ohlcv.merge(df_onchain, on="date", how="inner")

    df = add_event_features(df, df_events, window_sizes=(3, 7, 14))
    df = add_association_flags(df)

    # Target classification mở rộng: ngày mai tăng hay không
    df["target_next_day_up"] = (df["close"].shift(-1) > df["close"]).astype(int)

    # Dòng cuối không có target tương lai
    if len(df) > 0:
        df.loc[df.index[-1], "target_next_day_up"] = np.nan

    df = df.sort_values("date").reset_index(drop=True)

    df.to_csv(MERGED_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved: {MERGED_FILE} | shape = {df.shape}")

    return df


# =========================
# MAIN
# =========================

def main():
    print("=====================================")
    print("FETCH BTC DATASETS FOR DATA MINING")
    print("=====================================")
    print(f"Start date: {START_DATE}")
    print(f"End date  : {END_DATE}")
    print("")

    df_ohlcv = fetch_btc_ohlcv_yfinance()
    df_onchain = build_onchain_dataset()
    df_events = create_political_events_template()

    df_merged = build_merged_dataset(df_ohlcv, df_onchain, df_events)

    print("")
    print("DONE.")
    print("Generated files:")
    print(f"- {OHLCV_FILE}")
    print(f"- {ONCHAIN_FILE}")
    print(f"- {EVENT_FILE}")
    print(f"- {MERGED_FILE}")

    print("")
    print("Preview merged dataset:")
    print(df_merged.head())

    print("")
    print("Merged dataset shape:")
    print(df_merged.shape)

    print("")
    print("Missing values summary:")
    print(df_merged.isna().sum().sort_values(ascending=False).head(40))

    print("")
    print("Columns:")
    for col in df_merged.columns:
        print(f"- {col}")


if __name__ == "__main__":
    main()