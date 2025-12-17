"""
Bot de Trading Principal
=========================
Clase principal que orquesta todo el sistema de trading.
"""

import time
import schedule
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger

from .config import get_settings
from .exchange.binance_client import BinanceClient
from .analysis.indicators import TechnicalIndicators
from .analysis.signals import Signal, SignalType
from .strategies.ml_strategy import MLStrategy
from .strategies.base_strategy import BaseStrategy
from .risk_management.risk_manager import RiskManager
from .utils.logger import setup_logger


@dataclass
class TradePosition:
    """Representa una posición activa."""
    symbol: str
    side: str  # 'LONG' o 'SHORT'
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    order_id: str


class TradingBot:
    """
    Bot de trading automatizado con IA.
    
    Funcionalidades principales:
    - Conexión a exchanges
    - Análisis de mercado con IA
    - Ejecución automática de órdenes
    - Gestión de riesgos
    - Monitoreo de posiciones
    """
    
    def __init__(
        self,
        symbol: str = None,
        timeframe: str = None,
        strategy: BaseStrategy = None,
        testnet: bool = True
    ):
        """
        Inicializa el bot de trading.
        
        Args:
            symbol: Par de trading (ej: 'BTCUSDT')
            timeframe: Intervalo de tiempo ('1h', '4h', etc.)
            strategy: Estrategia de trading a usar
            testnet: Si usar testnet (recomendado para pruebas)
        """
        self.settings = get_settings()
        self.symbol = symbol or self.settings.trading.symbol
        self.timeframe = timeframe or self.settings.trading.timeframe
        self.testnet = testnet
        
        # Componentes
        self.exchange: Optional[BinanceClient] = None
        self.strategy: Optional[BaseStrategy] = strategy
        self.risk_manager: Optional[RiskManager] = None
        
        # Estado
        self._is_running = False
        self._position: Optional[TradePosition] = None
        self._last_signal: Optional[Signal] = None
        self._stats = {
            'trades_executed': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0
        }
        
        # Configurar logger
        setup_logger(self.settings.log_level)
    
    def initialize(self) -> bool:
        """
        Inicializa todos los componentes del bot.
        
        Returns:
            True si la inicialización fue exitosa
        """
        logger.info("=" * 50)
        logger.info("Inicializando Trading Bot")
        logger.info("=" * 50)
        
        try:
            # 1. Conectar al exchange
            logger.info(f"Conectando a Binance {'TESTNET' if self.testnet else 'MAINNET'}...")
            self.exchange = BinanceClient(testnet=self.testnet)
            
            if not self.exchange.connect():
                logger.error("No se pudo conectar al exchange")
                return False
            
            # 2. Obtener balance inicial
            balances = self.exchange.get_balance('USDT')
            if balances:
                capital = balances[0].free
                logger.info(f"Balance USDT: {capital:.2f}")
            else:
                capital = 10000.0  # Default para simulación
                logger.warning(f"Usando capital simulado: {capital:.2f}")
            
            # 3. Inicializar gestor de riesgos
            self.risk_manager = RiskManager(
                max_position_size=self.settings.trading.max_position_size,
                max_risk_per_trade=self.settings.trading.max_risk_per_trade
            )
            self.risk_manager.set_capital(capital)
            
            # 4. Inicializar estrategia
            if self.strategy is None:
                self.strategy = MLStrategy(
                    model_type=self.settings.model.model_type,
                    min_confidence=self.settings.model.prediction_threshold
                )
            
            # Obtener datos históricos para entrenar
            logger.info(f"Obteniendo datos históricos de {self.symbol}...")
            historical_data = self.exchange.get_klines(
                symbol=self.symbol,
                interval=self.timeframe,
                limit=500
            )
            
            # Añadir indicadores
            historical_data = TechnicalIndicators.add_all_indicators(historical_data)
            
            # Inicializar estrategia con datos
            self.strategy.initialize(historical_data=historical_data)
            
            logger.info("Bot inicializado correctamente")
            logger.info(f"  Símbolo: {self.symbol}")
            logger.info(f"  Timeframe: {self.timeframe}")
            logger.info(f"  Estrategia: {self.strategy.name}")
            logger.info(f"  Capital: {capital:.2f} USDT")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar: {e}")
            return False
    
    def analyze_market(self) -> Optional[Signal]:
        """
        Analiza el mercado y genera una señal.
        
        Returns:
            Signal con la recomendación
        """
        try:
            # Obtener datos actuales
            df = self.exchange.get_klines(
                symbol=self.symbol,
                interval=self.timeframe,
                limit=200
            )
            
            # Añadir indicadores
            df = TechnicalIndicators.add_all_indicators(df)
            
            # Generar señal
            signal = self.strategy.generate_signal(df)
            
            self._last_signal = signal
            
            logger.info(f"Señal: {signal}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error al analizar mercado: {e}")
            return None
    
    def execute_signal(self, signal: Signal) -> bool:
        """
        Ejecuta una señal de trading.
        
        Args:
            signal: Señal a ejecutar
            
        Returns:
            True si se ejecutó correctamente
        """
        if signal.signal_type == SignalType.HOLD:
            return False
        
        # Verificar si hay posición abierta
        if self._position is not None:
            logger.info(f"Ya hay posición abierta: {self._position.side}")
            
            # Verificar si la señal es opuesta (cerrar posición)
            if (self._position.side == 'LONG' and signal.signal_type == SignalType.SELL) or \
               (self._position.side == 'SHORT' and signal.signal_type == SignalType.BUY):
                return self._close_position(signal.price)
            
            return False
        
        # Verificar si se puede operar
        if not self.risk_manager.can_trade():
            logger.warning("No se puede operar según reglas de riesgo")
            return False
        
        # Calcular tamaño de posición
        side = 'BUY' if signal.signal_type == SignalType.BUY else 'SELL'
        position_size = self.risk_manager.calculate_position_size(
            entry_price=signal.price,
            stop_loss=signal.stop_loss
        )
        
        # Evaluar riesgo
        trade_risk = self.risk_manager.evaluate_trade(
            symbol=self.symbol,
            side=side,
            entry_price=signal.price,
            quantity=position_size,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit
        )
        
        if not trade_risk.is_approved:
            logger.warning(f"Operación rechazada: {trade_risk.rejection_reason}")
            return False
        
        # Ejecutar orden
        try:
            order = self.exchange.place_market_order(
                symbol=self.symbol,
                side=side,
                quantity=position_size
            )
            
            if order.status in ['FILLED', 'NEW']:
                self._position = TradePosition(
                    symbol=self.symbol,
                    side='LONG' if side == 'BUY' else 'SHORT',
                    quantity=position_size,
                    entry_price=order.avg_fill_price or signal.price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    entry_time=datetime.now(),
                    order_id=order.order_id
                )
                
                # Registrar en gestor de riesgos
                self.risk_manager.add_open_position(
                    symbol=self.symbol,
                    side=self._position.side,
                    quantity=position_size,
                    entry_price=self._position.entry_price
                )
                
                # Colocar stop loss
                sl_side = 'SELL' if side == 'BUY' else 'BUY'
                self.exchange.place_stop_loss_order(
                    symbol=self.symbol,
                    side=sl_side,
                    quantity=position_size,
                    stop_price=signal.stop_loss
                )
                
                self._stats['trades_executed'] += 1
                
                logger.info(f"✓ Posición abierta: {self._position.side} {position_size} @ {self._position.entry_price}")
                logger.info(f"  Stop Loss: {signal.stop_loss}")
                logger.info(f"  Take Profit: {signal.take_profit}")
                
                return True
            
        except Exception as e:
            logger.error(f"Error al ejecutar orden: {e}")
        
        return False
    
    def _close_position(self, current_price: float) -> bool:
        """
        Cierra la posición actual.
        
        Args:
            current_price: Precio actual
            
        Returns:
            True si se cerró correctamente
        """
        if self._position is None:
            return False
        
        try:
            # Cerrar posición
            close_side = 'SELL' if self._position.side == 'LONG' else 'BUY'
            
            order = self.exchange.place_market_order(
                symbol=self.symbol,
                side=close_side,
                quantity=self._position.quantity
            )
            
            if order.status in ['FILLED', 'NEW']:
                close_price = order.avg_fill_price or current_price
                
                # Calcular PnL
                if self._position.side == 'LONG':
                    pnl = (close_price - self._position.entry_price) * self._position.quantity
                else:
                    pnl = (self._position.entry_price - close_price) * self._position.quantity
                
                # Actualizar estadísticas
                self._stats['total_pnl'] += pnl
                if pnl > 0:
                    self._stats['wins'] += 1
                else:
                    self._stats['losses'] += 1
                
                # Registrar en gestor de riesgos
                self.risk_manager.register_trade(
                    symbol=self.symbol,
                    side=close_side,
                    quantity=self._position.quantity,
                    entry_price=close_price,
                    pnl=pnl
                )
                self.risk_manager.remove_open_position(self.symbol, self._position.side)
                
                logger.info(f"✓ Posición cerrada @ {close_price}")
                logger.info(f"  PnL: {pnl:+.2f} USDT")
                logger.info(f"  Total PnL: {self._stats['total_pnl']:+.2f} USDT")
                
                # Cancelar órdenes pendientes
                open_orders = self.exchange.get_open_orders(self.symbol)
                for o in open_orders:
                    self.exchange.cancel_order(self.symbol, o.order_id)
                
                self._position = None
                return True
                
        except Exception as e:
            logger.error(f"Error al cerrar posición: {e}")
        
        return False
    
    def check_position(self) -> None:
        """Verifica el estado de la posición actual."""
        if self._position is None:
            return
        
        try:
            current_price = self.exchange.get_current_price(self.symbol)
            
            # Verificar stop loss
            if self._position.side == 'LONG' and current_price <= self._position.stop_loss:
                logger.warning(f"Stop loss alcanzado: {current_price}")
                self._close_position(current_price)
                return
            
            if self._position.side == 'SHORT' and current_price >= self._position.stop_loss:
                logger.warning(f"Stop loss alcanzado: {current_price}")
                self._close_position(current_price)
                return
            
            # Verificar take profit
            if self._position.side == 'LONG' and current_price >= self._position.take_profit:
                logger.info(f"Take profit alcanzado: {current_price}")
                self._close_position(current_price)
                return
            
            if self._position.side == 'SHORT' and current_price <= self._position.take_profit:
                logger.info(f"Take profit alcanzado: {current_price}")
                self._close_position(current_price)
                return
            
            # Verificar con la estrategia
            df = self.exchange.get_klines(self.symbol, self.timeframe, 50)
            df = TechnicalIndicators.add_all_indicators(df)
            
            if self.strategy.should_close_position(df, self._position.side, self._position.entry_price):
                self._close_position(current_price)
                
        except Exception as e:
            logger.error(f"Error al verificar posición: {e}")
    
    def run_cycle(self) -> None:
        """Ejecuta un ciclo de trading."""
        logger.debug(f"Ejecutando ciclo de trading - {datetime.now()}")
        
        # 1. Verificar posición actual
        self.check_position()
        
        # 2. Analizar mercado
        signal = self.analyze_market()
        
        if signal is None:
            return
        
        # 3. Ejecutar señal si aplica
        if signal.signal_type != SignalType.HOLD:
            self.execute_signal(signal)
    
    def run(self, interval_seconds: int = 60) -> None:
        """
        Inicia el bot en modo de ejecución continua.
        
        Args:
            interval_seconds: Segundos entre cada ciclo
        """
        if not self.initialize():
            logger.error("No se pudo inicializar el bot")
            return
        
        self._is_running = True
        logger.info(f"Bot iniciado - Ejecutando cada {interval_seconds}s")
        logger.info("Presiona Ctrl+C para detener")
        
        try:
            while self._is_running:
                self.run_cycle()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Detenido por usuario")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Detiene el bot de manera segura."""
        logger.info("Deteniendo bot...")
        
        self._is_running = False
        
        # Cerrar posiciones abiertas
        if self._position is not None:
            logger.warning("Cerrando posición abierta...")
            current_price = self.exchange.get_current_price(self.symbol)
            self._close_position(current_price)
        
        # Desconectar
        if self.exchange:
            self.exchange.disconnect()
        
        # Mostrar estadísticas finales
        self._print_stats()
    
    def _print_stats(self) -> None:
        """Muestra estadísticas del bot."""
        logger.info("=" * 50)
        logger.info("ESTADÍSTICAS FINALES")
        logger.info("=" * 50)
        logger.info(f"  Operaciones ejecutadas: {self._stats['trades_executed']}")
        logger.info(f"  Ganadoras: {self._stats['wins']}")
        logger.info(f"  Perdedoras: {self._stats['losses']}")
        
        if self._stats['trades_executed'] > 0:
            win_rate = self._stats['wins'] / self._stats['trades_executed'] * 100
            logger.info(f"  Win Rate: {win_rate:.1f}%")
        
        logger.info(f"  PnL Total: {self._stats['total_pnl']:+.2f} USDT")
        
        if self.risk_manager:
            daily_stats = self.risk_manager.get_daily_stats()
            logger.info(f"  Drawdown actual: {daily_stats['drawdown']:.1%}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del bot."""
        return {
            'is_running': self._is_running,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'testnet': self.testnet,
            'position': self._position.__dict__ if self._position else None,
            'last_signal': str(self._last_signal) if self._last_signal else None,
            'stats': self._stats,
            'risk_stats': self.risk_manager.get_daily_stats() if self.risk_manager else {}
        }
