import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    """
    Farklı formatlardaki (PDF, TXT, MD) dökümanları otomatik olarak tanıyan,
    yükleyen ve küçük parçalara ayıran sınıf.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def process(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Döküman bulunamadı: {self.file_path}")

        ext = os.path.splitext(self.file_path)[-1].lower()
        
        # (unit test de test_unsupported_file_extension() için fix)
        # Hata yakalamayı  önce yapalım. sadece desteklediğimiz türden dosyaları alacağız, else , throw "ValueError"
        if ext == ".pdf":
            loader = PyPDFLoader(self.file_path)
        elif ext == ".txt":
            loader = TextLoader(self.file_path, encoding='utf-8')
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(self.file_path)
        else:
            # burası doğrudan fırlatılmalı
            raise ValueError(f"Desteklenmeyen dosya formatı: {ext}. Lütfen PDF, TXT veya MD kullanın.")
        
        # sadece dosya okuma işlemini try-except içine alalım
        try:
            documents = loader.load()
        except Exception as e:
            raise Exception(f"Döküman okunurken teknik bir hata oluştu: {str(e)}")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        return text_splitter.split_documents(documents)