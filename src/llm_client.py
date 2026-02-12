import httpx
from langfuse import get_client


class LLMClient:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"

        # En az iki farklı yerel model konfigürasyonu kullanımı
        self.models = {
            "fast": "llama3.2:latest",  # Basit ve hızlı görevler için küçük model
            "smart": "llama3.1:8b",  # Karmaşık ve ayrıntılı cevap gerektiren görevler için büyük model
        }

        # Langfuse client (env: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL)
        # Yoksa SDK no-op çalışır, uygulama bozulmaz.
        self.langfuse = get_client()

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
        Otomatik model seçimi ile Ollama API üzerinden yanıt üretir.
        Langfuse ile her çağrı bir `generation` olarak izlenir.
        """
        selected_model = self._select_model(task_type, prompt)

        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
        }

        # Langfuse generation span
        with self.langfuse.start_as_current_observation(
            as_type="generation",
            name="llm_client.ask",
            model=selected_model,
        ) as gen:
            gen.update(
                input=prompt,
                metadata={"task_type": task_type, "model": selected_model},
            )

            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    response = await client.post(self.base_url, json=payload)
                    response.raise_for_status()
                    text = response.json().get("response", "Cevap alınamadı.")
                    gen.update(output=text)
                    return text
                except Exception as e:
                    error_text = f"Model hatası ({selected_model}): {str(e)}"
                    gen.update(output=error_text, level="error")
                    return error_text