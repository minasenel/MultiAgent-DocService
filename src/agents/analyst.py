import json
from src.llm_client import LLMClient


class QueryAnalyst:
    """Sorguyu analiz edip hangi node'a gidileceğine karar verir. LangGraph'ın giriş node'udur."""

    def __init__(self, client: LLMClient):
        self.client = client

    async def analyze(self, query: str) -> dict:
        """task_type döndürür: web_search/rag → researcher, coding → coder, aksi halde general."""
        system_prompt = """Sen çok ajanlı sistemin planlayıcısısın. Kullanıcı sorusuna göre hangi aracın kullanılacağına karar ver.

Araçlar:
- web_search veya rag: Sadece bilgi, liste, açıklama; metin cevap yeterli.
- coding: Sayı, toplam, ortalama, istatistik, hesaplama; veya veri dosyalarından SAYIP/SIRALAYIP cevap (en çok satan, en az, hangisi birinci, kaç adet vb.). Bu tür sorularda mutlaka coding seç; dosyayı okuyup sayan kod gerekir.
- general: Belirsiz veya sohbet.

Yanıtın SADECE aşağıdaki JSON olsun, başka metin ekleme:
{"task_type": "web_search"|"rag"|"coding"|"general", "reason": "kısa gerekçe", "plan": ["Adım 1", "Adım 2"]}"""

        response = await self.client.ask(f"{system_prompt}\n\nKullanıcı Sorgusu: {query}", task_type="general")

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Model bazen JSON etrafına metin ekler; ilk { ile başlayan en kısa geçerli JSON'u dene
            start = response.find("{")
            if start != -1:
                depth = 0
                for i, c in enumerate(response[start:], start):
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(response[start : i + 1])
                            except json.JSONDecodeError:
                                break
            return {"task_type": "general", "reason": "JSON ayrıştırılamadı.", "plan": ["Doğrudan cevap üret."]}