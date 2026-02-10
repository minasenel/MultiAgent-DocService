from duckduckgo_search import DDGS

class SearchTool:
    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, query: str) -> str:
        """
        DuckDuckGo üzerinden internet araması yapar.
        """
        try:
            results = []
            
            with DDGS() as ddgs:
                
                search_results = ddgs.text(query, max_results=self.max_results)
                
                res_list = list(search_results)
                
                for r in res_list:
                    results.append(f"Başlık: {r.get('title')}\nÖzet: {r.get('body')}\nKaynak: {r.get('href')}\n")
            
            if not results:
                return "Şu an internet sonuçlarına ulaşılamıyor (Bot koruması olabilir). Lütfen biraz sonra tekrar deneyin."
            
            return "\n---\n".join(results)
            
        except Exception as e:
            return f"Arama Hatası: {str(e)}"