#!/usr/bin/env python3
"""
🚀 ANALIZADOR INTERACTIVO DE MERCADOS
=====================================

Script simple para analizar cualquier moneda o acción.
NO REQUIERE API KEYS - Usa fuentes públicas gratuitas.

Uso:
    python3 analizar.py              # Menú interactivo
    python3 analizar.py BTC          # Analizar Bitcoin
    python3 analizar.py ETH SOL XRP  # Analizar múltiples
"""

import sys
from datetime import datetime

# Importar módulos del sistema
from core import DataFetcher, TechnicalIndicators, SignalGenerator, MarketAnalyzer
from strategies import MultiIndicatorStrategy
from utils import DisplayManager


def format_price(precio):
    """Formatea el precio según su magnitud."""
    if precio is None:
        return "N/A"
    if precio < 0.0001:
        return f"${precio:.10f}"
    elif precio < 1:
        return f"${precio:.6f}"
    elif precio < 100:
        return f"${precio:.4f}"
    else:
        return f"${precio:,.2f}"


def analizar_moneda(symbol: str, mostrar_detalle: bool = True):
    """Analiza una moneda y muestra resultados."""
    display = DisplayManager()
    
    # Detectar tipo de mercado
    if '=' in symbol or symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']:
        market_type = 'forex'
        if '=' not in symbol:
            symbol = f"{symbol}=X"
    elif symbol.upper() in get_crypto_list():
        market_type = 'crypto'
    else:
        market_type = 'stock'
    
    print(f"\n{'='*60}")
    print(f"  📊 ANALIZANDO: {symbol.upper()}")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  🏪 Mercado: {market_type.upper()}")
    print(f"{'='*60}")
    
    # 1. Obtener datos
    fetcher = DataFetcher()
    df = fetcher.get_data(symbol, market_type)
    
    if df.empty or len(df) < 50:
        print(f"\n❌ No se pudieron obtener suficientes datos para {symbol}")
        return None
    
    # 2. Calcular indicadores
    df = TechnicalIndicators.calculate_all(df)
    
    # 3. Obtener precio actual
    precio_actual = df['close'].iloc[-1]
    precio_anterior = df['close'].iloc[-2]
    cambio = ((precio_actual - precio_anterior) / precio_anterior) * 100
    emoji_cambio = "🟢" if cambio > 0 else "🔴" if cambio < 0 else "⚪"
    
    # Formatear precio según magnitud (para memecoins con muchos decimales)
    if precio_actual < 0.0001:
        precio_fmt = f"${precio_actual:.10f}"
    elif precio_actual < 1:
        precio_fmt = f"${precio_actual:.6f}"
    elif precio_actual < 100:
        precio_fmt = f"${precio_actual:.4f}"
    else:
        precio_fmt = f"${precio_actual:,.2f}"
    
    print(f"\n  💰 PRECIO ACTUAL: {precio_fmt}")
    print(f"  {emoji_cambio} Cambio: {cambio:+.2f}%")
    
    # 4. Generar señal
    signal_gen = SignalGenerator()
    signal = signal_gen.generate_signal(df)
    
    print(f"\n  🎯 SEÑAL: {signal.type.value}")
    print(f"  💪 Fuerza: {signal.strength:.0f}%")
    
    if signal.stop_loss:
        print(f"  🛑 Stop Loss: {format_price(signal.stop_loss)}")
        print(f"  🎯 Take Profit: {format_price(signal.take_profit)}")
    
    # 5. Análisis de mercado
    analyzer = MarketAnalyzer()
    analysis = analyzer.analyze(df, symbol)
    
    print(f"\n  📈 Tendencia: {analysis.trend}")
    print(f"  📊 Volatilidad: {analysis.volatility}")
    print(f"  ⚠️  Riesgo: {analysis.risk_score:.1f}/10")
    
    # 6. Buscar setup
    strategy = MultiIndicatorStrategy()
    setup = strategy.find_setup(df)
    
    if setup:
        print(f"\n  {'='*50}")
        print(f"  🔥 ¡SETUP ENCONTRADO!")
        print(f"  {'='*50}")
        emoji = "🟢" if setup.position.value == "LONG" else "🔴"
        print(f"  {emoji} Posición: {setup.position.value}")
        print(f"  💵 Entrada: {format_price(setup.entry_price)}")
        print(f"  🛑 Stop Loss: {format_price(setup.stop_loss)}")
        print(f"  🎯 TP1: {format_price(setup.take_profit_1)}")
        print(f"  🎯 TP2: {format_price(setup.take_profit_2)}")
        print(f"  📊 Risk/Reward: {setup.risk_reward:.2f}")
        print(f"  💪 Confianza: {setup.confidence:.0f}%")
        print(f"  📏 Tamaño sugerido: {setup.size_recommendation.upper()}")
    else:
        print(f"\n  ⚪ No hay setup claro - ESPERAR")
    
    if mostrar_detalle and signal.reasons:
        print(f"\n  📋 RAZONES:")
        for reason in signal.reasons:
            print(f"     • {reason}")
    
    if mostrar_detalle and analysis.key_insights:
        print(f"\n  💡 INSIGHTS:")
        for insight in analysis.key_insights:
            print(f"     {insight}")
    
    if mostrar_detalle:
        print(f"\n  📊 NIVELES CLAVE:")
        if analysis.support_levels:
            for i, s in enumerate(analysis.support_levels[:3], 1):
                print(f"     Soporte {i}: {format_price(s)}")
        if analysis.resistance_levels:
            for i, r in enumerate(analysis.resistance_levels[:3], 1):
                print(f"     Resistencia {i}: {format_price(r)}")
    
    print(f"\n{'='*60}\n")
    
    return {
        'symbol': symbol,
        'precio': precio_actual,
        'cambio': cambio,
        'signal': signal,
        'analysis': analysis,
        'setup': setup
    }


def get_crypto_list():
    """Lista de criptomonedas conocidas."""
    return [
        'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT',
        'MATIC', 'SHIB', 'LTC', 'AVAX', 'LINK', 'UNI', 'ATOM',
        'XLM', 'ALGO', 'VET', 'FTM', 'SAND', 'MANA', 'AAVE',
        'AXS', 'THETA', 'EOS', 'XTZ', 'CAKE', 'NEO', 'PEPE',
        'ARB', 'OP', 'SUI', 'APT', 'INJ', 'TRX', 'NEAR', 'ICP',
        'FIL', 'HBAR', 'LDO', 'APE', 'CRO', 'QNT', 'MKR', 'RUNE',
        'EGLD', 'FLOW', 'KAVA', 'GMX', 'CFX', 'MINA', 'FXS',
        'SNX', 'RPL', 'IMX', 'ENJ', 'GRT', 'CHZ', '1INCH', 'BAT',
        'COMP', 'CRV', 'SUSHI', 'YFI', 'ZRX', 'KNC', 'REN',
        'BONK', 'WIF', 'FLOKI', 'GALA', 'ENS', 'LRC', 'MAGIC'
    ]


def menu_interactivo():
    """Muestra un menú interactivo."""
    print("\n" + "🚀"*25)
    print("  ANALIZADOR DE MERCADOS")
    print("  Sin API Keys - 100% Gratis")
    print("🚀"*25)
    
    print("\n📊 CRIPTOMONEDAS POPULARES:")
    print("   BTC, ETH, SOL, XRP, ADA, DOGE, DOT, MATIC")
    print("   AVAX, LINK, UNI, ATOM, LTC, SHIB, PEPE, ARB")
    
    print("\n📈 ACCIONES (ejemplos):")
    print("   AAPL, TSLA, MSFT, GOOGL, AMZN, META, NVDA")
    
    print("\n💱 FOREX (ejemplos):")
    print("   EURUSD, GBPUSD, USDJPY, AUDUSD")
    
    print("\n" + "-"*50)
    
    while True:
        try:
            entrada = input("\n🔍 Ingresa símbolo(s) a analizar (o 'salir'): ").strip()
            
            if entrada.lower() in ['salir', 'exit', 'q', 'quit']:
                print("\n👋 ¡Hasta pronto! Éxito en tus trades.")
                break
            
            if not entrada:
                continue
            
            # Permitir múltiples símbolos separados por espacio o coma
            simbolos = [s.strip().upper() for s in entrada.replace(',', ' ').split()]
            
            for simbolo in simbolos:
                analizar_moneda(simbolo)
            
            # Preguntar si quiere continuar
            continuar = input("¿Analizar otro? (Enter para sí, 'n' para salir): ").strip()
            if continuar.lower() == 'n':
                print("\n👋 ¡Hasta pronto! Éxito en tus trades.")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def escanear_mercado(tipo: str = 'crypto'):
    """Escanea múltiples activos buscando oportunidades."""
    print(f"\n🔍 ESCANEANDO MERCADO ({tipo.upper()})...")
    print("="*60)
    
    if tipo == 'crypto':
        simbolos = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'LINK', 'DOT', 'MATIC']
    elif tipo == 'stock':
        simbolos = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']
    else:
        simbolos = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X']
    
    oportunidades = []
    
    for simbolo in simbolos:
        try:
            resultado = analizar_moneda(simbolo, mostrar_detalle=False)
            if resultado and resultado['setup']:
                oportunidades.append(resultado)
        except Exception as e:
            print(f"  ⚠️ Error con {simbolo}: {e}")
    
    if oportunidades:
        print("\n" + "🔥"*25)
        print("  OPORTUNIDADES ENCONTRADAS")
        print("🔥"*25)
        
        # Ordenar por confianza
        oportunidades.sort(key=lambda x: x['setup'].confidence, reverse=True)
        
        for opp in oportunidades:
            setup = opp['setup']
            emoji = "🟢" if setup.position.value == "LONG" else "🔴"
            print(f"\n  {emoji} {opp['symbol']}: {setup.position.value}")
            print(f"     Confianza: {setup.confidence:.0f}% | R/R: {setup.risk_reward:.2f}")
            print(f"     Entrada: {format_price(setup.entry_price)}")
    else:
        print("\n  ⚪ No se encontraron oportunidades claras")
    
    return oportunidades


def main():
    """Punto de entrada principal."""
    if len(sys.argv) > 1:
        # Modo línea de comandos
        if sys.argv[1].lower() == '--scan':
            tipo = sys.argv[2] if len(sys.argv) > 2 else 'crypto'
            escanear_mercado(tipo)
        else:
            # Analizar símbolos pasados como argumentos
            for simbolo in sys.argv[1:]:
                analizar_moneda(simbolo.upper())
    else:
        # Modo interactivo
        menu_interactivo()


if __name__ == '__main__':
    main()
