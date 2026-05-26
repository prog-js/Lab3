import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import List, Dict, Tuple, Optional
import os
import warnings
warnings.filterwarnings('ignore')

class GraduateAnalytics:
    """
    Аналитический модуль для работы с данными выпускников
    - топ направлений по зарплате в регионе (с разбивкой по годам)
    - прогноз роста зарплаты (история + прогноз)
    - топ регионов для вуза+направления (с разбивкой по годам)
    """
    data_path = os.path.join('data', 'data_graduates_university_specialty_124_v20250709.csv')
    def __init__(self, data_path=data_path):
        self.df = pd.read_csv(data_path, low_memory=False, sep=';')
        self.salary_col = 'average_salary_norm_med'
        
        # Приводим год к целому числу
        if 'year' in self.df.columns:
            self.df['year'] = pd.to_numeric(self.df['year'], errors='coerce').fillna(0).astype(int)
    
    def get_top_specialties_in_region_by_year(self, region_name: str, top_n: int = 5) -> pd.DataFrame:
        """
        Топ-N направлений подготовки по зарплате в выбранном регионе
        с разбивкой по годам (для тепловой матрицы)
        
        Args:
            region_name: название региона (object_name)
            top_n: количество записей в топе
        
        Returns:
            DataFrame с колонками: 
            - specialty (направление)
            - university (вуз)
            - year (год)
            - salary (зарплата нормированная медианная)
            - rank (место в топе за последний год)
        """
        # Фильтр по региону и удаление пропусков
        df_region = self.df[
            (self.df['object_name'] == region_name) & 
            (self.df[self.salary_col].notna())
        ].copy()
        
        if df_region.empty:
            return pd.DataFrame(columns=['specialty', 'university', 'year', 'salary'])
        
        # Определяем топ направления по средней зарплате за последний год
        latest_year = df_region['year'].max()
        df_latest = df_region[df_region['year'] == latest_year]
        
        top_specialties = df_latest.groupby(['specialty', 'university'])[self.salary_col].mean().reset_index()
        top_specialties = top_specialties.sort_values(self.salary_col, ascending=False).head(top_n)
        top_specialties['rank'] = range(1, len(top_specialties) + 1)
        
        # Получаем все данные по топ направлениям за все годы
        result = df_region[
            df_region[['specialty', 'university']].apply(tuple, axis=1).isin(
                top_specialties[['specialty', 'university']].apply(tuple, axis=1)
            )
        ].groupby(['specialty', 'university', 'year'])[self.salary_col].mean().reset_index()
        
        # Добавляем ранг
        result = result.merge(top_specialties[['specialty', 'university', 'rank']], on=['specialty', 'university'])
        
        # Сортируем по рангу и году
        result = result.sort_values(['rank', 'year'])
        
        result.columns = ['Направление', 'ВУЗ', 'Год', 'Средняя зарплата (норм.)', 'Ранг']
        return result
    
    def get_top_specialties_matrix(self, region_name: str, top_n: int = 5) -> pd.DataFrame:
        """
        Подготовка данных для тепловой матрицы (pivot-таблица)
        
        Returns:
            DataFrame: строки = направления, столбцы = годы, значения = зарплаты
        """
        df_details = self.get_top_specialties_in_region_by_year(region_name, top_n)
        if df_details.empty:
            return pd.DataFrame()
        
        # Создаём подпись для строк: "Направление (ВУЗ)"
        df_details['Строка'] = df_details['Направление'] + ' (' + df_details['ВУЗ'] + ')'
        
        # Создаём pivot-таблицу для тепловой матрицы
        pivot = df_details.pivot_table(
            index='Строка',
            columns='Год',
            values='Средняя зарплата (норм.)',
            aggfunc='mean'
        )
        
        # Сортируем по рангу
        ranks = df_details[['Строка', 'Ранг']].drop_duplicates().set_index('Строка')['Ранг']
        pivot = pivot.reindex(ranks.sort_values().index)
        
        return pivot
    
    def get_attractive_regions_by_year(self, university_name: str, specialty_name: str, 
                                        top_n: int = 5, min_data_points: int = 2) -> pd.DataFrame:
        """
        Топ-N регионов с самой высокой зарплатой для заданного вуза и направления
        с разбивкой по годам (для тепловой матрицы)
        
        Args:
            university_name: название вуза
            specialty_name: направление подготовки
            top_n: количество регионов в топе
            min_data_points: минимальное количество лет с данными для включения
        
        Returns:
            DataFrame с колонками:
            - region (регион)
            - year (год)
            - salary (зарплата)
            - rank (место в топе за последний год)
        """
        df_filtered = self.df[
            (self.df['university'] == university_name) &
            (self.df['specialty'] == specialty_name) &
            (self.df[self.salary_col].notna())
        ].copy()
        
        if df_filtered.empty:
            return pd.DataFrame(columns=['region', 'year', 'salary'])
        
        # Определяем топ регионов по средней зарплате за последний год
        latest_year = df_filtered['year'].max()
        df_latest = df_filtered[df_filtered['year'] == latest_year]
        
        top_regions = df_latest.groupby('object_name')[self.salary_col].mean().reset_index()
        top_regions = top_regions.sort_values(self.salary_col, ascending=False).head(top_n)
        top_regions['rank'] = range(1, len(top_regions) + 1)
        
        # Получаем все данные по топ регионам за все годы
        result = df_filtered[
            df_filtered['object_name'].isin(top_regions['object_name'])
        ].groupby(['object_name', 'year'])[self.salary_col].mean().reset_index()
        
        # Фильтр по минимальному количеству лет
        region_years = result.groupby('object_name')['year'].count().reset_index()
        valid_regions = region_years[region_years['year'] >= min_data_points]['object_name'].tolist()
        result = result[result['object_name'].isin(valid_regions)]
        
        # Добавляем ранг
        result = result.merge(top_regions[['object_name', 'rank']], on='object_name')
        
        # Сортируем по рангу и году
        result = result.sort_values(['rank', 'year'])
        
        result.columns = ['Регион', 'Год', 'Средняя зарплата (норм.)', 'Ранг']
        return result
    
    def get_attractive_regions_matrix(self, university_name: str, specialty_name: str, 
                                       top_n: int = 5) -> pd.DataFrame:
        """
        Подготовка данных для тепловой матрицы регионов
        
        Returns:
            DataFrame: строки = регионы, столбцы = годы, значения = зарплаты
        """
        df_details = self.get_attractive_regions_by_year(university_name, specialty_name, top_n)
        if df_details.empty:
            return pd.DataFrame()
        
        # Создаём pivot-таблицу для тепловой матрицы
        pivot = df_details.pivot_table(
            index='Регион',
            columns='Год',
            values='Средняя зарплата (норм.)',
            aggfunc='mean'
        )
        
        # Сортируем по рангу
        ranks = df_details[['Регион', 'Ранг']].drop_duplicates().set_index('Регион')['Ранг']
        pivot = pivot.reindex(ranks.sort_values().index)
        
        return pivot
    
    def get_salary_forecast(self, region_name: str, specialty_name: str, 
                            university_name: str, years_ahead: int = 3) -> Dict:
        """
        Прогноз роста зарплаты с историческими данными и прогнозом
        для построения столбиковой диаграммы
        
        Args:
            region_name: регион
            specialty_name: направление
            university_name: вуз
            years_ahead: на сколько лет вперёд прогноз
        
        Returns:
            Словарь с полями:
            - history: список словарей {year, salary, type="history"}
            - forecast: список словарей {year, salary, type="forecast"}
            - growth_rate: процент роста
            - r2_score: качество модели
        """
        df_filtered = self.df[
            (self.df['object_name'] == region_name) &
            (self.df['specialty'] == specialty_name) &
            (self.df['university'] == university_name) &
            (self.df[self.salary_col].notna())
        ].copy()
        
        if df_filtered.empty:
            return {'error': 'Нет данных для указанной комбинации'}
        
        # Группировка по году
        yearly = df_filtered.groupby('year')[self.salary_col].mean().reset_index()
        yearly = yearly.sort_values('year')
        
        if len(yearly) < 2:
            return {'error': 'Недостаточно лет для построения прогноза (минимум 2)'}
        
        # Линейная регрессия
        X = yearly['year'].values.reshape(-1, 1)
        y = yearly[self.salary_col].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # История
        history = [
            {'year': int(row['year']), 'salary': float(row[self.salary_col]), 'type': 'history'}
            for _, row in yearly.iterrows()
        ]
        
        # Прогноз
        last_year = yearly['year'].max()
        forecast = []
        for i in range(1, years_ahead + 1):
            pred_year = last_year + i
            pred_salary = model.predict([[pred_year]])[0]
            forecast.append({
                'year': int(pred_year), 
                'salary': float(pred_salary),
                'type': 'forecast',
                'confidence_lower': float(pred_salary * 0.85),
                'confidence_upper': float(pred_salary * 1.15)
            })
        
        # Рост в процентах
        growth_rate = (forecast[-1]['salary'] / history[-1]['salary'] - 1) * 100
        
        # Объединяем для столбиковой диаграммы
        all_data = history + forecast
        
        return {
            'region': region_name,
            'specialty': specialty_name,
            'university': university_name,
            'data': all_data,  # готовые данные для столбиковой диаграммы
            'growth_rate_percent': round(growth_rate, 2),
            'r2_score': round(model.score(X, y), 3),
            'avg_salary_last_year': history[-1]['salary'],
            'avg_salary_forecast': forecast[-1]['salary']
        }
    
    def get_all_regions(self) -> List[str]:
        """Получить список всех уникальных регионов"""
        return sorted(self.df['object_name'].dropna().unique().tolist())
    
    def get_all_universities(self) -> List[str]:
        """Получить список всех уникальных вузов"""
        return sorted(self.df['university'].dropna().unique().tolist())
    
    def get_specialties_by_university(self, university_name: str) -> List[str]:
        """Получить список направлений в конкретном вузе"""
        specialties = self.df[self.df['university'] == university_name]['specialty'].dropna().unique()
        return sorted(specialties.tolist())
    
    def get_years_range(self) -> Tuple[int, int]:
        """Получить минимальный и максимальный год в данных"""
        return (int(self.df['year'].min()), int(self.df['year'].max()))
    def get_available_filters(self) -> Dict:
        """
        Возвращает все доступные значения для фильтров
        """
        return {
            'regions': sorted(self.df['object_name'].dropna().unique().tolist()),
            'specialties': sorted(self.df['specialty'].dropna().unique().tolist()),
            'universities': sorted(self.df['university'].dropna().unique().tolist()),
            'years': sorted(self.df['year'].dropna().unique().tolist())
        }

# Пример использования (для теста)
if __name__ == '__main__':
    analytics = GraduateAnalytics()
    
#    print("=== Топ-5 направлений в Москве с разбивкой по годам ===")
#    top = analytics.get_top_specialties_in_region_by_year('Москва', top_n=5)
#    print(top)
    
#    print("\n=== Тепловая матрица (pivot) ===")
#    matrix = analytics.get_top_specialties_matrix('Москва', top_n=5)
#    print(matrix)
     
    #print("\n=== Прогноз зарплаты ===")
    #forecast = analytics.get_salary_forecast('Москва', 'Наукоемкие технологии и экономика инноваций', 'Московский физико-технический институт', years_ahead=3)
    #print(forecast)
    
    #print("\n=== Топ регионов для МГУ / Прикладная математика ===")
    #regions = analytics.get_attractive_regions_by_year('Московский физико-технический институт', 'Наукоемкие технологии и экономика инноваций', top_n=5)
    #print(regions)