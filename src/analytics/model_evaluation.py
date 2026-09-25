import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Lag1_Return'] = df['Return'].shift(1)
    df['Lag2_Return'] = df['Return'].shift(2)
    df['Lag3_Return'] = df['Return'].shift(3)
    
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_5_Ratio'] = df['Close'] / df['SMA_5']
    df['Volatility_5'] = df['Return'].rolling(window=5).std()
    
    df['Prev_Range'] = (df['High'] - df['Low']).shift(1)
    df['Prev_Open_to_Close'] = (df['Close'] - df['Open']).shift(1)
    
    return df.dropna()

def calculate_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'R2': r2}

class SimpleLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=32, num_layers=1):
        super(SimpleLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

def evaluate_models(history_df: pd.DataFrame):
    print("Starting Model Evaluation...")
    
    df = add_technical_features(history_df)
    features = ['Lag1_Return', 'Lag2_Return', 'Lag3_Return', 'SMA_5_Ratio', 'Volatility_5', 'Prev_Range', 'Prev_Open_to_Close']
    target = 'Return'
    
    # Chronological split (Walk-forward / TimeSeriesSplit)
    # 80% train, 20% test
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    print(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")
    
    # XGBoost Tuning & Evaluation
    xgb_model = xgb.XGBRegressor(
        n_estimators=100, learning_rate=0.05, max_depth=4, 
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    
    # LSTM Evaluation
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    X_train_t = torch.FloatTensor(X_train_scaled).unsqueeze(1)
    y_train_t = torch.FloatTensor(y_train.values).unsqueeze(1)
    X_test_t = torch.FloatTensor(X_test_scaled).unsqueeze(1)
    
    lstm_model = SimpleLSTM(input_size=len(features))
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(lstm_model.parameters(), lr=0.01)
    
    for epoch in range(100):
        optimizer.zero_grad()
        outputs = lstm_model(X_train_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()
        
    with torch.no_grad():
        lstm_preds = lstm_model(X_test_t).squeeze().numpy()
        
    print("\n--- XGBoost Metrics (Return Prediction) ---")
    print(calculate_metrics(y_test, xgb_preds))
    
    print("\n--- LSTM Metrics (Return Prediction) ---")
    print(calculate_metrics(y_test, lstm_preds))
    
    # Convert predictions back to close price to evaluate price metrics
    prev_close = test_df['Close'].shift(1).fillna(train_df['Close'].iloc[-1])
    true_close = test_df['Close']
    xgb_close_preds = prev_close * np.exp(xgb_preds)
    lstm_close_preds = prev_close * np.exp(lstm_preds)
    
    print("\n--- XGBoost Metrics (Close Price) ---")
    print(calculate_metrics(true_close, xgb_close_preds))
    
    print("\n--- LSTM Metrics (Close Price) ---")
    print(calculate_metrics(true_close, lstm_close_preds))
    
if __name__ == "__main__":
    # Mock data for testing the script structure
    dates = pd.date_range(start='2020-01-01', periods=500, freq='B')
    mock_df = pd.DataFrame({
        'Open': np.random.uniform(100, 200, 500),
        'High': np.random.uniform(100, 200, 500) + 10,
        'Low': np.random.uniform(100, 200, 500) - 10,
        'Close': np.random.uniform(100, 200, 500)
    }, index=dates)
    
    evaluate_models(mock_df)
