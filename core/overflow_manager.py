class OverflowManager:
    """
    溢位管理模組，負責收集在 PDF 頁面中因為空間不足而無法完整容納的翻譯文本，
    以便在 PDF 結尾統一渲染「翻譯溢位附錄」頁面。
    """
    def __init__(self):
        self.overflows = []

    def add_overflow(self, page_num: int, block_id: int, original_text: str, full_translation: str):
        """
        記錄溢位區塊的相關資訊
        :param page_num: 發生溢位的頁碼 (1-indexed)
        :param block_id: 發生溢位的區塊識別碼
        :param original_text: 英文原文
        :param full_translation: 完整中文譯文
        """
        self.overflows.append({
            "page_num": page_num,
            "block_id": block_id,
            "original_text": original_text,
            "full_translation": full_translation
        })

    def has_overflows(self) -> bool:
        """
        當前是否有任何溢位資料
        """
        return len(self.overflows) > 0

    def get_all_overflows(self) -> list[dict]:
        """
        取得所有溢位紀錄
        """
        return self.overflows

    def clear(self):
        """
        清空既有紀錄，常用於開啟新任務時
        """
        self.overflows = []
