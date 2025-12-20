"""
Análisis estadístico de los números del Loto de LEIDSA
"""

import json
import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict
from datetime import datetime


class LotoStatistics:
    """Clase para analizar estadísticas del Loto de LEIDSA"""
    
    def __init__(self, results: List[Dict]):
        self.results = results
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Crea un DataFrame con los resultados"""
        data = []
        for result in self.results:
            if 'numeros' in result and result['numeros']:
                data.append({
                    'fecha': result.get('fecha', ''),
                    'numero1': result['numeros'][0] if len(result['numeros']) > 0 else None,
                    'numero2': result['numeros'][1] if len(result['numeros']) > 1 else None,
                    'numero3': result['numeros'][2] if len(result['numeros']) > 2 else None,
                    'numero4': result['numeros'][3] if len(result['numeros']) > 3 else None,
                    'numero5': result['numeros'][4] if len(result['numeros']) > 4 else None,
                    'numero6': result['numeros'][5] if len(result['numeros']) > 5 else None,
                })
        
        return pd.DataFrame(data)
    
    def get_frequency_stats(self) -> Dict:
        """Calcula la frecuencia de cada número"""
        all_numbers = []
        for result in self.results:
            if 'numeros' in result:
                all_numbers.extend(result['numeros'])
        
        frequency = Counter(all_numbers)
        
        # Ordenar por frecuencia
        sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'frequency': dict(frequency),
            'most_frequent': sorted_freq[:10],
            'least_frequent': sorted_freq[-10:] if len(sorted_freq) >= 10 else sorted_freq,
            'total_draws': len(self.results),
            'total_numbers': len(all_numbers)
        }
    
    def get_number_range_stats(self) -> Dict:
        """Estadísticas por rangos de números"""
        all_numbers = []
        for result in self.results:
            if 'numeros' in result:
                all_numbers.extend(result['numeros'])
        
        ranges = {
            '1-10': sum(1 for n in all_numbers if 1 <= n <= 10),
            '11-20': sum(1 for n in all_numbers if 11 <= n <= 20),
            '21-30': sum(1 for n in all_numbers if 21 <= n <= 30),
            '31-38': sum(1 for n in all_numbers if 31 <= n <= 38),
        }
        
        return ranges
    
    def get_consecutive_numbers(self) -> List[Dict]:
        """Encuentra números consecutivos en los sorteos"""
        consecutive_results = []
        
        for result in self.results:
            if 'numeros' in result and len(result['numeros']) >= 2:
                nums = sorted(result['numeros'])
                consecutive = []
                for i in range(len(nums) - 1):
                    if nums[i+1] - nums[i] == 1:
                        consecutive.append((nums[i], nums[i+1]))
                
                if consecutive:
                    consecutive_results.append({
                        'fecha': result.get('fecha', ''),
                        'numeros': result['numeros'],
                        'consecutivos': consecutive
                    })
        
        return consecutive_results
    
    def get_sum_statistics(self) -> Dict:
        """Estadísticas de la suma de los números"""
        sums = []
        for result in self.results:
            if 'numeros' in result and result['numeros']:
                sums.append(sum(result['numeros']))
        
        if not sums:
            return {}
        
        return {
            'promedio': np.mean(sums),
            'mediana': np.median(sums),
            'minimo': min(sums),
            'maximo': max(sums),
            'desviacion': np.std(sums)
        }
    
    def get_pair_frequency(self) -> Dict:
        """Frecuencia de pares de números"""
        pairs = []
        for result in self.results:
            if 'numeros' in result and len(result['numeros']) >= 2:
                nums = sorted(result['numeros'])
                for i in range(len(nums)):
                    for j in range(i + 1, len(nums)):
                        pairs.append((nums[i], nums[j]))
        
        pair_freq = Counter(pairs)
        return dict(sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def generate_report(self) -> str:
        """Genera un reporte completo de estadísticas"""
        report = []
        report.append("=" * 60)
        report.append("ESTADÍSTICAS DEL LOTO DE LEIDSA")
        report.append("=" * 60)
        report.append("")
        
        # Frecuencia de números
        freq_stats = self.get_frequency_stats()
        report.append(f"Total de sorteos analizados: {freq_stats['total_draws']}")
        report.append("")
        report.append("NÚMEROS MÁS FRECUENTES:")
        for num, count in freq_stats['most_frequent']:
            percentage = (count / freq_stats['total_numbers']) * 100
            report.append(f"  Número {num:2d}: {count:3d} veces ({percentage:.2f}%)")
        
        report.append("")
        report.append("NÚMEROS MENOS FRECUENTES:")
        for num, count in freq_stats['least_frequent']:
            percentage = (count / freq_stats['total_numbers']) * 100
            report.append(f"  Número {num:2d}: {count:3d} veces ({percentage:.2f}%)")
        
        report.append("")
        report.append("DISTRIBUCIÓN POR RANGOS:")
        range_stats = self.get_number_range_stats()
        total_range = sum(range_stats.values())
        for rango, count in range_stats.items():
            percentage = (count / total_range * 100) if total_range > 0 else 0
            report.append(f"  {rango}: {count:3d} números ({percentage:.2f}%)")
        
        report.append("")
        report.append("ESTADÍSTICAS DE SUMAS:")
        sum_stats = self.get_sum_statistics()
        if sum_stats:
            report.append(f"  Promedio: {sum_stats['promedio']:.2f}")
            report.append(f"  Mediana: {sum_stats['mediana']:.2f}")
            report.append(f"  Mínimo: {sum_stats['minimo']}")
            report.append(f"  Máximo: {sum_stats['maximo']}")
            report.append(f"  Desviación estándar: {sum_stats['desviacion']:.2f}")
        
        report.append("")
        report.append("PARES DE NÚMEROS MÁS FRECUENTES:")
        pair_freq = self.get_pair_frequency()
        for (num1, num2), count in list(pair_freq.items())[:10]:
            report.append(f"  ({num1:2d}, {num2:2d}): {count} veces")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "estadisticas_loto_leidsa.txt"):
        """Guarda el reporte en un archivo"""
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Reporte guardado en {filename}")


if __name__ == "__main__":
    # Cargar resultados
    try:
        with open('leidsa_loto_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        if results:
            stats = LotoStatistics(results)
            print(stats.generate_report())
            stats.save_report()
        else:
            print("No hay resultados para analizar.")
            print("Ejecuta primero leidsa_scraper.py para obtener datos.")
    except FileNotFoundError:
        print("No se encontró el archivo leidsa_loto_results.json")
        print("Ejecuta primero leidsa_scraper.py para obtener datos.")
        print("O agrega datos manualmente al archivo JSON.")
