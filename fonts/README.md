# 字型資料夾 (Fonts Folder)

本資料夾用於放置自訂的 TrueType/OpenType 中文字型檔。

## 預設行為
程式會自動偵測作業系統中的中文字型：
- **Windows**: 優先使用 `Microsoft JhengHei` (微軟正黑體，檔名：`msjh.ttc` 或 `msjh.ttf`)。
- **macOS**: 優先使用 `PingFang TC` (蘋方-繁，檔名：`PingFang.ttc`) 或 `STHeiti` (黑體-繁)。

## 手動安裝自訂字型
如果您在 PDF 輸出中看到「豆腐字」（無法顯示的字元）或者想要使用特定的中文字型：
1. 下載支援繁體中文的 `.ttf` 或 `.otf` 字型（例如 Google 的 `Noto Sans TC` 系列）。
2. 將字型檔案放置於本資料夾 (`fonts/`) 底下。
3. 命名為 `custom.ttf`，或者在設定檔或介面中指定字型路徑。
