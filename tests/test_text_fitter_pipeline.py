import pytest
from core.text_fitter import TextFitter

def test_text_fitter_pipeline():
    layout_cfg = {
        "min_font_size": 8.0,
        "min_line_height": 1.05,
        "default_line_height": 1.25
    }
    fitter = TextFitter(layout_cfg)
    
    # 原始文字框
    original_bbox = (100.0, 100.0, 200.0, 150.0) # width=100, height=50
    
    # 1. 測試 Stage 1 (原字號，預設行高能塞下)
    # 中文字元為 10pt，平均寬 10，10字約為 100，剛好一行，預計高度 = 10 * 1.25 = 12.5 < 50
    text_stage1 = "\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341"
    bbox, fs, lh, rendered, is_overflow = fitter.fit_text(
        page_num=1,
        block_id=1,
        translated_text=text_stage1,
        original_bbox=original_bbox,
        original_font_size=10.0,
        obstacles=[],
        page_width=600.0,
        page_height=800.0
    )
    assert not is_overflow
    assert fs == 10.0
    assert lh == 1.25
    assert rendered == text_stage1
    
    # 2. 測試 Stage 5 (極端過長，觸發溢位降級)
    # 500 個中文字，無論如何擴張與壓縮，都不可能在 100x50 或者擴張後的寬高下塞下
    # 預期會回報 is_overflow = True，且 rendered 尾端有 "[+...]"
    text_stage5 = "\u9019\u662f\u975e\u5e38\u9577\u7684\u4e00\u6bb5\u6e2c\u8a66\u6587\u5b57\uff0c" * 1000
    bbox_5, fs_5, lh_5, rendered_5, is_overflow_5 = fitter.fit_text(
        page_num=1,
        block_id=2,
        translated_text=text_stage5,
        original_bbox=original_bbox,
        original_font_size=10.0,
        obstacles=[],
        page_width=600.0,
        page_height=800.0
    )
    assert is_overflow_5
    assert rendered_5.endswith("[+...]")
