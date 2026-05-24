import os
import fitz  # PyMuPDF
from utils.logger import get_logger
from utils.file_utils import get_safe_output_path
from core.font_manager import FontManager
from core.text_extractor import TextExtractor
from core.text_filter import TextFilter
from core.paragraph_grouper import ParagraphGrouper
from core.obstacle_detector import ObstacleDetector
from core.text_fitter import TextFitter
from core.overflow_manager import OverflowManager
from utils.cc_converter import CCConverter

class PDFProcessor:
    """
    PDF 翻譯核心處理器。
    串聯所有核心模組，負責開啟 PDF、逐頁進行版面分析、過濾公式與頁碼、
    呼叫翻譯器、進行碰撞偵測與安全擴張擬合，並寫回 PDF（包含除錯疊加層與溢位附錄頁）。
    """
    def __init__(self, translator, config=None, progress_callback=None):
        """
        :param translator: BaseTranslator 的實作實例 (如 GoogleTranslator)
        :param config: 專案組態 dict
        :param progress_callback: 用於 GUI 進度更新的回呼函數，格式為 cb(current_page, total_pages, logs, overflow_count)
        """
        self.logger = get_logger()
        self.translator = translator
        self.config = config or {}
        self.progress_callback = progress_callback
        
        # 初始化核心引擎元件
        self.font_manager = FontManager(self.config.get("fonts"))
        self.text_extractor = TextExtractor()
        self.text_filter = TextFilter()
        self.paragraph_grouper = ParagraphGrouper()
        self.obstacle_detector = ObstacleDetector()
        
        layout_cfg = self.config.get("layout", {})
        self.text_fitter = TextFitter(layout_cfg)
        self.overflow_manager = OverflowManager()
        self.cc_converter = CCConverter()

    def process_pdf(self, input_pdf_path: str, output_dir: str = None, debug_mode: bool = False) -> tuple[str, str | None]:
        """
        執行完整的 PDF 解析與翻譯流程。
        :param input_pdf_path: 來源 PDF 檔案路徑
        :param output_dir: 輸出資料夾路徑，若為 None 則與來源檔案同目錄
        :param debug_mode: 是否同時輸出多色除錯框線的 PDF 檔案
        :return: (譯文PDF路徑, 除錯PDF路徑)
        """
        self.logger.info(f"開始處理文件: {input_pdf_path}")
        self.overflow_manager.clear()
        self.text_fitter.clear_logs()
        
        # 決定輸出路徑
        output_pdf_path = get_safe_output_path(input_pdf_path, output_dir, suffix=".zh-TW")
        debug_pdf_path = get_safe_output_path(input_pdf_path, output_dir, suffix=".zh-TW.debug") if debug_mode else None
        
        # 開啟文件
        doc = fitz.open(input_pdf_path)
        total_pages = len(doc)
        
        # 若為除錯模式，同步建立一個複製的文件，專門用來繪製除錯輔助框
        debug_doc = fitz.open(input_pdf_path) if debug_mode else None
        
        # 載入系統繁中字型
        font_name, font_file = self.font_manager.get_font_info()
        self.logger.info(f"使用字型: {font_name} (來源: {font_file or 'PyMuPDF內建'})")
        
        for page_idx in range(total_pages):
            page_num = page_idx + 1
            self.logger.info(f"--- 正在解析第 {page_num} / {total_pages} 頁 ---")
            
            page = doc[page_idx]
            page_w, page_h = page.rect.width, page.rect.height
            
            # 1. 偵測頁面中的硬障礙物 (圖、表、公式、頁首頁尾安全區)
            obstacles_data = self.obstacle_detector.detect_obstacles(page)
            hard_obstacles = obstacles_data["hard"]
            
            # 2. 擷取頁面文字
            raw_blocks = self.text_extractor.extract_page_text_blocks(page)
            
            # 3. 段落群組分析 (含雙欄偵測、閱讀順序排序、行距相近塊合併)
            grouped_blocks, column_dividers = self.paragraph_grouper.analyze_layout_and_group(page, raw_blocks)
            
            # 建立 soft obstacles 列表 (除當前處理塊外，所有其他 text blocks 都是 soft obstacles)
            all_text_bboxes = [g["bbox"] for g in grouped_blocks]
            
            # 用於暫存待寫入的譯文資料，避免逐一 apply_redactions 導致 PDF 檔案增量結構膨脹
            pending_inserts = []
            
            # 4. 逐一處理每個文字區塊
            for block in grouped_blocks:
                block_id = block["block_id"]
                original_text = block["text"]
                bbox = block["bbox"]
                orig_fs = block["font_size"]
                
                # 判斷是否需要翻譯
                if not self.text_filter.should_translate(original_text, bbox, page_h):
                    self.logger.debug(f"頁 {page_num} 塊 {block_id}: 過濾公式/頁碼/數字，跳過翻譯。")
                    continue
                
                # 執行翻譯
                self.logger.info(f"頁 {page_num} 塊 {block_id}: 翻譯中 (字數: {len(original_text)})...")
                raw_translation = self.translator.translate(original_text)
                translated_text = self.cc_converter.convert(raw_translation)
                
                # 判定翻譯是否有效。若為空、僅有空白、與原文相同，或者包含翻譯失敗的錯誤標記，則保留原文不予擦除
                is_failed = False
                for err_marker in ["[翻譯失敗]", "[Gemini 翻譯失敗]", "[OpenAI 翻譯失敗]", "[DeepL 翻譯失敗]"]:
                    if err_marker in translated_text:
                        is_failed = True
                        break
                
                if not translated_text or not translated_text.strip() or translated_text.strip() == original_text.strip() or is_failed:
                    self.logger.warning(f"頁 {page_num} 塊 {block_id}: 翻譯無效或失敗，保留原始英文文字，避免空白。")
                    continue
                
                # 決定當前區塊的欄位限制
                col_bounds = None
                if column_dividers:
                    center_x = column_dividers[0]
                    if bbox[2] <= center_x + 5.0:
                        col_bounds = (15.0, center_x - 5.0)
                    elif bbox[0] >= center_x - 5.0:
                        col_bounds = (center_x + 5.0, page_w - 15.0)
                
                # 障礙物列表：合集 = 硬障礙物 + 其他 soft text blocks
                # 在 fitter 裡會把當前 block 本身排除
                combined_obstacles = hard_obstacles + all_text_bboxes
                
                # 5. 進行 Layout-Aware 空間擬合計算
                final_bbox, final_fs, final_lh, rendered_text, is_overflow = self.text_fitter.fit_text(
                    page_num=page_num,
                    block_id=block_id,
                    translated_text=translated_text,
                    original_bbox=bbox,
                    original_font_size=orig_fs,
                    obstacles=combined_obstacles,
                    page_width=page_w,
                    page_height=page_h,
                    column_bounds=col_bounds,
                    exclude_bboxes=[bbox]
                )
                
                # 6. 處理溢位資料
                if is_overflow:
                    self.logger.warning(f"頁 {page_num} 塊 {block_id}: 觸發溢位備援，部分文字被截斷。")
                    self.overflow_manager.add_overflow(page_num, block_id, original_text, translated_text)
                
                # 暫存此區塊待寫入之資料
                pending_inserts.append({
                    "bbox": bbox,
                    "final_bbox": final_bbox,
                    "rendered_text": rendered_text,
                    "final_fs": final_fs,
                    "final_lh": final_lh,
                    "font_color": block.get("font_color", 0x1a1a1a),
                    "is_overflow": is_overflow,
                    "block_id": block_id
                })
                
                # 8. 除錯層圖案繪製
                if debug_mode and debug_doc:
                    db_page = debug_doc[page_idx]
                    # 畫出原始 bbox (藍色)
                    db_page.draw_rect(fitz.Rect(bbox), color=(0, 0, 1), width=0.8)
                    # 畫出最終/擴張後 bbox (綠色)
                    db_page.draw_rect(fitz.Rect(final_bbox), color=(0, 0.8, 0), width=0.8)
                    # 標註 block_id
                    db_page.insert_text(fitz.Point(bbox[0], bbox[1] - 2), f"ID:{block_id} ({orig_fs:.1f}pt)", fontsize=6.0, color=(0, 0, 1))

            # 7. 一次性執行頁面擦除 (Redaction) 與中文譯文寫入
            if pending_inserts:
                try:
                    for item in pending_inserts:
                        rect = fitz.Rect(item["bbox"])
                        page.add_redact_annot(rect, fill=False)
                    page.apply_redactions()
                except Exception as e:
                    self.logger.error(f"頁 {page_num} 一次性執行擦除 (Redactions) 失敗: {e}")

                # 寫入翻譯新文
                for item in pending_inserts:
                    try:
                        # 擷取原文字型顏色並轉換為 RGB (0.0~1.0)
                        orig_color = item["font_color"]
                        r = ((orig_color >> 16) & 255) / 255.0
                        g = ((orig_color >> 8) & 255) / 255.0
                        b = (orig_color & 255) / 255.0
                        text_color = (r, g, b)
                        
                        # 覆寫繁體中文新文，並使用原文字體顏色
                        page.insert_textbox(
                            fitz.Rect(item["final_bbox"]),
                            item["rendered_text"],
                            fontname=font_name,
                            fontfile=font_file,
                            fontsize=item["final_fs"],
                            lineheight=item["final_lh"],
                            color=text_color
                        )
                        
                        # 如果有溢位，在右下角繪製一朵小紅花或紅色 [+] 符號
                        if item["is_overflow"]:
                            page.insert_text(
                                fitz.Point(item["final_bbox"][2] - 12, item["final_bbox"][3] - 2),
                                "[+]",
                                fontsize=8.0,
                                color=(1.0, 0.0, 0.0)
                            )
                    except Exception as e:
                        self.logger.error(f"寫入 PDF 頁 {page_num} 塊 {item['block_id']} 時出錯: {e}")

            # 繪製公共障礙物 (硬障礙物) 至除錯頁
            if debug_mode and debug_doc:
                db_page = debug_doc[page_idx]
                # 畫出欄位分界線 (灰色)
                for div in column_dividers:
                    db_page.draw_line(fitz.Point(div, 0), fitz.Point(div, page_h), color=(0.5, 0.5, 0.5), width=0.5, dashes="[3 3] 0")
                # 畫出硬障礙物 (紅色)
                for obs in hard_obstacles:
                    # 排除頁眉頁腳本身，以便單獨標註
                    if obs == obstacles_data["header_zone"] or obs == obstacles_data["footer_zone"]:
                        db_page.draw_rect(fitz.Rect(obs), color=(0, 0, 0), width=0.5, fill=(0.95, 0.95, 0.95), overlay=False) # 黑色安全區
                    else:
                        db_page.draw_rect(fitz.Rect(obs), color=(1, 0, 0), width=0.8, dashes="[2 2] 0")
            
            # 回報進度給 GUI
            if self.progress_callback:
                self.progress_callback(
                    page_num,
                    total_pages,
                    f"完成第 {page_num} 頁翻譯，本頁文字塊數: {len(grouped_blocks)}",
                    len(self.overflow_manager.get_all_overflows())
                )

        # =========================================================================
        # 9. 翻譯溢位附錄頁面生成 (Overflow Appendix Generation)
        # =========================================================================
        if self.overflow_manager.has_overflows():
            self.logger.info("檢測到溢位段落，開始生成附錄頁面...")
            self._generate_appendix(doc, font_name, font_file)
            if debug_mode and debug_doc:
                self._generate_appendix(debug_doc, font_name, font_file)

        # 儲存檔案前進行字型子集化 (Subset Fonts) 以極致最佳化檔案體積
        try:
            doc.subset_fonts()
            self.logger.info("譯文 PDF 字型子集化 (subset_fonts) 完成。")
        except Exception as e:
            self.logger.warning(f"譯文 PDF 字型子集化失敗: {e}")

        doc.save(output_pdf_path)
        doc.close()
        self.logger.info(f"成功儲存譯文 PDF 至: {output_pdf_path}")
        
        if debug_mode and debug_doc:
            try:
                debug_doc.subset_fonts()
                self.logger.info("除錯 PDF 字型子集化 (subset_fonts) 完成。")
            except Exception as e:
                self.logger.warning(f"除錯 PDF 字型子集化失敗: {e}")
            debug_doc.save(debug_pdf_path)
            debug_doc.close()
            self.logger.info(f"成功儲存除錯 PDF 至: {debug_pdf_path}")

        return output_pdf_path, debug_pdf_path

    def _generate_appendix(self, doc: fitz.Document, font_name: str, font_file: str | None):
        """
        在文檔末尾動態加入精美的翻譯溢位附錄
        """
        page_w = doc[0].rect.width
        page_h = doc[0].rect.height
        
        # 建立新頁面
        page = doc.new_page(width=page_w, height=page_h)
        
        # 繪製邊界與頁首
        margin = 35.0
        y_cursor = 50.0
        
        # 繪製附錄大標題
        page.insert_text(
            fitz.Point(margin, y_cursor),
            "翻譯溢位附錄 (Translation Overflow Appendix)",
            fontsize=16.0,
            fontname=font_name,
            fontfile=font_file,
            color=(0.8, 0.1, 0.1) # 紅褐色標題
        )
        
        page.draw_line(
            fitz.Point(margin, y_cursor + 10),
            fitz.Point(page_w - margin, y_cursor + 10),
            color=(0.8, 0.1, 0.1),
            width=1.5
        )
        
        y_cursor += 35.0
        
        # 逐一繪製溢位區塊
        overflows = self.overflow_manager.get_all_overflows()
        
        for idx, item in enumerate(overflows):
            # 每條記錄預估高度 (原文 + 譯文)
            # 若接近底部，自動開闢新頁面
            if y_cursor > page_h - 90.0:
                page = doc.new_page(width=page_w, height=page_h)
                y_cursor = 50.0
                # 新頁面標題
                page.insert_text(
                    fitz.Point(margin, y_cursor),
                    "翻譯溢位附錄 (續頁)",
                    fontsize=12.0,
                    fontname=font_name,
                    fontfile=font_file,
                    color=(0.8, 0.1, 0.1)
                )
                page.draw_line(
                    fitz.Point(margin, y_cursor + 6),
                    fitz.Point(page_w - margin, y_cursor + 6),
                    color=(0.8, 0.1, 0.1),
                    width=0.8
                )
                y_cursor += 25.0

            header_text = f"◆ 項目 {idx+1} [原始第 {item['page_num']} 頁，Block ID: {item['block_id']}]"
            page.insert_text(
                fitz.Point(margin, y_cursor),
                header_text,
                fontsize=9.5,
                fontname=font_name,
                fontfile=font_file,
                color=(0.0, 0.4, 0.8) # 藍色項目頁頭
            )
            
            y_cursor += 15.0
            
            # 原文 (英文)
            orig_text_formatted = f"英文原文: {item['original_text']}"
            # 計算英文高度並繪製
            orig_h = self.text_fitter.calculate_text_height(orig_text_formatted, page_w - 2*margin, 8.0, 1.15)
            page.insert_textbox(
                fitz.Rect(margin, y_cursor, page_w - margin, y_cursor + orig_h + 5),
                orig_text_formatted,
                fontsize=8.0,
                color=(0.4, 0.4, 0.4) # 灰色原文
            )
            
            y_cursor += orig_h + 8.0
            
            # 譯文 (中文)
            trans_text_formatted = f"完整中文翻譯: {item['full_translation']}"
            trans_h = self.text_fitter.calculate_text_height(trans_text_formatted, page_w - 2*margin, 8.5, 1.2)
            page.insert_textbox(
                fitz.Rect(margin, y_cursor, page_w - margin, y_cursor + trans_h + 5),
                trans_text_formatted,
                fontname=font_name,
                fontfile=font_file,
                fontsize=8.5,
                lineheight=1.2,
                color=(0.1, 0.1, 0.1)
            )
            
            y_cursor += trans_h + 15.0
            # 畫一條極淡的水平分割線
            page.draw_line(
                fitz.Point(margin, y_cursor - 6),
                fitz.Point(page_w - margin, y_cursor - 6),
                color=(0.9, 0.9, 0.9),
                width=0.5
            )
