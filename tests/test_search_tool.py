"""SearchTool birim testleri: tüm kaynaklar başarısız olduğunda anlamlı hata mesajı."""
import os
import pytest
from unittest.mock import patch, MagicMock

from src.tools.search_tool import SearchTool


class TestSearchToolErrorCases:
    """Arama başarısız olduğunda (Tavily yok, scraping/Wikipedia da sonuç vermez): anlamlı mesaj."""

    def test_search_with_source_returns_meaningful_message_when_all_fail(self):
        """Tavily key yok, scraping ve Wikipedia mock ile boş dönerse: kullanıcıya net mesaj."""
        with patch.dict(os.environ, {}, clear=False):
            # TAVILY_API_KEY yok
            if "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]
        tool = SearchTool()
        with patch.object(tool, "_search_with_direct_scraping", return_value=None), \
             patch.object(tool, "_search_with_simple_api", return_value=None):
            text, source, tavily_err = tool.search_with_source("test query")
        assert "ulaşılamıyor" in text or "internet" in text.lower()
        assert "TAVILY_API_KEY" in text or "tekrar deneyin" in text
        assert source == "yok"

    def test_search_returns_same_message_when_all_sources_fail(self):
        """search() sadece metni döndürür; aynı anlamlı mesaj olmalı."""
        with patch.dict(os.environ, {}, clear=False):
            if "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]
        tool = SearchTool()
        with patch.object(tool, "_search_with_direct_scraping", return_value=None), \
             patch.object(tool, "_search_with_simple_api", return_value=None):
            result = tool.search("test")
        assert "ulaşılamıyor" in result or "internet" in result.lower() or "TAVILY" in result


class TestSearchToolTavilyError:
    """Tavily API key varken Tavily hata döndürürse: hata mesajı üçlüde (tavily_error) taşınır."""

    def test_tavily_error_propagated_in_tuple(self):
        tool = SearchTool()
        with patch.dict(os.environ, {"TAVILY_API_KEY": "fake-key"}, clear=False):
            tool.tavily_api_key = "fake-key"
        with patch.object(tool, "_search_with_tavily", return_value=(None, "API kotası aşıldı")), \
             patch.object(tool, "_search_with_direct_scraping", return_value=None), \
             patch.object(tool, "_search_with_simple_api", return_value=None):
            text, source, tavily_error = tool.search_with_source("test")
        assert tavily_error == "API kotası aşıldı"
        assert source == "yok"
