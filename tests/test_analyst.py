"""QueryAnalyst birim testleri: normal JSON analizi, eksik/hatalı giriş, JSON ayrıştırma hatası."""
import pytest
from unittest.mock import AsyncMock, patch

from src.agents.analyst import QueryAnalyst


class TestQueryAnalystNormalFlow:
    """Normal akış: geçerli sorgu, model geçerli JSON döndürür."""

    @pytest.mark.asyncio
    async def test_analyze_returns_dict_with_task_type(self, mock_llm_client):
        mock_llm_client.ask = AsyncMock(
            return_value='{"task_type": "coding", "reason": "hesaplama var", "plan": ["Kod yaz"]}'
        )
        analyst = QueryAnalyst(mock_llm_client)
        result = await analyst.analyze("orders.json'dan toplam sipariş sayısı?")
        assert result["task_type"] == "coding"
        assert "reason" in result
        assert "plan" in result

    @pytest.mark.asyncio
    async def test_analyze_rag_task_type(self, mock_llm_client):
        mock_llm_client.ask = AsyncMock(
            return_value='{"task_type": "rag", "reason": "bilgi sorusu", "plan": ["Ara"]}'
        )
        analyst = QueryAnalyst(mock_llm_client)
        result = await analyst.analyze("Menüde hangi pizzalar var?")
        assert result["task_type"] == "rag"


class TestQueryAnalystBadInputAndFormat:
    """Eksik/hatalı giriş ve model yanıt formatı hataları."""

    @pytest.mark.asyncio
    async def test_analyze_empty_query_still_calls_llm_returns_fallback_if_invalid(self, mock_llm_client):
        """Boş sorgu: LLM çağrılır; dönen yanıt geçersiz JSON ise fallback dict döner."""
        mock_llm_client.ask = AsyncMock(return_value="Sadece düz metin, JSON yok.")
        analyst = QueryAnalyst(mock_llm_client)
        result = await analyst.analyze("")
        assert result["task_type"] == "general"
        assert "JSON ayrıştırılamadı" in result["reason"]

    @pytest.mark.asyncio
    async def test_analyze_malformed_json_uses_fallback_with_meaningful_reason(self, mock_llm_client):
        """Model bozuk JSON döndürürse: anlamlı gerekçe ile general fallback."""
        mock_llm_client.ask = AsyncMock(return_value='{"task_type": "coding"')  # eksik kapanış
        analyst = QueryAnalyst(mock_llm_client)
        result = await analyst.analyze("bir şey sor")
        assert result["task_type"] == "general"
        assert "JSON ayrıştırılamadı" in result["reason"]
        assert result["plan"] == ["Doğrudan cevap üret."]

    @pytest.mark.asyncio
    async def test_analyze_json_with_extra_text_extracts_valid_object(self, mock_llm_client):
        """Yanıt 'Evet şöyle: {...}' gibi metin içeriyorsa: ilk geçerli JSON objesi alınır."""
        raw = 'Cevap şöyle:\n{"task_type": "web_search", "reason": "ara", "plan": ["Ara"]}'
        mock_llm_client.ask = AsyncMock(return_value=raw)
        analyst = QueryAnalyst(mock_llm_client)
        result = await analyst.analyze("test")
        assert result["task_type"] == "web_search"
