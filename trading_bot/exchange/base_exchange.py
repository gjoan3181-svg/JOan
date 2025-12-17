"""
Clase base abstracta para exchanges
====================================
Define la interfaz común para todos los exchanges.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd


@dataclass
class Order:
    """Representa una orden de trading."""
    order_id: str
    symbol: str
    side: str  # 'BUY' o 'SELL'
    order_type: str  # 'MARKET', 'LIMIT', 'STOP_LOSS', etc.
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "NEW"  # NEW, FILLED, CANCELED, etc.
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Position:
    """Representa una posición abierta."""
    symbol: str
    side: str  # 'LONG' o 'SHORT'
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0


@dataclass
class Balance:
    """Representa el balance de una cuenta."""
    asset: str
    free: float
    locked: float
    
    @property
    def total(self) -> float:
        return self.free + self.locked


class BaseExchange(ABC):
    """Clase base abstracta para conexión con exchanges."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establece conexión con el exchange."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Cierra la conexión con el exchange."""
        pass
    
    @abstractmethod
    def get_balance(self, asset: str = None) -> List[Balance]:
        """Obtiene el balance de la cuenta."""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Obtiene el precio actual de un símbolo."""
        pass
    
    @abstractmethod
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        limit: int = 500,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Obtiene datos históricos de velas (OHLCV)."""
        pass
    
    @abstractmethod
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Order:
        """Coloca una orden de mercado."""
        pass
    
    @abstractmethod
    def place_limit_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> Order:
        """Coloca una orden límite."""
        pass
    
    @abstractmethod
    def place_stop_loss_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        stop_price: float
    ) -> Order:
        """Coloca una orden stop loss."""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancela una orden."""
        pass
    
    @abstractmethod
    def get_order(self, symbol: str, order_id: str) -> Optional[Order]:
        """Obtiene información de una orden."""
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Obtiene órdenes abiertas."""
        pass
    
    @abstractmethod
    def get_positions(self, symbol: str = None) -> List[Position]:
        """Obtiene posiciones abiertas."""
        pass
