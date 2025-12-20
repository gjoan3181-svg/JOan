"""
Script principal para obtener y analizar estadísticas del Loto de LEIDSA
"""

import json
from leidsa_scraper import LeidsaLotoScraper
from loto_statistics import LotoStatistics


def main():
    print("=" * 60)
    print("ANÁLISIS DE ESTADÍSTICAS - LOTO LEIDSA")
    print("República Dominicana")
    print("=" * 60)
    print()
    
    scraper = LeidsaLotoScraper()
    
    # Intentar cargar resultados existentes
    existing_results = scraper.load_results()
    
    if existing_results:
        print(f"Se encontraron {len(existing_results)} resultados guardados.")
        use_existing = input("¿Usar resultados existentes? (s/n): ").lower()
        
        if use_existing != 's':
            print("\nBuscando nuevos resultados...")
            new_results = scraper.get_recent_results()
            if new_results:
                scraper.save_results(new_results)
                existing_results = new_results
            else:
                print("No se pudieron obtener nuevos resultados.")
    else:
        print("Buscando resultados...")
        results = scraper.get_recent_results()
        if results:
            scraper.save_results(results)
            existing_results = results
        else:
            print("\nNo se pudieron obtener resultados automáticamente.")
            print("Puedes agregar resultados manualmente editando leidsa_loto_results.json")
            print("\nFormato esperado:")
            print("""
[
  {
    "fecha": "01/01/2024",
    "numeros": [5, 12, 18, 23, 29, 35]
  },
  ...
]
            """)
            return
    
    if existing_results:
        print(f"\nAnalizando {len(existing_results)} resultados...")
        stats = LotoStatistics(existing_results)
        
        print("\n" + stats.generate_report())
        stats.save_report()
        
        print("\n" + "=" * 60)
        print("Análisis completado!")
        print("=" * 60)


if __name__ == "__main__":
    main()
