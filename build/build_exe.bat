@echo off
title TramsLay - PyInstaller Onedir 打包工具
echo =======================================================
echo     TramsLay Layout-Preserving PDF Translator
echo               Onedir 打包程序啟動
echo =======================================================
echo.

:: 切換至批次檔所在目錄
cd /d "%~dp0"

echo 正在執行 PyInstaller 清理並根據規格檔進行打包...
pyinstaller --clean pyinstaller_onedir.spec

echo.
echo =======================================================
echo 任務結束！
echo 若打包順利，輸出檔案已儲存在：
echo "%~dp0dist\TramsLay"
echo =======================================================
echo.
pause
