import os
import sys
import re
from io import StringIO
import traceback
import signal
from contextlib import contextmanager
from typing import Optional


# Proje kökü: kod ./data/ gibi yollarla çalışsın diye exec öncesi chdir yapılacak
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TimeoutError(Exception):
    """Kod çalıştırma timeout hatası."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """Unix sistemlerde timeout için signal kullanır, Windows'ta çalışmaz."""
    if sys.platform == "win32":
        # Windows'ta timeout yok, sadece context manager olarak çalışır
        yield
        return
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Kod çalıştırma {seconds} saniye içinde tamamlanamadı.")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class CodeExecutor:
    """
    LLM çıktısından kodu çıkarır ve proje kökünde çalıştırır (./data/ erişilebilir olur).
    
    Özellikler:
    - Standart Python kütüphanelerini otomatik import eder (json, os, pathlib, re, math, statistics, collections, datetime)
    - Return değerlerini yakalar (kod bir değer döndürüyorsa)
    - Stdout ve stderr'i ayrı yakalar
    - Timeout desteği (30 saniye)
    - Gelişmiş kod bloğu çıkarma (markdown, farklı formatlar)
    """

    def __init__(self, timeout_seconds: int = 30):
        """
        Args:
            timeout_seconds: Kod çalıştırma için maksimum süre (saniye). Varsayılan: 30.
        """
        self.timeout_seconds = timeout_seconds

    def _extract_code(self, code: str) -> str:
        """
        LLM çıktısından Python kod bloğunu çıkarır.
        
        Desteklenen formatlar:
        - ```python\n...\n```
        - ```\n...\n```
        - Ham kod (backtick yoksa)
        
        Birden fazla kod bloğu varsa ilkini alır.
        """
        # Önce markdown kod bloğu ara (```python veya ```)
        patterns = [
            r"```python\s*\n(.*?)```",  # ```python ... ```
            r"```\s*python\s*\n(.*?)```",  # ``` python ... ```
            r"```\s*\n(.*?)```",  # ``` ... ```
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code, re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                if extracted:  # Boş değilse döndür
                    return extracted
        
        # Kod bloğu yoksa, backtick'leri temizle ve ham kodu döndür
        cleaned = code.replace("```python", "").replace("```", "").strip()
        return cleaned

    def _create_safe_namespace(self):
        """
        Güvenli bir namespace oluşturur.
        Standart Python kütüphanelerini içerir ama tehlikeli işlemleri engellemez
        (çünkü data/ klasörüne erişmesi gerekiyor).
        """
        safe_dict = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
            "__file__": os.path.join(_PROJECT_ROOT, "executed_code.py"),
        }
        
        # Standart kütüphaneleri import et
        try:
            import json
            safe_dict["json"] = json
        except ImportError:
            pass
        
        try:
            import os as os_module
            safe_dict["os"] = os_module
        except ImportError:
            pass
        
        try:
            from pathlib import Path
            safe_dict["Path"] = Path
            safe_dict["pathlib"] = __import__("pathlib")
        except ImportError:
            pass
        
        try:
            import re as re_module
            safe_dict["re"] = re_module
        except ImportError:
            pass
        
        try:
            import math
            safe_dict["math"] = math
        except ImportError:
            pass
        
        try:
            import statistics
            safe_dict["statistics"] = statistics
        except ImportError:
            pass
        
        try:
            from collections import defaultdict, Counter, deque
            safe_dict["defaultdict"] = defaultdict
            safe_dict["Counter"] = Counter
            safe_dict["deque"] = deque
            safe_dict["collections"] = __import__("collections")
        except ImportError:
            pass
        
        try:
            from datetime import datetime, date, timedelta
            safe_dict["datetime"] = datetime
            safe_dict["date"] = date
            safe_dict["timedelta"] = timedelta
        except ImportError:
            pass
        
        return safe_dict

    def execute(self, code: str) -> str:
        """
        Kodu çıkarır, çalıştırır ve sonucu döndürür.
        
        Args:
            code: LLM'den gelen kod çıktısı (markdown bloğu veya ham kod)
            
        Returns:
            Kod çıktısı (stdout), return değeri veya hata mesajı
        """
        clean_code = self._extract_code(code)
        if not clean_code:
            return "Kod Çalıştırma Hatası: Yanıtta çalıştırılacak kod bloğu bulunamadı."

        # Çıktı yakalama için buffer'lar
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_cwd = os.getcwd()
        
        result_value = None
        exc_info = None
        timeout_occurred = False

        try:
            # Stdout ve stderr'i yakala
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer
            
            # Çalışma dizinini proje köküne değiştir
            os.chdir(_PROJECT_ROOT)
            
            # Güvenli namespace oluştur
            safe_namespace = self._create_safe_namespace()
            
            # Timeout ile çalıştır (Unix sistemlerde)
            try:
                if sys.platform != "win32":
                    with timeout_context(self.timeout_seconds):
                        # Kodu compile et ve çalıştır
                        compiled_code = compile(clean_code, "<string>", "exec")
                        exec(compiled_code, safe_namespace)
                else:
                    # Windows'ta timeout yok, direkt çalıştır
                    compiled_code = compile(clean_code, "<string>", "exec")
                    exec(compiled_code, safe_namespace)
                
                # Eğer kod bir değer döndürdüyse yakala (son satır expression ise)
                # Not: exec() return değeri döndürmez, ama son satırı eval edebiliriz
                try:
                    # Son satırı expression olarak değerlendirmeyi dene
                    lines = clean_code.strip().split('\n')
                    last_line = lines[-1].strip()
                    # Basit bir kontrol: eğer son satır bir ifade gibi görünüyorsa
                    if last_line and not last_line.startswith('#') and '=' not in last_line:
                        # Eğer print() çağrısı değilse, değerlendirmeyi dene
                        if not last_line.startswith('print('):
                            try:
                                result_value = eval(last_line, safe_namespace)
                            except:
                                pass  # Eval başarısız olursa görmezden gel
                except:
                    pass  # Return değeri yakalama başarısız olursa görmezden gel
                    
            except TimeoutError as e:
                timeout_occurred = True
                exc_info = str(e)
            except Exception:
                exc_info = traceback.format_exc()
                
        finally:
            # Her zaman eski duruma geri dön
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            os.chdir(old_cwd)

        # Stderr varsa önce onu göster
        stderr_output = stderr_buffer.getvalue()
        stdout_output = stdout_buffer.getvalue()
        
        if timeout_occurred:
            return f"Kod Çalıştırma Hatası: {exc_info}"
        
        if exc_info:
            # Hata varsa traceback'i döndür
            error_msg = f"Kod Çalıştırma Hatası:\n{exc_info}"
            if stderr_output:
                error_msg += f"\n\nStderr:\n{stderr_output}"
            return error_msg
        
        # Stderr varsa ama exception yoksa, uyarı olarak ekle
        if stderr_output:
            if stdout_output or result_value is not None:
                return f"{stdout_output}{stderr_output}"
            return f"Kod Çalıştırma Hatası: {stderr_output}"
        
        # Return değeri varsa onu önceliklendir
        if result_value is not None:
            return str(result_value)
        
        # Stdout varsa onu döndür
        if stdout_output:
            return stdout_output.strip()
        
        # Hiç çıktı yoksa bilgilendirici mesaj
        return "Kod başarıyla çalıştı (Çıktı üretilmedi)."
