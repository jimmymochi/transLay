import re
from utils.logger import get_logger

class TextFilter:
    """
    文字過濾器，負責過濾掉不需進行翻譯的區塊（如單純的數值、公式、頁碼、文獻引用符號等），
    維持論文排版中公式與特殊標記的原汁原味。
    """
    def __init__(self):
        self.logger = get_logger()
        # 匹配數學公式的特徵正則表達式
        # 例如：單獨一行的 x = a + b, f(x) = y, E = mc^2, 包含大量 +, -, =, *, /, ^, <, > 符號
        self.math_symbols = re.compile(r'^[a-zA-Z\d\s\+\-\*\/=\(\)\<\>\,\.\_\^\\\{\}\[\]\:\;\#\%\!\?\$\&\|]+$')
        
    def is_suspected_formula(self, text: str) -> bool:
        """
        利用幾何與正則特徵判定該文字是否為公式。
        """
        clean_text = text.strip()
        if not clean_text:
            return False
            
        # 1. 如果極短，且主要由符號和單個字母組成，例如 "x", "y = ax + b", "(1)"
        if len(clean_text) < 15:
            # 判斷是否為公式標號例如 "(1)", "(2a)"
            if re.match(r'^\(\d+[a-zA-Z]?\)$', clean_text):
                return True
            # 判斷是否為純變數運算
            if self.math_symbols.match(clean_text) and any(op in clean_text for op in ['+', '-', '=', '*', '/', '<', '>', '^']):
                return True

        # 2. 如果包含 LaTeX 常用關鍵字
        latex_keywords = ['\\alpha', '\\beta', '\\gamma', '\\theta', '\\sigma', '\\sum', '\\int', '\\frac', '\\partial', '\\infty']
        if any(kw in clean_text for kw in latex_keywords):
            return True

        return False

    def is_suspected_page_number_or_header(self, text: str, bbox: tuple[float, float, float, float], page_height: float) -> bool:
        """
        判斷文字是否為頁碼或常規頁首頁尾
        """
        clean_text = text.strip()
        y0, _, _, y1 = bbox
        
        # 1. 極短且僅有數字 (通常是頁碼)
        if clean_text.isdigit() and len(clean_text) <= 3:
            # 在最頂部或最底部
            if y0 < 50.0 or y1 > page_height - 50.0:
                return True
                
        # 2. 頁底或頁頂常見的論文標記（例如 "Preprint", "arXiv:...", "Vol. No."）
        if y0 < 40.0 or y1 > page_height - 40.0:
            patterns = [
                r'^arxiv:\d+\.\d+.*$',
                r'^volume\s+\d+.*$',
                r'^page\s+\d+.*$',
                r'^proceedings\s+.*$',
                r'^journal\s+of\s+.*$',
                r'^copyright\s+.*$',
                r'^\d{4}\s+ieee.*$'
            ]
            for pat in patterns:
                if re.match(pat, clean_text, re.IGNORECASE):
                    return True
                    
        return False

    def should_translate(self, text: str, bbox: tuple[float, float, float, float], page_height: float) -> bool:
        """
        統合判斷：此區塊是否應該被翻譯。
        """
        clean_text = text.strip()
        
        # 1. 空字串不翻譯
        if not clean_text:
            return False
            
        # 2. 長度小於 2 且非中英文字母（如單個標點符號）不翻譯
        if len(clean_text) < 2 and not clean_text.isalnum():
            return False
            
        # 3. 頁首頁尾與頁碼不翻譯
        if self.is_suspected_page_number_or_header(clean_text, bbox, page_height):
            return False
            
        # 4. 公式與純數學式不翻譯
        if self.is_suspected_formula(clean_text):
            return False
            
        # 5. 純數字或符號（如 [1], 2026, 1.25）不翻譯
        if re.match(r'^[\d\s\.,\[\]\-]+$', clean_text):
            return False
            
        return True
