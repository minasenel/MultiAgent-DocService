import httpx

class LLMClient:
    def __init__(self, model_name="llama3.2"):
         # Ollama yerelde bu porttan yayın yapar
        self.base_url = "http://localhost:11434/api/generate"
        self.model_name = model_name

    async def ask(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "Cevap alınamadı.")
            except Exception as e:
                return f"Hata oluştu: {str(e)}"
            
