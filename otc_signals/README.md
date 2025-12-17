# 🎯 BULLEX BOT - Señales de Trading en Tiempo Real

Sistema de señales de trading que conecta directamente a Bullex para obtener datos de sentimiento de traders en tiempo real.

## 🚀 Uso Rápido

```bash
cd /workspace/otc_signals
python3 bot_final.py
```

## 📊 Archivos Principales

| Archivo | Descripción |
|---------|-------------|
| `bot_final.py` | **🌟 Bot principal** - Señales en tiempo real con sentimiento de traders |
| `senales.py` | Bot de señales alternativo |
| `debug.py` | Script de diagnóstico |
| `test_subs.py` | Test de suscripciones |

## 🔐 Credenciales

Las credenciales están configuradas en el código. Para mayor seguridad, usa variables de entorno:

```bash
export BULLEX_EMAIL="tu_email@ejemplo.com"
export BULLEX_PASSWORD="tu_contraseña"
python3 bot_final.py
```

## 📈 Interpretación de Señales

### Niveles de Señal

| Emoji | Nivel | Significado |
|-------|-------|-------------|
| 🟢🟢🟢🟢🟢 | EXTREMO (>95%) | Señal muy fuerte CALL |
| 🟢🟢🟢🟢 | FUERTE (85-95%) | Señal fuerte CALL |
| 🟢🟢🟢 | BUENA (75-85%) | Señal buena CALL |
| 🟢🟢 | NORMAL (65-75%) | Señal normal CALL |
| 🔴🔴🔴🔴🔴 | EXTREMO (>95%) | Señal muy fuerte PUT |
| 🔴🔴🔴🔴 | FUERTE (85-95%) | Señal fuerte PUT |
| 🔴🔴🔴 | BUENA (75-85%) | Señal buena PUT |
| 🔴🔴 | NORMAL (65-75%) | Señal normal PUT |

### Tipos de Instrumento

| Símbolo | Tipo | Duración |
|---------|------|----------|
| ⚡ | BLITZ | 5 segundos |
| 🚀 | TURBO | 1 minuto |
| (sin icono) | BINARY | Variable |

## ⚠️ Advertencias

1. **Riesgo**: El trading conlleva riesgo de pérdida de capital
2. **Sentimiento**: Las señales se basan en el sentimiento de otros traders, no en análisis técnico
3. **Volatilidad**: Las señales extremas pueden cambiar rápidamente
4. **Verificación**: Siempre verifica las señales con tu propio análisis

## 🛠️ Requisitos

```bash
pip3 install aiohttp websockets
```

## 📝 Notas Técnicas

- Conexión WebSocket a `wss://ws.trade.bull-ex.com/echo/websocket`
- API REST en `https://api.trade.bull-ex.com/v2/login`
- Suscripción al canal `traders-mood-changed` para sentimiento
- El valor 0.5 = 50% CALL / 50% PUT (equilibrado)
- Valores > 0.65 = señal CALL, valores < 0.35 = señal PUT

## 📊 Activos Soportados

El bot soporta más de 200 activos incluyendo:
- Forex (EUR/USD, GBP/USD, etc.)
- Criptomonedas (BTC, ETH, SOL, etc.)
- Memecoins (PEPE, DOGE, SHIB, TRUMP, MELANIA, etc.)
- Acciones (Tesla, Apple, NVIDIA, etc.)

---

Desarrollado para análisis de mercado OTC en Bullex.
