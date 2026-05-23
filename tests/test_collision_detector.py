import pytest
from core.collision_detector import CollisionDetector

def test_intersects():
    detector = CollisionDetector()
    # 兩個有重疊的矩形
    rect_a = (10.0, 10.0, 50.0, 50.0)
    rect_b = (40.0, 40.0, 80.0, 80.0)
    assert detector.intersects(rect_a, rect_b)

    # 兩個不重疊的矩形
    rect_c = (10.0, 10.0, 30.0, 30.0)
    rect_d = (40.0, 40.0, 80.0, 80.0)
    assert not detector.intersects(rect_c, rect_d)

    # 精確浮點數的微小接觸判定 (考慮 tolerance)
    rect_e = (10.0, 10.0, 40.0, 40.0)
    rect_f = (40.0, 40.0, 80.0, 80.0)
    # tolerance 為 0.5，會讓邊界向內縮小 0.5 再比對，因此 40.0 接觸點應該不相交
    assert not detector.intersects(rect_e, rect_f, tolerance=0.5)

def test_is_colliding():
    detector = CollisionDetector()
    target = (10.0, 10.0, 50.0, 50.0)
    obstacles = [
        (45.0, 45.0, 90.0, 90.0), # 有碰撞
        (100.0, 100.0, 150.0, 150.0) # 無碰撞
    ]
    # 當沒有排除 list 時，應該發生碰撞
    assert detector.is_colliding(target, obstacles)

    # 排除有碰撞的障礙物後，應該不發生碰撞
    assert not detector.is_colliding(target, obstacles, exclude_bboxes=[(45.0, 45.0, 90.0, 90.0)])

def test_is_within_bounds():
    detector = CollisionDetector()
    # 頁面尺寸 600 x 800， margin = 15.0
    bbox = (20.0, 20.0, 100.0, 100.0)
    assert detector.is_within_bounds(bbox, 600.0, 800.0)

    # 超出頁面右邊界
    bbox_out = (20.0, 20.0, 590.0, 100.0)
    assert not detector.is_within_bounds(bbox_out, 600.0, 800.0)

    # 跨欄限制測試：
    # col_bounds 為 (15.0, 280.0)
    bbox_col = (20.0, 20.0, 250.0, 100.0)
    assert detector.is_within_bounds(bbox_col, 600.0, 800.0, column_bounds=(15.0, 280.0))

    # 超出欄寬
    bbox_col_out = (20.0, 20.0, 290.0, 100.0)
    assert not detector.is_within_bounds(bbox_col_out, 600.0, 800.0, column_bounds=(15.0, 280.0))
