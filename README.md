# 🤖 Trading Bot con Inteligencia Artificial

Sistema de trading automatizado que utiliza **Machine Learning** para analizar mercados de criptomonedas y ejecutar operaciones automáticamente.

## 📋 Características

- ✅ **Conexión a Binance** (Testnet y Mainnet)
- ✅ **Análisis Técnico** (RSI, MACD, Bollinger Bands, etc.)
- ✅ **Modelos de ML** (Random Forest, Gradient Boosting, XGBoost)
- ✅ **Gestión de Riesgos** (Stop Loss, Take Profit, Position Sizing)
- ✅ **Backtesting** con datos históricos
- ✅ **Modo Paper Trading** para pruebas sin riesgo

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd trading_bot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales
nano .env
```

## 🔑 Obtener API Keys de Binance

### Para Testnet (Recomendado para empezar):

1. Ve a [Binance Testnet](https://testnet.binance.vision/)
2. Inicia sesión con GitHub
3. Genera tus API keys
4. Cópialas en el archivo `.env`

### Para Mainnet (Trading real):

1. Ve a [Binance](https://www.binance.com/)
2. Crea una cuenta o inicia sesión
3. Ve a API Management
4. Crea nuevas API keys
5. **⚠️ IMPORTANTE:** Habilita solo los permisos necesarios

## 📖 Uso

### Trading en Testnet (Simulación)

```bash
# Ejecutar con configuración por defecto
python main.py

# Especificar par y timeframe
python main.py --symbol BTCUSDT --timeframe 1h

# Con intervalo de ejecución personalizado (en segundos)
python main.py --interval 120
```

### Backtesting

```bash
# Backtest básico
python main.py --backtest

# Con modelo específico
python main.py --backtest --model gradient_boosting

# Con par diferente
python main.py --backtest --symbol ETHUSDT
```

### Entrenar Modelo

```bash
# Entrenar y mostrar métricas
python main.py --train

# Entrenar y guardar modelo
python main.py --train --save

# Con modelo específico
python main.py --train --model xgboost --save
```

### Trading Real (⚠️ PRECAUCIÓN)

```bash
# ¡CUIDADO! Esto usa dinero real
python main.py --live
```

## 🏗️ Arquitectura del Sistema

```
trading_bot/
├── config/           # Configuración
│   └── settings.py   # Carga de variables de entorno
├── exchange/         # Conexión a exchanges
│   ├── base_exchange.py    # Clase base abstracta
│   └── binance_client.py   # Cliente de Binance
├── analysis/         # Análisis de mercado
│   ├── indicators.py # Indicadores técnicos
│   └── signals.py    # Generador de señales
├── models/           # Modelos de ML
│   ├── feature_engineer.py  # Preparación de features
│   └── ml_predictor.py      # Predictor ML
├── strategies/       # Estrategias de trading
│   ├── base_strategy.py     # Clase base
│   └── ml_strategy.py       # Estrategia con ML
├── risk_management/  # Gestión de riesgos
│   └── risk_manager.py      # Control de riesgos
├── utils/            # Utilidades
│   └── logger.py     # Sistema de logging
└── bot.py            # Bot principal
```

## 📊 Indicadores Técnicos Incluidos

| Indicador | Descripción |
|-----------|-------------|
| SMA | Media Móvil Simple (10, 20, 50) |
| EMA | Media Móvil Exponencial (10, 20) |
| RSI | Índice de Fuerza Relativa |
| MACD | Convergencia/Divergencia de Medias Móviles |
| Bollinger Bands | Bandas de volatilidad |
| ATR | Rango Verdadero Promedio |
| Stochastic | Oscilador Estocástico |
| ADX | Índice Direccional Promedio |
| OBV | On-Balance Volume |
| VWAP | Precio Promedio Ponderado por Volumen |

## 🧠 Modelos de Machine Learning

### Random Forest (Default)
- Bueno para datos tabulares
- Robusto a overfitting
- Fácil de interpretar

### Gradient Boosting
- Mayor precisión potencial
- Requiere más tuning
- Más lento en entrenamiento

### XGBoost
- Mejor rendimiento general
- Requiere instalación adicional
- Optimizado para velocidad

## ⚠️ Gestión de Riesgos

El sistema incluye múltiples controles:

| Control | Default | Descripción |
|---------|---------|-------------|
| `max_position_size` | 10% | Tamaño máximo de posición |
| `max_risk_per_trade` | 2% | Riesgo máximo por operación |
| `max_daily_trades` | 10 | Máximo de operaciones diarias |
| `max_daily_loss` | 5% | Pérdida diaria máxima |
| `min_risk_reward` | 1.5:1 | Ratio mínimo riesgo/recompensa |
| `max_drawdown` | 15% | Drawdown máximo permitido |

## 📝 Ejemplo de Código

### Uso básico del bot

```python
from trading_bot.bot import TradingBot

# Crear bot
bot = TradingBot(
    symbol='BTCUSDT',
    timeframe='1h',
    testnet=True  # Siempre testnet para empezar
)

# Inicializar
if bot.initialize():
    # Ejecutar un ciclo
    bot.run_cycle()
    
    # Ver estado
    print(bot.get_status())
```

### Usar solo el predictor ML

```python
from trading_bot.exchange.binance_client import BinanceClient
from trading_bot.analysis.indicators import TechnicalIndicators
from trading_bot.models.ml_predictor import MLPredictor

# Obtener datos
exchange = BinanceClient(testnet=True)
exchange.connect()
df = exchange.get_klines('BTCUSDT', '1h', limit=500)

# Añadir indicadores
df = TechnicalIndicators.add_all_indicators(df)

# Entrenar modelo
predictor = MLPredictor(model_type='random_forest')
metrics = predictor.train(df)
print(f"Accuracy: {metrics['accuracy']:.2%}")

# Hacer predicción
prediction = predictor.predict(df)
print(f"Predicción: {prediction}")
```

### Generar señales técnicas

```python
from trading_bot.analysis.signals import SignalGenerator
from trading_bot.analysis.indicators import TechnicalIndicators

# Generar señales
signal_gen = SignalGenerator()
df = TechnicalIndicators.add_all_indicators(df)
signal = signal_gen.generate_signal(df)

print(f"Señal: {signal.signal_type.value}")
print(f"Fuerza: {signal.strength:.2%}")
print(f"Razón: {signal.reason}")
```

## 📈 Resultados de Ejemplo

```
================== RESULTADOS DEL BACKTEST ==================
Total operaciones: 47
Ganadoras: 28
Perdedoras: 19
Win Rate: 59.6%
PnL Total: $1,247.35
PnL Promedio: $26.54
Capital Final: $11,247.35
Retorno: +12.47%
=============================================================
```

## ⚡ Consejos Importantes

1. **Siempre usa Testnet primero** - Prueba tu estrategia sin arriesgar dinero real.

2. **No confíes ciegamente en el modelo** - Los modelos de ML pueden fallar, especialmente en condiciones de mercado inusuales.

3. **Gestiona tu riesgo** - Nunca arriesgues más del 2% de tu capital por operación.

4. **Monitorea el bot** - Aunque es automático, revisa regularmente su comportamiento.

5. **Actualiza el modelo** - Re-entrena el modelo periódicamente con datos recientes.

## 🔧 Troubleshooting

### Error: "python-binance no está instalado"
```bash
pip install python-binance
```

### Error: "No se pudo conectar al exchange"
- Verifica tus API keys en el archivo `.env`
- Asegúrate de tener conexión a internet
- Si usas testnet, verifica que `USE_TESTNET=true`

### Error: "Datos insuficientes para entrenar"
- Necesitas al menos 100 velas para entrenar
- Aumenta el `limit` al obtener datos históricos

## 📄 Licencia

Este proyecto es solo para fines educativos. El trading de criptomonedas conlleva riesgos significativos. No inviertas más de lo que puedas permitirte perder.

## ⚠️ Disclaimer

**ADVERTENCIA:** Este software es solo para propósitos educativos. El trading de criptomonedas es altamente volátil y riesgoso. Las decisiones de trading tomadas por este bot no garantizan ganancias. El autor no se hace responsable de pérdidas financieras que puedan resultar del uso de este software.

---

Desarrollado con ❤️ para la comunidad de trading algorítmico.
