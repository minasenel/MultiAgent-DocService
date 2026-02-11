from src.llm_client import LLMClient
from src.tools.search_tool import SearchTool
from src.utils.vector_store import VectorStoreManager # Yeni aracımızı içe aktarıyoruz

class ResearcherAgent:
    def __init__(self, client: LLMClient, search_tool: SearchTool, vector_store: VectorStoreManager):
        self.client = client
        self.search_tool = search_tool
        self.vector_store = vector_store # RAG yöneticisini bağladık

    async def research(self, query: str) -> str:
        """
        Hem yerel dökümanları hem de interneti kullanarak hibrit bir araştırma yapar.
        """
        # 1. Adım: Yerel Vektör Veritabanında (RAG) Ara
        rag_docs = self.vector_store.search(query, k=3)
        # Gelen Document objelerinden sadece içeriği (page_content) alıyoruz
        rag_context = "\n".join([doc.page_content for doc in rag_docs]) if rag_docs else "Yerel dökümanlarda bilgi bulunamadı."
        
        # 2. Adım: İnternet Araması Yap
        search_results = self.search_tool.search(query)
        
        # 3. Adım: Tüm Veriyi Llama'ya Sentezlet
        prompt = f"""
        Aşağıda kullanıcının sorusu için toplanan hibrit bilgiler yer alıyor. 
        Bu bilgileri analiz et ve kapsamlı, Türkçe bir yanıt oluştur.

        Kullanıcı Sorusu: {query}
        
        [YEREL DÖKÜMANLARDAN GELEN BİLGİLER]:
        {rag_context}
        
        [İNTERNETTEN GELEN GÜNCEL BİLGİLER]:
        {search_results}
        
        Not: Eğer yerel dökümanlar ile internet bilgileri çelişiyorsa, yerel dökümanlara öncelik ver.
        """
        
        # Bilgi sentezi için hızlı ve etkili modelimizi kullanıyoruz
        return await self.client.ask(prompt, task_type="general")