import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import numpy as np
import streamlit as st

@st.cache_data(ttl=900, show_spinner=False)
def train_and_predict_close(history_df: pd.DataFrame, today_open: float, today_high: float, today_low: float) -> float:
    """
    Trains a GradientBoostingRegressor model on historical features to predict Close.
    Uses the provided today_open, today_high, today_low to predict today's closing price.
    Caches the result to prevent slow re-training on every UI interaction.
    """
    if history_df is None or len(history_df) < 5:
        return today_open
        
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in history_df.columns for col in required_cols):
        return today_open
        
    try:
        train_df = history_df.dropna(subset=required_cols).copy()
        
        if len(train_df) < 5:
            return today_open
            
        # Feature engineering for better accuracy
        train_df['Range'] = train_df['High'] - train_df['Low']
        train_df['Open_to_Low'] = train_df['Open'] - train_df['Low']
        train_df['High_to_Open'] = train_df['High'] - train_df['Open']
            
        X_train = train_df[['Open', 'High', 'Low', 'Range', 'Open_to_Low', 'High_to_Open']]
        y_train = train_df['Close']
        
        # GradientBoostingRegressor is generally more accurate than simple LinearRegression
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        
        # Prepare today's features
        today_range = today_high - today_low
        today_open_to_low = today_open - today_low
        today_high_to_open = today_high - today_open
        
        X_test = pd.DataFrame({
            'Open': [today_open],
            'High': [today_high],
            'Low': [today_low],
            'Range': [today_range],
            'Open_to_Low': [today_open_to_low],
            'High_to_Open': [today_high_to_open]
        })
        
        predicted_close = model.predict(X_test)[0]
        
        # Sanity bounds
        predicted_close = max(today_low, min(today_high, predicted_close))
        
        return round(float(predicted_close), 2)
        
    except Exception as e:
        print(f"Error predicting close price: {e}")
        return today_open
