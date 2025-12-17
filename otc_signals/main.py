#!/usr/bin/env python3
"""
OTC Market Signal Generator
===========================

Sistema de análisis técnico y generación de señales para mercados OTC,
criptomonedas y forex.

Uso:
    python main.py                          # Análisis de BTC/USDT
    python main.py --symbol ETH/USDT        # Análisis de ETH
    python main.py --symbol AAPL --market stock  # Análisis de acciones
    python main.py --symbol EURUSD=X --market forex  # Análisis de forex
    python main.py --scan                   # Escanear múltiples activos
"""

import argparse
import sys
from datetime import datetime

# Importar módulos del sistema
from core import DataFetcher, TechnicalIndicators, SignalGenerator, MarketAnalyzer
from strategies import MultiIndicatorStrategy
from utils import DisplayManager


def analyze_single(symbol: str, market_type: str = 'crypto', **kwargs):
    """
    Realiza análisis completo de un solo activo.
    
    Args:
        symbol: Símbolo del activo
        market_type: Tipo de mercado ('crypto', 'stock', 'forex')
    """
    display = DisplayManager()
    
    print(f"\n🔄 Obteniendo datos de {symbol}...")
    
    # 1. Obtener datos
    fetcher = DataFetcher()
    df = fetcher.get_data(symbol, market_type, **kwargs)
    
    if df.empty:
        print(f"❌ No se pudieron obtener datos para {symbol}")
        return
    
    print(f"✅ {len(df)} velas obtenidas")
    display.print_price_data(df)
    
    # 2. Calcular indicadores
    print("\n🔄 Calculando indicadores técnicos...")
    df = TechnicalIndicators.calculate_all(df)
    display.print_indicators(df)
    
    # 3. Generar señal
    print("\n🔄 Generando señal...")
    signal_gen = SignalGenerator()
    signal = signal_gen.generate_signal(df)
    display.print_signal(signal)
    
    # 4. Análisis de mercado
    print("\n🔄 Analizando condiciones de mercado...")
    analyzer = MarketAnalyzer()
    analysis = analyzer.analyze(df, symbol)
    display.print_analysis(analysis)
    
    # 5. Buscar setup de trading
    print("\n🔄 Buscando setup de trading...")
    strategy = MultiIndicatorStrategy()
    setup = strategy.find_setup(df)
    
    if setup:
        display.print_setup(setup)
    else:
        print("\n⚪ No hay setup claro en este momento.")
        print("   Esperando mejores condiciones de entrada...")
    
    # 6. Resumen final
    print_summary(signal, analysis, setup)
    
    return df, signal, analysis, setup


def scan_multiple(symbols: list, market_type: str = 'crypto'):
    """
    Escanea múltiples activos en busca de oportunidades.
    
    Args:
        symbols: Lista de símbolos a analizar
        market_type: Tipo de mercado
    """
    display = DisplayManager()
    display.print_header("ESCÁNER DE MERCADO")
    
    fetcher = DataFetcher()
    signal_gen = SignalGenerator()
    strategy = MultiIndicatorStrategy()
    
    opportunities = []
    
    for symbol in symbols:
        print(f"\n  Analizando {symbol}...", end=" ")
        
        try:
            df = fetcher.get_data(symbol, market_type)
            df = TechnicalIndicators.calculate_all(df)
            signal = signal_gen.generate_signal(df)
            setup = strategy.find_setup(df)
            
            print(f"{signal.type.value}")
            
            if setup and setup.confidence >= 60:
                opportunities.append({
                    'symbol': symbol,
                    'signal': signal,
                    'setup': setup
                })
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Mostrar oportunidades encontradas
    if opportunities:
        display.print_header("OPORTUNIDADES ENCONTRADAS")
        
        # Ordenar por confianza
        opportunities.sort(key=lambda x: x['setup'].confidence, reverse=True)
        
        for opp in opportunities:
            print(f"\n  {'=' * 40}")
            print(f"  📊 {opp['symbol']}")
            print(f"  {opp['signal'].type.value} | Confianza: {opp['setup'].confidence:.0f}%")
            print(f"  Entrada: ${opp['setup'].entry_price:.4f}")
            print(f"  R/R: {opp['setup'].risk_reward:.2f}")
    else:
        print("\n  ⚪ No se encontraron oportunidades claras")


def run_backtest(symbol: str, market_type: str = 'crypto'):
    """
    Ejecuta un backtest de la estrategia.
    
    Args:
        symbol: Símbolo a testear
        market_type: Tipo de mercado
    """
    display = DisplayManager()
    display.print_header(f"BACKTEST: {symbol}")
    
    print("\n🔄 Obteniendo datos históricos...")
    
    fetcher = DataFetcher()
    df = fetcher.get_data(symbol, market_type)
    
    print(f"✅ {len(df)} velas para backtest")
    
    print("\n🔄 Calculando indicadores...")
    df = TechnicalIndicators.calculate_all(df)
    
    print("\n🔄 Ejecutando backtest...")
    strategy = MultiIndicatorStrategy()
    results = strategy.backtest_simple(df)
    
    display.print_backtest(results)
    
    return results


def print_summary(signal, analysis, setup):
    """Imprime un resumen ejecutivo."""
    print("\n" + "=" * 60)
    print("  📋 RESUMEN EJECUTIVO")
    print("=" * 60)
    
    # Recomendación
    print(f"\n  🎯 Señal:     {signal.type.value}")
    print(f"  📈 Tendencia: {analysis.trend}")
    print(f"  ⚠️  Riesgo:    {analysis.risk_score:.1f}/10")
    
    if setup:
        print(f"\n  💡 ACCIÓN RECOMENDADA:")
        action = "COMPRAR" if setup.position.value == "LONG" else "VENDER"
        print(f"     {action} con tamaño {setup.size_recommendation.upper()}")
        print(f"     Entrada: ${setup.entry_price:.4f}")
        print(f"     SL: ${setup.stop_loss:.4f}")
        print(f"     TP: ${setup.take_profit_2:.4f}")
    else:
        print(f"\n  💡 ACCIÓN RECOMENDADA:")
        print(f"     ESPERAR - No hay setup claro")
    
    print("\n" + "=" * 60)


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description='OTC Market Signal Generator - Análisis técnico y señales de trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                                    Analiza BTC/USDT
  %(prog)s --symbol ETH/USDT                  Analiza Ethereum
  %(prog)s --symbol AAPL --market stock       Analiza Apple
  %(prog)s --symbol EURUSD=X --market forex   Analiza EUR/USD
  %(prog)s --scan                             Escanea múltiples activos
  %(prog)s --backtest --symbol BTC/USDT       Backtest de BTC
        """
    )
    
    parser.add_argument(
        '--symbol', '-s',
        type=str,
        default='BTC/USDT',
        help='Símbolo a analizar (default: BTC/USDT)'
    )
    
    parser.add_argument(
        '--market', '-m',
        type=str,
        choices=['crypto', 'stock', 'forex'],
        default='crypto',
        help='Tipo de mercado (default: crypto)'
    )
    
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Escanear múltiples activos'
    )
    
    parser.add_argument(
        '--backtest', '-b',
        action='store_true',
        help='Ejecutar backtest de la estrategia'
    )
    
    parser.add_argument(
        '--timeframe', '-t',
        type=str,
        default='1h',
        help='Timeframe para crypto (default: 1h)'
    )
    
    parser.add_argument(
        '--symbols-file',
        type=str,
        help='Archivo con lista de símbolos para escanear'
    )
    
    args = parser.parse_args()
    
    print("\n" + "🚀" * 20)
    print("  OTC MARKET SIGNAL GENERATOR")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀" * 20)
    
    try:
        if args.scan:
            # Escanear múltiples activos
            if args.market == 'crypto':
                symbols = [
                    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT',
                    'SOL/USDT', 'ADA/USDT', 'DOGE/USDT', 'DOT/USDT'
                ]
            elif args.market == 'stock':
                symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
            else:
                symbols = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X']
            
            scan_multiple(symbols, args.market)
        
        elif args.backtest:
            # Ejecutar backtest
            run_backtest(args.symbol, args.market)
        
        else:
            # Análisis de un solo activo
            kwargs = {}
            if args.market == 'crypto':
                kwargs['timeframe'] = args.timeframe
            
            analyze_single(args.symbol, args.market, **kwargs)
    
    except KeyboardInterrupt:
        print("\n\n👋 Análisis cancelado por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
