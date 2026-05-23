import os
import sys

def resource_path(relative_path):
    """
    取得 PyInstaller 打包後資源檔案的絕對路徑 (支援開發期與單一檔案 .exe)
    """
    try:
        # PyInstaller 建立的暫存資料夾位於 sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def ensure_dir(path):
    """
    確保指定的資料夾路徑存在
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_safe_output_path(input_path, output_dir=None, suffix=".zh-TW"):
    """
    產生安全的輸出檔案名稱，預設加上 .zh-TW 並且不覆蓋原始檔案
    """
    dir_name, file_name = os.path.split(input_path)
    base_name, ext = os.path.splitext(file_name)
    
    target_dir = output_dir if output_dir else dir_name
    if not target_dir:
        target_dir = os.getcwd()
        
    out_name = f"{base_name}{suffix}{ext}"
    return os.path.join(target_dir, out_name)
