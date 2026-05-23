from utils.logger import get_logger

class BBoxExpander:
    """
    區塊擴張器，依據幾何投影計算原 bbox 周圍的安全邊界，
    可在不進行逐像素掃描的情況下，精確計算出最大的不碰撞擴張範圍。
    """
    def __init__(self, page_width: float, page_height: float, margin: float = 15.0):
        self.logger = get_logger()
        self.page_width = page_width
        self.page_height = page_height
        self.margin = margin

    def get_max_safe_expansion(
        self,
        bbox: tuple[float, float, float, float],
        obstacles: list[tuple[float, float, float, float]],
        column_bounds: tuple[float, float] = None,
        exclude_bboxes: list[tuple[float, float, float, float]] = None
    ) -> tuple[float, float, float, float]:
        """
        核心擴張邏輯：依據優先級（下 -> 右 -> 左 -> 上）動態調整文字框邊界。
        在不與任何 hard/soft 障礙物碰撞的前提下，計算出安全擴充後的 bbox。
        :param bbox: 原始文字框 (x0, y0, x1, y1)
        :param obstacles: 障礙物清單
        :param column_bounds: 欄位左右界 (col_left, col_right)
        :param exclude_bboxes: 需排除的障礙物 (例如自身 block)
        """
        x0, y0, x1, y1 = bbox
        exclude_set = set(exclude_bboxes) if exclude_bboxes else set()
        
        # 過濾出非排除對象的有效障礙物
        active_obs = [obs for obs in obstacles if obs not in exclude_set]
        
        # 決定水平界線限制 (欄界或頁面邊界)
        limit_left = column_bounds[0] if column_bounds else self.margin
        limit_right = column_bounds[1] if column_bounds else (self.page_width - self.margin)
        limit_top = self.margin
        limit_bottom = self.page_height - self.margin

        # =========================================================================
        # 1. 向下擴張 (優先度最高，用以應付中文行數增加)
        # =========================================================================
        max_down = limit_bottom - y1
        for obs_x0, obs_y0, obs_x1, obs_y1 in active_obs:
            # 投影重合檢查：障礙物與當前水平範圍 (x0, x1) 有交集，且障礙物在當前 bbox 下方
            if max(obs_x0, x0) < min(obs_x1, x1) and obs_y0 >= y1:
                dist = obs_y0 - y1 - 2.0  # 扣掉 2pt 安全距離
                if dist < max_down:
                    max_down = max(0.0, dist)
        
        # 實施向下擴張
        y1_new = y1 + max_down

        # =========================================================================
        # 2. 向右微調擴張 (優先度第二，在同欄內向右擴充寬度)
        # =========================================================================
        max_right = limit_right - x1
        for obs_x0, obs_y0, obs_x1, obs_y1 in active_obs:
            # 投影重合檢查：障礙物與當前垂直範圍 (y0, y1_new) 有交集，且在當前 bbox 右方
            if max(obs_y0, y0) < min(obs_y1, y1_new) and obs_x0 >= x1:
                dist = obs_x0 - x1 - 2.0
                if dist < max_right:
                    max_right = max(0.0, dist)
        
        # 實施向右微調，最多向右擴展欄位剩餘寬度或障礙物距離
        x1_new = x1 + max_right

        # =========================================================================
        # 3. 向左微調擴張 (優先度第三)
        # =========================================================================
        max_left = x0 - limit_left
        for obs_x0, obs_y0, obs_x1, obs_y1 in active_obs:
            # 投影重合檢查：與當前垂直範圍有交集，且在左方
            if max(obs_y0, y0) < min(obs_y1, y1_new) and obs_x1 <= x0:
                dist = x0 - obs_x1 - 2.0
                if dist < max_left:
                    max_left = max(0.0, dist)
                    
        x0_new = x0 - max_left

        # =========================================================================
        # 4. 向上少量擴張 (優先度最低，當下面都卡死時，向上爭取少量空間)
        # =========================================================================
        max_up = y0 - limit_top
        # 限制向上擴張最多為 20pt (避免侵入頁眉或造成版面過度扭曲)
        max_up = min(max_up, 20.0)
        
        for obs_x0, obs_y0, obs_x1, obs_y1 in active_obs:
            # 投影重合檢查：與當前水平範圍 (x0_new, x1_new) 有交集，且在上方
            if max(obs_x0, x0_new) < min(obs_x1, x1_new) and obs_y1 <= y0:
                dist = y0 - obs_y1 - 2.0
                if dist < max_up:
                    max_up = max(0.0, dist)
                    
        y0_new = y0 - max_up

        expanded_bbox = (x0_new, y0_new, x1_new, y1_new)
        return expanded_bbox
