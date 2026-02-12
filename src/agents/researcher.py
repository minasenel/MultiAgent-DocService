import os
import glob
from src.llm_client import LLMClient
from src.tools.search_tool import SearchTool
from src.utils.vector_store import VectorStoreManager

# Proje kökündeki data/ klasörü (main.py ile aynı seviye)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")

class ResearcherAgent:
    def __init__(self, client: LLMClient, search_tool: SearchTool, vector_store: VectorStoreManager):
        self.client = client
        self.search_tool = search_tool
        self.vector_store = vector_store

    def _read_data_folder(self) -> str:
        """data/ klasöründeki tüm .txt, .md ve .json dosyalarını doğrudan okur."""
        if not os.path.exists(DATA_DIR):
            return ""
        parts = []
        for ext in ["*.txt", "*.md", "*.json"]:
            for path in sorted(glob.glob(os.path.join(DATA_DIR, ext))):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content:
                        parts.append(f"--- Dosya: {os.path.basename(path)} ---\n{content}")
                except Exception:
                    pass
        return "\n\n".join(parts) if parts else ""

    async def research(self, query: str) -> str:
        """Yerel data/ dosyaları + RAG + internet araması ile yanıt üretir. LangGraph researcher node bu metodu çağırır."""
        direct_data = self._read_data_folder()
        rag_docs = self.vector_store.search(query, k=5)
        rag_context = "\n".join([d.page_content for d in rag_docs]) if rag_docs else ""

        if direct_data:
            local_context = f"""[DATA KLASÖRÜNDEKİ DOSYALAR]
{direct_data}

[RAG SONUÇLARI]
{rag_context or "Ek eşleşme yok."}"""
        else:
            local_context = rag_context or "Yerel dökümanlarda ilgili bilgi bulunamadı."

        search_results = self.search_tool.search(query)

        prompt = f"""Kullanıcı sorusu: {query}

[YEREL DÖKÜMANLAR - ÖNCELİKLİ - MUTLAKA BURAYA BAK]
{local_context}

[İNTERNET]
{search_results}

Kurallar:
- ÖNCE yukarıdaki [YEREL DÖKÜMANLAR] bölümünde cevabı ara. Özellikle welcome.txt, menu.json, orders.json, reviews.json dosyalarına bak.
- Eğer yerel dosyalarda net bir cevap varsa, onu doğrudan kullan. İnternet sonuçlarını görmezden gel.
- Yerel dosyalarda bilgi yoksa veya belirsizse, internet sonuçlarını kullan.
- Türkçe, net ve kısa bir yanıt ver. Yerel dosyadan bulduğun bilgiyi kelimesi kelimesine kullan; uydurma yapma."""
        return await self.client.ask(prompt, task_type="general")