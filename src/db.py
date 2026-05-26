import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from src.vault_client import VaultClient

# Инициализация Vault
vault = VaultClient()
db_config = vault.get_db_config()

DB_HOST = db_config.get('host', 'localhost')
DB_PORT = db_config.get('port', '5432')
DB_USER = db_config.get('user', 'ml_user')
DB_PASSWORD = db_config.get('password', '')
DB_NAME = db_config.get('name', 'ml_models')

# Загрузка конфигурации из переменных окружения
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

# Формирование URL для подключения
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание движка SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель для хранения предсказаний
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_features = Column(JSON, nullable=False)
    prediction = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String, default="1.0")
    user_id = Column(String, nullable=True)  # Для авторизации

# Модель для хранения метрик модели
class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    model_version = Column(String, default="1.0")

# Модель для хранения данных обучения
class TrainingData(Base):
    __tablename__ = "training_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    features = Column(JSON, nullable=False)
    target = Column(Integer, nullable=False)
    dataset_type = Column(String)  # 'train', 'val', 'test'

# Создание таблиц
def init_db():
    Base.metadata.create_all(bind=engine)

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()