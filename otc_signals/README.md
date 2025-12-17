# 📊 OTC Market Signal Generator

Sistema avanzado de análisis técnico y generación de señales de trading para mercados OTC, criptomonedas y forex.

## 🚀 Características

- **Análisis multi-indicador**: RSI, MACD, Bollinger Bands, Stochastic, ADX, y más
- **Señales automáticas**: Genera señales de compra/venta con niveles de SL/TP
- **Soporte multi-mercado**: Crypto, acciones (incluyendo OTC), y Forex
- **Análisis de tendencia**: Identifica tendencias y su fuerza
- **Gestión de riesgo**: Calcula automáticamente niveles de riesgo
- **Backtesting**: Prueba estrategias con datos históricos

## 📦 Instalación

```bash
# Clonar o descargar el proyecto
cd otc_signals

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Uso Rápido

### Análisis de una criptomoneda

```bash
# Analizar Bitcoin
python main.py

# Analizar Ethereum
python main.py --symbol ETH/USDT

# Analizar Solana con timeframe de 4 horas
python main.py --symbol SOL/USDT --timeframe 4h
```

### Análisis de acciones

```bash
# Analizar Apple
python main.py --symbol AAPL --market stock

# Analizar Tesla
python main.py --symbol TSLA --market stock
```

### Análisis de Forex

```bash
# Analizar EUR/USD
python main.py --symbol EURUSD=X --market forex

# Analizar GBP/USD
python main.py --symbol GBPUSD=X --market forex
```

### Escanear múltiples activos

```bash
# Escanear las principales criptos
python main.py --scan --market crypto

# Escanear acciones populares
python main.py --scan --market stock
```

### Ejecutar backtesting

```bash
# Backtest de BTC
python main.py --backtest --symbol BTC/USDT
```

## 📈 Indicadores Técnicos Incluidos

| Indicador | Descripción | Uso |
|-----------|-------------|-----|
| **RSI** | Relative Strength Index | Sobrecompra/sobreventa |
| **MACD** | Moving Average Convergence Divergence | Momentum y cruces |
| **Bollinger Bands** | Bandas de volatilidad | Zonas de precio |
| **Stochastic** | Oscilador estocástico | Momentum |
| **ADX** | Average Directional Index | Fuerza de tendencia |
| **ATR** | Average True Range | Volatilidad |
| **OBV** | On-Balance Volume | Confirmación por volumen |
| **VWAP** | Volume Weighted Average Price | Precio promedio ponderado |
| **SMA/EMA** | Medias móviles | Tendencia |
| **Ichimoku** | Sistema Ichimoku | Análisis completo |

## 🎯 Tipos de Señales

| Señal | Significado | Acción Sugerida |
|-------|-------------|-----------------|
| 🟢 COMPRA FUERTE | Múltiples indicadores alcistas | Considerar entrada larga |
| 🔵 COMPRA | Indicadores moderadamente alcistas | Evaluar entrada |
| ⚪ NEUTRAL | Sin dirección clara | Esperar |
| 🟠 VENTA | Indicadores moderadamente bajistas | Evaluar salida/corto |
| 🔴 VENTA FUERTE | Múltiples indicadores bajistas | Considerar salida/corto |

## 📊 Estructura del Proyecto

```
otc_signals/
├── core/
│   ├── __init__.py
│   ├── data_fetcher.py    # Obtención de datos
│   ├── indicators.py       # Indicadores técnicos
│   ├── signals.py          # Generación de señales
│   └── analyzer.py         # Análisis de mercado
├── strategies/
│   ├── __init__.py
│   └── multi_indicator.py  # Estrategia principal
├── utils/
│   ├── __init__.py
│   └── display.py          # Visualización
├── main.py                 # Script principal
├── requirements.txt        # Dependencias
└── README.md              # Este archivo
```

## 🔧 Configuración Avanzada

### Personalizar umbrales de señales

```python
from core import SignalGenerator

config = {
    'rsi': {
        'oversold': 25,      # Más agresivo
        'overbought': 75,
        'weight': 20
    },
    'macd': {
        'weight': 25
    },
    # ... más configuraciones
}

signal_gen = SignalGenerator(config=config)
```

### Usar como librería

```python
from core import DataFetcher, TechnicalIndicators, SignalGenerator, MarketAnalyzer
from strategies import MultiIndicatorStrategy

# Obtener datos
fetcher = DataFetcher()
df = fetcher.fetch_crypto('BTC/USDT', timeframe='1h', limit=500)

# Calcular indicadores
df = TechnicalIndicators.calculate_all(df)

# Generar señal
signal_gen = SignalGenerator()
signal = signal_gen.generate_signal(df)

print(f"Señal: {signal.type.value}")
print(f"Fuerza: {signal.strength}%")
print(f"Stop Loss: ${signal.stop_loss}")
print(f"Take Profit: ${signal.take_profit}")
```

## ⚠️ Disclaimer

**IMPORTANTE**: Este software es solo para fines educativos y de investigación.

- No constituye asesoramiento financiero
- El trading de mercados OTC conlleva alto riesgo
- Los resultados pasados no garantizan resultados futuros
- Siempre haz tu propia investigación (DYOR)
- Nunca inviertas más de lo que puedas permitirte perder

## 📝 Licencia

MIT License - Libre para uso personal y comercial.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor abre un issue o pull request.

---

**¿Preguntas?** Abre un issue en el repositorio.

*Hecho con ❤️ para traders*
