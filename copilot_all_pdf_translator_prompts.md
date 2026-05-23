# PDF Translator 專案：所有可貼給 Copilot 的提示詞合集

> 這份檔案把目前所有要貼給 VS Code GitHub Copilot / Copilot Agent 的提示詞整理在一起。  
> 建議用法：依照專案階段，複製對應章節貼給 Copilot。  
> 專案目標：建立一個英文 PDF 論文翻譯成繁體中文 PDF 的桌面應用程式，盡可能保留原始雙欄排版、圖片、表格、公式與頁面結構，最後可打包成 Windows `.exe` 並上傳 GitHub。

---

# 目錄

1. [提示詞 01：完整專案生成提示詞](#提示詞-01完整專案生成提示詞)
2. [提示詞 02：Layout-Aware Text Fitter 強化提示詞](#提示詞-02layout-aware-text-fitter-強化提示詞)
3. [提示詞 03：實作計畫修正提示詞](#提示詞-03實作計畫修正提示詞)
4. [提示詞 04：核心管線補強提示詞](#提示詞-04核心管線補強提示詞)
5. [提示詞 05：GUI 與 PyInstaller 打包階段修正提示詞](#提示詞-05gui-與-pyinstaller-打包階段修正提示詞)
6. [提示詞 06：如果排版仍失敗時的修正提示詞](#提示詞-06如果排版仍失敗時的修正提示詞)
7. [建議開發流程](#建議開發流程)

---

# 提示詞 01：完整專案生成提示詞

```text
你現在要扮演一位資深 Python 桌面應用程式工程師、PDF 排版處理工程師、版面配置演算法工程師、開源專案架構師。

請幫我從零開始建立一個可以翻譯英文 PDF 論文的桌面應用程式，最終目標是可以打包成 Windows .exe，並且可以上傳到 GitHub 給其他人使用。

這個工具的核心目標是：

1. 輸入一份英文 PDF。
2. 輸出一份繁體中文 PDF。
3. 只翻譯英文文字成繁體中文。
4. 必須盡可能保持原始 PDF 的排版不變。
5. 原本的圖片、表格、公式、頁面大小、邊界、雙欄排版、文字區塊位置都不能被破壞。
6. 論文常見的雙欄格式必須能正確處理。
7. 不要把整頁文字抽出後重新排版成普通文件。
8. 翻譯後的中文應該放回原本英文文字附近，但不能無腦鎖死在原始 bbox 裡。
9. 必須導入 Layout-Aware Text Fitter：把 PDF 頁面視為二維空間圖層，透過碰撞偵測與安全擴張解決中文翻譯後空間不足的問題。
10. 最終產生的 PDF 應該看起來像原本 PDF，只是英文文字變成繁體中文。

請使用 Python 3.10 或 Python 3.11 開發，並規劃成一個乾淨、可維護、可上傳 GitHub 的開源專案。

請優先使用 PyMuPDF，也就是 fitz，作為主要 PDF 解析與輸出工具。

請避免使用只抽文字再重新產生 PDF 的方法，因為這會破壞雙欄論文排版。

請建立以下專案結構：

pdf-translator/
│
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ .gitignore
├─ main.py
├─ run_cli.py
├─ config.example.json
│
├─ app/
│  ├─ __init__.py
│  ├─ gui.py
│  ├─ app_controller.py
│
├─ core/
│  ├─ __init__.py
│  ├─ pdf_processor.py
│  ├─ layout_analyzer.py
│  ├─ paragraph_grouper.py
│  ├─ text_extractor.py
│  ├─ text_filter.py
│  ├─ text_fitter.py
│  ├─ font_manager.py
│  ├─ ocr_engine.py
│  ├─ obstacle_detector.py
│  ├─ collision_detector.py
│  ├─ bbox_expander.py
│  ├─ overflow_manager.py
│
├─ translators/
│  ├─ __init__.py
│  ├─ base_translator.py
│  ├─ dummy_translator.py
│  ├─ openai_translator.py
│  ├─ deepl_translator.py
│
├─ utils/
│  ├─ __init__.py
│  ├─ logger.py
│  ├─ file_utils.py
│  ├─ config_loader.py
│
├─ fonts/
│  ├─ README.md
│
├─ tests/
│  ├─ test_layout_analyzer.py
│  ├─ test_text_filter.py
│  ├─ test_text_fitter.py
│  ├─ test_collision_detector.py
│  ├─ test_bbox_expander.py
│  ├─ test_overflow_manager.py
│  ├─ test_dummy_translator_modes.py
│
├─ examples/
│  ├─ README.md
│
└─ build/
   ├─ build_exe.bat
   ├─ build_exe_onefile.bat
   ├─ pyinstaller.spec

requirements.txt 至少包含：

- pymupdf
- pillow
- requests
- python-dotenv
- tqdm
- pyinstaller
- pytest
- openai
- deepl

請建立 Translator 介面：

- BaseTranslator
- DummyTranslator
- OpenAITranslator
- DeepLTranslator

DummyTranslator 必須支援多種測試模式：

- same
- short
- normal
- long
- stress

CLI 必須支援：

python run_cli.py input.pdf --debug --dummy-mode stress

請讓 run_cli.py 保留作為 regression/debug/CI 的入口，不要被 main.py 取代。

main.py 則是 GUI 正式入口。

請建立 tkinter GUI，繁體中文介面，包含：

1. 選擇輸入 PDF。
2. 選擇輸出資料夾。
3. 選擇翻譯服務。
4. Dummy mode 下拉選單。
5. OpenAI API Key 輸入框。
6. Debug 模式 checkbox。
7. OCR checkbox，初版可先預留。
8. 進度條。
9. 顯示目前處理到第幾頁。
10. 即時 log 視窗。
11. Overflow 數量顯示。
12. 完成後可開啟輸出 PDF。
13. 完成後可開啟輸出資料夾。

請實作 Layout-Aware Text Fitter，重點如下：

1. PDF 頁面視為二維空間圖層。
2. 每個文字 block、圖片、表格、公式、頁眉、頁腳都要有 bbox。
3. 寫入翻譯文字前，必須建立 obstacle map。
4. 中文不應該無腦塞進原 bbox。
5. 先嘗試原 bbox 排版。
6. 不足時先壓縮行高。
7. 仍不足時安全擴張 bbox。
8. 再不足才縮小字號。
9. 最後才 overflow fallback。
10. 絕對不能讓文字蓋到圖片、表格、公式、其他段落或另一欄文字。

請實作 overflow fallback：

1. 主文顯示可容納的部分。
2. 主文尾端加紅色 [+...]。
3. 完整譯文或剩餘譯文存入 overflow manager。
4. PDF 最後新增「翻譯溢位附錄」。
5. 附錄依頁碼與 block id 列出原文與完整譯文。

請建立 debug overlay 功能，輸出 original.zh-TW.debug.pdf，並使用多色框線：

- 藍色：原始 text block bbox
- 紅色：hard obstacles
- 橘色：soft obstacles
- 綠色：expanded bbox
- 紫色：paragraph group bbox
- 灰色：column boundaries
- 黑色：header/footer safe zones

請提供完整可執行的初版程式碼。不要只給概念。請按照檔案路徑分段輸出程式碼。如果單次回答太長，請先完成核心版本，再告訴我下一步要產生哪些檔案。
```

---

# 提示詞 02：Layout-Aware Text Fitter 強化提示詞

```text
請升級目前的 text_fitter，不要只用「縮小字體」解決中文翻譯後塞不進原 bbox 的問題。

請導入 Layout-Aware Text Fitter 架構，核心原則如下：

1. PDF 頁面應被視為二維空間圖層。
2. 每個文字 block、圖片、表格、公式都應該有 bbox。
3. 在寫入翻譯文字前，必須根據頁面上其他物件建立 obstacle map。
4. 翻譯後的中文不應該無腦塞進原 bbox。
5. 系統應該先嘗試在原 bbox 中排版。
6. 如果放不下，先壓縮行高，而不是直接縮小字體。
7. 如果仍放不下，計算原 bbox 周圍的安全空白區。
8. 允許 bbox 在不碰撞其他物件、不跨欄、不超出頁面、不侵入頁眉頁腳的前提下動態擴張。
9. 擴張優先順序為：
   - 向下擴張
   - 在同欄內向右微擴張
   - 在同欄內向左微擴張
   - 必要時少量向上擴張
10. 每次擴張都必須進行 collision detection。
11. 不要真的每 1 pixel 掃描，請計算最近 obstacle 的距離，取得最大安全擴張量。
12. 擴張後仍放不下時，再依據可用 bbox 面積與中文字數估算理論最大字號。
13. 字號不能低於最低可讀字號，例如 8pt 或 9pt。
14. 行高不能低於安全下限，例如 1.05。
15. 如果仍放不下，啟用 graceful degradation。
16. 主文中只顯示可容納的部分，最後加上紅色 `[+...]` 標記。
17. 被截斷的完整翻譯或剩餘翻譯要存入 overflow manager。
18. 在整份 PDF 最後自動新增「翻譯溢位附錄」頁面。
19. 溢位附錄需依照頁碼與 block id 列出完整翻譯內容。
20. 絕對不能讓文字超出 bbox、蓋到其他段落、圖片、表格或公式。

請新增或修改以下模組：

core/obstacle_detector.py
core/collision_detector.py
core/bbox_expander.py
core/text_fitter.py
core/overflow_manager.py

請讓 pdf_processor.py 使用這個新的 fitting pipeline。
```

---

# 提示詞 03：實作計畫修正提示詞

```text
這個計畫方向可以，但請先依照以下要求修正 implementation_plan.md。尤其是 CLI、paragraph grouping、debug overlay、fitting pipeline、obstacle exclusion、geometry unit tests，這些要先做，GUI 和 exe 可以後面再做。

請修正 implementation_plan.md，補上以下要求：

1. 第一階段不要優先做完整 GUI，請先建立 CLI 測試入口 run_cli.py，讓我可以用 DummyTranslator 快速測試 PDF 版面。
2. 請加入 paragraph_grouper.py，負責把同欄、相近、屬於同一自然段的 block 合併，不要把左右欄或 caption/正文錯誤合併。
3. 請明確定義 Layout-Aware Text Fitter 的 fitting pipeline：
   - 原 bbox + 原字號 + 1.2 行高
   - 原 bbox + 原字號 + 壓縮行高
   - expanded bbox + 原字號 + 壓縮行高
   - expanded bbox + 降低字號 + 壓縮行高
   - overflow fallback
4. obstacle map 在處理 block_i 時，必須排除 block_i 本身，以及同一 paragraph group 裡的 block。
5. obstacle_detector 必須明確處理：
   - text block bbox
   - image bbox
   - drawing/vector bbox
   - suspected table bbox
   - suspected formula bbox
   - header/footer/page number area
6. collision_detector 和 bbox_expander 必須先寫單元測試，再整合進 pdf_processor。
7. 新增 debug layout overlay 功能，可以輸出 debug PDF，畫出：
   - text block bbox
   - obstacle bbox
   - expanded bbox
   - column boundary
   - overflow block
8. 輸出檔案不得覆蓋原始 PDF，預設命名為：
   - original.zh-TW.pdf
   - original.zh-TW.debug.pdf
9. 請在驗證計畫中加入至少 3 種測試 PDF：
   - 單欄論文
   - 雙欄論文
   - 含圖片/表格/公式的雙欄論文
10. 請把 GUI 與 .exe 打包排到核心 PDF pipeline 穩定之後。
```

---

# 提示詞 04：核心管線補強提示詞

```text
目前進度方向正確。請先不要進入 GUI 或 .exe 階段，請繼續強化核心 PDF pipeline。

請優先完成以下改進：

1. 強化 debug overlay：
   - 藍色：原始 text block bbox
   - 紅色：hard obstacles
   - 橘色：soft obstacles
   - 綠色：expanded bbox
   - 紫色：paragraph group bbox
   - 灰色：column boundary
   - 黑色：header/footer safe zone
   請不要全部只用紅色框，否則難以判斷問題來源。

2. 強化 DummyTranslator：
   請加入 dummy mode：
   - same
   - short
   - normal
   - long
   - stress

   讓 CLI 可以這樣使用：
   python run_cli.py input.pdf --debug --dummy-mode stress

3. 強化 text_fitter.py：
   請明確實作以下 fitting pipeline：
   - 原 bbox + 原字號 + 1.2 行高
   - 原 bbox + 原字號 + 壓縮行高
   - expanded bbox + 原字號 + 壓縮行高
   - expanded bbox + 降低字號 + 壓縮行高
   - overflow fallback

4. 請加入 fitting decision log。
   每個 block 至少記錄：
   - page number
   - block id
   - original bbox
   - expanded bbox
   - original font size
   - final font size
   - final line height
   - fitting strategy
   - overflow true/false

5. 請確認 overflow fallback 完整實作：
   - 主文尾端加入紅色 [+...]
   - overflow_manager 記錄完整譯文
   - PDF 最後新增「翻譯溢位附錄」
   - 附錄內容包含頁碼、block id、原文、完整譯文

6. 請新增或補強測試：
   - test_dummy_translator_modes.py
   - test_text_fitter_pipeline.py
   - test_overflow_appendix.py
   - test_debug_overlay.py

完成後請再給我下一份進度報告，並列出可以執行的 CLI 測試指令。
```

---

# 提示詞 05：GUI 與 PyInstaller 打包階段修正提示詞

```text
請針對「GUI 與打包階段」實作計畫，補上/修正以下所有項目，並逐條落實到程式與文件，以避免 Windows + PyInstaller + tkinter + PyMuPDF 常見翻車點。

【A. 開發流程與入口】
1. 不要用 main.py「取代」run_cli.py。
   - main.py = GUI 正式入口
   - run_cli.py = 保留做 regression / debug / CI 的 CLI 入口
   - README 需同時保留 GUI 與 CLI 使用方法。

【B. tkinter 背景執行緒】
2. tkinter UI 更新只能在主執行緒進行。
   - app_controller 必須使用 queue.Queue 傳遞 progress/log/overflow
   - GUI 必須使用 root.after() 週期性 poll queue 更新 UI
   - 禁止在 background thread 直接呼叫任何 tkinter widget。

【C. PyInstaller 資源路徑】
3. font_manager 必須支援 PyInstaller 資源路徑，尤其 onefile 模式。
   - 實作 resource_path()：
     - 開發模式：相對路徑 fonts/xxx.ttf
     - 打包模式：從 sys._MEIPASS/fonts/xxx.ttf 讀取
   - 若找不到字型，GUI 需顯示明確錯誤，不要默默輸出豆腐字 PDF。

【D. onedir → onefile 打包策略】
4. 打包先用 --onedir 驗證穩定後才嘗試 --onefile。
   - build_exe.bat 預設先跑 onedir
   - 驗證通過後可選 onefile，可做成另一個 bat：build_exe_onefile.bat。

【E. 打包後驗證項目】
5. 手動驗證流程要補上「字型與中文輸出」驗證：
   - exe 產出的 PDF 內中文是否正常顯示，不能是方塊
   - overflow appendix 的中文是否正常顯示
   - debug overlay 是否仍可輸出
   - output 檔名不得覆蓋原始 PDF，預設 original.zh-TW.pdf / original.zh-TW.debug.pdf。

【F. GUI 功能補強】
6. GUI 必須提供 Debug 模式與 Dummy 壓力測試模式：
   - checkbox：輸出除錯 PDF，等同 CLI 的 --debug
   - dropdown：Dummy mode，包含 same / short / normal / long / stress
   - 選 Dummy 時不需 API Key；選 OpenAI 時才顯示或要求 API Key。

7. 進度條定義清楚，建議以「頁」為單位：
   - 進度條：第 X / Y 頁
   - log 顯示本頁 block 數、overflow 數
   - GUI 不可凍結，需 thread + queue + after。

8. API Key 處理規範：
   - 預設僅存在記憶體 session
   - 若要保存需使用者勾選同意，寫入 .env，並確保 .env 在 .gitignore
   - GUI 不要把 key 寫進 log。

9. 完成後快捷操作：
   - 按鈕：開啟輸出 PDF
   - 按鈕：開啟輸出資料夾
   - 可選：按鈕開啟 log 檔。

【G. Debug overlay 顯示層】
10. Debug PDF 不要只畫一種紅框；請改成多層顏色以利定位：
   - 藍色：原始 text block bbox
   - 紅色：hard obstacles
   - 橘色：soft obstacles
   - 綠色：expanded bbox
   - 紫色：paragraph group bbox
   - 灰色：column boundaries
   - 黑色：header/footer safe zones

【H. 錯誤處理與紀錄】
11. 所有例外必須：
   - 顯示在 GUI，使用友善訊息
   - 寫入 log 檔，含 stack trace
   - 不可直接讓程式崩潰或 UI 卡死。

12. fitting decision log 必須保留：
   - page number, block id
   - original bbox, expanded bbox
   - original font size, final font size
   - line height
   - strategy
   - overflow true/false

【I. PyMuPDF + PyInstaller 兼容性備援】
13. 若打包後 exe 無法啟動或缺 DLL：
   - 先改用 onedir 再排查
   - spec 增加必要的 hiddenimports / binaries 收集策略
   - 在 README 加「打包疑難排解」章節。

【J. README 補充】
14. README 必須補上：
   - GUI 用法、CLI 用法
   - 字型放置與打包後字型來源說明
   - overflow appendix 行為說明，主文 [+...] + 附錄完整譯文
   - 常見問題：豆腐字、找不到字型、exe 無法啟動、PDF 太複雜導致 overflow 多等。

請依上述項目更新：

- app/gui.py
- app/app_controller.py
- main.py
- run_cli.py
- core/font_manager.py
- build/pyinstaller.spec
- build/build_exe.bat
- build/build_exe_onefile.bat
- README.md

完成後請提供：

1. GUI 介面欄位清單
2. 打包指令與產物位置
3. 打包後的驗證結果 checklist，包含中文、overflow、debug overlay
```

---

# 提示詞 06：如果排版仍失敗時的修正提示詞

```text
請修正目前 PDF 翻譯流程。

目前最大的問題是中文翻譯後仍然會爆出 bbox、重疊其他文字，或破壞雙欄論文排版。請不要只靠縮小字體，也不要把整頁文字合併翻譯。

請改成真正的 Layout-Aware Text Fitter：

1. 每個 paragraph/block 都必須保留原始 bbox。
2. 每頁必須建立 obstacle map。
3. obstacle map 至少包含其他文字 block、圖片、表格、公式、頁眉、頁腳、頁碼。
4. fit 文字前必須先檢查原 bbox 是否足夠。
5. 不足時，先壓縮行高，行高最低 1.05。
6. 行高壓縮仍不足時，計算安全擴張 bbox。
7. bbox 擴張不能跨欄、不能超出頁面、不能撞到 hard obstacles。
8. 擴張方式不要每 1px brute force，而是計算最近 obstacle 的距離。
9. 擴張後仍不足時，再縮小字號。
10. 字號不得低於 8pt 或 9pt。
11. 仍不足時，啟用 overflow fallback。
12. 主文尾端加入紅色 `[+...]`。
13. 完整譯文或剩餘譯文寫入 overflow_manager。
14. 最後在 PDF 末端新增「翻譯溢位附錄」。
15. 絕對不能讓任何中文文字蓋到圖片、表格、公式、其他段落或另一欄文字。

請直接修改：

- core/pdf_processor.py
- core/layout_analyzer.py
- core/paragraph_grouper.py
- core/obstacle_detector.py
- core/collision_detector.py
- core/bbox_expander.py
- core/text_fitter.py
- core/overflow_manager.py

請提供可執行的修正版程式碼。
```

---

# 建議開發流程

```text
Phase 1：專案骨架 + CLI + DummyTranslator
Phase 2：PDF text extraction + layout debug overlay
Phase 3：雙欄偵測 + paragraph grouping
Phase 4：obstacle map + collision detector + bbox expander
Phase 5：text fitter + overflow appendix
Phase 6：pdf_processor 整合輸出
Phase 7：GUI
Phase 8：OpenAI / DeepL
Phase 9：PyInstaller .exe
```

重點：

```text
不要太早進 GUI / OpenAI / exe。
先把 layout engine 測到穩。
```

---

# 測試指令建議

```bash
python run_cli.py samples/single_column.pdf --debug --dummy-mode normal
python run_cli.py samples/two_column.pdf --debug --dummy-mode normal
python run_cli.py samples/two_column_with_figures.pdf --debug --dummy-mode normal
python run_cli.py samples/two_column_with_figures.pdf --debug --dummy-mode stress
```

若要測 GUI：

```bash
python main.py
```

若要打包：

```bat
build\build_exe.bat
```

若要測 onefile：

```bat
build\build_exe_onefile.bat
```
