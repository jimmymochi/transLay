import fitz
from utils.logger import get_logger

class ParagraphGrouper:
    """
    段落群組器，負責將 PyMuPDF 擷取到的零散文字行/區塊進行物理與邏輯上的整合。
    - 能正確識別單欄/雙欄排版，防止左右欄文字被錯誤合併。
    - 依據閱讀順序（先左欄、後右欄）進行重排。
    - 將相近且語意連續的文字行合併為完整的段落進行翻譯，保障翻譯品質。
    """
    def __init__(self, gutter_width_threshold: float = 15.0):
        self.logger = get_logger()
        self.gutter_width_threshold = gutter_width_threshold

    def analyze_layout_and_group(self, page: fitz.Page, blocks: list[dict]) -> tuple[list[dict], list[float]]:
        """
        分析頁面排版並進行段落重組。
        :param page: PyMuPDF Page 物件
        :param blocks: 由 text_extractor 提取的 dict 格式 block 列表
        :return: (grouped_blocks, column_dividers)
        """
        rect = page.rect
        page_width = rect.width
        
        # 1. 預設欄位劃分 (雙欄論文的核心)
        # 尋找雙欄分界線：通常在頁面中心左右 (例如 A4/Letter 寬約 595~612pt，中心在 297~306pt 左右)
        center_x = page_width / 2.0
        
        # 偵測文字塊的分佈，判定是否為雙欄
        left_count = 0
        right_count = 0
        span_count = 0
        
        for b in blocks:
            x0, _, x1, _ = b["bbox"]
            if x1 <= center_x:
                left_count += 1
            elif x0 >= center_x:
                right_count += 1
            else:
                span_count += 1
                
        # 判斷標準：如果左右兩側均有一定數量的文字區塊，且橫跨中心的區塊相對較少，則視為雙欄
        is_two_column = (left_count > 1 or right_count > 1) and (left_count + right_count > span_count)
        
        column_dividers = [center_x] if is_two_column else []
        
        # 2. 文字塊分類與排序
        left_col = []
        right_col = []
        spanning_blocks = [] # 跨欄區塊 (如標題、全寬圖表說明)
        
        for b in blocks:
            x0, y0, x1, y1 = b["bbox"]
            # 清理文字內容中的多餘換行
            b["text"] = " ".join([line["text"] for line in b.get("lines", [])]).strip()
            
            if is_two_column:
                # 判定屬於左欄、右欄或跨欄
                if x1 <= center_x + 5.0:
                    left_col.append(b)
                elif x0 >= center_x - 5.0:
                    right_col.append(b)
                else:
                    spanning_blocks.append(b)
            else:
                spanning_blocks.append(b)
                
        # 排序：左欄由上至下，右欄由上至下，跨欄由上至下
        left_col.sort(key=lambda x: x["bbox"][1])
        right_col.sort(key=lambda x: x["bbox"][1])
        spanning_blocks.sort(key=lambda x: x["bbox"][1])
        
        # 3. 雙欄順序排版重組 (先左欄，後右欄，跨欄依據 y 座標穿插)
        ordered_blocks = []
        if is_two_column:
            self.logger.info("檢測為雙欄 (Two-Column) 排版，啟動雙欄閱讀順序最佳化。")
            # 依據 y 座標，交錯合併跨欄與分欄區塊
            # 建立一個簡單的合併序列：將所有區塊混合，但保留左右欄的優先順序
            # 這裡我們採取：小於跨欄區塊 Y 的左/右欄區塊先排，再排跨欄，以此類推
            all_blocks = []
            
            # 分欄區塊
            cols = left_col + right_col
            # 分欄區塊按欄位排序：左欄全部在前，右欄全部在後
            # 或者，更精確的閱讀順序是：先把左欄 y0 範圍內的所有塊處理完，再處理右欄
            # 跨欄區塊通常是 Title 或是底部 Footnote。
            # 如果 Title y 坐標很小，它應該最先被放入
            
            # 簡單可靠的穿插演算法：
            # 先將 spanning blocks 依 y 排序。
            # 每一個 spanning block 作為一個水平分界線。
            # 分界線以上的左欄塊 -> 分界線以上的右欄塊 -> 分界線 block -> 下一循環。
            last_y = 0.0
            for span in spanning_blocks:
                span_y = span["bbox"][1]
                # 抽出所有在 last_y 到 span_y 之間的左欄塊
                current_left = [b for b in left_col if last_y <= b["bbox"][1] < span_y]
                current_right = [b for b in right_col if last_y <= b["bbox"][1] < span_y]
                
                ordered_blocks.extend(current_left)
                ordered_blocks.extend(current_right)
                ordered_blocks.append(span)
                
                # 從原始列表中移除
                for b in current_left: left_col.remove(b)
                for b in current_right: right_col.remove(b)
                last_y = span["bbox"][3] # span block 的底部
                
            # 剩餘的左右欄放入
            ordered_blocks.extend(left_col)
            ordered_blocks.extend(right_col)
        else:
            self.logger.info("檢測為單欄 (Single-Column) 排版。")
            ordered_blocks = spanning_blocks
            
        # 4. 相鄰段落合併 (Paragraph Merging)
        # 合併條件：在同一欄內、垂直距離極近 (例如 < 8pt)、字型大小相近、且前段句尾不完整
        grouped_blocks = []
        if not ordered_blocks:
            return [], column_dividers
            
        current_group = ordered_blocks[0]
        
        for next_block in ordered_blocks[1:]:
            cg_x0, cg_y0, cg_x1, cg_y1 = current_group["bbox"]
            nb_x0, nb_y0, nb_x1, nb_y1 = next_block["bbox"]
            
            # 檢查是否在同一側/同一欄
            same_column = True
            if is_two_column:
                # 若一個在左側，一個在右側，則不能合併
                if (cg_x1 <= center_x and nb_x0 >= center_x) or (cg_x0 >= center_x and nb_x1 <= center_x):
                    same_column = False
            
            # 距離與換行符比對
            y_distance = nb_y0 - cg_y1
            
            # 若距離小於 8pt，且在同一欄，且前一區塊最後不是句尾標點 (如 . ? !)
            # 或是前一區塊字串未以句號結尾，則進行合併
            text_ends_sentence = current_group["text"].strip().endswith((".", "?", "!", ":"))
            
            if same_column and y_distance < 8.0 and not text_ends_sentence:
                # 合併 bbox
                new_bbox = (
                    min(cg_x0, nb_x0),
                    min(cg_y0, nb_y0),
                    max(cg_x1, nb_x1),
                    max(cg_y1, nb_y1)
                )
                current_group["bbox"] = new_bbox
                current_group["text"] = current_group["text"] + " " + next_block["text"]
                # 合併 lines 用於繪製或重新排版
                current_group["lines"] = current_group.get("lines", []) + next_block.get("lines", [])
            else:
                grouped_blocks.append(current_group)
                current_group = next_block
                
        grouped_blocks.append(current_group)
        
        # 為每個 group 賦予唯一的 block_id
        for idx, g in enumerate(grouped_blocks):
            g["block_id"] = idx
            
        return grouped_blocks, column_dividers
