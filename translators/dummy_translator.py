import random
from translators.base_translator import BaseTranslator

class DummyTranslator(BaseTranslator):
    """
    用於開發除錯、壓力測試與版面調校的 Mock 翻譯器
    """
    def __init__(self, mode="normal"):
        """
        :param mode: 模擬模式，可為 "same"、"short"、"normal"、"long"、"stress"
        """
        self.mode = mode.lower()
        
        # 學術論文常用詞彙庫，用來生成看起來逼真的中文論文段落
        self.subjects = ["本研究", "此演算法", "實驗結果", "版面分析引擎", "雙欄文檔解析", "深度學習模型", "擬合演算法", "二維碰撞偵測"]
        self.verbs = ["提出了一種新的", "有效解決了", "全面優化了", "深入分析了", "詳細展示了", "顯著提升了", "完美保留了"]
        self.objects = ["空間擴張與碰撞預估策略", "雙欄論文排版錯亂問題", "中文翻譯長度溢出限制", "圖片與表格覆蓋衝突", "段落合併後的翻譯語意", "多維度文字擬合效率"]
        self.connectors = ["並進一步證明了", "從而有效克服了", "同時相容於", "旨在保障其", "在高難度情境下展現出"]
        self.conclusions = ["優異的效能與穩健性。", "顯著的排版還原度。", "極佳的實用商業價值。", "超越傳統方法的適應力。"]

    def _generate_sentence(self) -> str:
        """
        隨機組裝一句論文風格的中文句子
        """
        sub = random.choice(self.subjects)
        verb = random.choice(self.verbs)
        obj = random.choice(self.objects)
        conn = random.choice(self.connectors)
        obj2 = random.choice(self.objects)
        conclusion = random.choice(self.conclusions)
        
        if random.random() > 0.4:
            return f"{sub}{verb}{obj}，{conn}{obj2}，{conclusion}"
        else:
            return f"{sub}{verb}{obj}，並呈現出{conclusion}"

    def translate(self, text: str) -> str:
        if not text or text.strip() == "":
            return ""

        words = text.split()
        word_count = len(words)

        if self.mode == "same":
            # 複製原文，但前後加中文字標記
            return f"[Same: {text}]"

        elif self.mode == "short":
            # 產生極短的中文字
            return "【短譯文】"

        elif self.mode == "normal":
            # 一般翻譯長度 (英文單字數的 1.2 倍中文字元左右)
            target_len = int(word_count * 1.5) + 5
            sentence = ""
            while len(sentence) < target_len:
                sentence += self._generate_sentence()
            return sentence[:target_len]

        elif self.mode == "long":
            # 偏長翻譯 (英文單字數的 2.5 倍中文字元)
            target_len = int(word_count * 2.8) + 15
            sentence = ""
            while len(sentence) < target_len:
                sentence += self._generate_sentence()
            return sentence[:target_len]

        elif self.mode == "stress":
            # 壓力測試 (英文單字數的 4 倍以上，保證觸發 bbox 擴張與 overflow appendix)
            target_len = int(word_count * 4.5) + 50
            sentence = ""
            while len(sentence) < target_len:
                sentence += self._generate_sentence()
            return "【壓測】" + sentence[:target_len]

        else:
            # 預設同 normal
            target_len = int(word_count * 1.5)
            sentence = ""
            while len(sentence) < target_len:
                sentence += self._generate_sentence()
            return sentence[:target_len]
