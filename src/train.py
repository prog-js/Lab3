import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import json
import configparser

class GraduateModelTrainer:
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
    def load_data(self):
        X_train = pd.read_csv('data/X_train.csv')
        X_val = pd.read_csv('data/X_val.csv')
        y_train = pd.read_csv('data/y_train.csv').values.ravel()
        y_val = pd.read_csv('data/y_val.csv').values.ravel()
        return X_train, y_train, X_val, y_val
    
    def train(self, X_train, y_train):
        model = RandomForestRegressor(
            n_estimators=int(self.config['model']['n_estimators']),
            max_depth=int(self.config['model']['max_depth']),
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        return model
    
    def evaluate(self, model, X_val, y_val):
        y_pred = model.predict(X_val)
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        print(f"Validation RMSE: {rmse:.2f}")
        print(f"Validation MAE: {mae:.2f}")
        print(f"Validation R2: {r2:.3f}")
        
        # Сохранить метрики
        metrics = {'rmse': float(rmse), 'mae': float(mae), 'r2': float(r2)}
        with open('metrics.json', 'w') as f:
            json.dump(metrics, f)
        
        return rmse
    
    def save_model(self, model, path='models/model.pkl'):
        import os
        os.makedirs('models', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(model, f)
        print(f"Model saved to {path}")

if __name__ == '__main__':
    trainer = GraduateModelTrainer()
    X_train, y_train, X_val, y_val = trainer.load_data()
    model = trainer.train(X_train, y_train)
    trainer.evaluate(model, X_val, y_val)
    trainer.save_model(model)