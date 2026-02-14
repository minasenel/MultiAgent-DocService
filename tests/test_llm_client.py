"""LLMClient birim testleri: model seçimi, başarılı çağrı, API hataları (geçersiz model vb.)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.llm_client import LLMClient


class TestLLMClientSelectModel:
    """_select_model: normal akış ve sınır değerleri."""

    @pytest.fixture(autouse=True)
    def _patch_langfuse(self):
        with patch("src.llm_client.get_client") as m:
            m.return_value = MagicMock()
            yield

    def test_coding_task_type_uses_smart(self):
        client = LLMClient()
        assert client._select_model("coding", "kısa") == client.models["smart"]

    def test_calculation_task_type_uses_smart(self):
        client = LLMClient()
        assert client._select_model("calculation", "x") == client.models["smart"]

    def test_complex_reasoning_uses_smart(self):
        client = LLMClient()
        assert client._select_model("complex_reasoning", "x") == client.models["smart"]

    def test_general_short_prompt_uses_fast(self):
        client = LLMClient()
        assert client._select_model("general", "Merhaba") == client.models["fast"]

    def test_long_prompt_uses_smart(self):
        client = LLMClient()
        long_prompt = "x" * 1600
        assert client._select_model("general", long_prompt) == client.models["smart"]

    def test_unknown_task_type_defaults_to_fast(self):
        client = LLMClient()
        assert client._select_model("bilinmeyen_tip", "kısa") == client.models["fast"]


class TestLLMClientAsk:
    """ask(): başarılı yanıt ve öngörülebilir hata durumları (geçersiz model, ağ hatası)."""

    @pytest.fixture(autouse=True)
    def _patch_langfuse(self):
        with patch("src.llm_client.get_client") as m:
            m.return_value = MagicMock()
            yield

    @pytest.mark.asyncio
    async def test_ask_returns_response_on_success(self):
        client = LLMClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Evet, pizza siparişi alınır."}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await client.ask("Pizza siparişi alıyor musunuz?", task_type="general")
            assert result == "Evet, pizza siparişi alınır."

    @pytest.mark.asyncio
    async def test_ask_returns_meaningful_error_on_404_invalid_model(self):
        """Geçersiz veya yüklü olmayan model: API 404 döndüğünde anlamlı hata mesajı."""
        client = LLMClient()
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Model not found", request=MagicMock(), response=MagicMock(status_code=404)
            ))
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post = mock_post
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await client.ask("Test", task_type="coding")

            assert "Model hatası" in result
            assert client.models["smart"] in result
            assert "404" in result or "Model not found" in result or "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_ask_returns_meaningful_error_on_500_server_error(self):
        """Sunucu hatası (500): anlamlı hata mesajı döner."""
        client = LLMClient()
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Internal Server Error", request=MagicMock(), response=MagicMock(status_code=500)
            ))
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post = mock_post
            mock_client.__aexit__.return_value = None
            mock_client_cls.return_value = mock_client

            result = await client.ask("Test", task_type="general")

            assert "Model hatası" in result
            assert client.models["fast"] in result
