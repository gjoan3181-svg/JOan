"""
Scraper para obtener resultados históricos del Loto de LEIDSA
Lotería Electrónica Internacional de Santo Domingo - República Dominicana
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import re


class LeidsaLotoScraper:
    """Clase para obtener resultados del Loto de LEIDSA"""
    
    def __init__(self):
        self.base_urls = [
            "https://www.leidsa.com",
            "https://leidsa.com.do",
            "https://www.loteria.com.do",
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
        self.results = []
    
    def get_results_from_api(self) -> Optional[List[Dict]]:
        """
        Intenta obtener resultados desde APIs públicas conocidas
        """
        # APIs comunes para loterías dominicanas
        api_urls = [
            "https://api.loteria.com.do/api/loto/resultados",
            "https://www.leidsa.com/api/resultados",
        ]
        
        for url in api_urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_api_response(data)
            except Exception as e:
                print(f"Error al acceder a {url}: {e}")
                continue
        
        return None
    
    def _parse_api_response(self, data: Dict) -> List[Dict]:
        """Parsea la respuesta de la API"""
        results = []
        # Adaptar según la estructura de la API
        if isinstance(data, list):
            for item in data:
                if 'numeros' in item or 'numbers' in item:
                    results.append(item)
        elif isinstance(data, dict) and 'resultados' in data:
            results = data['resultados']
        
        return results
    
    def scrape_website(self, url: str) -> Optional[List[Dict]]:
        """
        Intenta hacer scraping del sitio web
        """
        try:
            session = requests.Session()
            session.headers.update(self.headers)
            
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return self._parse_html(soup)
        except Exception as e:
            print(f"Error al hacer scraping de {url}: {e}")
        
        return None
    
    def _parse_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Parsea el HTML para extraer resultados"""
        results = []
        
        # Buscar tablas o divs con resultados
        # Patrones comunes en sitios de lotería
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Intentar extraer fecha y números
                    date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', str(cells[0]))
                    if date_match:
                        fecha = date_match.group()
                        numeros = []
                        for cell in cells[1:]:
                            num_match = re.findall(r'\b\d{1,2}\b', cell.get_text())
                            numeros.extend([int(n) for n in num_match if 1 <= int(n) <= 38])
                        
                        if numeros:
                            results.append({
                                'fecha': fecha,
                                'numeros': numeros[:6] if len(numeros) >= 6 else numeros
                            })
        
        return results
    
    def get_recent_results(self) -> List[Dict]:
        """
        Obtiene los resultados más recientes disponibles
        """
        # Intentar API primero
        api_results = self.get_results_from_api()
        if api_results:
            return api_results
        
        # Intentar scraping de sitios alternativos
        alternative_sites = [
            "https://www.loteria.com.do/resultados/loto",
            "https://resultadosloterias.com.do/leidsa/loto",
        ]
        
        for site in alternative_sites:
            results = self.scrape_website(site)
            if results:
                return results
        
        return []
    
    def save_results(self, results: List[Dict], filename: str = "leidsa_loto_results.json"):
        """Guarda los resultados en un archivo JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Resultados guardados en {filename}")
    
    def load_results(self, filename: str = "leidsa_loto_results.json") -> List[Dict]:
        """Carga resultados desde un archivo JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []


if __name__ == "__main__":
    scraper = LeidsaLotoScraper()
    print("Buscando resultados del Loto de LEIDSA...")
    results = scraper.get_recent_results()
    
    if results:
        print(f"Se encontraron {len(results)} resultados")
        scraper.save_results(results)
    else:
        print("No se pudieron obtener resultados automáticamente.")
        print("Por favor, proporciona los datos manualmente o verifica la conexión.")
