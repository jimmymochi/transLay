import fitz
from utils.logger import get_logger

class TextExtractor:
    """
    文字擷取器，負責調用 PyMuPDF 的底層 API，將 PDF 頁面中的文字轉換為
    高精度的結構化資料 (含座標、字體、大小、顏色等詮釋資料)。
    """
    def __init__(self):
        self.logger = get_logger()

    def extract_page_text_blocks(self, page: fitz.Page) -> list[dict]:
        """
        擷取頁面上所有的純文字區塊，並結構化為包含線段與字型屬性的字典列表。
        """
        raw_blocks = []
        
        # 呼叫 page.get_text("dict") 獲取最詳盡的二維版面屬性
        page_dict = page.get_text("dict")
        
        blocks = page_dict.get("blocks", [])
        
        for b in blocks:
            # type = 0 為文字，type = 1 為影像
            if b.get("type") != 0:
                continue
                
            lines = b.get("lines", [])
            if not lines:
                continue
                
            block_bbox = b.get("bbox")
            
            # 解析 block 內所有 spans，提取主力字型與字號
            extracted_lines = []
            all_spans_text = []
            
            # 用於估計整個 Block 的主要字體特徵
            font_sizes = []
            font_names = []
            font_colors = []
            
            for line in lines:
                line_spans = line.get("spans", [])
                line_text = ""
                
                for span in line_spans:
                    span_text = span.get("text", "")
                    if span_text.strip():
                        line_text += span_text
                        font_sizes.append(span.get("size", 10.0))
                        font_names.append(span.get("font", "sans-serif"))
                        font_colors.append(span.get("color", 0x1a1a1a))
                        
                if line_text.strip():
                    extracted_lines.append({
                        "bbox": line.get("bbox"),
                        "text": line_text
                    })
                    all_spans_text.append(line_text)
                    
            if not extracted_lines:
                continue
                
            # 計算此 Block 的主導字號 (取眾數或平均值)
            main_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 10.0
            main_font = max(set(font_names), key=font_names.count) if font_names else "Helvetica"
            main_color = max(set(font_colors), key=font_colors.count) if font_colors else 0x1a1a1a
            
            raw_blocks.append({
                "bbox": block_bbox,
                "lines": extracted_lines,
                "text": " ".join(all_spans_text),
                "font_size": main_size,
                "font_name": main_font,
                "font_color": main_color
            })
            
        return raw_blocks
