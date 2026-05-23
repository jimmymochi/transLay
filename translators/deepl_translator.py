import deepl
from translators.base_translator import BaseTranslator
from utils.logger import get_logger

class DeepLTranslator(BaseTranslator):
    """
    DeepL 翻譯整合模組，使用官方 DeepL API 進行專業翻譯。
    """
    def __init__(self, api_key: str):
        self.logger = get_logger()
        self.api_key = api_key
        
        if api_key:
            try:
                # 官方 SDK 會自動判斷是 Free 還是 Pro 帳號
                self.translator = deepl.Translator(api_key)
            except Exception as e:
                self.logger.error(f"DeepL 客戶端初始化失敗: {e}")
                self.translator = None
        else:
            self.translator = None

    def translate(self, text: str) -> str:
        if not text or text.strip() == "":
            return ""
        if not self.translator:
            self.logger.error("未設定 DeepL API 金鑰，無法翻譯！")
            return f"[未設定 DeepL API Key] {text}"

        try:
            # 由於 DeepL 的 target_lang 使用 "ZH" (Chinese) 同時適用於簡繁，
            # 我們已在 pdf_processor 內掛載了 CCConverter (OpenCC - s2twp)，
            # 因此這裡直接翻譯成 "ZH" 即可，後置轉換器會把簡體或大陸用語完全優化為台灣學術繁體！
            result = self.translator.translate_text(text, target_lang="ZH")
            return result.text
        except Exception as e:
            self.logger.error(f"DeepL 翻譯失敗: {e}")
            return f"[DeepL 翻譯失敗] {text}"
