from src.llm_client import LLMClient
from src.tools.code_executor import CodeExecutor

class CoderAgent:
    def __init__(self, client: LLMClient, executor: CodeExecutor):
        self.client = client
        self.executor = executor

    async def solve(self, query: str) -> str:
        """
        Kullanıcının sorusunu çözmek için Python kodu yazar, çalıştırır ve sonucu döndürür.
        Kod yazımı her zaman 'smart' (ileri) model ile yapılır.
        """
        prompt = f"""Sen uzman bir Python programcısısın. Aşağıdaki soruyu çözmek için yalnızca çalıştırılabilir Python kodu yaz.

Kurallar:
- Yanıtında SADECE tek bir ```python ... ``` bloğu olsun; açıklama veya örnek çıktı yazma.
- Kod tam ve çalışır olsun: open() ile dosya oku, parse et, hesapla, print() ile sonucu yazdır. Placeholder veya "..." kullanma.
- Veri ./data/ klasöründe; metin/kelime eşleştirmede büyük/küçük harfe duyarsız ol (örn. .lower() veya re.IGNORECASE).

Soru: {query}"""
        
        code_response = await self.client.ask(prompt, task_type="coding")
        
        # 2. Adım: Markdown içinden kodu çıkar ve çalıştır
        execution_result = self.executor.execute(code_response)
        
        # 3. Adım: Hata varsa bir kez düzeltmeyi dene (yine smart model)
        if "Kod Çalıştırma Hatası" in execution_result:
            fix_prompt = f"""Kullanıcı sorusu: {query}
Üretilen kod (hata veriyor): {code_response}
Hata: {execution_result}
Bu hatayı gideren, çalışan tam Python kodunu yaz. Yanıtında SADECE ```python ... ``` bloğu olsun."""
            code_response = await self.client.ask(fix_prompt, task_type="coding")
            execution_result = self.executor.execute(code_response)
        
        final_prompt = f"""Kullanıcı sorusu: {query}
Kod çalıştırma çıktısı: {execution_result}
Bu çıktıyı kullanarak kısa, Türkçe bir özet ver. Çıktıda sayı varsa ona göre cevap ver; uydurma yapma."""
        return await self.client.ask(final_prompt, task_type="general")