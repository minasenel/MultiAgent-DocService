"""CodeExecutor birim testleri: normal çalıştırma, eksik kod bloğu, çalışma zamanı hatası."""
from src.tools.code_executor import CodeExecutor


class TestCodeExecutorNormalFlow:
    """Normal akış: geçerli kod bloğu çalıştırılır."""

    def test_execute_python_block_returns_stdout(self):
        executor = CodeExecutor()
        code = "```python\nprint(42)\n```"
        result = executor.execute(code)
        assert result.strip() == "42"

    def test_execute_raw_code_without_backticks(self):
        executor = CodeExecutor()
        result = executor.execute("print('merhaba')")
        assert "merhaba" in result

    def test_execute_no_output_returns_meaningful_message(self):
        executor = CodeExecutor()
        code = "```python\nx = 1 + 1\n```"
        result = executor.execute(code)
        assert "Kod başarıyla çalıştı (Çıktı üretilmedi)" in result


class TestCodeExecutorErrorCases:
    """Hata senaryoları: eksik/hatalı giriş, tool çıktısında kod yok, sözdizimi/çalışma hatası."""

    def test_execute_empty_string_returns_meaningful_error(self):
        executor = CodeExecutor()
        result = executor.execute("")
        assert "Kod Çalıştırma Hatası" in result
        assert "kod bloğu bulunamadı" in result

    def test_execute_no_code_block_returns_meaningful_error(self):
        """Boş kod bloğu (```\n\n```) veya kod olmayan girişte anlamlı hata."""
        executor = CodeExecutor()
        # Boş blok: _extract_code boş string döner
        result = executor.execute("```\n\n```")
        assert "Kod Çalıştırma Hatası" in result
        assert "kod bloğu bulunamadı" in result

    def test_execute_syntax_error_returns_traceback_message(self):
        executor = CodeExecutor()
        code = "```python\nif True\n    pass\n```"
        result = executor.execute(code)
        assert "Kod Çalıştırma Hatası" in result
        assert "SyntaxError" in result or "Traceback" in result

    def test_execute_runtime_error_returns_meaningful_message(self):
        executor = CodeExecutor()
        code = "```python\n1 / 0\n```"
        result = executor.execute(code)
        assert "Kod Çalıştırma Hatası" in result
        assert "ZeroDivisionError" in result or "Traceback" in result
