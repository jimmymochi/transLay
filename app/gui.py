import os
import sys
import queue
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from utils.config_loader import load_config
from utils.logger import setup_logger
from app.app_controller import AppController

# 設置 CustomTkinter 預設外觀與配色
ctk.set_appearance_mode("System")  # System, Dark, Light
ctk.set_default_color_theme("blue") # Blue, Green, Dark-blue

class TranslatorGUI:
    """
    TramsLay PDF 翻譯器極簡現代風格 GUI 介面。
    基於 CustomTkinter 重構，支援自適應深色/淺色主題，具備精美圓角卡片與無阻塞背景執行緒輪詢。
    """
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("TramsLay - 論文排版還原 PDF 翻譯器")
        self.root.geometry("840x740")
        self.root.minsize(800, 680)
        
        # 載入組態
        self.config = load_config()
        
        # 建立 UI 專屬通訊 Queue 與 Controller
        self.ui_queue = queue.Queue()
        self.controller = AppController(self.ui_queue)
        
        # 保存暫存輸出檔案路徑，用於快捷開啟
        self.out_pdf_path = None
        self.out_dir_path = None
        
        # 初始化 UI 變數與元件
        self._setup_variables()
        self._create_widgets()
        
        # 啟動 Queue 輪詢監聽 (每 100ms 檢查一次)
        self.root.after(100, self._poll_queue)

    def _setup_variables(self):
        """
        初始化 UI 變數
        """
        self.var_input_pdf = tk.StringVar(value="")
        self.var_output_dir = tk.StringVar(value="")
        
        # 預設翻譯服務
        default_trans = self.config.get("default_translator", "google")
        self.var_translator = tk.StringVar(value=default_trans)
        
        # 各翻譯服務的 API Key / 設定變數
        self.var_openai_key = tk.StringVar(value=self.config.get("openai", {}).get("api_key", ""))
        self.var_openai_model = tk.StringVar(value=self.config.get("openai", {}).get("model", "gpt-4o-mini"))
        self.var_deepl_key = tk.StringVar(value=self.config.get("deepl", {}).get("api_key", ""))
        self.var_gemini_key = tk.StringVar(value=self.config.get("gemini", {}).get("api_key", ""))
        self.var_gemini_model = tk.StringVar(value=self.config.get("gemini", {}).get("model", "gemini-1.5-flash"))
        
        self.var_dummy_mode = tk.StringVar(value="normal")
        self.var_debug_mode = tk.BooleanVar(value=False)
        self.var_ocr_mode = tk.BooleanVar(value=False)
        
        # API Key 密文顯示切換
        self.var_show_keys = tk.BooleanVar(value=False)
        
        # 進度狀態與溢位資訊
        self.var_progress_pct = tk.DoubleVar(value=0.0)
        self.var_progress_txt = tk.StringVar(value="狀態：等待任務啟動...")
        self.var_overflow_cnt = tk.StringVar(value="已偵測溢位段落: 0")

    def _create_widgets(self):
        """
        建立精美的 CustomTkinter 元件版面
        """
        # =========================================================================
        # 1. 頂部 Banner 區
        # =========================================================================
        banner = ctk.CTkFrame(self.root, corner_radius=0, height=75, fg_color=("#2C3E50", "#0F172A"))
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)
        
        title_lbl = ctk.CTkLabel(
            banner, 
            text="TramsLay PDF 論文排版還原翻譯系統", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=18, weight="bold"), 
            text_color="white"
        )
        title_lbl.pack(side="left", pady=15, padx=25)
        
        # 主題風格切換下拉選單 (極具現代質感)
        theme_menu = ctk.CTkOptionMenu(
            banner, 
            values=["System", "Dark", "Light"],
            command=self._change_appearance_mode,
            width=100
        )
        theme_menu.pack(side="right", pady=15, padx=25)
        theme_menu.set("System")

        # 主體內容卡片滾動區
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=25, pady=20)

        # =========================================================================
        # 2. 檔案選取區卡片 (Input / Output Paths)
        # =========================================================================
        path_card = ctk.CTkFrame(main_container)
        path_card.pack(fill="x", pady=(0, 15), ipady=5)
        
        card_title = ctk.CTkLabel(
            path_card, 
            text="📁 檔案與輸出路徑設定", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
            text_color=("#34495E", "#3498DB")
        )
        card_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        inner_path_frame = ctk.CTkFrame(path_card, fg_color="transparent")
        inner_path_frame.pack(fill="x", padx=15, pady=5)
        
        # 來源 PDF
        lbl_in = ctk.CTkLabel(inner_path_frame, text="來源 PDF:")
        lbl_in.grid(row=0, column=0, sticky="w", pady=6, padx=(0, 10))
        self.ent_in = ctk.CTkEntry(inner_path_frame, textvariable=self.var_input_pdf, placeholder_text="請點選右側瀏覽按鈕選擇英文 PDF 論文...", width=450)
        self.ent_in.grid(row=0, column=1, pady=6, padx=5, sticky="ew")
        btn_browse_in = ctk.CTkButton(inner_path_frame, text="選擇檔案", width=90, command=self._browse_input_pdf)
        btn_browse_in.grid(row=0, column=2, pady=6, padx=(10, 0))
        
        # 輸出目錄
        lbl_out = ctk.CTkLabel(inner_path_frame, text="輸出目錄:")
        lbl_out.grid(row=1, column=0, sticky="w", pady=6, padx=(0, 10))
        self.ent_out = ctk.CTkEntry(inner_path_frame, textvariable=self.var_output_dir, placeholder_text="預設存放於來源檔案同資料夾...", width=450)
        self.ent_out.grid(row=1, column=1, pady=6, padx=5, sticky="ew")
        btn_browse_out = ctk.CTkButton(inner_path_frame, text="選擇目錄", width=90, command=self._browse_output_dir)
        btn_browse_out.grid(row=1, column=2, pady=6, padx=(10, 0))
        
        inner_path_frame.columnconfigure(1, weight=1)

        # =========================================================================
        # 3. 翻譯與參數設定卡片
        # =========================================================================
        settings_card = ctk.CTkFrame(main_container)
        settings_card.pack(fill="x", pady=(0, 15), ipady=5)
        
        card_title_2 = ctk.CTkLabel(
            settings_card, 
            text="⚙️ 翻譯服務與排版演算法設定", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
            text_color=("#34495E", "#3498DB")
        )
        card_title_2.pack(anchor="w", padx=15, pady=(10, 5))
        
        top_settings_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        top_settings_frame.pack(fill="x", padx=15, pady=5)
        
        # 選擇翻譯器
        ctk.CTkLabel(top_settings_frame, text="翻譯服務提供商:").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.cbo_trans = ctk.CTkOptionMenu(
            top_settings_frame, 
            variable=self.var_translator,
            values=["gemini", "google", "openai", "deepl", "dummy"],
            command=self._on_translator_change,
            width=130
        )
        self.cbo_trans.grid(row=0, column=1, pady=5, padx=5, sticky="w")
        
        # 密碼明文切換
        self.chk_show = ctk.CTkCheckBox(
            top_settings_frame, 
            text="顯示 API 金鑰", 
            variable=self.var_show_keys, 
            command=self._toggle_key_visibility
        )
        self.chk_show.grid(row=0, column=2, pady=5, padx=25, sticky="w")

        # ---------------- 翻譯商專屬動態配置面板 ----------------
        self.config_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        self.config_frame.pack(fill="x", padx=15, pady=8)
        self.config_frame.columnconfigure(1, weight=1)
        
        # 初次載入渲染
        self._on_translator_change(self.var_translator.get())

        # ---------------- 排版參數與除錯選項 ----------------
        opt_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        opt_frame.pack(fill="x", padx=15, pady=5)
        
        chk_debug = ctk.CTkCheckBox(opt_frame, text="啟用除錯模式 (同步繪製多色邊界框 PDF)", variable=self.var_debug_mode)
        chk_debug.pack(side="left", padx=(0, 30))
        
        chk_ocr = ctk.CTkCheckBox(opt_frame, text="啟用 OCR 圖層預先分析", variable=self.var_ocr_mode)
        chk_ocr.pack(side="left")

        # =========================================================================
        # 4. 控制按鈕與快捷捷徑
        # =========================================================================
        control_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0, 15))
        
        self.btn_start = ctk.CTkButton(
            control_frame, 
            text="🚀 啟動翻譯管線", 
            font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold"),
            command=self._start_translation,
            fg_color=("#3498DB", "#1F9FFB"),
            hover_color=("#2980B9", "#0086E6"),
            height=36,
            width=160
        )
        self.btn_start.pack(side="left", padx=(0, 20))
        
        # 快捷開啟面板 (預設隱藏)
        self.shortcut_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        self.shortcut_frame.pack(side="left", fill="x")
        
        self.btn_open_pdf = ctk.CTkButton(
            self.shortcut_frame, 
            text="📖 開啟譯文 PDF", 
            command=self._open_result_pdf,
            fg_color="#2C3E50",
            hover_color="#34495E",
            height=36
        )
        self.btn_open_pdf.pack(side="left", padx=5)
        
        self.btn_open_folder = ctk.CTkButton(
            self.shortcut_frame, 
            text="📂 開啟存放夾", 
            command=self._open_result_folder,
            fg_color="#2C3E50",
            hover_color="#34495E",
            height=36
        )
        self.btn_open_folder.pack(side="left", padx=5)
        
        self.shortcut_frame.pack_forget()

        # =========================================================================
        # 5. 即時進度與日誌 Scrolled Text CTkTextbox
        # =========================================================================
        progress_card = ctk.CTkFrame(main_container)
        progress_card.pack(fill="both", expand=True)
        
        prog_info_frame = ctk.CTkFrame(progress_card, fg_color="transparent")
        prog_info_frame.pack(fill="x", padx=15, pady=(8, 4))
        
        lbl_prog_txt = ctk.CTkLabel(prog_info_frame, textvariable=self.var_progress_txt, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"))
        lbl_prog_txt.pack(side="left")
        
        lbl_overflow = ctk.CTkLabel(prog_info_frame, textvariable=self.var_overflow_cnt, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color="#E74C3C")
        lbl_overflow.pack(side="right")
        
        # 進度列
        self.prog_bar = ctk.CTkProgressBar(progress_card)
        self.prog_bar.pack(fill="x", padx=15, pady=(0, 10))
        self.prog_bar.set(0.0)
        
        # 日誌終端
        self.txt_log = ctk.CTkTextbox(
            progress_card, 
            font=ctk.CTkFont(family="Consolas", size=11), 
            fg_color=("#1E1E1E", "#111111"), 
            text_color="#D4D4D4",
            corner_radius=6
        )
        self.txt_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.txt_log.configure(state="disabled")

    def _change_appearance_mode(self, new_appearance_mode: str):
        """
        一鍵切換深色/淺色外觀
        """
        ctk.set_appearance_mode(new_appearance_mode)

    def _on_translator_change(self, selected_trans: str):
        """
        切換翻譯器時，動態渲染專屬設定面板
        """
        # 清除舊面板元件
        for widget in self.config_frame.winfo_children():
            widget.destroy()
            
        trans = selected_trans.lower()
        
        if trans == "gemini":
            ctk.CTkLabel(self.config_frame, text="Gemini API Key:").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
            self.ent_gemini_key = ctk.CTkEntry(
                self.config_frame, 
                textvariable=self.var_gemini_key, 
                width=350, 
                show="" if self.var_show_keys.get() else "*"
            )
            self.ent_gemini_key.grid(row=0, column=1, columnspan=2, sticky="w", pady=4, padx=5)
            
            ctk.CTkLabel(self.config_frame, text="模型選擇:").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 10))
            cbo_model = ctk.CTkOptionMenu(
                self.config_frame, 
                variable=self.var_gemini_model, 
                values=["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-pro-exp"],
                width=160
            )
            cbo_model.grid(row=1, column=1, sticky="w", pady=4, padx=5)
            
        elif trans == "openai":
            ctk.CTkLabel(self.config_frame, text="OpenAI API Key:").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
            self.ent_openai_key = ctk.CTkEntry(
                self.config_frame, 
                textvariable=self.var_openai_key, 
                width=350, 
                show="" if self.var_show_keys.get() else "*"
            )
            self.ent_openai_key.grid(row=0, column=1, columnspan=2, sticky="w", pady=4, padx=5)
            
            ctk.CTkLabel(self.config_frame, text="模型選擇:").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 10))
            cbo_model = ctk.CTkOptionMenu(
                self.config_frame, 
                variable=self.var_openai_model, 
                values=["gpt-4o-mini", "gpt-4o", "o1-mini"],
                width=130
            )
            cbo_model.grid(row=1, column=1, sticky="w", pady=4, padx=5)
            
        elif trans == "deepl":
            ctk.CTkLabel(self.config_frame, text="DeepL API Key:").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
            self.ent_deepl_key = ctk.CTkEntry(
                self.config_frame, 
                textvariable=self.var_deepl_key, 
                width=350, 
                show="" if self.var_show_keys.get() else "*"
            )
            self.ent_deepl_key.grid(row=0, column=1, columnspan=2, sticky="w", pady=4, padx=5)
            
        elif trans == "dummy":
            ctk.CTkLabel(self.config_frame, text="Dummy 測試模式:").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
            cbo_dummy = ctk.CTkOptionMenu(
                self.config_frame, 
                variable=self.var_dummy_mode, 
                values=["same", "short", "normal", "long", "stress"],
                width=110
            )
            cbo_dummy.grid(row=0, column=1, sticky="w", pady=4, padx=5)
            
            ctk.CTkLabel(
                self.config_frame, 
                text="💡 壓力測試 (stress) 模式下會保證觸發 bbox 安全擴張與溢位附錄", 
                font=ctk.CTkFont(family="Microsoft JhengHei", size=11),
                text_color="#7F8C8D"
            ).grid(row=0, column=2, sticky="w", pady=4, padx=15)
            
        else:
            # Google 翻譯免 Key
            ctk.CTkLabel(
                self.config_frame, 
                text="✨ Google 翻譯免配置 API Key，開箱即刻極速翻譯！", 
                font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
                text_color="#2980B9"
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=6, padx=5)

    def _toggle_key_visibility(self):
        """
        密碼明暗文切換
        """
        show_char = "" if self.var_show_keys.get() else "*"
        trans = self.var_translator.get()
        if trans == "gemini" and hasattr(self, "ent_gemini_key"):
            self.ent_gemini_key.configure(show=show_char)
        elif trans == "openai" and hasattr(self, "ent_openai_key"):
            self.ent_openai_key.configure(show=show_char)
        elif trans == "deepl" and hasattr(self, "ent_deepl_key"):
            self.ent_deepl_key.configure(show=show_char)

    def _browse_input_pdf(self):
        file_path = filedialog.askopenfilename(
            title="請選擇要翻譯的英文 PDF 檔案",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            self.var_input_pdf.set(file_path)
            if not self.var_output_dir.get():
                self.var_output_dir.set(os.path.dirname(file_path))

    def _browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="請選擇譯文 PDF 輸出存放目錄")
        if dir_path:
            self.var_output_dir.set(dir_path)

    def _write_log(self, message):
        """
        將日誌添加至現代化 CTkTextbox 中並滾動到底部
        """
        self.txt_log.configure(state="normal")
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state="disabled")

    def _start_translation(self):
        """
        進行必填欄位安全性檢查，並呼叫控制器啟動背景執行緒
        """
        input_pdf = self.var_input_pdf.get().strip()
        output_dir = self.var_output_dir.get().strip()
        translator_name = self.var_translator.get()
        
        if not input_pdf:
            messagebox.showerror("欄位缺失", "請先選擇輸入英文 PDF 檔案！")
            return
        if not os.path.exists(input_pdf):
            messagebox.showerror("檔案不存在", f"找不到指定輸入檔案: {input_pdf}")
            return
        if not output_dir:
            output_dir = os.path.dirname(input_pdf)
            self.var_output_dir.set(output_dir)

        # 打包組態
        run_config = self.config.copy()
        if "gemini" not in run_config: run_config["gemini"] = {}
        if "openai" not in run_config: run_config["openai"] = {}
        if "deepl" not in run_config: run_config["deepl"] = {}
        
        if translator_name == "gemini":
            api_key = self.var_gemini_key.get().strip()
            if not api_key:
                messagebox.showerror("金鑰缺失", "選用 Gemini 翻譯時，API Key 欄位不可空白！")
                return
            run_config["gemini"]["api_key"] = api_key
            run_config["gemini"]["model"] = self.var_gemini_model.get()
            
        elif translator_name == "openai":
            api_key = self.var_openai_key.get().strip()
            if not api_key:
                messagebox.showerror("金鑰缺失", "選用 OpenAI 翻譯時，API Key 欄位不可空白！")
                return
            run_config["openai"]["api_key"] = api_key
            run_config["openai"]["model"] = self.var_openai_model.get()
            
        elif translator_name == "deepl":
            api_key = self.var_deepl_key.get().strip()
            if not api_key:
                messagebox.showerror("金鑰缺失", "選用 DeepL 翻譯時，API Key 欄位不可空白！")
                return
            run_config["deepl"]["api_key"] = api_key

        # 重設狀態
        self.prog_bar.set(0.0)
        self.var_progress_txt.set("狀態：初始化翻譯管線...")
        self.var_overflow_cnt.set("已偵測溢位段落: 0")
        
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.configure(state="disabled")
        
        self.shortcut_frame.pack_forget()
        self.out_pdf_path = None
        self.out_dir_path = None
        
        # 停用啟動按鈕
        self.btn_start.configure(state="disabled")
        
        # 背景啟動
        self.controller.start_translation(
            input_pdf=input_pdf,
            output_dir=output_dir,
            translator_name=translator_name,
            dummy_mode=self.var_dummy_mode.get(),
            debug_mode=self.var_debug_mode.get(),
            config=run_config
        )
        self._write_log(">>> 背景翻譯工作線啟動成功，GUI 將維持順暢響應...")

    def _poll_queue(self):
        """
        核心 Queue 輪詢處理器，週期性安全更新 UI
        """
        for _ in range(25):
            try:
                msg = self.ui_queue.get_nowait()
            except queue.Empty:
                break
                
            # 1. 優先檢查是否為純文字日誌 (包含 logger 拋出的 str)，防止 str 呼叫 .get() 導致 AttributeError 崩潰
            if isinstance(msg, str):
                self._write_log(msg)
                self.ui_queue.task_done()
                continue
                
            # 2. 安全防護：若非字典格式，跳過處理防止異常
            if not isinstance(msg, dict):
                self.ui_queue.task_done()
                continue
                
            msg_type = msg.get("type")
            
            if msg_type == "progress":
                curr = msg.get("current", 0)
                total = msg.get("total", 0)
                log_msg = msg.get("msg", "")
                overflow = msg.get("overflow", 0)
                
                pct = (curr / total) if total > 0 else 0.0
                self.prog_bar.set(pct)
                self.var_progress_txt.set(f"狀態：正在翻譯第 {curr} / {total} 頁")
                self.var_overflow_cnt.set(f"已偵測溢位段落: {overflow}")
                
            elif msg_type == "success":
                self.out_pdf_path = msg.get("out_pdf")
                self.out_dir_path = os.path.dirname(self.out_pdf_path) if self.out_pdf_path else None
                
                self.prog_bar.set(1.0)
                self.var_progress_txt.set("狀態：翻譯任務成功完成！")
                
                self._write_log("\n=== 🎉 翻譯工作成功結束 ===")
                self._write_log(f"譯文 PDF 已生成: {self.out_pdf_path}")
                if msg.get("db_pdf"):
                    self._write_log(f"除錯 PDF 已生成: {msg.get('db_pdf')}")
                    
                self.shortcut_frame.pack(side="left", padx=5)
                messagebox.showinfo("成功", "PDF 論文翻譯任務已順利完成！")
                
            elif msg_type == "error":
                err_msg = msg.get("message", "未知錯誤")
                details = msg.get("details", "")
                
                self.var_progress_txt.set("狀態：任務失敗")
                self._write_log(f"\n❌ [嚴重錯誤] {err_msg}")
                if details:
                    self._write_log(details)
                messagebox.showerror("錯誤", f"翻譯管線發生嚴重錯誤:\n{err_msg}")
                
            elif msg_type == "finished":
                self.btn_start.configure(state="normal")
                
            self.ui_queue.task_done()
            
        self.root.after(100, self._poll_queue)

    def _open_result_pdf(self):
        if self.out_pdf_path and os.path.exists(self.out_pdf_path):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(self.out_pdf_path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{self.out_pdf_path}"')
                else:
                    os.system(f'xdg-open "{self.out_pdf_path}"')
            except Exception as e:
                messagebox.showerror("錯誤", f"無法開啟 PDF 檔案: {e}")
        else:
            messagebox.showerror("錯誤", "找不到譯文 PDF 檔案！")

    def _open_result_folder(self):
        if self.out_dir_path and os.path.exists(self.out_dir_path):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(self.out_dir_path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{self.out_dir_path}"')
                else:
                    os.system(f'xdg-open "{self.out_dir_path}"')
            except Exception as e:
                messagebox.showerror("錯誤", f"無法開啟資料夾: {e}")
        else:
            messagebox.showerror("錯誤", "找不到輸出目錄！")
