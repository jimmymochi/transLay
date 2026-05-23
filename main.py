import sys
import customtkinter as ctk
from app.gui import TranslatorGUI

def main():
    """
    TramsLay 桌面應用程式 GUI 模式啟動入口
    """
    root = ctk.CTk()
    
    # 建立 GUI 實例並啟動事件迴圈
    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
