import os
import sys
import logging
from datetime import datetime

# 全域的 GUI Log 佇列 (Tkinter 執行緒讀取用)
gui_log_queue = None

class QueueHandler(logging.Handler):
    """
    自訂 Logging Handler，將 Log 訊息傳送到 Queue，提供給 Tkinter GUI 更新介面使用
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.log_queue is not None:
                self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

def setup_logger(debug=False, log_queue=None):
    """
    初始化全域 Logger，支援 Console, 檔案與 GUI 佇列
    """
    global gui_log_queue
    if log_queue:
        gui_log_queue = log_queue

    logger = logging.getLogger("PDFTranslator")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # 清空既有的 Handler，避免重複輸出
    logger.handlers = []

    # 設定輸出格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(console_handler)

    # 2. File Handler (優先使用系統 Temp 目錄，防止 OneDrive/Dropbox 等同步軟體鎖定檔案導致 I/O 死鎖)
    try:
        # 使用系統 Temp 臨時區存放日誌，100% 避免同步鎖定與唯讀目錄權限衝突
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or os.getcwd()
        log_dir = os.path.join(temp_dir, "TramsLay_Logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"translator_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"無法建立日誌檔案: {e}", file=sys.stderr)

    # 3. GUI Queue Handler
    if gui_log_queue is not None:
        queue_handler = QueueHandler(gui_log_queue)
        queue_handler.setFormatter(formatter)
        queue_handler.setLevel(logging.INFO)
        logger.addHandler(queue_handler)

    return logger

def get_logger():
    """
    取得已建立的 Logger 實例
    """
    return logging.getLogger("PDFTranslator")
