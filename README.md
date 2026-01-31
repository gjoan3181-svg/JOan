# Bot Adaptativo v2.1 - Sistema Inteligente + IA

Bot de trading para opciones binarias OTC en Bullex con sistema de IA como filtro inteligente.

## Características

### Sistema de IA como Filtro
- La IA **CONFIRMA o RECHAZA** señales técnicas
- Analiza contexto: tendencia, historial, patrones
- Auto-evaluación de efectividad
- Tracking de señales rechazadas

### Sistema de Aprendizaje
- Por activo (bloquea < 35%)
- Por dirección (CALL vs PUT)
- Por tendencia (a favor vs contra)
- Ajuste automático de parámetros

### Análisis Técnico
- 500 velas para detectar tendencia
- RSI, Bollinger Bands, EMA
- Patrones de velas (Doji, Hammer, Engulfing, etc.)
- 60 activos OTC de Bullex

### Categorías de Activos
- **FOREX**: EUR/USD, GBP/USD, USD/JPY, etc.
- **CRYPTO**: BTC, ETH, SOL, DOGE, etc.
- **COMMODITIES**: Oro, Plata
- **ÍNDICES**: US 30, US 100
- **ACCIONES**: Apple, Tesla, Amazon, etc.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python bot_adaptativo.py
```

## Configuración

Antes de usar, configura las siguientes variables en el código:

- `MI_SSID`: Tu SSID de Bullex
- `OPENAI_API_KEY`: Tu API key de OpenAI
- `TELEGRAM_TOKEN`: Token de tu bot de Telegram
- `TELEGRAM_CHAT_ID`: Tu chat ID de Telegram

## Menú del Bot

| Opción | Descripción |
|--------|-------------|
| 1 | Obtener MEJOR señal (con filtro IA) |
| 2 | Ver estado del mercado |
| 3 | Estadísticas completas |
| 4 | Ranking de activos |
| 5 | Enviar stats a Telegram |
| 6 | Señales pendientes |
| 7 | Historial reciente |
| 8 | Ver aprendizaje |
| 9 | Ver rechazadas por IA |
| g | Marcar última señal como GANADA |
| p | Marcar última señal como PERDIDA |
| g # | Marcar señal específica como GANADA |
| p # | Marcar señal específica como PERDIDA |

## Disclaimer

Este bot es solo para fines educativos. El trading de opciones binarias conlleva riesgos significativos. Úsalo bajo tu propia responsabilidad.
