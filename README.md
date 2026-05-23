# TramsLay - Layout-Preserving PDF Translator (論文排版還原翻譯器)

<div align="center">
  <br />
  <a href="https://github.com/jimmymochi/transLay/releases/download/v1.0.0/TramsLay_Windows_Launcher.exe">
    <img src="https://img.shields.io/badge/📥_點我一鍵下載_Windows_啟動器-(3MB)-blue?style=for-the-badge&logo=windows&logoColor=white" alt="Download Windows" />
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://github.com/jimmymochi/transLay/releases/download/v1.0.0/TramsLay_macOS_Launcher.dmg">
    <img src="https://img.shields.io/badge/📥_點我一鍵下載_macOS_啟動器-(3MB)-black?style=for-the-badge&logo=apple&logoColor=white" alt="Download macOS" />
  </a>
  <br />
  <br />
  <a href="https://github.com/jimmymochi/transLay/releases/latest">
    <img src="https://img.shields.io/badge/🔍_前往_GitHub_最新_Release_發佈頁面-orange?style=flat-square" alt="Latest Release" />
  </a>
  &nbsp;&nbsp;
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
  </a>
</div>

<br />

TramsLay 是一款專為學術論文打造的 **PDF 版面還原翻譯工具**。它致力於將英文 PDF 論文翻譯為流暢的繁體中文，且**極致保留原始雙欄結構、圖片、表格、公式與頁首頁尾**，讓您閱讀譯文時如同閱讀原文般直觀舒適。

---

## 🌟 核心特色

1. **二維圖層避障 (Layout-Aware Text Fitter)**：將 PDF 視為二維畫布，文字寫入前進行碰撞偵測，絕不覆蓋圖片、公式與表格。
2. **五階段幾何擬合管線**：
   - 先嘗試原始邊界框 (BBox) 寫入。
   - 空間不足時，自動壓縮行高。
   - 仍不足時，計算周圍安全留白進行 **動態 BBox 擴張**（不跨欄、不越界）。
   - 必要時微幅縮小字號（保證不低於最低可讀極限）。
   - 極端情況下啟用 **優雅降級溢位備援 (Graceful Degradation)**，在尾端加上紅色 `[+]`，並於 PDF 末尾自動生成精美的「翻譯溢位附錄 (Translation Overflow Appendix)」。
3. **台灣學術用語在地化 (OpenCC)**：後端完美掛載 OpenCC 簡繁學術名詞修正引擎，將譯文自動優化為貼近台灣習慣的繁中用語（如*資訊*、*資料庫*、*演算*）。
4. **極致現代風格 GUI (CustomTkinter)**：精緻的圓角扁平化外觀，支援「深色/淺色/系統」主題切換，內含多執行緒防凍結機制，提供極佳的互動響應。
5. **多系統直接下載支持**：配置 GitHub Actions 自動化管線，於 Release 頁面提供 Windows 獨立 EXE 與 macOS App 的直接下載。

---

## 🚀 下載與安裝 (智慧啟動與下載器 — 免安裝一鍵秒開)

我們提供了體積極小、極速下載的 **TramsLay 智慧型啟動下載器 (Smart Launcher)**。您再也不需要手動下載幾十 MB 的大軟體，更不需要任何繁瑣的終端機操作，雙擊即可一鍵全自動下載、安裝、更新並直接啟動正式軟體！

### 📥 從 GitHub Release 下載啟動器 (推薦)
1. 前往本專案的 **[GitHub Releases]** 頁面。
2. 下載適合您平台的微型啟動器：
   - **Windows 用戶**：下載 **`TramsLay_Windows_Launcher.exe`** (僅約 3MB，雙擊直接彈出美麗的下載介面，無後台黑框命令行視窗！)。
   - **macOS 用戶**：下載 **`TramsLay_macOS_Launcher.dmg`** (僅約 3MB，雙擊開啟後，拖曳至應用程式夾即完成安裝！)。

---

### 💻 雙擊極速使用指南

#### 🔷 Windows 系統：
1. 雙擊打開下載的 `TramsLay_Windows_Launcher.exe`。
2. 啟動器會自動偵測您的系統主題 (適配深色與淺色模式)，展示高質感的現代進度條，**自動從 GitHub 下載最新版主程式**。
3. 下載完成後，會**自動在您的 Windows 桌面建立捷徑**，並**全自動拉起正式的翻譯軟體介面**！
4. **以後再次點擊**，啟動器會在一秒內直接閃開，秒速拉起您的論文翻譯器，並隨時自動保持在最新版本！

#### 🍏 macOS 系統：
1. 雙擊掛載 `TramsLay_macOS_Launcher.dmg`，將 `TramsLay_Launcher.app` 拖移入 `Applications` (應用程式) 資料夾。
2. 雙擊 `TramsLay_Launcher` 即可全自動下載安裝主程式並拉起美麗的 CustomTkinter 現代主畫面！

> [!CAUTION]
> **🍏 macOS 首次開啟「安全性與隱私權」限制繞過指南：**
> 由於開源軟體未進行 Apple 付費開發者認證，首次雙擊開啟 `TramsLay_Launcher.app` 時，macOS 可能會顯示 **「無法辨識的開發者」** 或 **「損毀且無法開啟」** 的警告。
> 請依據以下方式解除限制：
> 1. 打開 **終端機 (Terminal)**。
> 2. 輸入以下指令並按下 Enter（需輸入 Mac 密碼授權）：
>    ```bash
>    sudo xattr -rd com.apple.quarantine /Applications/TramsLay_Launcher.app
>    ```
>    *(若您將 App 放在下載資料夾，請將路徑改為 `~/Downloads/TramsLay_Launcher.app`)*
> 3. 再次雙擊 App 即可完美正常開啟！

---

## 💻 本地運行與開發

如果您是開發者，想在本地運行源碼或進行二次開發：

### 1. 複製專案與安裝依賴
```bash
git clone https://github.com/your-username/TramsLay.git
cd TramsLay
pip install -r requirements.txt
```

### 2. 啟動現代風格 GUI 介面
```bash
python main.py
```

### 3. 啟動命令行 CLI 模式 (適合批次處理/CI測試)
```bash
# 基本使用 (Google 翻譯)
python run_cli.py input.pdf

# 壓力測試 (使用 Dummy 模擬大長度翻譯，並輸出多色避障除錯邊界框 PDF)
python run_cli.py input.pdf --debug --translator dummy --dummy-mode stress
```

---

## 🧪 自動化測試

為了保障 Layout 還原引擎的幾何計算精準度，專案提供完整的 `pytest` 測試套件：

```powershell
# 設定 Python PATH 並運行所有幾何碰撞與擬合管線測試
$env:PYTHONPATH="."; pytest tests/
```

---

## 📦 本地打包指南

如果您修改了代碼，想要在本地重新打包出發佈軟體：

*   **Windows 打包 (onedir/onefile)**：
    雙擊執行 `build/build_exe.bat` 或是 `build/build_exe_onefile.bat`。
*   **macOS 打包 (生成 .app 與 .dmg)**：
    在終端機執行：
    ```bash
    chmod +x build/build_app.sh
    ./build/build_app.sh
    ```

---

## 🤖 GitHub 自動雲端打包發佈 (CI/CD)

本專案已完美整合了 **GitHub Actions**。當您完成代碼修改並決定發布新版本時：
1. 在本地或 GitHub 上建立一個符合 `v*` 格式的 Git Tag（例如 `v1.0.0`）：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. GitHub Actions 會自動開啟 `TramsLay Multi-OS Release Build` 工作流，自動於雲端虛擬機中打包出 Windows 的 `TramsLay_Windows.exe` 與 macOS 的 `TramsLay_macOS.dmg`，並在 3 分鐘內自動創建一個漂亮的 Release 頁面並發布這兩個下載包。

---

## 📄 開源授權

本專案基於 **[MIT License](LICENSE)** 條款開源發佈。
