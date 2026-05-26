#!/usr/bin/env python
"""
Скрипт для наполнения базы данных наборами для обучения/валидации.
Запуск: python scripts/init_db.py
"""
import os
import sys
import pandas as pd
from sqlalchemy.orm import Session

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from db import SessionLocal, TrainingData, init_db, engine
from db import Base

def load_training_data():
    """Загрузка данных из CSV в БД"""
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Train_Iris_X.csv')
    
    if not os.path.exists(csv_path):
        print(f"Файл не найден: {csv_path}")
        print("Использую тестовые данные...")
        # Создаём тестовые данные
        import numpy as np
        X = np.random.rand(100, 4).tolist()
        y = np.random.randint(0, 3, 100).tolist()
    else:
        df = pd.read_csv(csv_path)
        X = df.values.tolist()
        # Заглушка для target (если нет отдельного файла)
        y = [0] * len(X)
    
    db = SessionLocal()
    try:
        # Очищаем старые данные
        db.query(TrainingData).delete()
        
        # Загружаем новые
        for features, target in zip(X, y):
            training_record = TrainingData(
                features=features,
                target=target,
                dataset_type='train'
            )
            db.add(training_record)
        
        db.commit()
        print(f"✅ Загружено {len(X)} записей в training_data")
    finally:
        db.close()

def load_validation_data():
    """Загрузка валидационных данных"""
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'X_val.csv')
    
    if not os.path.exists(csv_path):
        print(f"Файл не найден: {csv_path}, пропускаю...")
        return
    
    df = pd.read_csv(csv_path)
    X = df.values.tolist()
    y = [0] * len(X)  # заглушка
    
    db = SessionLocal()
    try:
        for features, target in zip(X, y):
            training_record = TrainingData(
                features=features,
                target=target,
                dataset_type='val'
            )
            db.add(training_record)
        db.commit()
        print(f"✅ Загружено {len(X)} записей в training_data (val)")
    finally:
        db.close()

if __name__ == "__main__":
    print("Инициализация базы данных...")
    init_db()
    print("Загрузка обучающих данных...")
    load_training_data()
    print("Загрузка валидационных данных...")
    load_validation_data()
    print("✅ Готово!")