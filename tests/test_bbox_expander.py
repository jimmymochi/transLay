import pytest
from core.bbox_expander import BBoxExpander

def test_get_max_safe_expansion():
    # 頁面寬高為 600 x 800，安全 margin 為 15.0
    expander = BBoxExpander(page_width=600.0, page_height=800.0, margin=15.0)
    
    # 原始 bbox 在 (100.0, 100.0, 200.0, 150.0)
    original_bbox = (100.0, 100.0, 200.0, 150.0)
    
    # 1. 測試在沒有任何障礙物、也沒有欄位限制的情況下，四個方向的最大擴張量
    # 擴張順序優先權為：下 -> 右 -> 左 -> 上
    # 下方無障礙物：可擴張到底 limit_bottom = 800 - 15 = 785
    # 右方無障礙物：可擴張到右 limit_right = 600 - 15 = 585
    # 左方無障礙物：可擴張到左 limit_left = 15
    # 上方無障礙物：最多向上擴張 20pt (BBoxExpander 內部硬限制 max_up = min(max_up, 20.0))，所以上界是 100 - 20 = 80.0
    
    expanded = expander.get_max_safe_expansion(original_bbox, obstacles=[])
    
    # 預期 expanded_bbox：
    # x0_new = 15.0 (左擴張)
    # y0_new = 80.0 (上擴張限制 20)
    # x1_new = 585.0 (右擴張)
    # y1_new = 785.0 (下擴張)
    assert expanded == (15.0, 80.0, 585.0, 785.0)
    
    # 2. 測試有下方硬障礙物時的向下擴張限制
    # 障礙物在下方 y=200 處 (x從 50 到 250，與當前水平 100~200 有投影重疊)
    # 扣除 2pt 安全距離，預期 y1_new 最多擴張到 200.0 - 2.0 = 198.0
    obstacle_down = (50.0, 200.0, 250.0, 300.0)
    expanded_down = expander.get_max_safe_expansion(
        original_bbox, 
        obstacles=[obstacle_down],
        exclude_bboxes=[original_bbox]
    )
    # 檢查 y1_new
    assert expanded_down[3] == 198.0
    
    # 3. 測試欄位邊界限制
    # column_bounds 為 (15.0, 250.0)
    # 預期右側最多擴張到 250.0
    expanded_col = expander.get_max_safe_expansion(
        original_bbox,
        obstacles=[],
        column_bounds=(15.0, 250.0)
    )
    assert expanded_col[2] == 250.0
