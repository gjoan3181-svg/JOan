"""
Feature Engineering
====================
Prepara características (features) para el modelo de ML.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple
from loguru import logger


class FeatureEngineer:
    """
    Prepara y transforma características para modelos de ML.
    """
    
    # Features por defecto a usar
    DEFAULT_FEATURES = [
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'bb_position', 'stoch_k', 'stoch_d', 'adx',
        'returns', 'volatility', 'price_momentum',
        'sma_10', 'sma_20', 'ema_10', 'ema_20'
    ]
    
    def __init__(
        self, 
        features: List[str] = None,
        lookback_periods: List[int] = None,
        prediction_horizon: int = 1
    ):
        """
        Inicializa el Feature Engineer.
        
        Args:
            features: Lista de features a usar
            lookback_periods: Períodos para crear features con lag
            prediction_horizon: Velas hacia adelante para predecir
        """
        self.features = features or self.DEFAULT_FEATURES
        self.lookback_periods = lookback_periods or [1, 2, 3, 5, 10]
        self.prediction_horizon = prediction_horizon
        
        self._feature_columns = None
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea features a partir del DataFrame con indicadores.
        
        Args:
            df: DataFrame con indicadores técnicos
            
        Returns:
            DataFrame con features adicionales
        """
        df = df.copy()
        
        # Crear features con lag (valores anteriores)
        for feature in self.features:
            if feature in df.columns:
                for lag in self.lookback_periods:
                    df[f'{feature}_lag_{lag}'] = df[feature].shift(lag)
        
        # Crear cambios porcentuales
        for feature in ['close', 'volume']:
            if feature in df.columns:
                for period in [1, 3, 5, 10]:
                    df[f'{feature}_pct_change_{period}'] = df[feature].pct_change(periods=period)
        
        # Features de tendencia
        if all(col in df.columns for col in ['sma_10', 'sma_50']):
            df['trend_strength'] = (df['sma_10'] - df['sma_50']) / df['sma_50']
        
        if all(col in df.columns for col in ['sma_10', 'sma_20']):
            df['ma_crossover'] = (df['sma_10'] > df['sma_20']).astype(int)
        
        # Features de volatilidad
        if 'close' in df.columns:
            df['price_range'] = (df['high'] - df['low']) / df['close']
            df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
            df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
            df['body'] = abs(df['close'] - df['open']) / df['close']
        
        # Features de volumen
        if 'volume' in df.columns:
            df['volume_sma_10'] = df['volume'].rolling(10).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma_10']
        
        # Features de momentum
        if 'close' in df.columns:
            df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
            df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        return df
    
    def create_target(
        self, 
        df: pd.DataFrame, 
        target_type: str = 'direction'
    ) -> pd.DataFrame:
        """
        Crea la variable objetivo para el modelo.
        
        Args:
            df: DataFrame con datos
            target_type: Tipo de objetivo
                - 'direction': 1 si el precio sube, 0 si baja
                - 'returns': Retorno porcentual
                - 'triple_barrier': -1, 0, 1 basado en barreras
                
        Returns:
            DataFrame con columna 'target'
        """
        df = df.copy()
        
        if target_type == 'direction':
            # Predicción binaria: ¿Subirá el precio?
            future_return = df['close'].shift(-self.prediction_horizon) / df['close'] - 1
            df['target'] = (future_return > 0).astype(int)
            
        elif target_type == 'returns':
            # Predicción de retorno continuo
            df['target'] = df['close'].shift(-self.prediction_horizon) / df['close'] - 1
            
        elif target_type == 'triple_barrier':
            # Triple barrier method
            df['target'] = self._triple_barrier_labels(df)
            
        return df
    
    def _triple_barrier_labels(
        self, 
        df: pd.DataFrame,
        take_profit: float = 0.02,
        stop_loss: float = 0.01,
        max_holding: int = 10
    ) -> pd.Series:
        """
        Implementa el método de triple barrera para etiquetado.
        
        Args:
            df: DataFrame con precios
            take_profit: Porcentaje de ganancia objetivo
            stop_loss: Porcentaje de pérdida máxima
            max_holding: Máximo de velas a mantener
            
        Returns:
            Serie con etiquetas (-1, 0, 1)
        """
        labels = []
        
        for i in range(len(df) - max_holding):
            entry_price = df['close'].iloc[i]
            upper = entry_price * (1 + take_profit)
            lower = entry_price * (1 - stop_loss)
            
            # Buscar cual barrera se toca primero
            label = 0  # Default: tiempo expirado
            
            for j in range(1, max_holding + 1):
                if i + j >= len(df):
                    break
                    
                high = df['high'].iloc[i + j]
                low = df['low'].iloc[i + j]
                
                # Take profit primero
                if high >= upper:
                    label = 1
                    break
                # Stop loss
                elif low <= lower:
                    label = -1
                    break
            
            labels.append(label)
        
        # Rellenar el final con NaN
        labels.extend([np.nan] * max_holding)
        
        return pd.Series(labels, index=df.index)
    
    def prepare_dataset(
        self, 
        df: pd.DataFrame, 
        target_type: str = 'direction'
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara el dataset completo para entrenamiento.
        
        Args:
            df: DataFrame con datos OHLCV e indicadores
            target_type: Tipo de variable objetivo
            
        Returns:
            Tuple de (X, y) listo para entrenamiento
        """
        # Crear features
        df = self.create_features(df)
        
        # Crear target
        df = self.create_target(df, target_type)
        
        # Eliminar filas con NaN
        df = df.dropna()
        
        # Seleccionar solo features numéricas válidas
        feature_cols = [col for col in df.columns if col not in 
                       ['timestamp', 'target', 'open', 'high', 'low', 'close', 'volume']]
        
        # Filtrar columnas con valores válidos
        valid_cols = []
        for col in feature_cols:
            if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                if not df[col].isnull().all():
                    valid_cols.append(col)
        
        self._feature_columns = valid_cols
        
        X = df[valid_cols]
        y = df['target']
        
        logger.info(f"Dataset preparado: {len(X)} muestras, {len(valid_cols)} features")
        
        return X, y
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma nuevos datos usando las mismas features.
        
        Args:
            df: DataFrame con nuevos datos
            
        Returns:
            DataFrame con features seleccionadas
        """
        if self._feature_columns is None:
            raise ValueError("Debe llamar prepare_dataset primero")
        
        df = self.create_features(df)
        
        # Asegurar que todas las columnas existen
        for col in self._feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        return df[self._feature_columns]
    
    @property
    def feature_columns(self) -> List[str]:
        """Retorna las columnas de features usadas."""
        return self._feature_columns or []
