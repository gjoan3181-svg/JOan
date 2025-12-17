"""
Gestión de Riesgos
===================
Sistema de control y gestión de riesgos para trading.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class TradeRisk:
    """Representa el riesgo de una operación."""
    symbol: str
    side: str  # 'BUY' o 'SELL'
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    risk_amount: float  # Cantidad en riesgo en USDT
    risk_percent: float  # Porcentaje del capital en riesgo
    reward_ratio: float  # Risk/Reward ratio
    is_approved: bool
    rejection_reason: Optional[str] = None


class RiskManager:
    """
    Gestor de riesgos para operaciones de trading.
    
    Implementa múltiples controles:
    - Tamaño máximo de posición
    - Riesgo máximo por operación
    - Límite de operaciones diarias
    - Drawdown máximo permitido
    - Correlación de posiciones
    """
    
    def __init__(
        self,
        max_position_size: float = 0.1,  # 10% del capital
        max_risk_per_trade: float = 0.02,  # 2% por operación
        max_daily_trades: int = 10,
        max_daily_loss: float = 0.05,  # 5% pérdida diaria máxima
        min_risk_reward: float = 1.5,  # Mínimo 1.5:1
        max_open_positions: int = 3,
        max_drawdown: float = 0.15  # 15% drawdown máximo
    ):
        """
        Inicializa el gestor de riesgos.
        
        Args:
            max_position_size: Tamaño máximo de posición (% del capital)
            max_risk_per_trade: Riesgo máximo por operación (% del capital)
            max_daily_trades: Número máximo de operaciones por día
            max_daily_loss: Pérdida máxima diaria permitida (% del capital)
            min_risk_reward: Ratio riesgo/recompensa mínimo
            max_open_positions: Número máximo de posiciones abiertas
            max_drawdown: Drawdown máximo permitido
        """
        self.max_position_size = max_position_size
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_trades = max_daily_trades
        self.max_daily_loss = max_daily_loss
        self.min_risk_reward = min_risk_reward
        self.max_open_positions = max_open_positions
        self.max_drawdown = max_drawdown
        
        # Estado interno
        self._daily_trades: List[Dict] = []
        self._daily_pnl: float = 0.0
        self._open_positions: List[Dict] = []
        self._peak_capital: float = 0.0
        self._current_capital: float = 0.0
        self._last_reset: datetime = datetime.now()
    
    def set_capital(self, capital: float) -> None:
        """
        Establece el capital disponible.
        
        Args:
            capital: Capital total en USDT
        """
        self._current_capital = capital
        if self._peak_capital == 0:
            self._peak_capital = capital
        elif capital > self._peak_capital:
            self._peak_capital = capital
    
    def evaluate_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float
    ) -> TradeRisk:
        """
        Evalúa si una operación cumple con las reglas de riesgo.
        
        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            entry_price: Precio de entrada
            quantity: Cantidad a operar
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            
        Returns:
            TradeRisk con la evaluación
        """
        # Resetear contadores diarios si es necesario
        self._check_daily_reset()
        
        # Calcular valores
        position_value = entry_price * quantity
        
        if side == 'BUY':
            risk_per_unit = entry_price - stop_loss
            reward_per_unit = take_profit - entry_price
        else:
            risk_per_unit = stop_loss - entry_price
            reward_per_unit = entry_price - take_profit
        
        risk_amount = abs(risk_per_unit * quantity)
        reward_amount = abs(reward_per_unit * quantity)
        
        risk_percent = risk_amount / self._current_capital if self._current_capital > 0 else 0
        reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        position_percent = position_value / self._current_capital if self._current_capital > 0 else 0
        
        # Verificar reglas
        rejection_reasons = []
        
        # 1. Verificar tamaño de posición
        if position_percent > self.max_position_size:
            rejection_reasons.append(
                f"Posición muy grande: {position_percent:.1%} > {self.max_position_size:.1%}"
            )
        
        # 2. Verificar riesgo por operación
        if risk_percent > self.max_risk_per_trade:
            rejection_reasons.append(
                f"Riesgo muy alto: {risk_percent:.1%} > {self.max_risk_per_trade:.1%}"
            )
        
        # 3. Verificar ratio riesgo/recompensa
        if reward_ratio < self.min_risk_reward:
            rejection_reasons.append(
                f"R/R insuficiente: {reward_ratio:.2f} < {self.min_risk_reward}"
            )
        
        # 4. Verificar número de operaciones diarias
        if len(self._daily_trades) >= self.max_daily_trades:
            rejection_reasons.append(
                f"Límite diario alcanzado: {len(self._daily_trades)}/{self.max_daily_trades}"
            )
        
        # 5. Verificar pérdida diaria
        if self._daily_pnl <= -self._current_capital * self.max_daily_loss:
            rejection_reasons.append(
                f"Pérdida diaria máxima alcanzada: {self._daily_pnl:.2f}"
            )
        
        # 6. Verificar posiciones abiertas
        if len(self._open_positions) >= self.max_open_positions:
            rejection_reasons.append(
                f"Máximo de posiciones abiertas: {len(self._open_positions)}/{self.max_open_positions}"
            )
        
        # 7. Verificar drawdown
        current_drawdown = (self._peak_capital - self._current_capital) / self._peak_capital
        if current_drawdown >= self.max_drawdown:
            rejection_reasons.append(
                f"Drawdown máximo alcanzado: {current_drawdown:.1%} >= {self.max_drawdown:.1%}"
            )
        
        # 8. Verificar stop loss válido
        if side == 'BUY' and stop_loss >= entry_price:
            rejection_reasons.append("Stop loss inválido para compra (debe ser menor al precio)")
        elif side == 'SELL' and stop_loss <= entry_price:
            rejection_reasons.append("Stop loss inválido para venta (debe ser mayor al precio)")
        
        is_approved = len(rejection_reasons) == 0
        
        trade_risk = TradeRisk(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            risk_percent=risk_percent,
            reward_ratio=reward_ratio,
            is_approved=is_approved,
            rejection_reason="; ".join(rejection_reasons) if rejection_reasons else None
        )
        
        if is_approved:
            logger.info(f"✓ Operación aprobada: {symbol} {side} {quantity} @ {entry_price}")
            logger.info(f"  Riesgo: {risk_percent:.2%}, R/R: {reward_ratio:.2f}")
        else:
            logger.warning(f"✗ Operación rechazada: {trade_risk.rejection_reason}")
        
        return trade_risk
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_amount: float = None
    ) -> float:
        """
        Calcula el tamaño óptimo de posición basado en el riesgo.
        
        Args:
            entry_price: Precio de entrada
            stop_loss: Precio de stop loss
            risk_amount: Cantidad a arriesgar (opcional, usa max_risk_per_trade)
            
        Returns:
            Cantidad óptima a operar
        """
        if risk_amount is None:
            risk_amount = self._current_capital * self.max_risk_per_trade
        
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        
        # Limitar por tamaño máximo de posición
        max_size = (self._current_capital * self.max_position_size) / entry_price
        position_size = min(position_size, max_size)
        
        return position_size
    
    def register_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        pnl: float = 0.0
    ) -> None:
        """
        Registra una operación ejecutada.
        
        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad operada
            entry_price: Precio de entrada
            pnl: Ganancia/pérdida (si es cierre)
        """
        trade = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': entry_price,
            'pnl': pnl,
            'timestamp': datetime.now()
        }
        
        self._daily_trades.append(trade)
        self._daily_pnl += pnl
        self._current_capital += pnl
        
        if self._current_capital > self._peak_capital:
            self._peak_capital = self._current_capital
    
    def add_open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float
    ) -> None:
        """Añade una posición abierta al tracking."""
        self._open_positions.append({
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': entry_price,
            'timestamp': datetime.now()
        })
    
    def remove_open_position(self, symbol: str, side: str) -> None:
        """Elimina una posición del tracking."""
        self._open_positions = [
            p for p in self._open_positions 
            if not (p['symbol'] == symbol and p['side'] == side)
        ]
    
    def _check_daily_reset(self) -> None:
        """Reinicia contadores si es un nuevo día."""
        now = datetime.now()
        if now.date() > self._last_reset.date():
            self._daily_trades = []
            self._daily_pnl = 0.0
            self._last_reset = now
            logger.info("Contadores diarios reiniciados")
    
    def get_daily_stats(self) -> Dict:
        """Retorna estadísticas del día."""
        return {
            'trades_count': len(self._daily_trades),
            'max_trades': self.max_daily_trades,
            'daily_pnl': self._daily_pnl,
            'daily_pnl_percent': self._daily_pnl / self._current_capital if self._current_capital > 0 else 0,
            'open_positions': len(self._open_positions),
            'max_positions': self.max_open_positions,
            'current_capital': self._current_capital,
            'peak_capital': self._peak_capital,
            'drawdown': (self._peak_capital - self._current_capital) / self._peak_capital if self._peak_capital > 0 else 0
        }
    
    def can_trade(self) -> bool:
        """Verifica si se puede operar según las reglas actuales."""
        self._check_daily_reset()
        
        # Verificar límites
        if len(self._daily_trades) >= self.max_daily_trades:
            return False
        
        if self._daily_pnl <= -self._current_capital * self.max_daily_loss:
            return False
        
        if len(self._open_positions) >= self.max_open_positions:
            return False
        
        drawdown = (self._peak_capital - self._current_capital) / self._peak_capital if self._peak_capital > 0 else 0
        if drawdown >= self.max_drawdown:
            return False
        
        return True
