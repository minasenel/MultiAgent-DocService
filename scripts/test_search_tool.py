#!/usr/bin/env python3
"""
Search tool test script.
Çalıştırma: Proje kökünden  PYTHONPATH=. python3 scripts/test_search_tool.py [arama_terimi]
"""
import os
import sys

# Proje kökü ve .env yükleme (script konumundan bağımsız çalışır)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# .env dosyasını proje kökünden açıkça yükle
_env_path = os.path.join(PROJECT_ROOT, ".env")
try:
    from dotenv import load_dotenv
    loaded = load_dotenv(_env_path)
    if not loaded and os.path.exists(_env_path):
        load_dotenv()  # cwd'deki .env'i dene
except ImportError:
    pass

from src.tools.search_tool import SearchTool

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "Türkiye dolar kuru bugün"
    
    key = os.getenv("TAVILY_API_KEY")
    key_preview = "(yok)" if not key else f"{key[:12]}... ({len(key)} karakter)" if len(key) > 12 else f"({len(key)} karakter)"
    
    print("=" * 60)
    print("SEARCH TOOL TEST")
    print("=" * 60)
    print(f".env yolu: {_env_path}")
    print(f".env var mı: {os.path.exists(_env_path)}")
    print(f"TAVILY_API_KEY: {key_preview}")
    print(f"Arama terimi: {query}")
    print("=" * 60)
    
    tool = SearchTool(max_results=3)
    result, source, tavily_error = tool.search_with_source(query)
    
    if tavily_error:
        print(f"UYARI – Tavily denendi ama hata: {tavily_error}")
        print()
    
    if "Arama Hatası" in result or "ulaşılamıyor" in result:
        print("SONUÇ: HATA veya sonuç yok")
        print(result)
        return 1
    
    print(f"Kullanılan kaynak: {source}")
    print("SONUÇ (ilk 3 kayıt):")
    print("-" * 60)
    print(result)
    print("-" * 60)
    print("OK – Search tool çalışıyor, sonuç döndü.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
