import httpx

class LLMClient:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        
        # En az iki farklı yerel model konfigürasyonu kullanımı 
        self.models = {
            "fast": "llama3.2:latest",   # Basit ve hızlı görevler için küçük model 
            "smart": "llama3.1:8b"   # Karmaşık ve ayrıntılı cevap gerektiren görevler için büyük model 
        }

    def _select_model(self, task_type: str, prompt: str) -> str:
        """
        Ajanların görevini ve metin uzunluğunu dikkate alan model seçim fonksiyonu
        """
        # Görevin türüne göre seçim 
        if task_type in ["coding", "calculation", "complex_reasoning"]:
            return self.models["smart"]
        
        # metnin uzunluğuna göre seçim
        if len(prompt) > 1500:
            return self.models["smart"]
        
        
        return self.models["fast"]

    async def ask(self, prompt: str, task_type: str = "general") -> str:
        """
        Otomatik model seçimi ile Ollama API üzerinden yanıt üretir
        """
        selected_model = self._select_model(task_type, prompt)
        
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "Cevap alınamadı.")
            except Exception as e:
                return f"Model hatası ({selected_model}): {str(e)}"