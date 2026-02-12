from src.llm_client import LLMClient
from src.tools.code_executor import CodeExecutor

class CoderAgent:
    def __init__(self, client: LLMClient, executor: CodeExecutor):
        self.client = client
        self.executor = executor

    async def solve(self, query: str) -> str:
        """
        Kullanıcının sorusunu çözmek için Python kodu yazar, çalıştırır ve sonucu döndürür.
        Kod yazımı her zaman 'smart' (ileri) model ile yapılır.
        """
        prompt = f"""Sen uzman bir Python programcısısın. Aşağıdaki soruyu çözmek için yalnızca çalıştırılabilir Python kodu yaz.

Kurallar:
- Yanıtında SADECE tek bir ```python ... ``` bloğu olsun; açıklama veya örnek çıktı yazma.
- Kod tam ve çalışır olsun: open() ile dosya oku, parse et, hesapla, print() ile sonucu yazdır. Placeholder veya "..." kullanma.
- Değişken isimlerini (örneğin \"pizza_type\") TANIMLAMADAN kullanma; her kullandığın değişken mutlaka daha önce atanmış olsun.
- Veri ./data/ klasöründe:
  * JSON dosyaları için: import json ile json.load() kullan (örn: menu.json, orders.json, reviews.json, expenses.json)
  * Metin dosyaları için: open() ile oku ve parse et
- JSON şemaları:
  * orders.json: kök dict; \"siparisler\" anahtarı altında müşteri listesi vardır. Her müşteri kaydında:
      - \"musteri_no\" (int)
      - \"isim\" (str)
      - \"yas_grubu\" (str)
      - \"siparisler\" (liste, içinde {{\"pizza\": str, \"adet\": int}})
    DİKKAT: Alan adı \"isim\"dir, asla \"name\" değildir. Bir müşteriyi isme göre ararken:
      - hem sorguyu hem de order[\"isim\"] değerini .lower() ile küçült ve karşılaştır.
    Örnek Python iskeleti (isimden sipariş bulmak için):
      import json
      with open(\"./data/orders.json\", encoding=\"utf-8\") as f:
          data = json.load(f)
      target_name = \"fatma çelik\"
      for order in data[\"siparisler\"]:
          if order[\"isim\"].lower() == target_name:
              print(order[\"siparisler\"])
              break
  * reviews.json: kök dict; \"puanlar\" anahtarı altında müşteri değerlendirmeleri listesi vardır. Her kayıtta:
      - \"musteri_no\" (int)
      - \"isim\" (str)
      - \"hiz\" (int)
      - \"lezzet\" (int)
      - \"sunum\" (int)
      - \"hizmet\" (int)
      - \"kalabalik\" (int)
    DİKKAT: Bu JSON'da TARİH ALANI YOKTUR. Asla review[\"tarih\"] veya benzeri alanlara erişmeye çalışma.
    \"3-9 Şubat aralığı\" gibi ifadeler sadece dönem açıklamasıdır; ortalama hesaplamak için TÜM kayıtlardaki ilgili puanları kullan.
    Örnek Python iskeleti (musteri_no ile bir puanı bulmak için):
      import json
      with open(\"./data/reviews.json\", encoding=\"utf-8\") as f:
          data = json.load(f)
      target_no = 9
      for review in data[\"puanlar\"]:
          if review[\"musteri_no\"] == target_no:
              print(review[\"hiz\"])
              break
    Örnek Python iskeleti (tüm müşteriler için ortalama \"hiz\" puanını bulmak için):
      import json
      with open(\"./data/reviews.json\", encoding=\"utf-8\") as f:
          data = json.load(f)
      total = 0
      count = 0
      for review in data[\"puanlar\"]:
          total += review[\"hiz\"]
          count += 1
      avg = total / count if count > 0 else 0
      print(avg)
  * menu.json: kök dict; \"pizzalar\" listesinde her öğede en az \"ad\" (str) ve \"fiyat\" (int) alanları bulunur.
  * expenses.json: kök dict; \"haftalik_toplam_gider\" anahtarı haftalık toplam gideri içerir.
- Metin/kelime eşleştirmede büyük/küçük harfe duyarsız ol (örn. .lower() veya re.IGNORECASE).

Soru: {query}"""

        code_response = await self.client.ask(prompt, task_type="coding")

        # 2. Adım: Markdown içinden kodu çıkar ve çalıştır
        execution_result = self.executor.execute(code_response)

        # Eğer kod çıktı üretmediyse bunu da hata olarak değerlendir
        if execution_result.strip().startswith("Kod başarıyla çalıştı (Çıktı üretilmedi)"):
            execution_result = "Kod Çalıştırma Hatası: Kod herhangi bir çıktı üretmedi, print() ile sonucu yazdırman gerekiyor."

        # 3. Adım: Hata varsa bir kez düzeltmeyi dene (yine smart model)
        if "Kod Çalıştırma Hatası" in execution_result:
            fix_prompt = f"""Kullanıcı sorusu: {query}
Üretilen kod (hata veriyor): {code_response}
Hata: {execution_result}
Yukarıdaki JSON şemalarını dikkate alarak bu hatayı gideren, çalışan tam Python kodunu yaz. Yanıtında SADECE ```python ... ``` bloğu olsun."""
            code_response = await self.client.ask(fix_prompt, task_type="coding")
            execution_result = self.executor.execute(code_response)

        # Eğer çıktı sade bir sayı ise, doğrudan onu döndür (özet için modele gitme)
        numeric_output = execution_result.strip()
        # Sona eklenmiş satır sonlarını veya boşlukları temizle
        try:
            # Tam sayı olarak parse edebiliyorsak, direkt sayıyı string olarak döndür
            int_value = int(numeric_output)
            return str(int_value)
        except ValueError:
            pass

        if "Kod Çalıştırma Hatası" in execution_result:
            final_prompt = f"""Kullanıcı sorusu: {query}
Kod çalıştırma çıktısı (hata): {execution_result}

Yalnızca hatayı 1-2 cümleyle, sade Türkçe olarak açıkla. Tahmini sonuç veya sayı üretme; sadece hatayı özetle."""
        else:
            final_prompt = f"""Kullanıcı sorusu: {query}
Kod çalıştırma çıktısı: {execution_result}

Bu çıktıyı kullanarak kısa, Türkçe bir özet ver. Çıktıda sayı varsa ona göre cevap ver; uydurma yapma."""

        return await self.client.ask(final_prompt, task_type="general")