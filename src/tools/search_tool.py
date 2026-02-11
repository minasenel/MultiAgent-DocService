import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

class SearchTool:
    """İnternet araması. LangGraph'taki Researcher node tarafından kullanılır."""

    def __init__(self, max_results: int = 3):
        self.max_results = max_results
        self.tavily_api_key = (os.getenv("TAVILY_API_KEY") or "").strip() or None
    
    def _search_with_tavily(self, query: str) -> tuple[str | None, str | None]:
        """Tavily API ile arama. (sonuç_metni, hata_mesajı) döndürür."""
        try:
            from tavily import TavilyClient
            
            if not self.tavily_api_key:
                return None, None

            client = TavilyClient(api_key=self.tavily_api_key)
            response = client.search(query, max_results=self.max_results)
            
            results = []
            for result in response.get('results', [])[:self.max_results]:
                results.append(
                    f"Başlık: {result.get('title', 'N/A')}\n"
                    f"Özet: {result.get('content', 'N/A')}\n"
                    f"Kaynak: {result.get('url', 'N/A')}\n"
                )
            
            return ("\n---\n".join(results) if results else None), None
        except ImportError:
            return None, "tavily-python yüklü değil (pip install tavily-python)"
        except Exception as e:
            return None, str(e)
    
    def _search_with_direct_scraping(self, query: str) -> str:
        """Direct web scraping ile arama yapar (API key gerektirmez)"""
        try:
            # DuckDuckGo HTML arama sayfasını kullanarak scraping yapıyoruz
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # DuckDuckGo HTML yapısına göre sonuçları çıkar
            result_divs = soup.find_all('div', class_='result')[:self.max_results]
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                url_elem = title_elem if title_elem else None
                
                title = title_elem.get_text(strip=True) if title_elem else "N/A"
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else "Özet bulunamadı"
                url = url_elem.get('href', 'N/A') if url_elem else "N/A"
                
                results.append(f"Başlık: {title}\nÖzet: {snippet}\nKaynak: {url}\n")
            
            return "\n---\n".join(results) if results else None
            
        except Exception as e:
            return None
    
    def _search_with_simple_api(self, query: str) -> str:
        """Basit bir alternatif: Wikipedia API (sadece Wikipedia sonuçları)"""
        try:
            # Wikipedia API kullanarak arama
            wiki_url = "https://tr.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(query)
            response = requests.get(wiki_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return (
                    f"Başlık: {data.get('title', 'N/A')}\n"
                    f"Özet: {data.get('extract', 'N/A')}\n"
                    f"Kaynak: {data.get('content_urls', {}).get('desktop', {}).get('page', 'N/A')}\n"
                )
        except Exception:
            pass
        return None

    def search(self, query: str) -> str:
        """İnternet araması yapar. Sonucu döndürür."""
        result, _, _ = self.search_with_source(query)
        return result

    def search_with_source(self, query: str) -> tuple[str, str, str | None]:
        """
        İnternet araması yapar. (sonuç_metni, kullanılan_kaynak, tavily_hata_mesajı) döndürür.
        """
        tavily_error = None
        
        # 1. Tavily API
        if self.tavily_api_key:
            result, err = self._search_with_tavily(query)
            if err:
                tavily_error = err
            if result:
                return result, "Tavily API", tavily_error

        # 2. Direct scraping dene
        result = self._search_with_direct_scraping(query)
        if result:
            return result, "DuckDuckGo (scraping)", tavily_error

        # 3. Wikipedia fallback
        result = self._search_with_simple_api(query)
        if result:
            return result, "Wikipedia API", tavily_error

        # Hiçbiri çalışmazsa
        msg = "Şu an internet sonuçlarına ulaşılamıyor. Lütfen biraz sonra tekrar deneyin veya Tavily API key ekleyin (TAVILY_API_KEY environment variable)."
        return msg, "yok", tavily_error