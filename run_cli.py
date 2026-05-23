import os
import sys
import time
import argparse
from utils.logger import setup_logger, get_logger
from utils.config_loader import load_config
from core.pdf_processor import PDFProcessor
from translators.google_translator import GoogleTranslator
from translators.dummy_translator import DummyTranslator

def main():
    parser = argparse.ArgumentParser(description="Layout-Preserving PDF Translator (CLI Mode)")
    
    # 必填位置參數
    parser.add_argument("input_pdf", type=str, help="輸入英文 PDF 檔案路徑")
    
    # 選項參數
    parser.add_argument("-o", "--output-dir", type=str, default=None, help="指定譯文輸出目錄 (預設與原文同資料夾)")
    parser.add_argument("-t", "--translator", type=str, default="google", choices=["google", "dummy"], help="翻譯服務提供者 (預設: google)")
    parser.add_argument("-d", "--debug", action="store_true", default=False, help="啟用除錯模式，同步輸出多色邊界框 PDF")
    parser.add_argument("-m", "--dummy-mode", type=str, default="normal", choices=["same", "short", "normal", "long", "stress"], help="僅當翻譯器設為 dummy 時有效：測試長度模式")
    
    args = parser.parse_args()

    # 1. 初始化日誌系統 (CLI 模式不傳入 GUI queue)
    logger = setup_logger(debug=args.debug)
    logger.info("=== 啟動 PDF 翻譯 CLI ===")
    
    # 檢查輸入檔案是否存在
    if not os.path.exists(args.input_pdf):
        logger.error(f"錯誤: 輸入檔案 '{args.input_pdf}' 不存在！")
        sys.exit(1)
        
    start_time = time.time()
    
    try:
        # 2. 載入組態設定
        config = load_config()
        
        # 3. 建立翻譯器實例
        if args.translator == "google":
            logger.info("使用 Google 翻譯服務 (免 API 密鑰)...")
            g_cfg = config.get("google", {})
            translator = GoogleTranslator(timeout=g_cfg.get("timeout", 10), user_agent=g_cfg.get("user_agent"))
        elif args.translator == "dummy":
            logger.info(f"使用 Dummy 測試翻譯器 (模式: {args.dummy_mode})...")
            translator = DummyTranslator(mode=args.dummy_mode)
        else:
            logger.error("不支援的翻譯服務提供者！")
            sys.exit(1)
            
        # 4. 初始化主管線處理器
        processor = PDFProcessor(translator=translator, config=config)
        
        # 5. 執行核心翻譯
        out_pdf, db_pdf = processor.process_pdf(
            input_pdf_path=args.input_pdf,
            output_dir=args.output_dir,
            debug_mode=args.debug
        )
        
        elapsed = time.time() - start_time
        logger.info("=== 翻譯任務成功結束 ===")
        logger.info(f"譯文 PDF 已儲存: {out_pdf}")
        if db_pdf:
            logger.info(f"除錯 PDF 已儲存: {db_pdf}")
        logger.info(f"總耗時: {elapsed:.2f} 秒")
        
    except KeyboardInterrupt:
        logger.warning("\n翻譯任務被使用者手動中止。")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"處理過程中發生嚴重錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
