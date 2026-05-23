import os
import sys
import time
import json
import threading
import subprocess
import requests
import customtkinter as ctk
from tkinter import messagebox

# 設置 CustomTkinter 外觀
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class LauncherGUI:
    """
    TramsLay 智慧型啟動、安裝與自動更新下載器。
    體積極小 (約 3MB)，能自適應系統深/淺色主題，
    自動連線 GitHub API 偵測、下載最新主程式並一鍵啟動。
    """
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("TramsLay 啟動與安裝管理器")
        self.root.geometry("520x350")
        self.root.resizable(False, False)
        
        # GitHub 倉庫設定
        self.repo_owner = "jimmymochi"
        self.repo_name = "transLay"
        
        # 本地主程式存放路徑
        self.bin_dir = os.path.join(os.getcwd(), "bin")
        if not os.path.exists(self.bin_dir):
            os.makedirs(self.bin_dir)
            
        self.is_windows = sys.platform.startswith("win")
        if self.is_windows:
            self.core_exe_name = "TramsLay_Core.exe"
        else:
            self.core_exe_name = "TramsLay_Core.dmg"
            
        self.core_path = os.path.join(self.bin_dir, self.core_exe_name)
        
        # 下載線程相關變數
        self.download_thread = None
        self.is_downloading = False
        
        self._create_widgets()
        
        # 啟動時自動進行版本檢測
        self.root.after(800, self._check_version_and_launch)

    def _create_widgets(self):
        """
        建立極具現代風格的啟動器介面
        """
        # 頂部主題裝飾
        banner = ctk.CTkFrame(self.root, corner_radius=0, height=8, fg_color=("#3498DB", "#2980B9"))
        banner.pack(fill="x", side="top")

        # 主要內容容器
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=25)
        
        # 標題
        title_lbl = ctk.CTkLabel(
            self.main_frame, 
            text="TramsLay PDF Translator", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=22, weight="bold"),
            text_color=("#2C3E50", "#3498DB")
        )
        title_lbl.pack(pady=(10, 5))
        
        # 副標題 (啟動器版本)
        self.sub_lbl = ctk.CTkLabel(
            self.main_frame, 
            text="智慧啟動與安裝管理器 v1.0.0", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=12),
            text_color="#7F8C8D"
        )
        self.sub_lbl.pack(pady=(0, 20))
        
        # 狀態訊息
        self.status_lbl = ctk.CTkLabel(
            self.main_frame, 
            text="正在連線 GitHub 檢測軟體版本...", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold")
        )
        self.status_lbl.pack(pady=10)
        
        # 現代化進度條 (預設隱藏)
        self.prog_bar = ctk.CTkProgressBar(self.main_frame, width=400)
        self.prog_bar.pack(pady=10)
        self.prog_bar.set(0.0)
        self.prog_bar.pack_forget()
        
        # 下載速率與預估時間標籤 (預設隱藏)
        self.speed_lbl = ctk.CTkLabel(
            self.main_frame, 
            text="", 
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#95A5A6"
        )
        self.speed_lbl.pack(pady=2)
        self.speed_lbl.pack_forget()

        # 下方控制按鈕區
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        self.btn_action = ctk.CTkButton(
            self.btn_frame, 
            text="請稍候...", 
            command=self._on_action_click,
            state="disabled",
            fg_color="#3498DB",
            hover_color="#2980B9"
        )
        self.btn_action.pack(side="right")
        
        # 自動建立捷徑 Checkbox (僅 Windows 顯示)
        self.var_shortcut = ctk.BooleanVar(value=True)
        self.chk_shortcut = ctk.CTkCheckBox(
            self.btn_frame, 
            text="在桌面建立軟體捷徑", 
            variable=self.var_shortcut,
            font=ctk.CTkFont(family="Microsoft JhengHei", size=11)
        )
        if self.is_windows:
            self.chk_shortcut.pack(side="left", pady=5)
        else:
            self.chk_shortcut.pack_forget()

    def _check_version_and_launch(self):
        """
        異步檢查遠端 GitHub 版本與本地核心主程式
        """
        threading.Thread(target=self._async_check_flow, daemon=True).start()

    def _create_launch_old_button(self):
        """
        發現更新時，動態在左側增加一個直接啟動本地舊版的按鈕
        """
        self.btn_launch_old = ctk.CTkButton(
            self.btn_frame, 
            text="🚀 直接啟動舊版", 
            command=self._launch_core_app,
            fg_color="#7F8C8D",
            hover_color="#95A5A6"
        )
        self.btn_launch_old.pack(side="right", padx=(0, 10))

    def _async_check_flow(self):
        # 1. 檢查本地是否存在主程式
        local_exists = os.path.exists(self.core_path)
        
        # 讀取本地版本資訊
        self.version_path = os.path.join(self.bin_dir, "version.txt")
        self.local_version = "未知"
        if local_exists and os.path.exists(self.version_path):
            try:
                with open(self.version_path, "r", encoding="utf-8") as f:
                    self.local_version = f.read().strip()
            except Exception:
                pass
        
        if not local_exists:
            self.status_lbl.configure(text="本地未安裝主程式，準備從雲端下載安裝...")
        else:
            self.status_lbl.configure(text="正在檢測 GitHub Release 雲端最新版本...")

        # 2. 獲取 GitHub 上的最新 Release
        try:
            api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            headers = {"User-Agent": "TramsLay-Launcher-Downloader"}
            res = requests.get(api_url, headers=headers, timeout=8)
            res.raise_for_status()
            release_data = res.json()
            
            tag_name = release_data.get("tag_name", "v1.0.0")
            self.latest_tag_name = tag_name
            self.sub_lbl.configure(text=f"智慧啟動與安裝管理器 (最新版本: {tag_name})")
            
            # 尋找對應平台的正式主程式 Asset
            target_asset = None
            search_pattern = "TramsLay_Windows_Core.exe" if self.is_windows else "TramsLay_macOS_Core.dmg"
            
            for asset in release_data.get("assets", []):
                if asset.get("name") == search_pattern:
                    target_asset = asset
                    break
                    
            if not target_asset:
                # Fallback: 如果沒有特定命名，模糊搜尋 Core 或對應副檔名
                for asset in release_data.get("assets", []):
                    name = asset.get("name", "")
                    if self.is_windows and name.endswith(".exe") and "launcher" not in name.lower():
                        target_asset = asset
                        break
                    elif not self.is_windows and name.endswith(".dmg") and "launcher" not in name.lower():
                        target_asset = asset
                        break

            if not target_asset:
                raise ValueError("在 GitHub Release 中找不到適配的主程式安裝包！")

            self.download_url = target_asset.get("browser_download_url")
            self.asset_size = target_asset.get("size", 0)
            
            if not local_exists:
                # 本地無軟體，引導下載
                self.status_lbl.configure(text=f"發現最新版 TramsLay ({tag_name})，點選下方按鈕一鍵安裝！")
                self.btn_action.configure(text="📥 一鍵下載與安裝", state="normal")
            elif self.local_version != tag_name:
                # 發現新版本，引導升級
                self.status_lbl.configure(text=f"發現新版本 {tag_name}！(您當前版本為 {self.local_version})")
                self.btn_action.configure(text="📥 一鍵升級至最新版", state="normal")
                # 建立啟動舊版按鈕
                self._create_launch_old_button()
            else:
                # 本地已是最新版，直接秒開
                self.status_lbl.configure(text="本地軟體已是最新版，準備為您極速啟動...")
                self._launch_core_app()
                
        except Exception as e:
            # 網路錯誤或解析出錯時的優雅降級
            if local_exists:
                self.status_lbl.configure(text="連線失敗，將為您啟動本地現有版本...")
                self._launch_core_app()
            else:
                self.status_lbl.configure(text="❌ 連線 GitHub 失敗，且本地無可用軟體！")
                self.btn_action.configure(text="重試連線", state="normal")
                messagebox.showerror("連線錯誤", f"無法連接至 GitHub 獲取安裝包，請檢查網路設定！\n錯誤: {e}")

    def _on_action_click(self):
        """
        按鈕點選動作
        """
        action = self.btn_action.cget("text")
        if "下載" in action:
            self._start_download_flow()
        elif "重試" in action:
            self.btn_action.configure(text="請稍候...", state="disabled")
            self._check_version_and_launch()
        elif "啟動" in action:
            self._launch_core_app()

    def _start_download_flow(self):
        """
        開啟背景流式下載線程
        """
        if self.is_downloading:
            return
            
        self.is_downloading = True
        self.btn_action.configure(state="disabled", text="正在安裝...")
        self.prog_bar.pack(pady=10)
        self.speed_lbl.pack(pady=2)
        
        self.download_thread = threading.Thread(target=self._async_downloader, daemon=True)
        self.download_thread.start()

    def _async_downloader(self):
        """
        高精度流式下載器，實時計算速率與剩餘時間
        """
        try:
            self.status_lbl.configure(text="正在建立安全下載連線...")
            headers = {"User-Agent": "TramsLay-Launcher-Downloader"}
            response = requests.get(self.download_url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', self.asset_size))
            
            self.status_lbl.configure(text="開始下載軟體主程式...")
            
            downloaded = 0
            start_time = time.time()
            last_time = start_time
            last_bytes = 0
            
            with open(self.core_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新進度條
                        pct = downloaded / total_size
                        self.prog_bar.set(pct)
                        
                        # 每 0.5 秒計算一次下載速率與剩餘時間
                        curr_time = time.time()
                        if curr_time - last_time > 0.5:
                            duration = curr_time - start_time
                            speed = downloaded / duration / 1024 / 1024  # MB/s
                            
                            # 剩餘時間
                            remaining_bytes = total_size - downloaded
                            rem_speed_bytes = downloaded / duration
                            eta = remaining_bytes / rem_speed_bytes if rem_speed_bytes > 0 else 0
                            
                            dl_mb = downloaded / 1024 / 1024
                            total_mb = total_size / 1024 / 1024
                            
                            self.status_lbl.configure(text=f"正在下載: {dl_mb:.1f}MB / {total_mb:.1f}MB")
                            self.speed_lbl.configure(text=f"下載速率: {speed:.2f} MB/s | 剩餘時間: {int(eta)} 秒")
                            last_time = curr_time
                            
            self.status_lbl.configure(text="📥 下載完成！正在為您初始化配置...")
            self.speed_lbl.configure(text="進度：100% | 下載已成功結束")
            self.prog_bar.set(1.0)
            
            # 寫入本地版本檔案
            try:
                with open(self.version_path, "w", encoding="utf-8") as f:
                    f.write(self.latest_tag_name)
            except Exception as ex:
                print(f"寫入本地版本檔失敗: {ex}")
            
            # 建立桌面捷徑 (僅 Windows 且勾選時)
            if self.is_windows and self.var_shortcut.get():
                try:
                    self._create_windows_shortcut()
                except Exception as ex:
                    print(f"建立桌面捷徑失敗: {ex}")
                    
            time.sleep(1.0)
            self._launch_core_app()
            
        except Exception as e:
            self.is_downloading = False
            self.status_lbl.configure(text="❌ 下載中斷，請重試！")
            self.btn_action.configure(state="normal", text="📥 重新下載與安裝")
            self.prog_bar.pack_forget()
            self.speed_lbl.pack_forget()
            messagebox.showerror("下載錯誤", f"主程式下載失敗: {e}\n請檢查您的網路連線！")

    def _create_windows_shortcut(self):
        """
        純 Python 免依賴 VBS 腳本建立 Windows 桌面捷徑，完美指向 Launcher 以便進行自動升級與顯示專屬圖示
        """
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        shortcut_path = os.path.join(desktop, "TramsLay 論文翻譯器.lnk")
        
        # 獲取 Launcher 自身的執行檔絕對路徑
        launcher_path = sys.executable
        launcher_dir = os.path.dirname(launcher_path)
        
        # 建立 WScript.Shell 的 VBScript，設定 TargetPath 為 Launcher 以便每次雙擊都享有自動更新檢查
        vbs_content = (
            f'Set sh = CreateObject("WScript.Shell")\n'
            f'Set shortcut = sh.CreateShortcut("{shortcut_path}")\n'
            f'shortcut.TargetPath = "{launcher_path}"\n'
            f'shortcut.WorkingDirectory = "{launcher_dir}"\n'
            f'shortcut.Description = "TramsLay 論文排版還原 PDF 翻譯器"\n'
            f'shortcut.IconLocation = "{launcher_path},0"\n'  # 完美提取 Launcher 內置的 3D 水晶圖標
            f'shortcut.Save()'
        )
        
        vbs_path = os.path.join(self.bin_dir, "create_shortcut.vbs")
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
            
        # 透過 Windows 內建的 cscript 隱密執行該 VBScript
        subprocess.run(["cscript", "//nologo", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 刪除暫存的 VBScript
        if os.path.exists(vbs_path):
            os.remove(vbs_path)

    def _launch_core_app(self):
        """
        直接啟動主程式，並退出 Launcher 本身
        """
        self.status_lbl.configure(text="🚀 正在拉起 TramsLay 正式版軟體...")
        time.sleep(0.8)
        
        try:
            if self.is_windows:
                # Windows 平台使用 os.startfile 模擬雙擊啟動，完美分離進程且絕無黑框，徹底避免 WinError 87 參數錯誤
                os.startfile(self.core_path)
            else:
                # macOS 上雙擊掛載 dmg 或者是如果是 app 則啟動之
                # 由於 macOS DMG 用戶可以拖曳，Launcher 主要在 Windows 上能發揮極致一鍵流
                # 這裡直接用 open 呼叫
                subprocess.Popen(["open", self.core_path])
                
            # 關閉 Launcher 本身，達成完美的「一鍵啟動」
            self.root.quit()
            sys.exit(0)
        except Exception as e:
            self.status_lbl.configure(text="❌ 無法啟動主程式！")
            self.btn_action.configure(state="normal", text="📥 重新下載與安裝")
            messagebox.showerror("啟動錯誤", f"主程式啟動失敗，請嘗試重新下載！\n錯誤: {e}")

if __name__ == "__main__":
    # 創建主視窗
    root = ctk.CTk()
    app = LauncherGUI(root)
    root.mainloop()
