import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """PDF, TXT, MD dosyalarını yükleyip parçalara ayırır. RAG / vector store için kullanılır."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def process(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Döküman bulunamadı: {self.file_path}")

        ext = os.path.splitext(self.file_path)[-1].lower()
        if ext == ".pdf":
            loader = PyPDFLoader(self.file_path)
        elif ext in (".txt", ".md"):
            loader = TextLoader(self.file_path, encoding="utf-8")
        else:
            raise ValueError(f"Desteklenmeyen format: {ext}. PDF, TXT veya MD kullanın.")

        try:
            documents = loader.load()
        except Exception as e:
            raise RuntimeError(f"Döküman okunamadı: {e}") from e

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        return splitter.split_documents(documents)