import json
from src.llm_client import LLMClient

class QueryAnalyst:
    def __init__(self, client: LLMClient):
        self.client = client

    async def analyze(self, query: str) -> dict:
        """
        kullanıcının sorgusunu analiz eder ve bir plan oluşturur.
        """
        system_prompt = """
        Sen çok ajanlı bir sistemin planlayıcı ajanısın. Görevin, kullanıcının sorusuna bakarak
        hangi araçların kullanılması gerektiğini belirlemektir. 
        
        Kullanabileceğin araçlar:
        1. 'web_search': Güncel bilgi veya internetten araştırma gerektiren durumlar.
        2. 'rag': Yerel dokümanlarda (PDF) bilgi aranması gereken durumlar. 
        3. 'coding': Hesaplama, veri işleme veya Python kodu çalıştırılması gereken durumlar.
        
        Yanıtını SADECE aşağıdaki JSON formatında ver, başka hiçbir metin ekleme:
        {
            "task_type": "web_search" | "rag" | "coding" | "general",
            "reason": "Neden bu aracı seçtiğinin kısa açıklaması",
            "plan": ["Adım 1...", "Adım 2..."]
        }
        """

        prompt = f"{system_prompt}\n\nKullanıcı Sorgusu: {query}"
        
        #  analiz görevi hızlı modelimiz llama3.2 ile kolayca yapılabilir. 
        response = await self.client.ask(prompt, task_type="general")
        
        try:
            return json.loads(response)
        #ilerde model eğer json formatında gereksiz açıklama eklerse regex helper function
        except Exception:
            # Eğer model JSON formatında hata yaparsa 
            return {
                "task_type": "general",
                "reason": "Format hatası nedeniyle genel cevap moduna geçildi.",
                "plan": ["Doğrudan cevap üret."]
            }