"""Pytest fixtures: mock LLM client, executor, search tool, vector store."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_llm_client():
    """LLMClient yerine kullanılacak mock; ask() async döner."""
    client = MagicMock()
    client.ask = AsyncMock(return_value='{"task_type": "general", "reason": "test", "plan": []}')
    return client


@pytest.fixture
def mock_code_executor():
    """CodeExecutor mock; execute() senaryoya göre ayarlanır."""
    return MagicMock()


@pytest.fixture
def mock_search_tool():
    """SearchTool mock; search() ve search_with_source() ayarlanabilir."""
    tool = MagicMock()
    tool.search = MagicMock(return_value="Mock arama sonucu")
    tool.search_with_source = MagicMock(
        return_value=("Mock arama sonucu", "mock", None)
    )
    return tool


@pytest.fixture
def mock_vector_store():
    """VectorStoreManager mock; search() boş veya dolu liste döner."""
    store = MagicMock()
    store.search = MagicMock(return_value=[])
    return store
