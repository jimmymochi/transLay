from abc import ABC, abstractmethod

class BaseTranslator(ABC):
    """
    所有翻譯器實作的抽象基底類別
    """
    
    @abstractmethod
    def translate(self, text: str) -> str:
        """
        單一字串翻譯介面
        :param text: 來源英文文字
        :return: 翻譯後的繁體中文文字
        """
        pass

    def translate_batch(self, texts: list[str]) -> list[str]:
        """
        批次翻譯預設實作，可由子類別優化以減少 API 請求次數
        :param texts: 來源英文文字列表
        :return: 翻譯後的繁體中文文字列表
        """
        return [self.translate(t) for t in texts]
