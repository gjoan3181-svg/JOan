# 🎯 BOT DE PRECISIÓN - GUÍA DE USO

## 📊 Objetivo: 80%+ Win Rate (8 de 10 ganadoras)

Este bot está diseñado para **calidad sobre cantidad**. Recibirás **menos señales**, pero **más precisas**.

---

## 🚀 Cómo Ejecutar

```bash
cd /workspace/otc_signals
python3 bot_precision.py
```

---

## 🔧 Configuración de Activos

### Paso 1: Edita `config_activos.py`

Abre el archivo y cambia `"activo": True` a `"activo": False` para deshabilitar activos que no tengas:

```python
# Ejemplo: Deshabilitar Bitcoin
212:  {"nombre": "Bitcoin", "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)", "activo": False},
```

### Paso 2: Verifica tus activos

```bash
python3 config_activos.py
```

Esto te mostrará la lista de activos habilitados.

---

## 🔒 Filtros Ultra-Estrictos

El bot aplica **9 filtros** antes de enviar una señal:

| # | Filtro | Valor | Descripción |
|---|--------|-------|-------------|
| 1 | Activo habilitado | ✓ | Solo activos en tu lista |
| 2 | Cooldown activo | 10 min | Entre señales del mismo activo |
| 3 | Cooldown global | 2 min | Entre cualquier señal |
| 4 | Límite horario | 6/hora | Máximo 6 señales por hora |
| 5 | Sentimiento | ≥92% | Solo sentimiento extremo |
| 6 | Puntuación | ≥85/100 | Score técnico mínimo |
| 7 | Confirmaciones | ≥4 | Mínimo 4 indicadores confirmando |
| 8 | Divergencias | Rechazadas | Si técnico contradice sentimiento |
| 9 | Probabilidad | ≥90% | Probabilidad final mínima |

---

## 📊 Sistema de Puntuación

Cada señal recibe una puntuación de 0-100 basada en:

| Indicador | Peso | Descripción |
|-----------|------|-------------|
| Sentimiento | 35% | % de traders en la dirección |
| Tendencia | 25% | EMA cross, cambio %, velas |
| Momentum | 20% | RSI, ROC, aceleración |
| Volatilidad | 10% | ATR, estabilidad |
| Volumen | 10% | Volumen vs promedio |

---

## 📋 Explicación de Señales

Cada señal incluye:

1. **Dirección**: CALL (🟢) o PUT (🔴)
2. **Probabilidad**: % de éxito estimado
3. **Puntuación**: Score técnico (0-100)
4. **Confirmaciones**: Lista de indicadores que confirman
5. **Razones**: Explicación detallada del PORQUÉ

### Ejemplo de Salida:

```
╔══════════════════════════════════════════════════════════════════════╗
║  🎯 SEÑAL DE PRECISIÓN - ✅ MUY ALTA                                 ║
║  ★★★★☆                                                               ║
╠══════════════════════════════════════════════════════════════════════╣
║  📍 Activo:       EUR/USD                                            ║
║  🏷️  Símbolo:      EUR/USD (OTC)                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║     🟢🟢🟢  COMPRAR (CALL) ↑                                          ║
╠══════════════════════════════════════════════════════════════════════╣
║  📈 Probabilidad:    93%                                             ║
║  🎯 Puntuación:      88/100                                          ║
║  👥 Sentimiento:     94% de traders                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  📋 ¿POR QUÉ ESTA SEÑAL?                                             ║
║  ──────────────────────────────────────────────────────────────────  ║
║  ✅ Sentimiento EXTREMO: 94%                                         ║
║  ✅ Tendencia CONFIRMA: ALCISTA ↑                                    ║
║  ✅ Momentum alcista: 67                                             ║
║  ✅ Volatilidad baja (predecible)                                    ║
║  ✅ Volumen alto: 1.4x                                               ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## ⚙️ Ajustar Parámetros

Si quieres ajustar los filtros, edita `bot_precision.py`:

```python
class ConfigPrecision:
    UMBRAL_SENTIMIENTO = 92      # Bajar a 90 = más señales
    PROBABILIDAD_MINIMA = 90     # Bajar a 85 = más señales
    PUNTUACION_MINIMA = 85       # Bajar a 80 = más señales
    MIN_CONFIRMACIONES = 4       # Bajar a 3 = más señales
    COOLDOWN_ACTIVO = 600        # Bajar a 300 = más señales
    MAX_SENALES_HORA = 6         # Subir a 10 = más señales
```

⚠️ **ADVERTENCIA**: Bajar los filtros aumentará las señales pero reducirá la precisión.

---

## 📈 Comparación de Versiones

| Característica | Bot Pro Final | Bot Precisión |
|----------------|---------------|---------------|
| Sentimiento mín | 88% | **92%** |
| Probabilidad mín | 85% | **90%** |
| Confirmaciones | 2 | **4** |
| Señales/hora | 15 | **6** |
| Cooldown activo | 5 min | **10 min** |
| Una señal a la vez | No | **Sí** |
| Explicación detallada | Básica | **Completa** |
| Filtro divergencias | No | **Sí** |

---

## 🎯 Estrategia Recomendada

1. **Paciencia**: Espera señales de alta calidad
2. **No persigas**: Si pierdes una señal, espera la siguiente
3. **Gestión de capital**: No arriesgues más del 2-3% por operación
4. **Horarios**: Los mejores horarios suelen ser:
   - 8:00 - 12:00 (mañana)
   - 14:00 - 18:00 (tarde)
5. **Verificación**: Compara la señal con tu propio análisis

---

## ⚠️ Disclaimer

Este bot es una herramienta de análisis. El trading OTC conlleva riesgos significativos.
No inviertas dinero que no puedas permitirte perder.

---

## 📞 Archivos del Bot

```
otc_signals/
├── bot_precision.py      # 🎯 Bot principal (ejecutar este)
├── config_activos.py     # ⚙️ Configuración de activos
├── bot_pro_final.py      # Versión anterior (más señales)
└── GUIA_BOT_PRECISION.md # Esta guía
```
