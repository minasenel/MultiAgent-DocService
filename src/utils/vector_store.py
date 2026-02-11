from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
import os

class VectorStoreManager:
    """Vektör veritabanı işlemlerini (kayıt ve arama) yöneten sınıf."""
    
    def __init__(self, chunks=None):
        # Ollama üzerinden Llama 3.2 modelini embedding için kullanıyoruz
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.persist_directory = "./chroma_db"
        
        if chunks:
            # Eğer döküman parçaları gelmişse veritabanını oluştur ve diske kaydet
            self.db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            # Eğer parçalar yoksa mevcut veritabanını diskten yükle
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

    def search(self, query: str, k: int = 3):
        """Soruyla en alakalı k adet döküman parçasını getirir."""
        if not self.db:
            return []
        return self.db.similarity_search(query, k=k)
    
    def add_documents(self, chunks):
        """Mevcut veritabanına yeni dokümanlar ekler (mevcut veriler korunur)."""
        if not self.db or not chunks:
            return False
        try:
            self.db.add_documents(chunks)
            return True
        except Exception as e:
            print(f"Hata: Yeni dokümanlar eklenirken hata oluştu: {e}")
            return False


#veri tabanı işlemleri için fonksiyonlar:
    # A. get_all_documents: veritabanındaki tüm dokümanları getirir
    def get_all_documents(self, limit: int = None):
        """Veritabanındaki tüm dokümanları getirir."""
        if not self.db:
            return []
        # Boş bir query ile tüm dokümanları almak için get() metodunu kullanıyoruz
        try:
            # Chromadbden tüm dokümanları çekmek için get() kullanılır
            results = self.db.get()
            if results and 'documents' in results:
                documents = results['documents']
                if limit:
                    documents = documents[:limit]
                return documents
            return []
        except Exception as e:
            # Eğer get() çalışmazsa, boş query ile similarity_search kullan
            if limit:
                return self.db.similarity_search("", k=limit)
            # Limit yoksa
            return self.db.similarity_search("", k=1000) # büyük bir sayı ile tümünü almaya çalış
    
    # B. get_document_count: veritabanındaki toplam doküman sayısını döndürür
    def get_document_count(self):
        """Veritabanındaki toplam doküman sayısını döndürür."""
        if not self.db: # eğer veritabanı yoksa 0 döndür
            return 0
        try:
            results = self.db.get() # veritabanındaki tüm dokümanları al
            if results and 'documents' in results:
                return len(results['documents']) # doküman sayısını döndür
            return 0
        except Exception:
            return 0
    
    # C. get_documents_with_metadata: veritabanındaki dokümanları metadata bilgileriyle birlikte getirir
    def get_documents_with_metadata(self, limit: int = 10): 
        """Dokümanları metadata bilgileriyle birlikte getirir."""
        if not self.db:
            return []
        try:
            # Boş query ile arama yaparak tüm dokümanları al
            docs = self.db.similarity_search("", k=limit if limit else 1000) # büyük bir sayı ile tümünü almaya çalış
            result = []
            for i, doc in enumerate(docs): 
                result.append({ # dictşonary for loop içinde oluşturulur ve sonuç listesine eklenir 
                    "id": i,
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content, 
                    "full_content": doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {} # eğer doc.metadata varsa onu döndür, yoksa boş bir dictionary döndür
                })
            return result
        except Exception as e:
            return [] 