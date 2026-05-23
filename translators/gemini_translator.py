import requests
from translators.base_translator import BaseTranslator
from utils.logger import get_logger

class GeminiTranslator(BaseTranslator):
    """
    基於 Google 官方 Gemini REST API 的翻譯整合模組。
    採用極輕量免 SDK 的 HTTPS POST 請求，保證二進位打包體積與最佳相容性。
    """
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.logger = get_logger()
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def translate(self, text: str) -> str:
        """
        利用 Gemini API 將英文文字精準翻譯成台灣習慣的繁體中文
        """
        if not text or text.strip() == "":
            return ""
        if not self.api_key:
            return f"[Gemini 未配置 API 金鑰] {text}"

        # 整理文字格式
        cleaned_text = text.replace("\r", "").replace("\n", " ").strip()

        # 設計精準的學術翻譯 System Prompt 提示詞
        prompt = (
            "You are a professional academic translator. "
            "Please translate the following English text to elegant Traditional Chinese (zh-TW), "
            "strictly adhering to standard Taiwanese academic terminology. "
            "Keep the original semantic structure and tone. "
            "Do NOT add any prefix, suffix, explanation, or notes. "
            "Return ONLY the translated Chinese text itself.\n\n"
            f"English text to translate:\n{cleaned_text}"
        )

        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95
            }
        }

        # 錯誤重試機制 (最多重試 3 次)
        for attempt in range(3):
            try:
                # 拼接帶有 API Key 的正式 URL
                request_url = f"{self.url}?key={self.api_key}"
                
                response = requests.post(
                    request_url,
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 429:
                    self.logger.warning("Gemini API 回報 429 配額超限，稍候重試...")
                    import time
                    time.sleep(2.0 * (attempt + 1))
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                # 解析 Gemini 回傳的標準 JSON 結構
                candidates = data.get("candidates", [])
                if candidates and len(candidates) > 0:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and len(parts) > 0:
                        translated_text = parts[0].get("text", "").strip()
                        if translated_text:
                            return translated_text
                            
                raise ValueError("無法解析 Gemini API 回傳的文字內容。")

            except Exception as e:
                self.logger.error(f"Gemini 翻譯嘗試第 {attempt + 1} 次失敗: {e}")
                if attempt == 2:
                    # 最終失敗，安全退回原文
                    return f"[Gemini 翻譯失敗] {text}"
                import time
                time.sleep(1.0)

        return text
