import fitz  # PyMuPDF
from utils.logger import get_logger

class ObstacleDetector:
    """
    障礙物偵測模組，負責掃描 PDF 頁面，識別出所有不可覆蓋的「硬障礙物」（如圖片、表格、向量線條、頁首頁尾等安全區）。
    同時收集其他段落作為「軟障礙物」。
    """
    def __init__(self, header_margin: float = 45.0, footer_margin: float = 45.0):
        self.logger = get_logger()
        self.header_margin = header_margin
        self.footer_margin = footer_margin

    def detect_obstacles(self, page: fitz.Page) -> dict[str, list[tuple[float, float, float, float]]]:
        """
        對指定頁面進行多維度掃描，分類擷取所有障礙物。
        :param page: PyMuPDF Page 物件
        :return: 包含 "hard" 與 "safe_zone" 鍵的字典，值為 bbox 元組列表
        """
        rect = page.rect
        page_width, page_height = rect.width, rect.height
        
        hard_obstacles = []
        
        # =========================================================================
        # 1. 頁首與頁尾安全區 (Headers & Footers Safe Zones)
        # =========================================================================
        # 將頁首和頁尾矩形區劃入硬障礙物，防止文字在擴張時侵入頁眉、頁碼
        header_safe_zone = (0.0, 0.0, page_width, self.header_margin)
        footer_safe_zone = (0.0, page_height - self.footer_margin, page_width, page_height)
        
        # =========================================================================
        # 2. 圖片邊界偵測 (Image Boundary Detection)
        # =========================================================================
        try:
            # page.get_image_info(xrefs=True) 回傳頁面上所有影像的詳細資訊 (含 bbox)
            images = page.get_image_info(xrefs=True)
            for img in images:
                bbox = img.get("bbox")
                if bbox:
                    # 確保是合理的 bbox
                    hard_obstacles.append(bbox)
        except Exception as e:
            self.logger.warning(f"擷取影像邊界時出錯: {e}")

        # =========================================================================
        # 3. 表格邊界偵測 (Table Boundary Detection)
        # =========================================================================
        try:
            # PyMuPDF 內建超強的表格分析引擎，可精確抓取表格框線
            tables = page.find_tables()
            if tables and tables.tables:
                for table in tables.tables:
                    if table.bbox:
                        hard_obstacles.append(table.bbox)
        except Exception as e:
            self.logger.warning(f"擷取表格邊界時出錯: {e}")

        # =========================================================================
        # 4. 向量圖形與繪圖偵測 (Vector Graphics Detection)
        # =========================================================================
        try:
            # 取得所有的繪圖路徑 (如直線、填充矩形、曲線等)
            drawings = page.get_drawings()
            for draw in drawings:
                draw_rect = draw.get("rect")
                if draw_rect:
                    # 過濾掉覆蓋整頁的背景色矩形 (例如大於頁面面積的 75%)
                    w = draw_rect.x1 - draw_rect.x0
                    h = draw_rect.y1 - draw_rect.y0
                    if (w * h) > (page_width * page_height * 0.75):
                        continue
                    
                    # 過濾掉極小或無效的線條 (例如寬高均小於 1pt)
                    if w < 1.0 and h < 1.0:
                        continue
                        
                    hard_obstacles.append((draw_rect.x0, draw_rect.y0, draw_rect.x1, draw_rect.y1))
        except Exception as e:
            self.logger.warning(f"擷取向量繪圖時出錯: {e}")

        # =========================================================================
        # 5. 合併與簡化障礙物 (將完全重疊或包含的矩形進行簡化，提升後續比對速度)
        # =========================================================================
        simplified_hard = []
        # 加入基本安全區
        simplified_hard.append(header_safe_zone)
        simplified_hard.append(footer_safe_zone)
        
        for obs in hard_obstacles:
            # 確保座標不超出頁面
            x0 = max(0.0, obs[0])
            y0 = max(0.0, obs[1])
            x1 = min(page_width, obs[2])
            y1 = min(page_height, obs[3])
            
            if x1 > x0 and y1 > y0:
                simplified_hard.append((x0, y0, x1, y1))

        return {
            "hard": simplified_hard,
            "header_zone": header_safe_zone,
            "footer_zone": footer_safe_zone
        }
