@echo off
title TramsLay - PyInstaller Onefile 打包工具
echo =======================================================
echo     TramsLay Layout-Preserving PDF Translator
echo               Onefile 單一檔案打包程序啟動
echo =======================================================
echo.

:: 切換至批次檔所在目錄
cd /d "%~dp0"

echo 正在執行 PyInstaller 清理並根據規格檔進行單一可執行檔打包...
pyinstaller --clean pyinstaller_onefile.spec

echo.
echo =======================================================
echo 任務結束！
echo 若打包順利，單一 EXE 執行檔已儲存在：
echo "%~dp0dist\TramsLay.exe"
echo =======================================================
echo.
pause
