from src.llm_client import LLMClient
from src.tools.code_executor import CodeExecutor

class CoderAgent:
    def __init__(self, client: LLMClient, executor: CodeExecutor):
        self.client = client
        self.executor = executor

    async def solve(self, query: str) -> str:
        """
        Kullanıcının sorusunu çözmek için Python kodu yazar, 
        çalıştırır ve sonucu analiz eder.
        """
        # 1. Adım: Kod Yazdırma (Burada 'smart' model yani llama 3.1  devreye girer)
        prompt = f"""
        Sen uzman bir Python yazılımcısısın. Aşağıdaki soruyu çözmek için SADECE Python kodu yaz.
        - Kodu yazarken 'print()' kullanarak sonucu ekrana basmayı unutma.
        - Yanıtında SADECE kod olsun, açıklama yapma.
        - Kod bloklarını ```python ... ``` içine al.

        Soru: {query}
        """
        
        # Kod yazımı hata kabul etmez, bu yüzden 'smart' modeli tetikliyoruz
        code_response = await self.client.ask(prompt, task_type="coding")
        
        # 2. Adım: Kodu Çalıştırma
        execution_result = self.executor.execute(code_response)
        
        # 3. Adım: Sonucu Kullanıcıya Açıklama
        final_prompt = f"""
        Kullanıcının sorusu: {query}
        Yazılan kodun çıktısı: {execution_result}
        
        Bu sonucu kullanıcıya nazikçe ve Türkçe olarak açıkla.
        """
        
        return await self.client.ask(final_prompt, task_type="general")