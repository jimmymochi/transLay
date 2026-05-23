from utils.logger import get_logger
from core.bbox_expander import BBoxExpander
from core.collision_detector import CollisionDetector

class TextFitter:
    """
    Layout-Aware Text Fitter 核心擬合引擎。
    實作五階段文字放置管線，透過行高壓縮、幾何安全擴充、字號微調及附錄溢位處理，
    確保中文譯文完美嵌入 PDF 且絕對不發生碰撞與越界。
    """
    def __init__(self, config_layout=None):
        self.logger = get_logger()
        self.config = config_layout or {}
        
        self.min_font_size = self.config.get("min_font_size", 8.5)
        self.min_line_height = self.config.get("min_line_height", 1.05)
        self.default_line_height = self.config.get("default_line_height", 1.25)
        
        self.decision_logs = []

    def clear_logs(self):
        self.decision_logs = []

    def get_decision_logs(self) -> list[dict]:
        return self.decision_logs

    def wrap_text_cjk(self, text: str, max_width: float, font_size: float) -> list[str]:
        """
        中英混合高精度排版斷行演算法。
        中文字元按正方形 (寬度 = font_size) 計算，ASCII 字元按平均 0.55 倍字號計算。
        """
        lines = []
        current_line = ""
        current_width = 0.0
        
        # 避免寬度極小導致無限循環
        if max_width < font_size:
            max_width = font_size

        for char in text:
            # 判斷是否為中文字元 (常規 CJK 範圍)
            is_cjk = ord(char) > 127
            char_w = font_size if is_cjk else (font_size * 0.55)
            
            # 若為換行符，直接強制換行
            if char == '\n':
                lines.append(current_line)
                current_line = ""
                current_width = 0.0
                continue

            if current_width + char_w > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = char
                current_width = char_w
            else:
                current_line += char
                current_width += char_w
                
        if current_line:
            lines.append(current_line)
            
        return lines

    def calculate_text_height(self, text: str, width: float, font_size: float, line_height: float) -> float:
        """
        計算文字在指定寬度、字號與行高下的預期總高度。
        """
        lines = self.wrap_text_cjk(text, width, font_size)
        return len(lines) * font_size * line_height

    def fit_text(
        self,
        page_num: int,
        block_id: int,
        translated_text: str,
        original_bbox: tuple[float, float, float, float],
        original_font_size: float,
        obstacles: list[tuple[float, float, float, float]],
        page_width: float,
        page_height: float,
        column_bounds: tuple[float, float] = None,
        exclude_bboxes: list[tuple[float, float, float, float]] = None
    ) -> tuple[tuple[float, float, float, float], float, float, str, bool]:
        """
        執行五階段排版管線。
        :return: (final_bbox, font_size, line_height, final_text, is_overflow)
        """
        ox0, oy0, ox1, oy1 = original_bbox
        orig_w = ox1 - ox0
        orig_h = oy1 - oy0
        
        # 建立輔助檢測物件
        collision_detector = CollisionDetector()
        bbox_expander = BBoxExpander(page_width, page_height)
        
        # ---------------------------------------------------------------------
        # 階段 1：原始 bbox + 原始字號 + 1.25x 行高
        # ---------------------------------------------------------------------
        h_stage1 = self.calculate_text_height(translated_text, orig_w, original_font_size, self.default_line_height)
        if h_stage1 <= orig_h:
            decision = {
                "page_num": page_num, "block_id": block_id, "original_bbox": original_bbox,
                "final_bbox": original_bbox, "original_font_size": original_font_size,
                "final_font_size": original_font_size, "final_line_height": self.default_line_height,
                "strategy": "Stage 1: Original Fit", "overflow": False
            }
            self.decision_logs.append(decision)
            return original_bbox, original_font_size, self.default_line_height, translated_text, False

        # ---------------------------------------------------------------------
        # 階段 2：原始 bbox + 原始字號 + 壓縮行高 (Step-down down to min_line_height)
        # ---------------------------------------------------------------------
        line_heights = [1.20, 1.15, 1.10, self.min_line_height]
        for lh in line_heights:
            h_stage2 = self.calculate_text_height(translated_text, orig_w, original_font_size, lh)
            if h_stage2 <= orig_h:
                decision = {
                    "page_num": page_num, "block_id": block_id, "original_bbox": original_bbox,
                    "final_bbox": original_bbox, "original_font_size": original_font_size,
                    "final_font_size": original_font_size, "final_line_height": lh,
                    "strategy": f"Stage 2: Line-height Compression ({lh}x)", "overflow": False
                }
                self.decision_logs.append(decision)
                return original_bbox, original_font_size, lh, translated_text, False

        # ---------------------------------------------------------------------
        # 階段 3：安全擴張 bbox + 原始字號 + 壓縮行高
        # ---------------------------------------------------------------------
        # 使用 BBoxExpander 計算最大安全擴張量
        expanded_bbox = bbox_expander.get_max_safe_expansion(
            original_bbox, obstacles, column_bounds, exclude_bboxes
        )
        ex0, ey0, ex1, ey1 = expanded_bbox
        exp_w = ex1 - ex0
        exp_h = ey1 - ey0
        
        # 嘗試以原始字號和壓縮行高放入擴張後的空間
        h_stage3 = self.calculate_text_height(translated_text, exp_w, original_font_size, self.min_line_height)
        if h_stage3 <= exp_h:
            decision = {
                "page_num": page_num, "block_id": block_id, "original_bbox": original_bbox,
                "final_bbox": expanded_bbox, "original_font_size": original_font_size,
                "final_font_size": original_font_size, "final_line_height": self.min_line_height,
                "strategy": "Stage 3: Dynamic BBox Expansion", "overflow": False
            }
            self.decision_logs.append(decision)
            return expanded_bbox, original_font_size, self.min_line_height, translated_text, False

        # ---------------------------------------------------------------------
        # 階段 4：安全擴張 bbox + 降低字號 + 壓縮行高
        # ---------------------------------------------------------------------
        # 逐級縮小字號 (從原本字號，以 0.5pt 為單位往下遞減，最低至 min_font_size)
        curr_fs = original_font_size - 0.5
        while curr_fs >= self.min_font_size:
            h_stage4 = self.calculate_text_height(translated_text, exp_w, curr_fs, self.min_line_height)
            if h_stage4 <= exp_h:
                decision = {
                    "page_num": page_num, "block_id": block_id, "original_bbox": original_bbox,
                    "final_bbox": expanded_bbox, "original_font_size": original_font_size,
                    "final_font_size": curr_fs, "final_line_height": self.min_line_height,
                    "strategy": f"Stage 4: Font Shrinking ({curr_fs}pt)", "overflow": False
                }
                self.decision_logs.append(decision)
                return expanded_bbox, curr_fs, self.min_line_height, translated_text, False
            curr_fs -= 0.5

        # ---------------------------------------------------------------------
        # 階段 5：溢位降級處理 (Overflow Fallback)
        # ---------------------------------------------------------------------
        # 既然完全塞不下，我們使用 Stage 4 的極限尺寸 (expanded_bbox + min_font_size + min_line_height)
        # 計算此極限尺寸下能容納多少個中文字，將超出的文字截斷，並在尾端加入紅色 [+...]
        limit_fs = self.min_font_size
        limit_lh = self.min_line_height
        
        # 找出能塞入的最大字數
        # 使用簡單的二分搜尋法或字元遞增法，找出不超高的最大截斷點
        fit_len = 0
        low = 0
        high = len(translated_text)
        
        while low <= high:
            mid = (low + high) // 2
            test_text = translated_text[:mid] + " [+...]"
            h_test = self.calculate_text_height(test_text, exp_w, limit_fs, limit_lh)
            if h_test <= exp_h:
                fit_len = mid
                low = mid + 1
            else:
                high = mid - 1
                
        # 擷取主文能放下的部分，並附上 [+...]
        visible_text = translated_text[:fit_len] + " [+...]"
        
        decision = {
            "page_num": page_num, "block_id": block_id, "original_bbox": original_bbox,
            "final_bbox": expanded_bbox, "original_font_size": original_font_size,
            "final_font_size": limit_fs, "final_line_height": limit_lh,
            "strategy": "Stage 5: Overflow Fallback", "overflow": True
        }
        self.decision_logs.append(decision)
        
        return expanded_bbox, limit_fs, limit_lh, visible_text, True
