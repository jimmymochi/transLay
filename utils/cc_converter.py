from utils.logger import get_logger

class CCConverter:
    """
    簡繁轉換與學術用語優化器。
    利用 opencc-python-reimplemented 將譯文轉換為符合台灣學術標準的繁體中文。
    """
    _instance = None
    _cc = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CCConverter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._cc is None:
            self.logger = get_logger()
            try:
                from opencc import OpenCC
                # s2twp.json: 簡體到繁體 (台灣標準，帶詞彙修正)
                self._cc = OpenCC('s2twp')
                self.logger.info("OpenCC 簡繁轉換引擎初始化成功 (配置: s2twp)")
            except Exception as e:
                self.logger.error(f"OpenCC 簡繁轉換引擎初始化失敗: {e}")
                self._cc = None

    def convert(self, text: str) -> str:
        """
        將輸入字串進行簡繁與台灣學術用語轉換
        """
        if not text:
            return ""
        if self._cc:
            try:
                return self._cc.convert(text)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"文字簡繁轉換時出錯: {e}")
        return text
