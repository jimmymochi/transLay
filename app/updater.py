"""
TramsLay 應用內自動更新模組。
負責連線 GitHub API 檢查最新版本，比較本地版本，
並在背景下載新版 .exe 完成無縫更新。
"""

import os
import sys
import time
import threading
import requests
from utils.logger import get_logger
from version import APP_VERSION, GITHUB_API_LATEST_RELEASE


class AppUpdater:
    """
    應用內更新器，提供版本檢查與背景下載更新功能。
    """
    def __init__(self, ui_callback=None):
        """
        :param ui_callback: GUI 回呼函數，格式為 cb(event_type, data)
               event_type: "checking", "no_update", "update_available", "downloading", "download_done", "error"
        """
        self.logger = get_logger()
        self.ui_callback = ui_callback or (lambda *a: None)
        self.is_checking = False
        self.is_downloading = False

    def get_current_version(self) -> str:
        return APP_VERSION

    def check_for_update(self):
        """
        在背景線程中檢查 GitHub 最新版本
        """
        if self.is_checking:
            return
        self.is_checking = True
        threading.Thread(target=self._async_check, daemon=True).start()

    def _async_check(self):
        try:
            self.ui_callback("checking", {"message": "正在連線 GitHub 檢查最新版本..."})

            headers = {"User-Agent": "TramsLay-Updater"}
            res = requests.get(GITHUB_API_LATEST_RELEASE, headers=headers, timeout=10)
            res.raise_for_status()
            release_data = res.json()

            remote_tag = release_data.get("tag_name", "")
            release_notes = release_data.get("body", "")

            if not remote_tag:
                self.ui_callback("error", {"message": "無法取得遠端版本資訊"})
                return

            # 版本比較 (簡易字串比較，v1.0.4 > v1.0.3)
            if self._is_newer(remote_tag, APP_VERSION):
                # 尋找對應平台的下載資產
                download_url, asset_name, asset_size = self._find_platform_asset(release_data)

                self.ui_callback("update_available", {
                    "remote_version": remote_tag,
                    "local_version": APP_VERSION,
                    "release_notes": release_notes,
                    "download_url": download_url,
                    "asset_name": asset_name,
                    "asset_size": asset_size
                })
            else:
                self.ui_callback("no_update", {
                    "message": f"您的版本 {APP_VERSION} 已是最新版！",
                    "remote_version": remote_tag
                })

        except Exception as e:
            self.logger.error(f"檢查更新時出錯: {e}")
            self.ui_callback("error", {"message": f"檢查更新失敗: {e}"})
        finally:
            self.is_checking = False

    def download_update(self, download_url: str, asset_name: str):
        """
        背景下載新版本
        """
        if self.is_downloading or not download_url:
            return
        self.is_downloading = True
        threading.Thread(
            target=self._async_download,
            args=(download_url, asset_name),
            daemon=True
        ).start()

    def _async_download(self, download_url: str, asset_name: str):
        try:
            self.ui_callback("downloading", {"message": "正在建立下載連線...", "progress": 0.0})

            # 決定下載儲存路徑 (與當前執行檔同目錄)
            current_exe = sys.executable if getattr(sys, 'frozen', False) else None
            if current_exe:
                download_dir = os.path.dirname(current_exe)
                # 一律在 Windows/macOS 下使用 .new 後綴，避免直接寫入/覆蓋正在運作的執行檔造成 OS 鎖定錯誤
                final_path = current_exe + ".new"
            else:
                # 開發環境
                download_dir = os.path.dirname(os.path.abspath(__file__))
                download_dir = os.path.dirname(download_dir)  # 從 app/ 回到根目錄
                final_path = os.path.join(download_dir, f"{asset_name}.new")

            # 下載為暫存檔案
            temp_path = os.path.join(download_dir, f"{asset_name}.downloading")

            headers = {"User-Agent": "TramsLay-Updater"}
            response = requests.get(download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            pct = downloaded / total_size
                            elapsed = time.time() - start_time
                            speed = downloaded / elapsed / 1024 / 1024 if elapsed > 0 else 0
                            dl_mb = downloaded / 1024 / 1024
                            total_mb = total_size / 1024 / 1024

                            self.ui_callback("downloading", {
                                "message": f"下載中: {dl_mb:.1f} / {total_mb:.1f} MB ({speed:.1f} MB/s)",
                                "progress": pct
                            })

            # 下載完成，安全覆蓋已存在的舊新檔 (.new)
            if os.path.exists(final_path):
                try:
                    os.remove(final_path)
                except Exception:
                    pass

            os.rename(temp_path, final_path)

            self.ui_callback("download_done", {
                "message": "更新下載完成！軟體即將自動重啟以載入最新版本。",
                "file_path": final_path
            })

        except Exception as e:
            self.logger.error(f"下載更新時出錯: {e}")
            self.ui_callback("error", {"message": f"下載更新失敗: {e}"})
            # 清理暫存檔
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
        finally:
            self.is_downloading = False

    def _is_newer(self, remote: str, local: str) -> bool:
        """
        比較兩個語義版本號 (如 v1.0.4 vs v1.0.3)
        """
        try:
            r_parts = [int(x) for x in remote.lstrip('v').split('.')]
            l_parts = [int(x) for x in local.lstrip('v').split('.')]
            # 補齊長度
            while len(r_parts) < 3:
                r_parts.append(0)
            while len(l_parts) < 3:
                l_parts.append(0)
            return tuple(r_parts) > tuple(l_parts)
        except (ValueError, AttributeError):
            return remote != local

    def _find_platform_asset(self, release_data: dict) -> tuple:
        """
        從 Release 資產中尋找對應平台的主程式下載連結
        """
        is_windows = sys.platform.startswith("win")
        assets = release_data.get("assets", [])

        # 優先精確匹配
        target_name = "TramsLay_Windows_Core.exe" if is_windows else "TramsLay_macOS_Core.dmg"
        for asset in assets:
            if asset.get("name") == target_name:
                return (
                    asset.get("browser_download_url", ""),
                    asset.get("name", ""),
                    asset.get("size", 0)
                )

        # 模糊匹配
        for asset in assets:
            name = asset.get("name", "")
            if is_windows and name.endswith(".exe") and "launcher" not in name.lower():
                return (asset.get("browser_download_url", ""), name, asset.get("size", 0))
            elif not is_windows and name.endswith(".dmg") and "launcher" not in name.lower():
                return (asset.get("browser_download_url", ""), name, asset.get("size", 0))

        return ("", "", 0)

    def restart_and_apply_update(self, new_exe_path: str):
        """
        在 Windows 或 macOS 下執行自動重啟與新舊檔案替換。
        """
        import subprocess
        
        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        
        if not current_exe:
            # 開發環境下，直接用 os.execv 重啟 python 腳本
            self.logger.info("開發環境：正在直接重啟 Python 應用程式...")
            try:
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                self.logger.error(f"重啟失敗: {e}")
            return

        # 打包環境下，建立獨立腳本來進行替換
        self.logger.info(f"打包環境：準備替換執行檔。當前: {current_exe}, 新版: {new_exe_path}")
        
        is_windows = sys.platform.startswith("win")
        
        if is_windows:
            # 建立 Windows 暫存的 .bat 批次檔
            bat_path = os.path.join(os.path.dirname(current_exe), "update_temp.bat")
            bat_content = f"""@echo off
timeout /t 1 /nobreak > NUL
:loop
del /f /q "{current_exe}"
if exist "{current_exe}" (
    timeout /t 1 /nobreak > NUL
    goto loop
)
move /y "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
            try:
                with open(bat_path, "w", encoding="ansi") as f:
                    f.write(bat_content)
                
                # 執行批次檔，使用 shell=True 且啟動 detached 處理，確保 main.py 關閉後批次檔仍能繼續執行
                subprocess.Popen(
                    [bat_path],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
                self.logger.info("Windows 更新批次檔已啟動，準備關閉主程式。")
                sys.exit(0)
            except Exception as e:
                self.logger.error(f"建立或啟動 Windows 更新批次檔失敗: {e}")
                raise e
        else:
            # 建立 macOS/Linux 暫存的 shell 腳本
            sh_path = os.path.join(os.path.dirname(current_exe), "update_temp.sh")
            sh_content = f"""#!/bin/bash
sleep 1
while [ -f "{current_exe}" ]; do
    rm -f "{current_exe}"
    sleep 1
done
mv "{new_exe_path}" "{current_exe}"
chmod +x "{current_exe}"
open "{current_exe}"
rm -- "$0"
"""
            try:
                with open(sh_path, "w", encoding="utf-8") as f:
                    f.write(sh_content)
                os.chmod(sh_path, 0o755)
                
                # 執行 shell 腳本並分離
                subprocess.Popen(
                    [sh_path],
                    shell=False,
                    start_new_session=True
                )
                self.logger.info("macOS 更新腳本已啟動，準備關閉主程式。")
                sys.exit(0)
            except Exception as e:
                self.logger.error(f"建立或啟動 macOS 更新腳本失敗: {e}")
                raise e
