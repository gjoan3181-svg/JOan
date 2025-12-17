"""
Estrategia Base
================
Clase base abstracta para estrategias de trading.
"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from ..analysis.signals import Signal


class BaseStrategy(ABC):
    """
    Clase base abstracta para estrategias de trading.
    
    Todas las estrategias deben heredar de esta clase
    e implementar el método generate_signal.
    """
    
    def __init__(self, name: str = "BaseStrategy"):
        """
        Inicializa la estrategia.
        
        Args:
            name: Nombre de la estrategia
        """
        self.name = name
        self._is_initialized = False
    
    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """Inicializa la estrategia con parámetros."""
        pass
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Genera una señal de trading basada en los datos.
        
        Args:
            df: DataFrame con datos OHLCV e indicadores
            
        Returns:
            Signal con la recomendación
        """
        pass
    
    @abstractmethod
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
            entry_price: Precio de entrada de la posición
            
        Returns:
            True si se debe cerrar
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Valida que el DataFrame tenga las columnas necesarias.
        
        Args:
            df: DataFrame a validar
            
        Returns:
            True si es válido
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_columns)
    
    @property
    def is_initialized(self) -> bool:
        """Indica si la estrategia está inicializada."""
        return self._is_initialized
