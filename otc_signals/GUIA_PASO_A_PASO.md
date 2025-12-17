# 🔮 GUÍA COMPLETA - BOT DE SEÑALES BULLEX

## ⚠️ IMPORTANTE: Este bot NO hace login automático

Para evitar los correos de "ingreso sospechoso", este bot usa las cookies de tu sesión existente del navegador.

---

## 📋 REQUISITOS PREVIOS

### En tu computadora necesitas:
1. **Python 3.8+** instalado
2. **Librerías**: `websockets` y `aiohttp`

### Instalar Python (si no lo tienes):
- **Windows**: Descarga de https://python.org
- **Mac**: `brew install python3`
- **Linux**: `sudo apt install python3`

### Instalar librerías:
```bash
pip install websockets aiohttp
```

---

## 🚀 PASO A PASO PARA USAR EL BOT

### PASO 1: Descarga el bot

Guarda el archivo `bot_seguro.py` en una carpeta de tu computadora.

### PASO 2: Abre Bullex en tu navegador

1. Abre **Chrome** o **Firefox**
2. Ve a: `https://trade.bull-ex.com`
3. Haz **login normal** con tu cuenta
4. Asegúrate de estar logueado correctamente

### PASO 3: Obtén tu SSID (cookie de sesión)

#### En Chrome:

1. Presiona **F12** (abre DevTools)
2. Haz clic en la pestaña **"Application"** (arriba)
   - Si no la ves, haz clic en `>>` para ver más pestañas
3. En el panel izquierdo, busca **"Cookies"**
4. Expande "Cookies" y haz clic en **"https://trade.bull-ex.com"**
5. En la lista, busca la fila que dice **"ssid"**
6. Haz **doble clic** en el valor (columna "Value")
7. Presiona **Ctrl+C** para copiar

```
Ejemplo de SSID (es un texto largo):
a]1234567890abcdef1234567890abcdef
```

#### En Firefox:

1. Presiona **F12** (abre DevTools)
2. Haz clic en la pestaña **"Storage"** (Almacenamiento)
3. Expande **"Cookies"**
4. Haz clic en **"https://trade.bull-ex.com"**
5. Busca **"ssid"** y copia el valor

### PASO 4: Configura el bot

**Opción A - Editar el archivo:**

1. Abre `bot_seguro.py` con un editor de texto (Notepad, VS Code, etc.)
2. Busca esta línea (cerca del inicio):
   ```python
   MI_SSID = ""
   ```
3. Pega tu SSID entre las comillas:
   ```python
   MI_SSID = "a]1234567890abcdef..."
   ```
4. Guarda el archivo

**Opción B - Ingresar al ejecutar:**

El bot te pedirá el SSID cuando lo ejecutes si no está configurado.

### PASO 5: Ejecuta el bot

Abre una terminal/cmd en la carpeta donde está el bot y ejecuta:

```bash
python3 bot_seguro.py
```

O en Windows:
```bash
python bot_seguro.py
```

---

## 📊 CÓMO INTERPRETAR LAS SEÑALES

Cuando aparece una señal, verás algo así:

```
╔══════════════════════════════════════════════════════════╗
║  🔮 SEÑAL - 🔥 EXTREMA                                  ║
╠══════════════════════════════════════════════════════════╣
║  📍 Bitcoin (BTC)                                        ║
║  📊 CRYPTO                                               ║
╠══════════════════════════════════════════════════════════╣
║     🟢🟢🟢  📈 SUBE (CALL)                              ║
╠══════════════════════════════════════════════════════════╣
║  📈 Probabilidad: 95%                                    ║
║  👥 Sentimiento:  92% traders                            ║
╠══════════════════════════════════════════════════════════╣
║  ⏰ ENTRAR EN:    2:45 minutos                           ║
║  🎯 HORA ENTRADA: 14:35:00                               ║
║  ⏱️  EXPIRACIÓN:   14:37:00                               ║
║  ⌛ DURACIÓN:     2 minutos                              ║
╠══════════════════════════════════════════════════════════╣
║  🕐 Hora RD:      14:32:15                               ║
╚══════════════════════════════════════════════════════════╝
```

### Significado de cada campo:

| Campo | Significado |
|-------|-------------|
| 🔮 SEÑAL | Nivel de confianza (EXTREMA, MUY ALTA, ALTA) |
| 📍 Activo | Nombre del activo (Bitcoin, EUR/USD, etc.) |
| 📊 Mercado | Tipo (CRYPTO, FOREX, ACCIONES) |
| 🟢/🔴 | Dirección: CALL (sube) o PUT (baja) |
| 📈 Probabilidad | Porcentaje de éxito estimado |
| 👥 Sentimiento | Porcentaje de traders en esa dirección |
| ⏰ ENTRAR EN | Tiempo restante hasta la entrada |
| 🎯 HORA ENTRADA | Hora exacta para abrir la operación |
| ⏱️ EXPIRACIÓN | Hora exacta cuando cierra |
| ⌛ DURACIÓN | Tiempo de la operación (2 minutos) |
| 🕐 Hora RD | Hora actual en República Dominicana |

---

## 🎯 CÓMO OPERAR CON LAS SEÑALES

### Cuando aparece una señal:

1. **Mira el activo** → Ej: "Bitcoin (BTC)"
2. **Mira la dirección** → 🟢 CALL (sube) o 🔴 PUT (baja)
3. **Mira la hora de entrada** → Ej: 14:35:00
4. **Prepárate** → Abre Bullex y busca el activo
5. **Espera la alerta** → El bot te avisa cuando entrar

### Cuando suena la alerta (🔔🔔🔔):

1. **Entra INMEDIATAMENTE** en Bullex
2. Selecciona el activo indicado
3. Elige la dirección (CALL o PUT)
4. Selecciona **2 minutos** de duración
5. Confirma la operación

### Después de la operación:

- El bot verificará automáticamente si ganaste o perdiste
- Verás: ✅ GANADA o ❌ PERDIDA
- Las estadísticas se actualizan automáticamente

---

## ⚠️ CONSEJOS IMPORTANTES

### Sobre el SSID:
- ❌ **NO cierres sesión** en el navegador mientras usas el bot
- ❌ Si cierras sesión, necesitas obtener un nuevo SSID
- ✅ Puedes tener el bot y el navegador abiertos al mismo tiempo
- ✅ El SSID dura mientras tu sesión esté activa

### Sobre las señales:
- ✅ Solo sigue señales con probabilidad **>85%**
- ✅ El bot filtra automáticamente las mejores señales
- ⚠️ No todas las señales serán ganadoras
- ⚠️ Opera con responsabilidad y gestiona tu riesgo

### Sobre la cuenta demo:
- ✅ **Recomendado**: Prueba primero en cuenta DEMO
- ✅ Crea una cuenta demo en Bullex para practicar
- ⚠️ No arriesgues dinero real hasta entender el sistema

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### "Error de conexión":
- Verifica que tu SSID sea correcto
- Obtén un nuevo SSID del navegador
- Asegúrate de estar logueado en Bullex

### "No aparecen señales":
- El mercado puede estar tranquilo
- Espera unos minutos
- Las señales aparecen cuando hay consenso >85%

### "El bot se desconecta":
- Normal si pasa mucho tiempo
- El bot intenta reconectar automáticamente
- Si no funciona, reinicia el bot

### "SSID inválido":
1. Cierra el bot
2. Ve a Bullex en el navegador
3. Cierra sesión y vuelve a entrar
4. Obtén el nuevo SSID
5. Ejecuta el bot de nuevo

---

## 📁 ARCHIVOS DEL BOT

```
📂 Tu carpeta/
├── 📄 bot_seguro.py      ← El bot principal
├── 📄 historial_senales.json  ← Historial (se crea automático)
└── 📄 GUIA_PASO_A_PASO.md    ← Esta guía
```

---

## 🆘 RESUMEN RÁPIDO

```
1. Abre Bullex en el navegador y haz login
2. F12 → Application → Cookies → ssid → Copiar valor
3. Ejecuta: python3 bot_seguro.py
4. Pega tu SSID cuando lo pida
5. Espera las señales y opera cuando te avise
```

---

## ⏰ ZONA HORARIA

El bot usa la hora de **República Dominicana (UTC-4)**

Todas las horas mostradas corresponden a tu zona horaria local.

---

¡Buena suerte con tus operaciones! 🍀
