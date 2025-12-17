"""
Utilidades para mostrar resultados de forma visual en la terminal.
"""

from typing import Optional
from datetime import datetime


class DisplayManager:
    """Maneja la visualización de resultados en la terminal."""
    
    @staticmethod
    def print_header(title: str):
        """Imprime un encabezado decorativo."""
        width = 60
        print("\n" + "=" * width)
        print(f"  {title.upper()}")
        print("=" * width)
    
    @staticmethod
    def print_section(title: str):
        """Imprime un título de sección."""
        print(f"\n{'─' * 40}")
        print(f"  {title}")
        print('─' * 40)
    
    @staticmethod
    def print_signal(signal):
        """Imprime una señal de trading."""
        DisplayManager.print_header("SEÑAL DE TRADING")
        
        print(f"\n  Tipo:      {signal.type.value}")
        print(f"  Fuerza:    {signal.strength:.1f}%")
        print(f"  Precio:    ${signal.price:.4f}")
        print(f"  Timestamp: {signal.timestamp}")
        
        if signal.stop_loss:
            print(f"\n  🛑 Stop Loss:   ${signal.stop_loss:.4f}")
        if signal.take_profit:
            print(f"  🎯 Take Profit: ${signal.take_profit:.4f}")
        
        if signal.reasons:
            DisplayManager.print_section("Razones")
            for reason in signal.reasons:
                print(f"    • {reason}")
    
    @staticmethod
    def print_analysis(analysis):
        """Imprime el análisis de mercado."""
        DisplayManager.print_header(f"ANÁLISIS DE {analysis.symbol}")
        
        print(f"\n  📅 Fecha:       {analysis.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"  📈 Tendencia:   {analysis.trend} ({analysis.trend_strength:.0f}%)")
        print(f"  📊 Volatilidad: {analysis.volatility} ({analysis.volatility_value:.2f}%)")
        print(f"  ⚠️  Riesgo:      {analysis.risk_score:.1f}/10")
        
        if analysis.support_levels:
            DisplayManager.print_section("Soportes")
            for i, level in enumerate(analysis.support_levels, 1):
                print(f"    S{i}: ${level:.4f}")
        
        if analysis.resistance_levels:
            DisplayManager.print_section("Resistencias")
            for i, level in enumerate(analysis.resistance_levels, 1):
                print(f"    R{i}: ${level:.4f}")
        
        if analysis.key_insights:
            DisplayManager.print_section("Insights")
            for insight in analysis.key_insights:
                print(f"    {insight}")
    
    @staticmethod
    def print_setup(setup):
        """Imprime un setup de trading."""
        DisplayManager.print_header("SETUP DE TRADING")
        
        emoji = "🟢" if setup.position.value == "LONG" else "🔴"
        print(f"\n  {emoji} Posición:    {setup.position.value}")
        print(f"  💵 Entrada:     ${setup.entry_price:.4f}")
        print(f"  🛑 Stop Loss:   ${setup.stop_loss:.4f}")
        print(f"  🎯 TP1:         ${setup.take_profit_1:.4f}")
        print(f"  🎯 TP2:         ${setup.take_profit_2:.4f}")
        print(f"  📊 Risk/Reward: {setup.risk_reward:.2f}")
        print(f"  💪 Confianza:   {setup.confidence:.0f}%")
        print(f"  📏 Tamaño:      {setup.size_recommendation.upper()}")
        
        DisplayManager.print_section("Razones de Entrada")
        for reason in setup.reasons:
            print(f"    • {reason}")
    
    @staticmethod
    def print_backtest(results: dict):
        """Imprime resultados de backtest."""
        DisplayManager.print_header("RESULTADOS DE BACKTEST")
        
        print(f"\n  📊 Total trades:  {results['total_trades']}")
        print(f"  ✅ Ganadores:     {results['wins']}")
        print(f"  ❌ Perdedores:    {results['losses']}")
        print(f"  📈 Win Rate:      {results['win_rate']:.1f}%")
        print(f"  💰 Capital Final: ${results['final_capital']:.2f}")
        print(f"  📊 Retorno:       {results['return_pct']:.2f}%")
    
    @staticmethod
    def print_price_data(df, num_rows: int = 5):
        """Imprime datos de precio recientes."""
        DisplayManager.print_section("Datos Recientes")
        
        recent = df.tail(num_rows)
        print(f"\n  {'Fecha':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>12}")
        print("  " + "-" * 74)
        
        for idx, row in recent.iterrows():
            date_str = idx.strftime('%Y-%m-%d %H:%M') if hasattr(idx, 'strftime') else str(idx)[:16]
            print(f"  {date_str:<20} {row['open']:>10.4f} {row['high']:>10.4f} {row['low']:>10.4f} {row['close']:>10.4f} {row['volume']:>12.0f}")
    
    @staticmethod
    def print_indicators(df):
        """Imprime valores actuales de indicadores."""
        DisplayManager.print_section("Indicadores Actuales")
        
        last = df.iloc[-1]
        
        indicators = [
            ('RSI', 'rsi', '.1f'),
            ('MACD', 'macd', '.4f'),
            ('MACD Signal', 'macd_signal', '.4f'),
            ('ADX', 'adx', '.1f'),
            ('ATR', 'atr', '.4f'),
            ('Stoch %K', 'stoch_k', '.1f'),
            ('BB Upper', 'bb_upper', '.4f'),
            ('BB Lower', 'bb_lower', '.4f'),
            ('SMA 20', 'sma_20', '.4f'),
            ('SMA 50', 'sma_50', '.4f'),
            ('Volume Ratio', 'volume_ratio', '.2f'),
        ]
        
        for name, col, fmt in indicators:
            if col in df.columns and not pd.isna(last[col]):
                value = last[col]
                print(f"    {name:<15}: {value:{fmt}}")


# Importar pandas solo si es necesario para print_indicators
try:
    import pandas as pd
except ImportError:
    pass
