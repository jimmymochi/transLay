import time
import urllib.parse
import requests
from translators.base_translator import BaseTranslator
from utils.logger import get_logger

class GoogleTranslator(BaseTranslator):
    """
    免費免密鑰的 Google 翻譯整合模組
    採用 Google 官方開放的單一查詢 Web 端點，適合非商業高頻使用
    """
    def __init__(self, timeout=10, user_agent=None):
        self.logger = get_logger()
        self.timeout = timeout
        self.url = "https://translate.googleapis.com/translate_a/single"
        self.headers = {
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def translate(self, text: str) -> str:
        """
        將英文文字翻譯成繁體中文 (zh-TW)
        """
        if not text or text.strip() == "":
            return ""

        # 清理換行符，保持段落連貫性
        cleaned_text = text.replace("\r", "").replace("\n", " ").strip()
        
        # 限制單次 GET 請求長度 (約 1800 字元)，若過長則進行分段翻譯
        if len(cleaned_text) > 1500:
            return self._translate_long_text(cleaned_text)

        return self._translate_single(cleaned_text)

    def _translate_single(self, cleaned_text: str) -> str:
        """
        執行單次 Google 翻譯 API 請求（不含長度檢查，避免遞迴）
        """
        # 請求參數
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-TW",
            "dt": "t",
            "q": cleaned_text
        }

        # 錯誤重試機制 (最多重試 3 次)
        for attempt in range(3):
            try:
                # 為了避免頻繁呼叫被 Google 封鎖，適當間隔時間
                if attempt > 0:
                    time.sleep(1.0 * attempt)
                    
                response = requests.get(
                    self.url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    self.logger.warning("Google 翻譯回報 429 Too Many Requests，稍候再試...")
                    time.sleep(2.0 * (attempt + 1))
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                # 解析 Google 巢狀 JSON 結構 (第一個元素內含多組分句對應)
                translated_parts = []
                if data and len(data) > 0 and data[0]:
                    for part in data[0]:
                        if part and len(part) > 0 and part[0]:
                            translated_parts.append(part[0])
                
                result = "".join(translated_parts)
                return result

            except Exception as e:
                self.logger.error(f"Google 翻譯嘗試第 {attempt + 1} 次失敗: {e}")
                if attempt == 2:
                    return f"[翻譯失敗] {cleaned_text}"
        
        return cleaned_text

    def _translate_long_text(self, text: str) -> str:
        """
        針對過長文字進行語意斷句批次翻譯
        """
        self.logger.info("檢測到超長文字區塊，啟用分段翻譯機制...")
        # 簡單的分句法 (以句號、問號、驚嘆號斷句)
        sentences = []
        current = []
        for word in text.split(" "):
            current.append(word)
            if word.endswith((".", "?", "!")):
                sentences.append(" ".join(current))
                current = []
        if current:
            sentences.append(" ".join(current))

        # 分組打包翻譯 (每組不超過 1000 字元)
        chunks = []
        temp_chunk = []
        temp_len = 0
        for sent in sentences:
            if temp_len + len(sent) > 1000:
                chunks.append(" ".join(temp_chunk))
                temp_chunk = [sent]
                temp_len = len(sent)
            else:
                temp_chunk.append(sent)
                temp_len += len(sent)
        if temp_chunk:
            chunks.append(" ".join(temp_chunk))

        translated_chunks = []
        for chunk in chunks:
            # 直接呼叫 _translate_single，不再經過 translate() 的長度檢查，徹底杜絕無限遞迴
            translated_chunks.append(self._translate_single(chunk))
            # 延遲避免請求過快
            time.sleep(0.5)

        return "".join(translated_chunks)
