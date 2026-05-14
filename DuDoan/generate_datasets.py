import pandas as pd
import numpy as np
import os
import sys
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler
from hmmlearn.hmm import GaussianHMM

try:
    import hdbscan
    HAS_HDBSCAN = True
except ImportError:
    hdbscan = None
    HAS_HDBSCAN = False

# ==========================================================
# PART 1: ULTIMATE FEATURE EXTRACTION LOGIC
# ==========================================================

class StandaloneBTCFeatureEngineer:
    def _compute_research_states(self, df_raw):
        """
        Optimized logic from BTC_Advanced_State_Discovery.ipynb
        Uses a 10-feature matrix for higher-dimensional regime discovery.
        """
        df = df_raw.copy()
        
        # 1. Prepare 10-feature matrix as defined in notebook
        feat = pd.DataFrame(index=df.index)
        feat['ret'] = df['close'].pct_change()
        feat['log_ret'] = np.log(df['close'] / df['close'].shift(1))
        feat['volatility'] = feat['log_ret'].rolling(24).std() * np.sqrt(24)
        feat['momentum'] = df['close'].pct_change(periods=12)
        
        hl = df['high'] - df['low']
        hc = (df['high'] - df['close'].shift(1)).abs()
        lc = (df['low'] - df['close'].shift(1)).abs()
        feat['atr'] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
        
        feat['vol_change'] = df['volume'].pct_change()
        feat['vol_z'] = (df['volume'] - df['volume'].rolling(24).mean()) / (df['volume'].rolling(24).std() + 1e-9)
        
        # RSI
        delta = df['close'].diff()
        g = delta.where(delta > 0, 0).rolling(14).mean()
        l = (-delta.where(delta < 0, 0)).rolling(14).mean()
        feat['rsi'] = 100 - 100 / (1 + g / (l + 1e-9))
        
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        feat['macd'] = ema12 - ema26
        
        ma20 = df['close'].rolling(20).mean()
        std20 = df['close'].rolling(20).std()
        feat['bb_width'] = (2 * std20) / (ma20 + 1e-9)
        
        feature_cols = ['ret', 'log_ret', 'volatility', 'momentum', 'atr', 'vol_change', 'vol_z', 'rsi', 'macd', 'bb_width']
        feat = feat.dropna(subset=feature_cols)
        
        if feat.empty: return pd.DataFrame()
        
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(feat[feature_cols])
        
        results = pd.DataFrame(index=feat.index)
        
        # Best GMM: Tied covariance, K=3
        gmm = GaussianMixture(n_components=3, covariance_type='tied', random_state=42)
        results['state_gmm'] = gmm.fit_predict(X_scaled)
        probs = gmm.predict_proba(X_scaled)
        results['gmm_uncertainty'] = 1.0 - probs.max(axis=1)
        
        # HMM
        hmm_model = GaussianHMM(n_components=3, covariance_type="full", n_iter=100, random_state=42)
        results['state_hmm'] = hmm_model.fit(X_scaled).predict(X_scaled)

        # HDBSCAN for Outlier/Noise detection (Best params from notebook)
        if HAS_HDBSCAN:
            hdb = hdbscan.HDBSCAN(min_cluster_size=24, min_samples=12)
            results['state_hdb'] = hdb.fit_predict(X_scaled)
        else:
            results['state_hdb'] = -1

        # Sort States by Volatility (interpretation helper)
        for col in ['state_gmm', 'state_hmm']:
            vol_means = feat.join(results[col]).groupby(col)['volatility'].mean().sort_values()
            vol_map = vol_means.index
            mapping = {vol_map[i]: i for i in range(len(vol_map))}
            results[col] = results[col].map(mapping)
            
            # If GMM, also save the sorted probabilities
            if col == 'state_gmm':
                for i in range(3):
                    # original index of the i-th volatility regime
                    orig_idx = vol_map[i]
                    results[f'gmm_prob_{i}'] = probs[:, orig_idx]
            
        # Persistence Feature: How long has the current state lasted?
        for col in ['state_gmm', 'state_hmm']:
            s = results[col]
            results[f'{col}_duration'] = s.groupby((s != s.shift()).cumsum()).cumcount() + 1
            
        return results

    def compute_all_features(self, df_raw):
        df = df_raw.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        essential_cols = ['open', 'high', 'low', 'close', 'volume']
        df = df[essential_cols]
        
        print("   -> Computing Baseline & Research Volatility...")
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        df['rsi'] = self._calculate_rsi(df['close'], 14)
        
        # 1. Volatility Dynamics
        df['vol_std_24h'] = df['log_return'].rolling(24).std() * np.sqrt(24)
        df['vol_parkinson'] = np.sqrt(1 / (4 * np.log(2)) * (np.log(df['high'] / df['low'])**2))
        
        ma20 = df['close'].rolling(20).mean()
        std20 = df['close'].rolling(20).std()
        df['bb_width'] = (std20 * 4) / (ma20 + 1e-9)
        df['vol_ratio'] = df['log_return'].rolling(7).std() / (df['log_return'].rolling(30).std() + 1e-9)
        df['is_squeeze'] = (df['bb_width'] < df['bb_width'].rolling(100).quantile(0.2)).astype(int)
        
        # ATR (Average True Range) - Optimal from Volatility Dynamics notebook
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift(1)).abs()
        tr3 = (df['low'] - df['close'].shift(1)).abs()
        df['atr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
        
        # 2. Behavioral Mining
        vol_ma_long = df['volume'].rolling(168).mean()
        vol_std_long = df['volume'].rolling(168).std()
        df['vol_z'] = (df['volume'] - vol_ma_long) / (vol_std_long + 1e-9)
        df['rel_volume'] = df['volume'] / (vol_ma_long + 1e-9)
        
        std_window = df['log_return'].rolling(100).std()
        df['event_price_spike'] = (df['log_return'] > std_window * 2).astype(int)
        df['event_price_drop'] = (df['log_return'] < -std_window * 2).astype(int)
        df['event_vol_spike'] = (df['vol_z'] > 2.5).astype(int)

        # Advanced Behavioral Metrics (from research notebook)
        # a) Event Frequency (Density)
        df['event_density_24h'] = (df['event_price_spike'] + df['event_price_drop'] + df['event_vol_spike']).rolling(24).sum()
        
        # b) Time Since Last Event (Temporal Precursors)
        # Include RSI and Volatility events from research
        df['event_rsi_ob'] = (df['rsi'] > 70).astype(int)
        df['event_rsi_os'] = (df['rsi'] < 30).astype(int)
        df['event_high_vol'] = (df['vol_parkinson'] > df['vol_parkinson'].rolling(100).quantile(0.8)).astype(int)

        for col in ['event_price_spike', 'event_price_drop', 'event_vol_spike', 'is_squeeze', 'event_rsi_ob', 'event_rsi_os', 'event_high_vol']:
            event_occured = df[col] == 1
            df[f'hours_since_{col}'] = df.index.to_series().diff().dt.total_seconds().div(3600).fillna(0).where(~event_occured).groupby(event_occured.cumsum()).cumsum()

        # c) Sequence Patterns (e.g., Squeeze followed by Volatility Expansion)
        df['pattern_squeeze_breakout'] = ((df['is_squeeze'].shift(1) == 1) & (df['event_vol_spike'] == 1)).astype(int)

        # d) Composite Pre-Crash Score (Weights based on lead-time importance from notebook)
        # Squeeze (23h) and RSI OB (20h) are early warnings. High Vol (16h) is medium.
        df['pre_crash_score'] = (
            df['is_squeeze'] * 3.0 + 
            df['event_rsi_ob'] * 2.0 + 
            df['event_high_vol'] * 1.5 + 
            df['event_vol_spike'] * 2.0
        ).rolling(12).mean()

        # 3. Model Outputs (Advanced State Discovery)
        print("   -> Computing Advanced States (GMM/HMM/HDBSCAN)...")
        states = self._compute_research_states(df)
        df = df.join(states)

        # Lags & Momentum
        for i in [1, 2, 3, 6, 12, 24, 168]:
            df[f'return_lag_{i}h'] = df['log_return'].shift(i)
            
        df['momentum_24h'] = df['close'].pct_change(24)
        
        # Time features
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['target_log_return'] = df['log_return'].shift(-1)
        
        df = df.rename(columns={'close': 'price', 'volume': 'Volume'})
        df = df.loc[:, ~df.columns.duplicated()]
        
        return df.dropna()


    def _calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))


# ==========================================================
# PART 2: GENERATE 3 CLEAN DATASETS
# ==========================================================

RAW_DATA = 'D:/DataMining/sgu-2026-datamining-timeseries/Data/btc_ohlcv_1h.csv'
DATA_DIR = 'D:/DataMining/sgu-2026-datamining-timeseries/Data/'

def generate_all_datasets():
    print("Step 1: Reading raw data...")
    df = pd.read_csv(RAW_DATA, parse_dates=True, index_col=0)
    df = df[~df.index.duplicated(keep='last')].sort_index()
    
    print("Step 2: Generating all features (Research Integrated)...")
    engineer = StandaloneBTCFeatureEngineer()
    full_df = engineer.compute_all_features(df)
    
    # Define Column Groups for Clean Export
    common_cols = ['price', 'Volume', 'log_return', 'hour', 'day_of_week',
                   'return_lag_1h', 'return_lag_12h', 'return_lag_24h', 'return_lag_168h',
                   'momentum_24h', 'rsi']
    
    vol_cols = ['vol_std_24h', 'vol_parkinson', 'atr', 'bb_width', 'vol_ratio', 'is_squeeze']
    model_output_cols = ['state_gmm', 'state_hmm', 'state_hdb', 'gmm_uncertainty', 
                         'gmm_prob_0', 'gmm_prob_1', 'gmm_prob_2',
                         'state_gmm_duration', 'state_hmm_duration']
    
    beh_cols = ['rel_volume', 'event_density_24h', 'pattern_squeeze_breakout', 'pre_crash_score']
    
    target_col = ['target_log_return']
    
    print("Step 3: Exporting clean files for A/B Testing...")
    # 1. Volatility Focus
    full_df[common_cols + vol_cols + target_col].to_csv(os.path.join(DATA_DIR, 'btc_base_plus_volatility.csv'))
    
    # 2. Regimes/States Focus
    full_df[common_cols + model_output_cols + target_col].to_csv(os.path.join(DATA_DIR, 'btc_base_plus_regimes.csv'))
    
    # 3. Behavioral Focus
    full_df[common_cols + beh_cols + target_col].to_csv(os.path.join(DATA_DIR, 'btc_base_plus_behavioral.csv'))
    

    
    # 5. Pure Baseline
    full_df[common_cols + target_col].to_csv(os.path.join(DATA_DIR, 'btc_base.csv'))
    
    print(f"Success! 5 Clean files created in: {DATA_DIR}")

if __name__ == "__main__":
    generate_all_datasets()
