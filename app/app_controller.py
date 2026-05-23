import threading
import queue
from utils.logger import setup_logger
from core.pdf_processor import PDFProcessor
from translators.google_translator import GoogleTranslator
from translators.dummy_translator import DummyTranslator

class AppController:
    """
    應用程式控制中心，做為 Tkinter UI 與底層 PDFProcessor 之間溝通的橋樑。
    使用執行緒與 Queue 佇列設計，確保重度 PDF 翻譯與網路請求時 GUI 不會凍結或無回應。
    """
    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue
        self.thread = None
        self.is_running = False

    def start_translation(
        self,
        input_pdf: str,
        output_dir: str,
        translator_name: str,
        dummy_mode: str,
        debug_mode: bool,
        config: dict
    ):
        """
        在獨立的背景執行緒中啟動翻譯工作線
        """
        if self.is_running:
            return
            
        self.is_running = True
        
        # 建立背景工作執行緒，防止主 UI 執行緒卡死
        self.thread = threading.Thread(
            target=self._run_pipeline,
            args=(input_pdf, output_dir, translator_name, dummy_mode, debug_mode, config),
            daemon=True
        )
        self.thread.start()

    def _run_pipeline(self, input_pdf, output_dir, translator_name, dummy_mode, debug_mode, config):
        """
        背景工作線核心邏輯，在完成各階段任務時透過 Queue 回傳訊號給主 UI 執行緒
        """
        try:
            # 0. 優先發送即時純文字訊號，確保 GUI 介面第一時間獲取反饋
            self.ui_queue.put(">>> 正在初始化系統日誌核心...")
            
            # 1. 設置專屬 GUI 日誌通道，將 logger 的輸出同時灌入 ui_queue
            logger = setup_logger(debug=debug_mode, log_queue=self.ui_queue)
            self.ui_queue.put(">>> 系統日誌核心載入成功！正在初始化 PDF 翻譯引擎...")
            logger.info("背景執行緒啟動成功，初始化翻譯管線...")

            # 2. 實例化選擇的翻譯器
            if translator_name == "google":
                g_cfg = config.get("google", {})
                translator = GoogleTranslator(
                    timeout=g_cfg.get("timeout", 10),
                    user_agent=g_cfg.get("user_agent")
                )
            elif translator_name == "openai":
                o_cfg = config.get("openai", {})
                from translators.openai_translator import OpenAITranslator
                translator = OpenAITranslator(
                    api_key=o_cfg.get("api_key", ""),
                    model=o_cfg.get("model", "gpt-4o-mini"),
                    temperature=o_cfg.get("temperature", 0.3)
                )
            elif translator_name == "deepl":
                d_cfg = config.get("deepl", {})
                from translators.deepl_translator import DeepLTranslator
                translator = DeepLTranslator(
                    api_key=d_cfg.get("api_key", "")
                )
            elif translator_name == "dummy":
                translator = DummyTranslator(mode=dummy_mode)
            else:
                raise ValueError(f"未支援的翻譯服務: {translator_name}")

            # 3. 定義進度更新 callback 函數，當 PDFProcessor 翻譯完一頁時即會呼叫此函式
            def progress_cb(current_page, total_pages, log_msg, overflow_count):
                self.ui_queue.put({
                    "type": "progress",
                    "current": current_page,
                    "total": total_pages,
                    "msg": log_msg,
                    "overflow": overflow_count
                })

            # 4. 初始化 PDF 處理器
            processor = PDFProcessor(
                translator=translator,
                config=config,
                progress_callback=progress_cb
            )

            # 5. 啟動翻譯
            out_pdf, db_pdf = processor.process_pdf(
                input_pdf_path=input_pdf,
                output_dir=output_dir,
                debug_mode=debug_mode
            )

            # 6. 成功完成，將結果透過 Queue 回傳
            self.ui_queue.put({
                "type": "success",
                "out_pdf": out_pdf,
                "db_pdf": db_pdf
            })

        except Exception as e:
            # 捕獲所有例外，回報給 UI，防止背景執行緒崩潰而 GUI 完全不知道
            import traceback
            err_details = traceback.format_exc()
            self.ui_queue.put({
                "type": "error",
                "message": str(e),
                "details": err_details
            })
        finally:
            self.is_running = False
            self.ui_queue.put({"type": "finished"})
