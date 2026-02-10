from src.llm_client import LLMClient
from src.tools.search_tool import SearchTool

class ResearcherAgent:
    def __init__(self, client: LLMClient, search_tool: SearchTool):
        self.client = client
        self.search_tool = search_tool

    async def research(self, query: str) -> str:
        """
        İnternet aramasını kullanarak bilgi toplar ve 
        gelen sonuçları analiz ederek bir özet sunar.
        """
        # 1. Adım: SearchTool ile internetten ham veriyi al
        search_results = self.search_tool.search(query)
        
        # 2. Adım: Toplanan veriyi LLM'e (Llama) gönderip anlamlı bir cevap üret
        prompt = f"""
        Aşağıda bir konu hakkında internetten toplanmış bilgiler yer alıyor. 
        Bu bilgileri kullanarak kullanıcı sorusuna kapsamlı ve doğru bir cevap ver. 
        Eğer bilgiler yetersizse veya 'sonuç bulunamadı' mesajı gelirse, elinden gelen en iyi genel cevabı ver.

        Kullanıcı Sorusu: {query}
        
        İnternet Sonuçları:
        {search_results}
        
        Yanıtın profesyonel, bilgilendirici ve Türkçe olsun.
        """
        
        # Analiz için hızlı ve etkili olan Llama 3.2 3B modelini (fast) kullanıyoruz
        return await self.client.ask(prompt, task_type="general")