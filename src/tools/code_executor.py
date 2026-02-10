import sys
from io import StringIO
import traceback

class CodeExecutor:
    """
    LLM tarafından üretilen Python kodlarını güvenli bir şekilde 
    çalıştırır ve çıktıları yakalar.
    """
    def execute(self, code: str) -> str:
        # Kodun içindeki gereksiz markdown işaretlerini temizle
        clean_code = code.replace("```python", "").replace("```", "").strip()
        
        # Standart çıktıyı (print) yakalamak için tampon
        output_buffer = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        # Kodun çalışacağı yerel değişkenler sözlüğü
        local_vars = {}
        
        try:
            # Kodu çalıştır
            exec(clean_code, {"__builtins__": __builtins__}, local_vars)
            sys.stdout = old_stdout # Çıktıyı normale döndür
            
            result = output_buffer.getvalue()
            return result if result else "Kod başarıyla çalıştı (Çıktı üretilmedi)."
            
        except Exception:
            sys.stdout = old_stdout
            # Hata oluşursa hatanın detayı
            return f"Kod Çalıştırma Hatası:\n{traceback.format_exc()}"