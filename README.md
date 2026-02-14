## Multi‑Agent Local DocService

Bu proje, yerel LLM’ler (Ollama) ve LangGraph kullanarak inşa edilmiş, çok ajanlı bir **doküman asistanı (DocService)**’tir.  
Ana amaç, `data/` klasöründeki yapılandırılabilir veri setleri + internet araması + kod çalıştırma kombinasyonuyla:

- soruları **analiz eden** bir ajan,
- **doküman + web araştırması** yapan bir ajan,
- **Python kodu yazarak** hesaplama/istatistik yapan bir ajan

üzerinden, uçtan uca bir çözüm üretmektir.

`data/` içindeki pizza restoranı verileri (menu/orders/reviews) **sadece mock ve test amaçlıdır**.  
Bu servis, aynı yapıyla bambaşka domain’lere (kurumsal dokümanlar, loglar, raporlar vb.) uyarlanmak üzere tasarlanmıştır:

- Yeni veriler eklemek için sadece `data/` klasörünü değiştirmek,
- Ajan davranışını güncellemek için ilgili prompt’ları düzenlemek yeterlidir.


### Mimari Genel Bakış

- **Yerel LLM Katmanı**
  - Ollama üzerinden iki model:
    - **fast**: `llama3.2:latest` – kısa/genel cevaplar
    - **smart**: `llama3.1:8b` – analiz, kod üretimi, karmaşık görevler
  - Model seçimi `src/llm_client.py` içindeki `_select_model` fonksiyonu ile `task_type` ve prompt uzunluğuna göre yapılır.

- **Ajanlar**
  - **Sorgu Analisti – `QueryAnalyst` (`src/agents/analyst.py`)**
    - Kullanıcı sorgusunu analiz eder.
    - Çıktısı: `{"task_type": "web_search" | "rag" | "coding" | "general", "reason": ..., "plan": [...]}`  
    - `task_type` alanına göre hangi node’un çalışacağına LangGraph karar verir.
  - **Araştırmacı Ajan – `ResearcherAgent` (`src/agents/researcher.py`)**
    - `data/` klasöründeki dosyaları (txt/md/json) doğrudan okur.
    - Chroma tabanlı vektör veritabanından (RAG) ek bağlam çeker.
    - Gerekirse internet araması yapar (`SearchTool`).
    - Tüm bu bağlamları birleştirip LLM’den **metinsel cevap** üretir.
  - **Kodlayıcı Ajan – `CoderAgent` (`src/agents/coder.py`)**
    - Soru hesaplama/istatistik gerektiriyorsa, LLM’den **sadece çalıştırılabilir Python kodu** ister.
    - Kodu `CodeExecutor` ile proje kökünde (`./data` erişilebilir) çalıştırır.
    - Gerekirse bir kez hata düzeltme denemesi yapar.
    - Çıktı sadece bir sayıysa doğrudan sayı döner; değilse kısa özet üretir.

- **Orkestrasyon – LangGraph**
  - `src/orchestration.py`:
    - `AgentState = { query, decision, response }`
    - Akış:
      1. **analyst** node → `QueryAnalyst.analyze`
      2. Karara göre:
         - `researcher` → `ResearcherAgent.research`
         - `coder` → `CoderAgent.solve`
         - `general` → doğrudan `LLMClient.ask`
      3. Seçilen node’un çıktısı `response` olarak kullanıcıya döner.

- **Monitoring – Langfuse**
  - `requirements.txt` → `langfuse` entegrasyonu.
  - `src/llm_client.py`
    - Her LLM çağrısı için Langfuse üzerinde bir **generation** observation oluşturur.
  - `main.py`
    - Her kullanıcı sorgusu için bir üst seviye **user_query span/trace** açılır.
  - Böylece:
    - Hangi soruda hangi ajan devreye girmiş,
    - Hangi prompt’lar gönderilmiş,
    - Hangi model seçilmiş,
    - Çıktı ne olmuş  
    bunlar Langfuse UI üzerinden izlenebilir.


### Önemli Dosyalar ve Rolleri

- **`main.py`**
  - Uygulamanın giriş noktası.
  - Ortam değişkenlerini (`.env`) yükler.
  - LLMClient, ajanlar, vektör veritabanı ve LangGraph grafini başlatır.
  - Kullanıcıdan CLI üzerinden soru alır, sonucu Rich ile panel olarak yazdırır.

- **`src/llm_client.py`**
  - Ollama üzerinden LLM çağrılarını yönetir.
  - `task_type` (general/coding/...) ve prompt uzunluğuna göre **fast vs smart** model seçer.
  - Langfuse ile her çağrıyı trace eder.

- **`src/agents/analyst.py`**
  - Sorgunun niyetini çözen analiz ajanı.
  - `task_type` kararının tek kaynağı; manuel `if/elif` routing yerine bu karar kullanılır.

- **`src/agents/researcher.py`**
  - `data/` klasöründeki tüm txt/md/json dosyalarını okur.
  - `VectorStoreManager` ile RAG araması yapar.
  - `SearchTool` ile internet araması yapar.
  - Yerel veri ile çelişen internet bilgisini görmezden gelerek yanıt üretir.

- **`src/agents/coder.py`**
  - İstatistik, sayma, toplam, ortalama vb. hesaplar için Python kodu üretir ve çalıştırır.
  - `orders.json`, `reviews.json`, `menu.json`, `expenses.json` şemaları prompt içinde açıkça tanımlanmıştır.

- **`src/tools/code_executor.py`**
  - LLM çıktısından ```python``` bloğunu ayıklar.
  - Kodu proje kök dizininde (`./data` yolları çalışsın diye) güvenli şekilde çalıştırır.
  - Çıktıyı veya traceback’i string olarak döner.

- **`src/tools/search_tool.py`**
  - Tavily API (varsa), DuckDuckGo ve Wikipedia üzerinden internet araması yapabilen tool.

- **`src/utils/document_processor.py`**
  - Pdf/txt/md/json dosyalarını parçalayarak vector store’a besler.

- **`src/utils/vector_store.py`**
  - Chroma tabanlı vektör veritabanı yönetimi (ekleme, arama).

- **`data/`**
  - **Mock / test data**. Projenin amacı **pizza analizi** değil; pizza verileri, ajanların veriyle nasıl çalıştığını test etmek için seçilmiş basit bir senaryo:
    - `menu.json`: Pizza çeşitleri, fiyatlar ve glutensiz/vejetaryen etiketleri.
    - `orders.json`: Müşteri siparişleri.
    - `reviews.json`: Müşteri değerlendirmeleri (hız, lezzet, sunum, hizmet, kalabalık).
    - `welcome.txt`: Dükkan kuralları, prim tarihi vb. sabit bilgiler.
  - Aynı yapı, farklı domain’ler için yeniden kullanılabilir:
    - Dosyaları değiştir,
    - Gerekirse ajan prompt’larını yeniden yaz,
    - Sistem yeni domain’de çalışmaya devam eder.


## Kurulum

### Gerekli önkoşullar

- Python 3.13 (veya en az 3.10+)
- Ollama kurulu ve aşağıdaki modeller indirilmiş olmalı:
  - `ollama pull llama3.2:latest`
  - `ollama pull llama3.1:8b`

### Adımlar

```bash
git clone <repo-url>
cd <repo-klasoru>

python3 -m venv .venv
source .venv/bin/activate  # Windows için: .venv\Scripts\activate

pip install -r requirements.txt
```

`.env` dosyasını proje kökünde oluştur:

```bash
cp .env.example .env  # varsa
```

veya manuel olarak:

```text
TAVILY_API_KEY=tvly-xxx           # varsa
LANGFUSE_PUBLIC_KEY=pk-lf-xxx     # Langfuse kullanıyorsan
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

Bu değişkenler set edilmemişse:

- Tavily yerine DuckDuckGo / Wikipedia fallback devreye girer.
- Langfuse SDK no-op çalışır; uygulama bozulmaz, sadece trace düşmez.


## Çalıştırma ve Önemli Komutlar

### Uygulamayı başlatma

Proje kökünde, sanal ortam aktifleştirilmişken:

```bash
PYTHONPATH=. python3 main.py
```

Başlangıçta:

- `data/` klasöründeki tüm txt/md/json dosyaları okunur.
- Chroma vektör veritabanına embed edilip kaydedilir (`./chroma_db`).

CLI’de:

- `Soru sorun (çıkış için 'exit'):` satırını göreceksin.
- `exit`, `quit` veya `çıkış` yazarak programdan çıkabilirsin.

### Vektör veritabanını (Chroma) temizleme

Yeni bir data set ile **sıfırdan** embed etmek istediğinde:

```bash
rm -rf chroma_db
PYTHONPATH=. python3 main.py
```

Bu komut:

- Eski tüm embedding’leri siler.
- Uygulama açılırken `data/` klasörünü yeniden okur ve yeni `chroma_db` oluşturur.


## Birim Testleri

Testler `tests/` klasöründe **pytest** ile yazılmıştır. Hem normal akışları hem de öngörülebilir hata durumlarını kapsar; bu senaryolarda üretilen **anlamlı hata mesajları** testlerle doğrulanır.

### Neler test ediliyor?

| Bileşen | Normal akış | Hata senaryoları |
|--------|-------------|------------------|
| **LLMClient** | Model seçimi (coding → smart, general/kısa → fast, uzun prompt → smart), başarılı `ask` yanıtı | API 404/500 (geçersiz veya yüklü olmayan model): "Model hatası (model_adı): ..." mesajı |
| **QueryAnalyst** | Geçerli JSON ile `task_type` (coding, rag, web_search), metin içinde gömülü JSON çıkarımı | Boş sorgu, bozuk JSON: fallback `task_type: general` ve "JSON ayrıştırılamadı." gerekçesi |
| **CodeExecutor** | ```python``` bloğu çalıştırma, ham kod, çıktı yoksa bilgilendirici mesaj | Boş/eksik kod bloğu: "Kod Çalıştırma Hatası: ... kod bloğu bulunamadı"; sözdizimi/çalışma hatası: traceback ile anlamlı mesaj |
| **SearchTool** | — | Tüm kaynaklar başarısız: "ulaşılamıyor", "TAVILY_API_KEY" veya "tekrar deneyin" içeren mesaj; Tavily hata mesajı üçlüde taşınır |
| **CoderAgent** | Sayısal çıktı doğrudan dönüş, metin çıktı için LLM özeti | Executor çıktı üretmezse veya iki kez hata verirse: anlamlı hata/özet mesajı |
| **ResearcherAgent** | LLM yanıtı, arama sonucunun prompt'a geçmesi | Arama "ulaşılamıyor" mesajı döndürse bile yerel bağlamla cevap üretimi |

### (a) Normal akış senaryoları — nasıl karşılanıyor?

- **LLMClient:** `_select_model` ile task_type ve prompt uzunluğuna göre doğru model seçilir; `ask` başarılı HTTP yanıtında gelen metin döner.
- **QueryAnalyst:** LLM geçerli JSON döndürdüğünde `task_type`, `reason`, `plan` alanları assert edilir; JSON metin içinde gömülüyse çıkarılıp parse edildiği test edilir.
- **CodeExecutor:** Geçerli kod bloğunun stdout'u, çıktı olmadığında ise "Kod başarıyla çalıştı (Çıktı üretilmedi)." mesajı doğrulanır.
- **CoderAgent / ResearcherAgent:** Mock client ve araçlarla başarılı akışta dönen cevap ve prompt içeriği kontrol edilir.

### (b) Öngörülebilir hata durumları — nasıl karşılanıyor?

- **Geçersiz model seçimi / API hatası:** Ollama'da olmayan model veya 404/500 yanıtı simüle edilir; dönen stringte "Model hatası" ve seçilen model adı assert edilir.
- **Eksik veya hatalı giriş formatı:** Analyst'e boş veya geçersiz JSON döndüren mock verilir; fallback dict ve "JSON ayrıştırılamadı." gerekçesi test edilir. CodeExecutor'a boş blok veya kod olmayan giriş verilir; "kod bloğu bulunamadı" veya SyntaxError/traceback mesajı doğrulanır.
- **Tool çağrısından dönen hata:** SearchTool tüm kaynaklar kapalıyken anlamlı mesaj ve kaynak "yok" döner; Tavily hata mesajı üçlüde taşınır. CodeExecutor sözdizimi/çalışma hatası döndürür; CoderAgent'ta executor iki kez hata verince veya çıktı üretmeyince son özet/hata mesajı assert edilir. Researcher'da arama hata mesajı döndürse bile akışın devam ettiği test edilir.

### (c) Anlamlı hata mesajları — nasıl doğrulanıyor?

Her hata senaryosunda testler, kullanıcıya veya geliştiriciye anlamlı bilgi veren ifadeleri **metin üzerinde assert** eder:

- Model/API: `"Model hatası"`, model adı.
- Analyst: `"JSON ayrıştırılamadı."`, `"Doğrudan cevap üret."` planı.
- CodeExecutor: `"Kod Çalıştırma Hatası"`, `"kod bloğu bulunamadı"`, `"SyntaxError"` / `"ZeroDivisionError"` veya traceback.
- SearchTool: `"ulaşılamıyor"`, `"TAVILY_API_KEY"` veya `"tekrar deneyin"`.
- CoderAgent: Çıktı yok veya tekrarlayan hata sonrası dönen özette hata ile ilgili anahtar kelimeler.

Böylece hata mesajları sadece üretilmiş olmakla kalmaz; değişiklik yapıldığında bozulmaları testler yakalar.

### Testler neden önemli?

- **Regresyonu önler:** Model seçimi, routing, JSON parsing veya tool hata davranışı değiştiğinde testler kırarak fark ettirir.
- **Hata davranışını sözleşme haline getirir:** "Geçersiz model" veya "kod bloğu bulunamadı" gibi mesajlar testte sabitlendiği için kullanıcıya tutarlı geri bildirim verilir.
- **Refactoring güveni verir:** Ajanları veya araçları yeniden düzenlerken mevcut davranışın korunduğu testlerle doğrulanır.
- **Dokümantasyon işlevi görür:** Test isimleri ve assert'ler, sistemin normal ve hata durumlarında ne yaptığını özetler.

### Testleri çalıştırma

Sanal ortam aktifken, proje kökünde:

```bash
pip install pytest pytest-asyncio   # gerekirse
PYTHONPATH=. pytest tests/ -v --tb=short
```


## Basit Çalışma Akışı (Algoritma)

1. **Kullanıcı girişi**
   - CLI üzerinden soru girilir:
     - Örnek: “Ortalama lezzet puanını JSON verileri üzerinden hesapla”

2. **Sorgu analizi (QueryAnalyst)**
   - Soru ve açıklayıcı sistem prompt’u birlikte LLM’e gönderilir.
   - LLM’den sadece JSON beklenir:
     - `task_type = "coding"` → sayı/istatistik/hesaplama
     - `task_type = "web_search" / "rag"` → açıklama/bilgi
     - `task_type = "general"` → sohbet / belirsiz

3. **LangGraph yönlendirmesi**
   - `task_type` değerine göre:
     - `coding` → `CoderAgent.solve`
     - `web_search` / `rag` → `ResearcherAgent.research`
     - `general` → doğrudan `LLMClient.ask`

4. **Researcher akışı**
   - `data/` klasöründeki dosyalar string olarak bir araya getirilir.
   - Vektör veritabanı ile anlam benzerliği araması yapılır.
   - İnternet araması (varsa Tavily) ile desteklenir.
   - Tüm bağlam, tek bir prompt içinde LLM’e verilir.
   - Yerel veri ile çelişen internet bilgisini görmezden gelerek yanıt üretir.

5. **Coder akışı**
   - LLM’e, **yalnızca tek bir ```python``` bloğu** üretmesi gerektiği, placeholder kullanmaması, `./data`’daki JSON şemalarına uyması gerektiği söylenir.
   - `CodeExecutor` bu kodu çalıştırır:
     - Hata varsa traceback string olarak döner.
     - Hiç çıktı yoksa bu da hata sayılır ve bir kez daha düzeltme denemesi yapılır.
   - Çıktı:
     - Salt bir sayıysa (örneğin `10` veya `4.6`) doğrudan kullanıcıya dönülür.
     - Değilse, kısa bir Türkçe özet üretilir.

6. **Cevabın gösterilmesi**
   - `main.py` Rich kullanarak cevabı çerçeveli panel içinde yazdırır.
   - Aynı soru Langfuse üzerinde bir trace olarak kaydedilir.


## Mock Pizza Verileri ve Modülerlik

Bu projede kullanılan pizza restoranı verileri **sadece örnek/müşterek bir senaryo**dur:

- Amaç, gerçek bir ürünün (örneğin iç sistem dokümanları, log analizi, sözleşme inceleme) yerini almak değil;
- Çok ajanlı mimariyi, RAG + web search + code execution kombinasyonunu **somut ve kolay anlaşılır** bir domain üzerinde göstermek.

- Yeni domain’e uyarlamak için:
  - `data/` klasöründeki dosyaları kendi verilerinle değiştir,
  - Gerekirse ajan prompt’larını (özellikle `QueryAnalyst`, `ResearcherAgent`, `CoderAgent`) kendi kullanım senaryona göre ayarla,
  - Aynı orkestrasyon ve araç setiyle sistemini çalıştır.
