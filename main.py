import os
import sys
import customtkinter as ctk
from app.gui import TranslatorGUI

def main():
    """
    TramsLay 桌面應用程式 GUI 模式啟動入口
    """
    root = ctk.CTk()
    
    # 設定視窗圖示 (支援 PyInstaller 打包與開發模式兩種路徑)
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包環境：圖示在 spec 中已嵌入 exe，
            # 但 runtime 視窗圖示需要從 _MEIPASS 暫存目錄或同目錄讀取
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            icon_path = os.path.join(base_path, "icon.ico")
        else:
            # 開發模式：從 build/ 目錄讀取
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "icon.ico")
        
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
            # 同時設定 taskbar 圖示 (Windows)
            if sys.platform.startswith('win'):
                import ctypes
                # 設定 AppUserModelID 使 Windows 工作列使用自訂圖示而非 Python 預設圖示
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.tramslay.pdf-translator")
    except Exception:
        pass  # 圖示設定失敗不影響主程式運行
    
    # 建立 GUI 實例並啟動事件迴圈
    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
