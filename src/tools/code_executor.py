import os
import sys
import re
from io import StringIO
import traceback


# Proje kökü: kod ./data/ gibi yollarla çalışsın diye exec öncesi chdir yapılacak
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class CodeExecutor:
    """LLM çıktısından kodu çıkarır ve proje kökünde çalıştırır (./data/ erişilebilir olur)."""

    def _extract_code(self, code: str) -> str:
        match = re.search(r"```(?:python)?\s*\n(.*?)```", code, re.DOTALL)
        if match:
            return match.group(1).strip()
        return code.replace("```python", "").replace("```", "").strip()

    def execute(self, code: str) -> str:
        clean_code = self._extract_code(code)
        if not clean_code:
            return "Kod Çalıştırma Hatası: Yanıtta çalıştırılacak kod bloğu bulunamadı."

        output_buffer = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        old_cwd = os.getcwd()
        exc_info = None

        try:
            os.chdir(_PROJECT_ROOT)
            exec(clean_code, {"__builtins__": __builtins__}, {})
        except Exception:
            exc_info = traceback.format_exc()
        finally:
            sys.stdout = old_stdout
            os.chdir(old_cwd)

        result = output_buffer.getvalue()
        if exc_info:
            return f"Kod Çalıştırma Hatası:\n{exc_info}"
        if result:
            return result
        return "Kod başarıyla çalıştı (Çıktı üretilmedi)."