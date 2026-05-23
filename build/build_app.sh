#!/bin/bash
# TramsLay - macOS PyInstaller 打包工具
echo "======================================================="
echo "    TramsLay Layout-Preserving PDF Translator"
echo "              macOS 打包程序啟動"
echo "======================================================="
echo.

# 取得目前腳本所在目錄
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "正在執行 PyInstaller 清理並根據 macOS 規格檔進行打包..."
pyinstaller --clean pyinstaller_macos.spec

echo.
echo "正在將生成的 TramsLay.app 封裝成 DMG 磁碟映像檔，以利 Mac 使用者拖曳安裝..."
cd dist
if [ -d "TramsLay.app" ]; then
    hdiutil create -volname "TramsLay" -srcfolder TramsLay.app -ov -format UDZO TramsLay_macOS.dmg
    echo "成功生成 TramsLay_macOS.dmg 安裝鏡像！"
else
    echo "❌ 錯誤：找不到生成的 TramsLay.app 檔案，打包可能失敗！"
    exit 1
fi

echo.
echo "======================================================="
echo "任務結束！"
echo "若打包順利，輸出 App 包與 ZIP 檔案已儲存在："
echo "$DIR/dist/"
echo "======================================================="
echo.
