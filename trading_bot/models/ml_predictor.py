"""
Predictor de Machine Learning
==============================
Modelo de ML para predecir movimientos de precio.
"""

import os
import pickle
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from loguru import logger

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

from .feature_engineer import FeatureEngineer


@dataclass
class PredictionResult:
    """Resultado de una predicción."""
    prediction: int  # 0: baja, 1: sube
    probability: float  # Probabilidad de la predicción
    confidence: str  # 'low', 'medium', 'high'
    features_used: int
    timestamp: datetime
    
    def __str__(self):
        direction = "SUBE ↑" if self.prediction == 1 else "BAJA ↓"
        return f"{direction} (prob: {self.probability:.2%}, confianza: {self.confidence})"


class MLPredictor:
    """
    Predictor basado en Machine Learning para trading.
    
    Soporta múltiples algoritmos:
    - Random Forest
    - Gradient Boosting
    - XGBoost (si está instalado)
    """
    
    MODELS_DIR = "models/saved"
    
    def __init__(
        self,
        model_type: str = "random_forest",
        feature_engineer: FeatureEngineer = None
    ):
        """
        Inicializa el predictor.
        
        Args:
            model_type: Tipo de modelo ('random_forest', 'gradient_boosting', 'xgboost')
            feature_engineer: Instancia de FeatureEngineer
        """
        self.model_type = model_type
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.model = None
        self.scaler = StandardScaler()
        self._is_trained = False
        self._training_metrics: Dict[str, float] = {}
    
    def _create_model(self):
        """Crea el modelo según el tipo especificado."""
        if self.model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == "xgboost":
            try:
                from xgboost import XGBClassifier
                return XGBClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42,
                    use_label_encoder=False,
                    eval_metric='logloss'
                )
            except ImportError:
                logger.warning("XGBoost no disponible, usando Random Forest")
                return self._create_model_rf()
        else:
            raise ValueError(f"Modelo desconocido: {self.model_type}")
    
    def train(
        self,
        df: pd.DataFrame,
        target_type: str = 'direction',
        test_size: float = 0.2,
        validation_split: bool = True
    ) -> Dict[str, float]:
        """
        Entrena el modelo con datos históricos.
        
        Args:
            df: DataFrame con datos OHLCV e indicadores
            target_type: Tipo de variable objetivo
            test_size: Proporción para test
            validation_split: Si dividir datos para validación
            
        Returns:
            Dict con métricas de entrenamiento
        """
        logger.info(f"Iniciando entrenamiento con {len(df)} muestras")
        
        # Preparar datos
        X, y = self.feature_engineer.prepare_dataset(df, target_type)
        
        if len(X) < 100:
            raise ValueError("Se necesitan al menos 100 muestras para entrenar")
        
        # Dividir datos
        if validation_split:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, shuffle=False  # No shuffle para series temporales
            )
        else:
            X_train, y_train = X, y
            X_test, y_test = X, y
        
        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Crear y entrenar modelo
        self.model = self._create_model()
        
        logger.info(f"Entrenando modelo {self.model_type}...")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluar
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)
        
        # Calcular métricas
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features': len(self.feature_engineer.feature_columns)
        }
        
        self._training_metrics = metrics
        self._is_trained = True
        
        logger.info(f"Entrenamiento completado:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"  Precision: {metrics['precision']:.4f}")
        logger.info(f"  Recall: {metrics['recall']:.4f}")
        logger.info(f"  F1 Score: {metrics['f1']:.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        logger.info(f"  CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        return metrics
    
    def predict(self, df: pd.DataFrame) -> PredictionResult:
        """
        Realiza una predicción con los datos actuales.
        
        Args:
            df: DataFrame con datos actuales e indicadores
            
        Returns:
            PredictionResult con la predicción
        """
        if not self._is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        # Preparar features
        X = self.feature_engineer.transform(df)
        
        if len(X) == 0:
            raise ValueError("No hay datos suficientes para predecir")
        
        # Usar última fila
        X_last = X.iloc[[-1]]
        
        # Reemplazar infinitos y NaN
        X_last = X_last.replace([np.inf, -np.inf], np.nan)
        X_last = X_last.fillna(0)
        
        # Escalar
        X_scaled = self.scaler.transform(X_last)
        
        # Predecir
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Obtener probabilidad de la predicción
        prob = probabilities[prediction]
        
        # Determinar nivel de confianza
        if prob >= 0.7:
            confidence = "high"
        elif prob >= 0.55:
            confidence = "medium"
        else:
            confidence = "low"
        
        return PredictionResult(
            prediction=int(prediction),
            probability=float(prob),
            confidence=confidence,
            features_used=len(self.feature_engineer.feature_columns),
            timestamp=datetime.now()
        )
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene la importancia de cada feature.
        
        Returns:
            DataFrame con features y su importancia
        """
        if not self._is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            features = self.feature_engineer.feature_columns
            
            importance_df = pd.DataFrame({
                'feature': features,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            return importance_df
        else:
            return pd.DataFrame()
    
    def save(self, path: str = None) -> str:
        """
        Guarda el modelo entrenado.
        
        Args:
            path: Ruta donde guardar (opcional)
            
        Returns:
            Ruta donde se guardó el modelo
        """
        if not self._is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        if path is None:
            os.makedirs(self.MODELS_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.MODELS_DIR, f"model_{self.model_type}_{timestamp}.pkl")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_engineer': self.feature_engineer,
            'model_type': self.model_type,
            'training_metrics': self._training_metrics,
            'timestamp': datetime.now()
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Modelo guardado en: {path}")
        return path
    
    def load(self, path: str) -> None:
        """
        Carga un modelo previamente guardado.
        
        Args:
            path: Ruta del modelo a cargar
        """
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_engineer = model_data['feature_engineer']
        self.model_type = model_data['model_type']
        self._training_metrics = model_data['training_metrics']
        self._is_trained = True
        
        logger.info(f"Modelo cargado desde: {path}")
        logger.info(f"Métricas del modelo: {self._training_metrics}")
    
    @property
    def is_trained(self) -> bool:
        """Indica si el modelo está entrenado."""
        return self._is_trained
    
    @property
    def training_metrics(self) -> Dict[str, float]:
        """Retorna las métricas de entrenamiento."""
        return self._training_metrics
