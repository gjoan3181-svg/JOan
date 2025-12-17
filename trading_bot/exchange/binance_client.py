"""
Cliente de Binance
==================
Implementación del cliente para conectarse a Binance (spot y futuros).
"""

import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
from loguru import logger

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    logger.warning("python-binance no está instalado. Usando modo simulación.")

from .base_exchange import BaseExchange, Order, Position, Balance
from ..config import get_settings


class BinanceClient(BaseExchange):
    """
    Cliente para conectarse a Binance Exchange.
    
    Soporta tanto el modo real como testnet para pruebas.
    """
    
    # URLs de Binance
    MAINNET_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"
    FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"
    
    def __init__(self, api_key: str = None, secret_key: str = None, testnet: bool = True):
        """
        Inicializa el cliente de Binance.
        
        Args:
            api_key: API key de Binance
            secret_key: Secret key de Binance
            testnet: Si es True, usa la red de pruebas
        """
        self.settings = get_settings()
        self.testnet = testnet
        
        # Usar credenciales proporcionadas o del entorno
        if testnet:
            self.api_key = api_key or self.settings.exchange.testnet_api_key
            self.secret_key = secret_key or self.settings.exchange.testnet_secret_key
        else:
            self.api_key = api_key or self.settings.exchange.api_key
            self.secret_key = secret_key or self.settings.exchange.secret_key
        
        self.client = None
        self._connected = False
        
    def connect(self) -> bool:
        """Establece conexión con Binance."""
        if not BINANCE_AVAILABLE:
            logger.warning("Modo simulación: python-binance no disponible")
            self._connected = True
            return True
            
        try:
            if self.testnet:
                self.client = Client(
                    self.api_key, 
                    self.secret_key,
                    testnet=True
                )
                logger.info("Conectado a Binance TESTNET")
            else:
                self.client = Client(self.api_key, self.secret_key)
                logger.info("Conectado a Binance MAINNET")
            
            # Verificar conexión
            self.client.ping()
            self._connected = True
            logger.info("Conexión exitosa con Binance")
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Error de API de Binance: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al conectar con Binance: {e}")
            return False
    
    def disconnect(self) -> None:
        """Cierra la conexión con Binance."""
        self.client = None
        self._connected = False
        logger.info("Desconectado de Binance")
    
    def get_balance(self, asset: str = None) -> List[Balance]:
        """Obtiene el balance de la cuenta."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        if not BINANCE_AVAILABLE:
            # Modo simulación
            return [Balance(asset="USDT", free=10000.0, locked=0.0)]
        
        try:
            account = self.client.get_account()
            balances = []
            
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                
                if free > 0 or locked > 0:
                    bal = Balance(
                        asset=balance['asset'],
                        free=free,
                        locked=locked
                    )
                    if asset is None or balance['asset'] == asset:
                        balances.append(bal)
            
            return balances
            
        except BinanceAPIException as e:
            logger.error(f"Error al obtener balance: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Obtiene el precio actual de un símbolo."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        if not BINANCE_AVAILABLE:
            # Modo simulación - precio ficticio
            return {
                'symbol': symbol,
                'price': 45000.0,
                'bid': 44990.0,
                'ask': 45010.0,
                'volume': 1000.0
            }
        
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            return {
                'symbol': ticker['symbol'],
                'price': float(ticker['lastPrice']),
                'bid': float(ticker['bidPrice']),
                'ask': float(ticker['askPrice']),
                'volume': float(ticker['volume']),
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent'])
            }
        except BinanceAPIException as e:
            logger.error(f"Error al obtener ticker: {e}")
            raise
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        limit: int = 500,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Obtiene datos históricos de velas (OHLCV).
        
        Args:
            symbol: Par de trading (ej: 'BTCUSDT')
            interval: Intervalo de tiempo ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Número de velas a obtener (máx 1000)
            start_time: Tiempo de inicio
            end_time: Tiempo de fin
            
        Returns:
            DataFrame con columnas: timestamp, open, high, low, close, volume
        """
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        if not BINANCE_AVAILABLE:
            # Modo simulación - generar datos ficticios
            import numpy as np
            dates = pd.date_range(end=datetime.now(), periods=limit, freq='1h')
            base_price = 45000
            
            data = {
                'timestamp': dates,
                'open': base_price + np.random.randn(limit) * 100,
                'high': base_price + np.random.randn(limit) * 100 + 50,
                'low': base_price + np.random.randn(limit) * 100 - 50,
                'close': base_price + np.random.randn(limit) * 100,
                'volume': np.random.rand(limit) * 1000
            }
            return pd.DataFrame(data)
        
        try:
            # Mapear intervalos
            interval_map = {
                '1m': Client.KLINE_INTERVAL_1MINUTE,
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '30m': Client.KLINE_INTERVAL_30MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR,
                '4h': Client.KLINE_INTERVAL_4HOUR,
                '1d': Client.KLINE_INTERVAL_1DAY,
                '1w': Client.KLINE_INTERVAL_1WEEK,
            }
            
            binance_interval = interval_map.get(interval, interval)
            
            # Construir parámetros
            params = {
                'symbol': symbol,
                'interval': binance_interval,
                'limit': limit
            }
            
            if start_time:
                params['startTime'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            klines = self.client.get_klines(**params)
            
            # Convertir a DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convertir tipos
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Mantener solo columnas relevantes
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error al obtener klines: {e}")
            raise
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Order:
        """Coloca una orden de mercado."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        logger.info(f"Colocando orden MARKET {side} {quantity} {symbol}")
        
        if not BINANCE_AVAILABLE:
            # Modo simulación
            return Order(
                order_id="SIM_" + str(datetime.now().timestamp()),
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
                status="FILLED",
                filled_quantity=quantity,
                avg_fill_price=45000.0,
                created_at=datetime.now()
            )
        
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            return Order(
                order_id=str(order['orderId']),
                symbol=order['symbol'],
                side=order['side'],
                order_type=order['type'],
                quantity=float(order['origQty']),
                status=order['status'],
                filled_quantity=float(order['executedQty']),
                avg_fill_price=float(order.get('avgPrice', 0)),
                created_at=datetime.fromtimestamp(order['transactTime'] / 1000)
            )
            
        except BinanceAPIException as e:
            logger.error(f"Error al colocar orden: {e}")
            raise
    
    def place_limit_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> Order:
        """Coloca una orden límite."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        logger.info(f"Colocando orden LIMIT {side} {quantity} {symbol} @ {price}")
        
        if not BINANCE_AVAILABLE:
            return Order(
                order_id="SIM_" + str(datetime.now().timestamp()),
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                status="NEW",
                created_at=datetime.now()
            )
        
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=str(price)
            )
            
            return Order(
                order_id=str(order['orderId']),
                symbol=order['symbol'],
                side=order['side'],
                order_type=order['type'],
                quantity=float(order['origQty']),
                price=float(order['price']),
                status=order['status'],
                created_at=datetime.fromtimestamp(order['transactTime'] / 1000)
            )
            
        except BinanceAPIException as e:
            logger.error(f"Error al colocar orden límite: {e}")
            raise
    
    def place_stop_loss_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        stop_price: float
    ) -> Order:
        """Coloca una orden stop loss."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        logger.info(f"Colocando STOP LOSS {side} {quantity} {symbol} @ {stop_price}")
        
        if not BINANCE_AVAILABLE:
            return Order(
                order_id="SIM_" + str(datetime.now().timestamp()),
                symbol=symbol,
                side=side,
                order_type="STOP_LOSS",
                quantity=quantity,
                stop_price=stop_price,
                status="NEW",
                created_at=datetime.now()
            )
        
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                stopPrice=str(stop_price),
                price=str(stop_price)  # Para STOP_LOSS_LIMIT necesitamos precio límite
            )
            
            return Order(
                order_id=str(order['orderId']),
                symbol=order['symbol'],
                side=order['side'],
                order_type=order['type'],
                quantity=float(order['origQty']),
                stop_price=float(order['stopPrice']),
                status=order['status'],
                created_at=datetime.fromtimestamp(order['transactTime'] / 1000)
            )
            
        except BinanceAPIException as e:
            logger.error(f"Error al colocar stop loss: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancela una orden."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        if not BINANCE_AVAILABLE:
            logger.info(f"[SIM] Orden {order_id} cancelada")
            return True
        
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Orden {order_id} cancelada")
            return True
        except BinanceAPIException as e:
            logger.error(f"Error al cancelar orden: {e}")
            return False
    
    def get_order(self, symbol: str, order_id: str) -> Optional[Order]:
        """Obtiene información de una orden."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        if not BINANCE_AVAILABLE:
            return None
        
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return Order(
                order_id=str(order['orderId']),
                symbol=order['symbol'],
                side=order['side'],
                order_type=order['type'],
                quantity=float(order['origQty']),
                price=float(order.get('price', 0)),
                status=order['status'],
                filled_quantity=float(order['executedQty'])
            )
        except BinanceAPIException as e:
            logger.error(f"Error al obtener orden: {e}")
            return None
    
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Obtiene órdenes abiertas."""
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        if not BINANCE_AVAILABLE:
            return []
        
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()
            
            return [
                Order(
                    order_id=str(o['orderId']),
                    symbol=o['symbol'],
                    side=o['side'],
                    order_type=o['type'],
                    quantity=float(o['origQty']),
                    price=float(o.get('price', 0)),
                    status=o['status']
                )
                for o in orders
            ]
        except BinanceAPIException as e:
            logger.error(f"Error al obtener órdenes abiertas: {e}")
            return []
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        """
        Obtiene posiciones abiertas.
        Nota: Para spot, las posiciones se calculan del balance.
        """
        if not self._connected:
            raise ConnectionError("No conectado a Binance")
        
        # En spot, no hay posiciones como tal, se calcula del balance
        return []
    
    def get_current_price(self, symbol: str) -> float:
        """Obtiene el precio actual de un símbolo."""
        ticker = self.get_ticker(symbol)
        return ticker['price']
