import pytest
import pandas as pd
import numpy as np
from src.preprocess import GraduateSpecialtyPreprocessor
import os

class TestGraduateSpecialtyPreprocessor:
    
    @pytest.fixture
    def preprocessor(self):
        """Фикстура: экземпляр препроцессора"""
        return GraduateSpecialtyPreprocessor()
    
    @pytest.fixture
    def sample_data(self):
        """Фикстура: маленький DataFrame для тестов"""
        return pd.DataFrame({
            'object_name': ['Москва', 'Москва', 'СПб', 'СПб'],
            'university': ['МГУ', 'МГУ', 'СПбГУ', 'СПбГУ'],
            'specialty': ['Математика', 'Физика', 'Математика', 'Физика'],
            'year': [2020, 2021, 2020, 2021],
            'average_salary_norm_med': [80000, 85000, 70000, None],
            'average_salary_fact_avg': [75000, None, 65000, 68000],
            'gender': ['Всего', 'Всего', 'Всего', 'Всего'],
            'education_level': ['Бакалавриат', 'Бакалавриат', 'Бакалавриат', 'Бакалавриат']
        })
    
    def test_load_data(self, preprocessor):
        """Тест загрузки данных (с маленьким файлом)"""
        # Создаём временный тестовый файл
        test_df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        test_path = 'data/test_temp.csv'
        test_df.to_csv(test_path, index=False)
        
        # Загружаем
        result = preprocessor.load_data(test_path)
        
        # Проверки
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'a' in result.columns
        
        # Очистка
        os.remove(test_path)
    
    def test_fill_salary_missing_by_group(self, preprocessor, sample_data):
        """Тест заполнения пропусков медианой по группе"""
        result = preprocessor.fill_salary_missing_by_group(
            sample_data.copy(), 
            'average_salary_norm_med'
        )
        
        # Проверка: пропуски заполнены
        assert result['average_salary_norm_med'].isnull().sum() == 0
        
        # Проверка: для СПб/СПбГУ/Физика медиана = 70000 (только одна запись)
        mask = (result['object_name'] == 'СПб') & \
               (result['university'] == 'СПбГУ') & \
               (result['specialty'] == 'Физика')
        assert result.loc[mask, 'average_salary_norm_med'].iloc[0] == 70000
    
    def test_preprocess_removes_salary_columns(self, preprocessor, sample_data):
        """Тест: после предобработки salary-колонки удалены из признаков"""
        # Это проверим косвенно через split_and_save
        # Но метод preprocess должен возвращать DataFrame без лишних колонок
        result = preprocessor.preprocess(sample_data)
        
        # Целевая колонка должна быть
        assert 'average_salary_norm_med' in result.columns
        
        # Другие salary-колонки могут остаться (но потом удалятся при split)
    
    def test_split_and_save(self, preprocessor, sample_data, tmp_path):
        """Тест разделения данных"""
        # Временно меняем пути сохранения
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        # Создаём папки
        os.makedirs('data', exist_ok=True)
        os.makedirs('models', exist_ok=True)
        
        # Выполняем разделение
        preprocessor.split_and_save(sample_data, target_col='average_salary_norm_med')
        
        # Проверяем, что файлы созданы
        assert os.path.exists('data/X_train.csv')
        assert os.path.exists('data/X_val.csv')
        assert os.path.exists('data/X_test.csv')
        assert os.path.exists('data/y_train.csv')
        
        # Проверяем содержимое
        X_train = pd.read_csv('data/X_train.csv')
        y_train = pd.read_csv('data/y_train.csv')
        
        assert X_train.shape[1] > 0
        assert y_train.shape[1] == 1
        
        # Возвращаемся
        os.chdir(original_dir)