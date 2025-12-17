# 📊 OTC Market Signal Generator

## 🚀 Sistema de Señales de Trading - SIN API KEYS

### ⭐ NUEVO: Soporte para OPCIONES BINARIAS OTC

Sistema completo de análisis técnico y generación de señales para:
- **Criptomonedas** (BTC, ETH, SOL, y 100+ más)
- **Acciones** (incluyendo OTC/Pink Sheets)
- **Forex** (EUR/USD, GBP/USD, etc.)

### ✅ NO NECESITAS API KEYS
Usa fuentes públicas gratuitas: Yahoo Finance, CoinGecko, Kraken.

---

## 📦 Instalación Rápida

```bash
cd otc_signals

# Instalar dependencias
pip3 install pandas numpy yfinance ta requests

# ¡Listo para usar!
```

---

## 🎯 OPCIONES BINARIAS OTC

Script especializado para binarias - Solo CALL o PUT, sin Stop Loss ni Take Profit.

### Uso Rápido

```bash
# Analizar una moneda
python3 binarias.py BTC

# Analizar varias
python3 binarias.py BTC ETH SOL

# Escanear mercado (buscar señales fuertes)
python3 binarias.py --scan

# Modo interactivo
python3 binarias.py
```

### ¿Qué te muestra?

```
╔════════════════════════════════════════════════╗
║                    🟢 CALL ↑                    ║
╚════════════════════════════════════════════════╝

📊 Probabilidad: 85%
💪 Fuerza: ⭐⭐⭐⭐☆
⏱️  Expiración: 3-5 min
🚦 Momento: 🔥 AHORA

📋 RAZONES:
   • 💪 Tres Soldados Blancos
   • 📈 Momentum alcista
   • 📉 Precio en zona inferior de Bollinger
```

### Indicadores que Analiza para Binarias

| Indicador | Uso en Binarias |
|-----------|-----------------|
| **Patrones de Velas** | Martillo, Envolvente, Doji, etc. |
| **Momentum** | Dirección de corto plazo |
| **RSI** | Zonas de sobreventa/sobrecompra |
| **Stochastic** | Cruces en zonas extremas |
| **Bollinger** | Rebotes en bandas |
| **MACD** | Cruces de señal |
| **EMAs** | Tendencia general |

### Niveles de Fuerza

| Fuerza | Significado | Acción |
|--------|-------------|--------|
| ⭐⭐⭐⭐⭐ | Señal muy fuerte | Operar con confianza |
| ⭐⭐⭐⭐☆ | Señal fuerte | Operar |
| ⭐⭐⭐☆☆ | Señal moderada | Operar con precaución |
| ⭐⭐☆☆☆ | Señal débil | Esperar confirmación |
| ⭐☆☆☆☆ | Muy débil | No operar |

---

## 🎯 USO RÁPIDO (Trading General)

### Analizar una moneda específica

```bash
# Criptomonedas
python3 analizar.py BTC        # Bitcoin
python3 analizar.py ETH        # Ethereum  
python3 analizar.py SOL        # Solana
python3 analizar.py DOGE       # Dogecoin
python3 analizar.py PEPE       # Pepe

# Múltiples monedas a la vez
python3 analizar.py BTC ETH SOL XRP

# Acciones
python3 analizar.py AAPL       # Apple
python3 analizar.py TSLA       # Tesla
python3 analizar.py NVDA       # Nvidia

# Forex
python3 analizar.py EURUSD     # Euro/Dólar
python3 analizar.py GBPUSD     # Libra/Dólar
```

### Modo Interactivo (menú)

```bash
python3 analizar.py
```

### Escanear mercado completo

```bash
python3 analizar.py --scan crypto   # Escanear criptos
python3 analizar.py --scan stock    # Escanear acciones
```

---

## 📊 ¿QUÉ INFORMACIÓN TE DA?

Cada análisis incluye:

| Información | Descripción |
|-------------|-------------|
| 💰 **Precio Actual** | Precio en tiempo real |
| 📈 **Cambio %** | Variación respecto a vela anterior |
| 🎯 **Señal** | COMPRA FUERTE / COMPRA / NEUTRAL / VENTA / VENTA FUERTE |
| 💪 **Fuerza** | Qué tan fuerte es la señal (0-100%) |
| 🛑 **Stop Loss** | Nivel sugerido para limitar pérdidas |
| 🎯 **Take Profit** | Nivel sugerido para tomar ganancias |
| 📈 **Tendencia** | ALCISTA / BAJISTA / LATERAL |
| 📊 **Volatilidad** | BAJA / MODERADA / ALTA / MUY ALTA |
| ⚠️ **Riesgo** | Score de 1-10 (mayor = más riesgoso) |
| 📋 **Razones** | Por qué se genera la señal |
| 💡 **Insights** | Observaciones importantes del mercado |
| 📊 **Soportes/Resistencias** | Niveles clave de precio |

---

## 🎯 TIPOS DE SEÑALES

| Señal | Emoji | Significado |
|-------|-------|-------------|
| **COMPRA FUERTE** | 🟢 | Múltiples indicadores alcistas - Alta probabilidad |
| **COMPRA** | 🔵 | Indicadores favorables - Considerar entrada |
| **NEUTRAL** | ⚪ | Sin dirección clara - Esperar |
| **VENTA** | 🟠 | Indicadores bajistas - Considerar salida |
| **VENTA FUERTE** | 🔴 | Múltiples indicadores bajistas - Alta probabilidad |

---

## 📈 INDICADORES TÉCNICOS

El sistema analiza 15+ indicadores:

- **RSI** - Sobrecompra/Sobreventa
- **MACD** - Momentum y cruces
- **Bollinger Bands** - Volatilidad y zonas de precio
- **Stochastic** - Momentum
- **ADX** - Fuerza de tendencia
- **ATR** - Volatilidad para calcular SL/TP
- **OBV** - Confirmación por volumen
- **VWAP** - Precio promedio ponderado
- **SMA/EMA** - Medias móviles (20, 50, 200)

---

## 💡 CRIPTOMONEDAS SOPORTADAS

```
BTC  ETH  BNB  SOL  XRP  ADA  DOGE DOT  MATIC SHIB
LTC  AVAX LINK UNI  ATOM XLM  ALGO VET  FTM   SAND
MANA AAVE AXS  THETA EOS XTZ  CAKE NEO  PEPE  ARB
OP   SUI  APT  INJ  TRX  NEAR ICP  FIL  HBAR  LDO
APE  CRO  QNT  MKR  RUNE EGLD FLOW KAVA GMX   CFX
BONK WIF  FLOKI GALA ENS LRC  MAGIC... y más
```

---

## 📁 Estructura del Proyecto

```
otc_signals/
├── analizar.py          # ⭐ Script principal (USA ESTE)
├── main.py              # Script con más opciones
├── core/
│   ├── data_fetcher.py  # Obtención de datos (sin API keys)
│   ├── indicators.py    # Indicadores técnicos
│   ├── signals.py       # Generación de señales
│   └── analyzer.py      # Análisis de mercado
├── strategies/
│   └── multi_indicator.py  # Estrategia de trading
├── utils/
│   └── display.py       # Visualización
└── requirements.txt     # Dependencias
```

---

## 🔧 Uso Avanzado (como librería)

```python
from core import DataFetcher, TechnicalIndicators, SignalGenerator

# Obtener datos
fetcher = DataFetcher()
df = fetcher.fetch_crypto('BTC', timeframe='1h', limit=500)

# Calcular indicadores
df = TechnicalIndicators.calculate_all(df)

# Generar señal
signal_gen = SignalGenerator()
signal = signal_gen.generate_signal(df)

print(f"Señal: {signal.type.value}")
print(f"Precio: ${df['close'].iloc[-1]:,.2f}")
print(f"Stop Loss: ${signal.stop_loss:,.2f}")
print(f"Take Profit: ${signal.take_profit:,.2f}")
```

---

## ⚠️ DISCLAIMER

**IMPORTANTE**: Este software es solo para fines educativos.

- ❌ No es asesoramiento financiero
- ❌ El trading conlleva riesgo de pérdida
- ❌ Resultados pasados no garantizan resultados futuros
- ✅ Siempre haz tu propia investigación (DYOR)
- ✅ Nunca inviertas más de lo que puedas perder
- ✅ Usa gestión de riesgo apropiada

---

## 🆘 Solución de Problemas

**Error: "No module named 'yfinance'"**
```bash
pip3 install yfinance
```

**Error: "No hay datos para X"**
- Verifica que el símbolo sea correcto
- Algunas monedas muy nuevas pueden no tener datos

**Los datos son de ejemplo**
- Si ves "Generando datos de ejemplo", significa que no se pudieron obtener datos reales
- Intenta con otra moneda más popular (BTC, ETH)

---

*Hecho con ❤️ para traders*
