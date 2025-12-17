#!/usr/bin/env python3
"""
Trading Bot con IA - Punto de Entrada Principal
=================================================
Bot de trading automatizado que usa Machine Learning
para generar señales y ejecutar operaciones.

Uso:
    python main.py                    # Modo normal
    python main.py --paper            # Paper trading (simulación)
    python main.py --backtest         # Backtesting
    python main.py --train            # Solo entrenar modelo
"""

import argparse
import sys
from datetime import datetime, timedelta

from trading_bot.bot import TradingBot
from trading_bot.config import get_settings
from trading_bot.exchange.binance_client import BinanceClient
from trading_bot.analysis.indicators import TechnicalIndicators
from trading_bot.strategies.ml_strategy import MLStrategy
from trading_bot.utils.logger import setup_logger
from loguru import logger


def run_live_trading(args):
    """Ejecuta el bot en modo trading en vivo o testnet."""
    logger.info("=" * 60)
    logger.info("TRADING BOT CON INTELIGENCIA ARTIFICIAL")
    logger.info("=" * 60)
    
    # Usar testnet por defecto para seguridad
    testnet = not args.live
    
    if not testnet:
        logger.warning("!" * 60)
        logger.warning("MODO REAL ACTIVADO - USANDO DINERO REAL")
        logger.warning("!" * 60)
        
        # Confirmación de seguridad
        confirm = input("¿Estás seguro de operar con dinero real? (escribe 'SI' para confirmar): ")
        if confirm != 'SI':
            logger.info("Operación cancelada")
            return
    
    # Crear y ejecutar bot
    bot = TradingBot(
        symbol=args.symbol,
        timeframe=args.timeframe,
        testnet=testnet
    )
    
    # Ejecutar
    bot.run(interval_seconds=args.interval)


def run_backtest(args):
    """Ejecuta backtesting con datos históricos."""
    logger.info("=" * 60)
    logger.info("MODO BACKTESTING")
    logger.info("=" * 60)
    
    from trading_bot.analysis.signals import SignalGenerator
    from trading_bot.models.ml_predictor import MLPredictor
    from trading_bot.models.feature_engineer import FeatureEngineer
    import pandas as pd
    
    # Conectar para obtener datos históricos
    exchange = BinanceClient(testnet=True)
    exchange.connect()
    
    logger.info(f"Obteniendo datos históricos de {args.symbol}...")
    
    # Obtener datos (máximo 1000 velas por request)
    df = exchange.get_klines(
        symbol=args.symbol,
        interval=args.timeframe,
        limit=1000
    )
    
    logger.info(f"Datos obtenidos: {len(df)} velas")
    
    # Añadir indicadores
    df = TechnicalIndicators.add_all_indicators(df)
    
    # Dividir datos: 70% entrenamiento, 30% test
    train_size = int(len(df) * 0.7)
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]
    
    logger.info(f"Datos de entrenamiento: {len(train_df)}")
    logger.info(f"Datos de prueba: {len(test_df)}")
    
    # Entrenar modelo
    feature_engineer = FeatureEngineer()
    predictor = MLPredictor(model_type=args.model)
    predictor.feature_engineer = feature_engineer
    
    metrics = predictor.train(train_df)
    
    logger.info("Modelo entrenado:")
    logger.info(f"  Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"  F1 Score: {metrics['f1']:.4f}")
    
    # Inicializar estrategia
    strategy = MLStrategy(model_type=args.model)
    strategy.predictor = predictor
    strategy.feature_engineer = feature_engineer
    strategy.signal_generator = SignalGenerator()
    strategy._is_initialized = True
    
    # Simular trading
    logger.info("\nSimulando trading en datos de prueba...")
    
    capital = 10000.0
    position = None
    trades = []
    
    for i in range(50, len(test_df)):
        subset = test_df.iloc[:i+1].copy()
        
        try:
            signal = strategy.generate_signal(subset)
        except Exception as e:
            continue
        
        current = subset.iloc[-1]
        price = current['close']
        
        # Lógica de trading simple
        if position is None:
            if signal.signal_type.value == 'BUY':
                position = {
                    'entry_price': price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'side': 'LONG'
                }
        else:
            # Verificar cierre
            close_trade = False
            
            if position['side'] == 'LONG':
                if price <= position['stop_loss']:
                    close_trade = True
                    reason = 'stop_loss'
                elif price >= position['take_profit']:
                    close_trade = True
                    reason = 'take_profit'
                elif signal.signal_type.value == 'SELL':
                    close_trade = True
                    reason = 'signal'
            
            if close_trade:
                pnl_pct = (price - position['entry_price']) / position['entry_price']
                pnl = capital * 0.02 * (pnl_pct / 0.02)  # Asumiendo 2% riesgo
                
                trades.append({
                    'entry': position['entry_price'],
                    'exit': price,
                    'pnl_pct': pnl_pct,
                    'pnl': pnl,
                    'reason': reason
                })
                
                capital += pnl
                position = None
    
    # Mostrar resultados
    logger.info("\n" + "=" * 60)
    logger.info("RESULTADOS DEL BACKTEST")
    logger.info("=" * 60)
    
    if trades:
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = sum(1 for t in trades if t['pnl'] <= 0)
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / len(trades)
        
        logger.info(f"Total operaciones: {len(trades)}")
        logger.info(f"Ganadoras: {wins}")
        logger.info(f"Perdedoras: {losses}")
        logger.info(f"Win Rate: {wins/len(trades)*100:.1f}%")
        logger.info(f"PnL Total: ${total_pnl:+.2f}")
        logger.info(f"PnL Promedio: ${avg_pnl:+.2f}")
        logger.info(f"Capital Final: ${capital:.2f}")
        logger.info(f"Retorno: {(capital-10000)/10000*100:+.2f}%")
    else:
        logger.warning("No se ejecutaron operaciones en el backtest")
    
    exchange.disconnect()


def train_model(args):
    """Entrena el modelo con datos históricos."""
    logger.info("=" * 60)
    logger.info("ENTRENAMIENTO DE MODELO")
    logger.info("=" * 60)
    
    from trading_bot.models.ml_predictor import MLPredictor
    
    # Conectar para obtener datos
    exchange = BinanceClient(testnet=True)
    exchange.connect()
    
    logger.info(f"Obteniendo datos de {args.symbol}...")
    
    df = exchange.get_klines(
        symbol=args.symbol,
        interval=args.timeframe,
        limit=1000
    )
    
    # Añadir indicadores
    df = TechnicalIndicators.add_all_indicators(df)
    
    # Entrenar
    predictor = MLPredictor(model_type=args.model)
    metrics = predictor.train(df)
    
    # Mostrar importancia de features
    logger.info("\nImportancia de Features (Top 10):")
    importance = predictor.get_feature_importance()
    for _, row in importance.head(10).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    # Guardar modelo
    if args.save:
        path = predictor.save()
        logger.info(f"\nModelo guardado en: {path}")
    
    exchange.disconnect()


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Trading Bot con Inteligencia Artificial',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                           # Trading en testnet
  python main.py --live                    # Trading en modo REAL (¡cuidado!)
  python main.py --backtest                # Backtest con datos históricos
  python main.py --train --save            # Entrenar y guardar modelo
  python main.py --symbol ETHUSDT          # Operar con Ethereum
        """
    )
    
    # Modos de operación
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--backtest', action='store_true',
                           help='Ejecutar backtesting')
    mode_group.add_argument('--train', action='store_true',
                           help='Solo entrenar modelo')
    mode_group.add_argument('--live', action='store_true',
                           help='Modo REAL (dinero real)')
    
    # Parámetros de trading
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='Par de trading (default: BTCUSDT)')
    parser.add_argument('--timeframe', type=str, default='1h',
                       choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                       help='Intervalo de tiempo (default: 1h)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Segundos entre ciclos (default: 60)')
    
    # Parámetros del modelo
    parser.add_argument('--model', type=str, default='random_forest',
                       choices=['random_forest', 'gradient_boosting', 'xgboost'],
                       help='Tipo de modelo ML (default: random_forest)')
    parser.add_argument('--save', action='store_true',
                       help='Guardar modelo entrenado')
    
    # Debug
    parser.add_argument('--debug', action='store_true',
                       help='Modo debug (más logs)')
    
    args = parser.parse_args()
    
    # Configurar logger
    log_level = 'DEBUG' if args.debug else 'INFO'
    setup_logger(log_level)
    
    # Ejecutar modo seleccionado
    try:
        if args.backtest:
            run_backtest(args)
        elif args.train:
            train_model(args)
        else:
            run_live_trading(args)
            
    except KeyboardInterrupt:
        logger.info("\nDetenido por usuario")
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
