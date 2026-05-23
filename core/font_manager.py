import os
import sys
import platform
from utils.logger import get_logger
from utils.file_utils import resource_path

class FontManager:
    """
    字型管理模組，負責在 Windows 與 macOS 上自動尋找支援繁體中文的 TrueType/OpenType 字型，
    避免在輸出 PDF 時產生豆腐字。
    """
    def __init__(self, config_fonts=None):
        self.logger = get_logger()
        self.config_fonts = config_fonts or {}
        self.resolved_font_path = None
        self.resolved_font_name = "SystemCJK"
        self._detect_system_font()

    def _detect_system_font(self):
        """
        核心偵測邏輯，依據不同作業系統載入適合的繁中字型
        """
        system = platform.system().lower()
        
        # 1. 檢查是否有自訂放在 fonts/ 目錄下的字型
        local_font_dir = resource_path("fonts")
        if os.path.exists(local_font_dir):
            for file in os.listdir(local_font_dir):
                if file.endswith((".ttf", ".otf", ".ttc")) and "readme" not in file.lower():
                    local_path = os.path.join(local_font_dir, file)
                    self.logger.info(f"偵測到自訂本地字型: {local_path}")
                    self.resolved_font_path = local_path
                    self.resolved_font_name = "CustomLocalFont"
                    return

        # 2. 作業系統原生字型比對
        candidates = []
        
        if system == "windows":
            # Windows 常見繁中字型
            system_root = os.environ.get("SystemRoot", "C:\\Windows")
            candidates = [
                os.path.join(system_root, "Fonts", "msjh.ttc"),      # 微軟正黑體 (預設優先)
                os.path.join(system_root, "Fonts", "msjhbd.ttc"),    # 微軟正黑體 粗體
                os.path.join(system_root, "Fonts", "mingliub.ttc"),  # 細明體-ExtB
                os.path.join(system_root, "Fonts", "kaiu.ttf"),      # 標楷體
            ]
        elif system == "darwin":
            # macOS 常見繁中字型
            candidates = [
                "/System/Library/Fonts/PingFang.ttc",                # 蘋方-繁 (預設優先)
                "/System/Library/Fonts/STHeiti Light.ttc",            # 華康黑體-細
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/Library/Fonts/Microsoft/Microsoft JhengHei.ttf",   # Office 安裝的微軟正黑
                "/Library/Fonts/Microsoft JhengHei.ttf"
            ]
        else:
            # Linux 常用開源字型
            candidates = [
                "/usr/share/fonts/truetype/droid/DroidSansFallback.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
            ]

        # 3. 逐一檢查候選路徑是否存在
        for path in candidates:
            if os.path.exists(path):
                self.logger.info(f"成功偵測到系統繁中字型: {path}")
                self.resolved_font_path = path
                self.resolved_font_name = "SystemCJK"
                return

        # 4. 如果所有路徑都找不到，警告並啟用 PyMuPDF 原生 fallback (PyMuPDF 內部預設有 CJK 支援，但用外部 TrueType 排版更穩定)
        self.logger.warning("警告: 未能在系統中偵測到任何標準繁中字型，可能會影響中文字型的呈現品質。")
        self.resolved_font_path = None
        self.resolved_font_name = "china-t" # PyMuPDF 內建繁中字型代碼

    def get_font_info(self) -> tuple[str, str | None]:
        """
        回傳字型名稱與字型絕對路徑
        :return: (fontname, fontfile_path)
        """
        return self.resolved_font_name, self.resolved_font_path
