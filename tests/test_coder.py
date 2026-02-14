"""CoderAgent birim testleri: normal çözüm, executor hatası, çıktı üretmeyen kod."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.coder import CoderAgent


class TestCoderAgentNormalFlow:
    """Normal akış: LLM kod üretir, executor başarıyla çalıştırır."""

    @pytest.mark.asyncio
    async def test_solve_returns_numeric_output_directly(self, mock_llm_client, mock_code_executor):
        mock_llm_client.ask = AsyncMock(side_effect=[
            "```python\nprint(42)\n```",
            "42 sayısı bulundu.",
        ])
        mock_code_executor.execute = MagicMock(return_value="42")
        coder = CoderAgent(mock_llm_client, mock_code_executor)
        result = await coder.solve("orders.json'dan kaç sipariş var?")
        assert result == "42"

    @pytest.mark.asyncio
    async def test_solve_returns_llm_summary_when_output_not_pure_number(self, mock_llm_client, mock_code_executor):
        mock_llm_client.ask = AsyncMock(side_effect=[
            "```python\nprint('Toplam: 10')\n```",
            "Toplam 10 sipariş vardır.",
        ])
        mock_code_executor.execute = MagicMock(return_value="Toplam: 10")
        coder = CoderAgent(mock_llm_client, mock_code_executor)
        result = await coder.solve("kaç sipariş?")
        assert "10" in result


class TestCoderAgentToolAndExecutionErrors:
    """Tool/executor hatası: anlamlı hata mesajı üretilir ve testle doğrulanır."""

    @pytest.mark.asyncio
    async def test_solve_executor_no_output_returns_meaningful_error(self, mock_llm_client, mock_code_executor):
        """Executor 'çıktı üretilmedi' döndürürse: net hata mesajı (kod + düzeltme + özet = 3 ask)."""
        mock_llm_client.ask = AsyncMock(side_effect=[
            "```python\nx = 1\n```",
            "```python\nprint(0)\n```",
            "Kod herhangi bir çıktı üretmedi; print() ile sonuç yazdırılmalı.",
        ])
        mock_code_executor.execute = MagicMock(
            return_value="Kod başarıyla çalıştı (Çıktı üretilmedi)."
        )
        coder = CoderAgent(mock_llm_client, mock_code_executor)
        result = await coder.solve("bir şey hesapla")
        assert "Kod Çalıştırma Hatası" in result or "çıktı üretmedi" in result or "print()" in result

    @pytest.mark.asyncio
    async def test_solve_executor_returns_traceback_then_llm_summarizes_error(self, mock_llm_client, mock_code_executor):
        """Executor SyntaxError/traceback döndürürse: bir düzeltme denemesi, sonra özet."""
        execution_error = "Kod Çalıştırma Hatası:\nTraceback... NameError: name 'x' is not defined"
        mock_llm_client.ask = AsyncMock(side_effect=[
            "```python\nprint(x)\n```",
            "```python\nprint(0)\n```",
            "Kod çalışırken 'x' tanımlı değildi; düzeltme sonrası 0 yazdırıldı.",
        ])
        mock_code_executor.execute = MagicMock(
            side_effect=[execution_error, "0"]
        )
        coder = CoderAgent(mock_llm_client, mock_code_executor)
        result = await coder.solve("test")
        assert "0" in result or "NameError" in result or "tanımlı" in result

    @pytest.mark.asyncio
    async def test_solve_executor_fails_twice_returns_final_error_summary(self, mock_llm_client, mock_code_executor):
        """İki kez de hata: son cevap hatayı özetleyen metin olmalı."""
        err_msg = "Kod Çalıştırma Hatası:\nSyntaxError: invalid syntax"
        mock_llm_client.ask = AsyncMock(side_effect=[
            "```python\nbroken\n```",
            "```python\nstill broken\n```",
            "Kod sözdizimi hatası nedeniyle çalıştırılamadı.",
        ])
        mock_code_executor.execute = MagicMock(return_value=err_msg)
        coder = CoderAgent(mock_llm_client, mock_code_executor)
        result = await coder.solve("test")
        assert "SyntaxError" in result or "sözdizimi" in result or "hatası" in result
