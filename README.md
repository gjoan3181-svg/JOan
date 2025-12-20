# Estadísticas del Loto de LEIDSA

Sistema para obtener y analizar estadísticas del juego Loto de LEIDSA (Lotería Electrónica Internacional de Santo Domingo) de la República Dominicana.

## Características

- **Obtención de datos**: Script para buscar resultados históricos del Loto
- **Análisis estadístico**: Cálculo de frecuencias, patrones y tendencias
- **Reportes**: Generación de reportes detallados con estadísticas

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Opción 1: Ejecutar el script principal
```bash
python main.py
```

### Opción 2: Usar los módulos individualmente

#### Obtener resultados:
```bash
python leidsa_scraper.py
```

#### Analizar estadísticas:
```bash
python statistics.py
```

## Estructura de Datos

Los resultados se guardan en `leidsa_loto_results.json` con el siguiente formato:

```json
[
  {
    "fecha": "01/01/2024",
    "numeros": [5, 12, 18, 23, 29, 35]
  }
]
```

## Estadísticas Incluidas

- **Frecuencia de números**: Números más y menos frecuentes
- **Distribución por rangos**: Análisis de números por rangos (1-10, 11-20, 21-30, 31-38)
- **Estadísticas de sumas**: Promedio, mediana, mínimo, máximo de las sumas
- **Pares frecuentes**: Combinaciones de números que aparecen juntos frecuentemente
- **Números consecutivos**: Identificación de números consecutivos en sorteos

## Notas

- El Loto de LEIDSA utiliza números del 1 al 38
- Se seleccionan 6 números por sorteo
- Los datos históricos pueden necesitar ser agregados manualmente si el scraping automático no funciona debido a protecciones del sitio web

## Fuentes de Datos

El script intenta obtener datos de:
- APIs públicas de loterías dominicanas
- Sitios web oficiales de LEIDSA
- Sitios alternativos de resultados de lotería

## Contribuir

Si tienes acceso a datos históricos del Loto de LEIDSA, puedes agregarlos manualmente al archivo `leidsa_loto_results.json` siguiendo el formato indicado.

## Licencia

Este proyecto es de código abierto y está disponible para uso educativo y personal.
