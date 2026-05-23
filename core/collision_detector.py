class CollisionDetector:
    """
    碰撞偵測模組，負責在排版過程中檢查文字框是否與其他物件重疊，或超出安全邊界。
    """
    
    @staticmethod
    def intersects(rect_a: tuple[float, float, float, float], rect_b: tuple[float, float, float, float], tolerance: float = 0.5) -> bool:
        """
        檢查兩個矩形 (x0, y0, x1, y1) 是否相交。
        加上微小的 tolerance 容差，避免精確浮點數帶來的微小接觸誤判。
        """
        ax0, ay0, ax1, ay1 = rect_a
        bx0, by0, bx1, by1 = rect_b
        
        # 加上容差：讓矩形向內縮小一點點再比對
        return not (
            ax1 - tolerance <= bx0 + tolerance or
            bx1 - tolerance <= ax0 + tolerance or
            ay1 - tolerance <= by0 + tolerance or
            by1 - tolerance <= ay0 + tolerance
        )

    def is_colliding(self, target_bbox: tuple[float, float, float, float], obstacles: list[tuple[float, float, float, float]], exclude_bboxes: list[tuple[float, float, float, float]] = None) -> bool:
        """
        檢查目標 bbox 是否與障礙物清單中的任何一個發生碰撞。
        :param target_bbox: 欲檢測的 (x0, y0, x1, y1)
        :param obstacles: 障礙物列表，每個障礙物均為 (x0, y0, x1, y1)
        :param exclude_bboxes: 需排除不檢測的 bbox 列表 (通常是文字區塊自身或同段落群組的兄弟節點)
        """
        exclude_set = set(exclude_bboxes) if exclude_bboxes else set()
        
        for obs in obstacles:
            if obs in exclude_set:
                continue
            if self.intersects(target_bbox, obs):
                return True
        return False

    def is_within_bounds(self, bbox: tuple[float, float, float, float], page_width: float, page_height: float, column_bounds: tuple[float, float] = None, margin: float = 15.0) -> bool:
        """
        檢查文字框是否超出頁面邊界或跨欄限制。
        :param bbox: 待測文字框 (x0, y0, x1, y1)
        :param page_width: 頁面總寬
        :param page_height: 頁面總高
        :param column_bounds: 當前欄位的左右水平限制 (col_left, col_right)，若有則嚴格限制不能越界
        :param margin: 頁面四周安全留白 (單位: pt)
        """
        x0, y0, x1, y1 = bbox
        
        # 頁面基本邊界檢查
        if x0 < margin or y0 < margin or x1 > page_width - margin or y1 > page_height - margin:
            return False
            
        # 欄位界線限制檢查 (防止雙欄排版文字跨越到另一欄)
        if column_bounds:
            col_left, col_right = column_bounds
            # 容許 2pt 的微小超出，以利美觀，但主要必須被限制在欄內
            if x0 < col_left - 2.0 or x1 > col_right + 2.0:
                return False
                
        return True
