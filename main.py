from dotenv import load_dotenv

load_dotenv()

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from langfuse import get_client

from src.llm_client import LLMClient
from src.agents.analyst import QueryAnalyst
from src.agents.researcher import ResearcherAgent
from src.agents.coder import CoderAgent
from src.tools.search_tool import SearchTool
from src.tools.code_executor import CodeExecutor
from src.utils.vector_store import VectorStoreManager
from src.utils.document_processor import DocumentProcessor
from src.orchestration import build_graph
import os
import glob

console = Console()
langfuse = get_client()

def load_data_files(vector_store: VectorStoreManager):
    """Data klasöründeki tüm dosyaları vector store'a yükler."""
    data_dir = "./data"
    if not os.path.exists(data_dir):
        return
    
    # Desteklenen dosya formatları
    supported_extensions = ["*.txt", "*.md", "*.pdf", "*.json"]
    all_chunks = []
    
    for ext in supported_extensions:
        files = glob.glob(os.path.join(data_dir, ext))
        for file_path in files:
            try:
                processor = DocumentProcessor(file_path)
                chunks = processor.process()
                all_chunks.extend(chunks)
                console.print(f"[green]✓[/green] Yüklendi: {os.path.basename(file_path)}")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Yüklenemedi {os.path.basename(file_path)}: {e}")
    
    # Tüm chunk'ları vector store'a ekle
    if all_chunks:
        vector_store.add_documents(all_chunks)
        console.print(f"[green]✓[/green] Toplam {len(all_chunks)} doküman parçası vector store'a eklendi.")

async def main():
    # 1. Başlangıç Ayarları
    console.print(Panel.fit("[bold magenta]Multi-Agent DocService Başlatılıyor...[/bold magenta]\n[cyan]MacBook M4 Pro - Yerel Llama Modelleri Aktif[/cyan]"))
    
    client = LLMClient()
    search_tool = SearchTool()
    executor = CodeExecutor()
    vector_store = VectorStoreManager() # RAG hafızası için
    
    # Data klasöründeki dosyaları yükle
    console.print("[cyan]Data klasöründeki dosyalar yükleniyor...[/cyan]")
    load_data_files(vector_store)
    
    # Ajanları oluştur
    analyst = QueryAnalyst(client)
    researcher = ResearcherAgent(client, search_tool, vector_store)
    coder = CoderAgent(client, executor)

    # LangGraph orkestrasyonu (analyst → researcher | coder | general)
    graph = build_graph(analyst, researcher, coder, client)

    while True:
        user_query = console.input("\n[bold green]Soru sorun (çıkış için 'exit'): [/bold green]")
        if user_query.lower() in ["exit", "quit", "çıkış"]:
            break

        try:
            # Her kullanıcı sorusu için Langfuse trace/span
            with langfuse.start_as_current_observation(
                as_type="span",
                name="user_query",
                input=user_query,
            ) as span:
                with Live(
                    Spinner("dots", text="Analiz ediliyor...", style="cyan"),
                    refresh_per_second=10,
                ):
                    result = await graph.ainvoke({"query": user_query})

                response = result.get("response", "Yanıt üretilemedi.")
                span.update(output=response)

            console.print(Panel(response, title="[bold green]Agent Yanıtı[/bold green]", border_style="green"))
        except Exception as e:
            console.print(f"[bold red]Bir hata oluştu: {e}[/bold red]")

if __name__ == "__main__":
    async def start():
        await main()
    
    asyncio.run(start())