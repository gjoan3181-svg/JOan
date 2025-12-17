"""
Estrategia basada en Machine Learning
======================================
Combina predicciones de ML con análisis técnico.
"""

import pandas as pd
from typing import Optional
from loguru import logger

from .base_strategy import BaseStrategy
from ..analysis.signals import Signal, SignalType, SignalGenerator
from ..analysis.indicators import TechnicalIndicators
from ..models.ml_predictor import MLPredictor
from ..models.feature_engineer import FeatureEngineer


class MLStrategy(BaseStrategy):
    """
    Estrategia que combina Machine Learning con análisis técnico.
    
    Genera señales basadas en:
    1. Predicciones del modelo ML
    2. Confirmación de indicadores técnicos
    3. Filtros de tendencia y volatilidad
    """
    
    def __init__(
        self,
        model_type: str = "random_forest",
        min_confidence: float = 0.6,
        require_confirmation: bool = True
    ):
        """
        Inicializa la estrategia ML.
        
        Args:
            model_type: Tipo de modelo ML a usar
            min_confidence: Confianza mínima para señales
            require_confirmation: Si requiere confirmación técnica
        """
        super().__init__(name="MLStrategy")
        self.model_type = model_type
        self.min_confidence = min_confidence
        self.require_confirmation = require_confirmation
        
        self.predictor: Optional[MLPredictor] = None
        self.signal_generator: Optional[SignalGenerator] = None
        self.feature_engineer: Optional[FeatureEngineer] = None
    
    def initialize(self, **kwargs) -> None:
        """
        Inicializa la estrategia con los componentes necesarios.
        
        Kwargs:
            historical_data: DataFrame con datos históricos para entrenar
            model_path: Ruta a un modelo pre-entrenado (opcional)
        """
        self.feature_engineer = FeatureEngineer()
        self.predictor = MLPredictor(
            model_type=self.model_type,
            feature_engineer=self.feature_engineer
        )
        self.signal_generator = SignalGenerator(
            min_signal_strength=0.4  # Umbral más bajo para confirmación
        )
        
        # Cargar modelo existente o entrenar
        model_path = kwargs.get('model_path')
        if model_path:
            self.predictor.load(model_path)
        else:
            historical_data = kwargs.get('historical_data')
            if historical_data is not None and len(historical_data) > 100:
                # Añadir indicadores
                historical_data = TechnicalIndicators.add_all_indicators(historical_data)
                # Entrenar modelo
                self.predictor.train(historical_data)
            else:
                logger.warning("Sin datos históricos suficientes para entrenar")
        
        self._is_initialized = True
        logger.info(f"Estrategia {self.name} inicializada")
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Genera una señal de trading combinando ML y análisis técnico.
        
        Args:
            df: DataFrame con datos OHLCV
            
        Returns:
            Signal con la recomendación
        """
        if not self._is_initialized:
            raise ValueError("La estrategia no ha sido inicializada")
        
        if not self.validate_data(df):
            raise ValueError("DataFrame inválido")
        
        # Añadir indicadores si no existen
        if 'rsi' not in df.columns:
            df = TechnicalIndicators.add_all_indicators(df)
        
        # Obtener última fila
        current = df.iloc[-1]
        price = current['close']
        timestamp = current.get('timestamp', pd.Timestamp.now())
        
        # 1. Obtener predicción ML
        ml_signal = SignalType.HOLD
        ml_probability = 0.5
        
        if self.predictor.is_trained:
            try:
                prediction = self.predictor.predict(df)
                ml_probability = prediction.probability
                
                if prediction.prediction == 1 and ml_probability >= self.min_confidence:
                    ml_signal = SignalType.BUY
                elif prediction.prediction == 0 and ml_probability >= self.min_confidence:
                    ml_signal = SignalType.SELL
                    
                logger.debug(f"ML Predicción: {prediction}")
            except Exception as e:
                logger.warning(f"Error en predicción ML: {e}")
        
        # 2. Obtener señal técnica
        tech_signal = self.signal_generator.generate_signal(df)
        
        # 3. Combinar señales
        final_signal = self._combine_signals(
            ml_signal, ml_probability,
            tech_signal,
            price, timestamp, df
        )
        
        return final_signal
    
    def _combine_signals(
        self,
        ml_signal: SignalType,
        ml_probability: float,
        tech_signal: Signal,
        price: float,
        timestamp: pd.Timestamp,
        df: pd.DataFrame
    ) -> Signal:
        """
        Combina señales de ML y análisis técnico.
        """
        current = df.iloc[-1]
        atr = current.get('atr', price * 0.02)
        
        # Calcular stop loss y take profit
        stop_loss_buy = price - (atr * 2)
        take_profit_buy = price + (atr * 3)
        stop_loss_sell = price + (atr * 2)
        take_profit_sell = price - (atr * 3)
        
        # Si no requiere confirmación, usar solo ML
        if not self.require_confirmation:
            if ml_signal == SignalType.BUY:
                return Signal(
                    signal_type=SignalType.BUY,
                    strength=ml_probability,
                    price=price,
                    reason=f"ML predice subida (prob: {ml_probability:.2%})",
                    timestamp=timestamp,
                    stop_loss=stop_loss_buy,
                    take_profit=take_profit_buy
                )
            elif ml_signal == SignalType.SELL:
                return Signal(
                    signal_type=SignalType.SELL,
                    strength=ml_probability,
                    price=price,
                    reason=f"ML predice bajada (prob: {ml_probability:.2%})",
                    timestamp=timestamp,
                    stop_loss=stop_loss_sell,
                    take_profit=take_profit_sell
                )
        
        # Requiere confirmación: ambas señales deben coincidir
        if ml_signal == SignalType.BUY and tech_signal.signal_type == SignalType.BUY:
            combined_strength = (ml_probability + tech_signal.strength) / 2
            return Signal(
                signal_type=SignalType.BUY,
                strength=combined_strength,
                price=price,
                reason=f"ML + {tech_signal.reason}",
                timestamp=timestamp,
                stop_loss=stop_loss_buy,
                take_profit=take_profit_buy
            )
        
        elif ml_signal == SignalType.SELL and tech_signal.signal_type == SignalType.SELL:
            combined_strength = (ml_probability + tech_signal.strength) / 2
            return Signal(
                signal_type=SignalType.SELL,
                strength=combined_strength,
                price=price,
                reason=f"ML + {tech_signal.reason}",
                timestamp=timestamp,
                stop_loss=stop_loss_sell,
                take_profit=take_profit_sell
            )
        
        # Sin confirmación - mantener
        return Signal(
            signal_type=SignalType.HOLD,
            strength=0.0,
            price=price,
            reason="Sin confirmación ML/Técnica",
            timestamp=timestamp
        )
    
    def should_close_position(
        self,
        df: pd.DataFrame,
        position_side: str,
        entry_price: float
    ) -> bool:
        """
        Determina si se debe cerrar una posición.
        
        Args:
            df: DataFrame con datos actuales
            position_side: 'LONG' o 'SHORT'
            entry_price: Precio de entrada
            
        Returns:
            True si se debe cerrar
        """
        if len(df) < 2:
            return False
        
        current = df.iloc[-1]
        price = current['close']
        
        # Calcular ganancia/pérdida
        if position_side == 'LONG':
            pnl_percent = (price - entry_price) / entry_price
        else:
            pnl_percent = (entry_price - price) / entry_price
        
        # Cerrar si la señal cambia de dirección
        signal = self.generate_signal(df)
        
        if position_side == 'LONG' and signal.signal_type == SignalType.SELL:
            logger.info(f"Cerrando LONG: señal de venta detectada")
            return True
        
        if position_side == 'SHORT' and signal.signal_type == SignalType.BUY:
            logger.info(f"Cerrando SHORT: señal de compra detectada")
            return True
        
        # Cerrar si hay ganancia significativa y el momentum cambia
        if 'rsi' in df.columns:
            rsi = current['rsi']
            
            if position_side == 'LONG' and pnl_percent > 0.02 and rsi > 70:
                logger.info(f"Cerrando LONG: RSI sobrecompra ({rsi:.1f})")
                return True
            
            if position_side == 'SHORT' and pnl_percent > 0.02 and rsi < 30:
                logger.info(f"Cerrando SHORT: RSI sobreventa ({rsi:.1f})")
                return True
        
        return False
    
    def retrain_model(self, df: pd.DataFrame) -> dict:
        """
        Re-entrena el modelo con nuevos datos.
        
        Args:
            df: DataFrame con nuevos datos históricos
            
        Returns:
            Métricas del entrenamiento
        """
        if not self._is_initialized:
            raise ValueError("La estrategia no ha sido inicializada")
        
        # Añadir indicadores
        df = TechnicalIndicators.add_all_indicators(df)
        
        # Re-entrenar
        metrics = self.predictor.train(df)
        
        logger.info(f"Modelo re-entrenado: accuracy={metrics['accuracy']:.4f}")
        
        return metrics
