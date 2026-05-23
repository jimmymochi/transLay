import openai
from translators.base_translator import BaseTranslator
from utils.logger import get_logger

class OpenAITranslator(BaseTranslator):
    """
    OpenAI 翻譯整合模組，使用 GPT-4o-mini 或其他 LLM 進行高品質學術論文翻譯。
    """
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.3):
        self.logger = get_logger()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                self.logger.error(f"OpenAI 客戶端初始化失敗: {e}")
                self.client = None
        else:
            self.client = None

    def translate(self, text: str) -> str:
        if not text or text.strip() == "":
            return ""
        if not self.client:
            self.logger.error("未設定 OpenAI API 金鑰，無法翻譯！")
            return f"[未設定 OpenAI API Key] {text}"

        # 學術翻譯 Prompt，注重台灣學術用語，且只輸出翻譯結果
        system_prompt = (
            "You are a professional academic translator. Translate the following English academic text into Elegant Traditional Chinese (zh-TW). "
            "Keep the academic terminology accurate, rigorous, and native to Taiwanese academics (e.g., use '資訊' instead of '信息', '資料庫' instead of '數據庫'). "
            "Translate ONLY the given text. Do not add any introduction, explanations, meta-comments, or markdown wrapper blocks."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=self.temperature
            )
            result = response.choices[0].message.content.strip()
            return result
        except Exception as e:
            self.logger.error(f"OpenAI 翻譯失敗: {e}")
            return f"[OpenAI 翻譯失敗] {text}"
