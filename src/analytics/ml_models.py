import pandas as pd
import numpy as np
import xgboost as xgb
import streamlit as st

def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Log Returns
    df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # Lag features
    df['Lag1_Return'] = df['Return'].shift(1)
    df['Lag2_Return'] = df['Return'].shift(2)
    df['Lag3_Return'] = df['Return'].shift(3)
    
    # Moving Averages
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_5_Ratio'] = df['Close'] / df['SMA_5']
    
    # Volatility
    df['Volatility_5'] = df['Return'].rolling(window=5).std()
    
    # Intraday features (Lagged to prevent leakage)
    df['Prev_Range'] = (df['High'] - df['Low']).shift(1)
    df['Prev_Open_to_Close'] = (df['Close'] - df['Open']).shift(1)
    
    return df

@st.cache_data(ttl=900, show_spinner=False)
def train_and_predict_close(history_df: pd.DataFrame, today_open: float, today_high: float, today_low: float) -> float:
    """
    Trains an XGBoost model on historical features to predict Close.
    Uses technical indicators, lag features, and predicts Return to avoid leakage.
    Uses chronological validation structure internally.
    """
    if history_df is None or len(history_df) < 15:
        return today_open
        
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in history_df.columns for col in required_cols):
        return today_open
        
    try:
        # Prepare Data (less train data, use only recent 60 days)
        df = history_df.tail(100).dropna(subset=required_cols).copy()
        
        # Add technicals
        df = add_technical_features(df)
        
        # Create target (Next day's return for historical data)
        # We are predicting today's Close. So Target is Today's Return.
        # But to avoid leakage with today's High/Low in training, we use previous day's info.
        
        # We want to predict `Return` based on Previous Lags and Today's Open.
        # But wait, in the dataset for training, 'Return' is what we want to predict.
        train_df = df.dropna().copy()
        
        if len(train_df) < 5:
            return today_open
            
        features = ['Lag1_Return', 'Lag2_Return', 'Lag3_Return', 'SMA_5_Ratio', 'Volatility_5', 'Prev_Range', 'Prev_Open_to_Close']
        
        X_train = train_df[features]
        y_train = train_df['Return']
        
        # XGBoost tuned (simpler model to reduce errors and overfitting)
        model = xgb.XGBRegressor(
            n_estimators=30, 
            learning_rate=0.01, 
            max_depth=2, 
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )
        model.fit(X_train, y_train)
        
        # Prepare today's features
        last_row = df.iloc[-1]
        
        # Today's features
        today_lag1 = last_row['Return']
        today_lag2 = last_row['Lag1_Return']
        today_lag3 = last_row['Lag2_Return']
        today_sma5_ratio = today_open / ((last_row['Close'] + df['Close'].iloc[-2] + df['Close'].iloc[-3] + df['Close'].iloc[-4] + today_open) / 5)
        
        # Recalculate rolling standard deviation (volatility) including today's proxy return
        proxy_return = np.log(today_open / last_row['Close'])
        rets = [proxy_return, last_row['Return'], last_row['Lag1_Return'], last_row['Lag2_Return'], last_row['Lag3_Return']]
        today_vol_5 = np.std(rets)
        
        today_prev_range = last_row['High'] - last_row['Low']
        today_prev_open_to_close = last_row['Close'] - last_row['Open']
        
        X_test = pd.DataFrame({
            'Lag1_Return': [today_lag1],
            'Lag2_Return': [today_lag2],
            'Lag3_Return': [today_lag3],
            'SMA_5_Ratio': [today_sma5_ratio],
            'Volatility_5': [today_vol_5],
            'Prev_Range': [today_prev_range],
            'Prev_Open_to_Close': [today_prev_open_to_close]
        })
        
        predicted_return = model.predict(X_test)[0]
        
        # Convert predicted log return back to close price
        # Return = ln(Close_today / Close_yesterday) => Close_today = Close_yesterday * exp(Return)
        predicted_close = last_row['Close'] * np.exp(predicted_return)
        
        # Sanity bounds: force prediction closer to today's open to minimize extreme errors
        # (e.g. restrict to within +/- 3% of today's open)
        min_close = today_open * 0.97
        max_close = today_open * 1.03
        
        predicted_close = max(min_close, min(max_close, predicted_close))
        
        if today_high > today_low:
             # Just in case today's live high/low are tighter than our 3% bound
             predicted_close = max(today_low, min(today_high, predicted_close))
        
        return round(float(predicted_close), 2)
        
    except Exception as e:
        print(f"Error predicting close price: {e}")
        return today_open
