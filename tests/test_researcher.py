"""ResearcherAgent birim testleri: normal araştırma, search/vector_store davranışı."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.researcher import ResearcherAgent


class TestResearcherAgentNormalFlow:
    """Normal akış: search ve vector_store sonuç döner, LLM cevap üretir."""

    @pytest.mark.asyncio
    async def test_research_returns_llm_response(self, mock_llm_client, mock_search_tool, mock_vector_store):
        mock_llm_client.ask = AsyncMock(return_value="Yerel menüde Margherita ve Pepperoni var.")
        mock_search_tool.search = MagicMock(return_value="İnternet: Pizza çeşitleri...")
        mock_vector_store.search = MagicMock(return_value=[])
        researcher = ResearcherAgent(mock_llm_client, mock_search_tool, mock_vector_store)
        result = await researcher.research("Menüde hangi pizzalar var?")
        assert "Margherita" in result or "Pizza" in result or "menü" in result.lower()

    @pytest.mark.asyncio
    async def test_research_passes_search_result_to_llm(self, mock_llm_client, mock_search_tool, mock_vector_store):
        mock_llm_client.ask = AsyncMock(return_value="Özet: A.")
        mock_search_tool.search = MagicMock(return_value="Önemli bilgi: X")
        researcher = ResearcherAgent(mock_llm_client, mock_search_tool, mock_vector_store)
        await researcher.research("test")
        call_args = mock_llm_client.ask.call_args[0][0]
        assert "Önemli bilgi: X" in call_args or "X" in call_args


class TestResearcherAgentSearchError:
    """Search tool hata/boş döndürürse: yine de LLM'e giden prompt'ta bu bilgi olmalı."""

    @pytest.mark.asyncio
    async def test_research_when_search_returns_error_message(self, mock_llm_client, mock_search_tool, mock_vector_store):
        """Search 'ulaşılamıyor' gibi mesaj döndürürse agent yine de cevap üretebilir."""
        mock_search_tool.search = MagicMock(
            return_value="Şu an internet sonuçlarına ulaşılamıyor. Lütfen biraz sonra tekrar deneyin veya Tavily API key ekleyin."
        )
        mock_llm_client.ask = AsyncMock(
            return_value="Yerel dosyalara göre menüde iki pizza var."
        )
        researcher = ResearcherAgent(mock_llm_client, mock_search_tool, mock_vector_store)
        result = await researcher.research("Menüde ne var?")
        assert "menü" in result.lower() or "pizza" in result.lower()
        call_args = mock_llm_client.ask.call_args[0][0]
        assert "ulaşılamıyor" in call_args or "Tavily" in call_args
