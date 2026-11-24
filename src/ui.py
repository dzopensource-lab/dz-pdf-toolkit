import json
import sys
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.pdf_engine import (
    get_pdf_page_count,
    merge_pdfs,
    split_pdf,
    rotate_pdf,
    optimize_and_protect_pdf,
)


def get_base_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


class HoverButton(tk.Button):
    def __init__(self, master, bg_color, hover_color, fg_color="#ffffff", **kwargs):
        super().__init__(
            master,
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            bd=0,
            relief="flat",
            cursor="hand2",
            **kwargs,
        )
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.bind("<Enter>", lambda e: self.configure(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.configure(bg=self.bg_color))


class DzPdfToolkitApp:
    LANG_MAP = {
        "🌐  Français": "fr",
        "🌐  العربية": "ar",
        "🌐  English": "en",
    }
    CODE_TO_LABEL = {v: k for k, v in LANG_MAP.items()}

    def __init__(self, root: tk.Tk):
        self.root = root
        self.base_path = get_base_path()
        self.current_lang = "fr"
        self.translations = self._load_translations()

        self.merge_files: list[str] = []
        self.split_file: str = ""
        self.split_total_pages: int = 0
        self.rotate_file: str = ""
        self.optimize_file: str = ""

        self.root.geometry("740x585")
        self.root.minsize(690, 550)
        self.root.configure(bg="#f1f5f9")
        icon_file = self.base_path / "assets" / "app_icon.ico"
        if icon_file.exists():
            try:
                self.root.iconbitmap(default=str(icon_file))
            except Exception:
                pass

        self._setup_styles()
        self._build_ui()
        self.apply_language("fr")

    def _load_translations(self) -> dict:
        data = {}
        for lang in ("fr", "ar", "en"):
            file_path = self.base_path / "locales" / f"{lang}.json"
            with open(file_path, "r", encoding="utf-8") as f:
                data[lang] = json.load(f)
        return data

    def t(self, key: str) -> str:
        return self.translations.get(self.current_lang, {}).get(key, key)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#f1f5f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#1e293b", font=("Segoe UI", 10))
        style.configure("FileTitle.TLabel", background="#f8fafc", foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 9))

        style.configure("TNotebook", background="#f1f5f9", borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure(
            "TNotebook.Tab",
            background="#e2e8f0",
            foreground="#475569",
            font=("Segoe UI", 9, "bold"),
            padding=[14, 9],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff")],
            foreground=[("selected", "#2563eb")],
        )
        style.configure("Lang.TCombobox", padding=5, font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        # 1. الشريط العلوي
        top_bar = tk.Frame(self.root, bg="#0f172a", height=58)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        title_box = tk.Frame(top_bar, bg="#0f172a")
        title_box.pack(side="left", padx=18)

        tk.Label(
            title_box, text="PDF", bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=7, pady=2
        ).pack(side="left", padx=(0, 10))

        self.lbl_header = tk.Label(
            title_box, text="", bg="#0f172a", fg="#f8fafc", font=("Segoe UI", 11, "bold")
        )
        self.lbl_header.pack(side="left")

        self.var_lang = tk.StringVar(value=self.CODE_TO_LABEL["fr"])
        self.combo_lang = ttk.Combobox(
            top_bar,
            textvariable=self.var_lang,
            values=list(self.LANG_MAP.keys()),
            state="readonly",
            width=14,
            style="Lang.TCombobox",
            cursor="hand2",
        )
        self.combo_lang.pack(side="right", padx=18)
        self.combo_lang.bind("<<ComboboxSelected>>", self._on_lang_selected)

        # 2. منطقة التبويبات الرئيسية
        main_container = tk.Frame(self.root, bg="#f1f5f9")
        main_container.pack(fill="both", expand=True, padx=16, pady=(14, 8))

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True)

        self.tab_merge = ttk.Frame(self.notebook, style="Card.TFrame", padding=18)
        self.tab_split = ttk.Frame(self.notebook, style="Card.TFrame", padding=18)
        self.tab_rotate = ttk.Frame(self.notebook, style="Card.TFrame", padding=18)
        self.tab_optimize = ttk.Frame(self.notebook, style="Card.TFrame", padding=18)
        self.tab_about = ttk.Frame(self.notebook, style="Card.TFrame", padding=18)

        self.notebook.add(self.tab_merge, text="")
        self.notebook.add(self.tab_split, text="")
        self.notebook.add(self.tab_rotate, text="")
        self.notebook.add(self.tab_optimize, text="")
        self.notebook.add(self.tab_about, text="")

        self._build_merge_tab()
        self._build_split_tab()
        self._build_rotate_tab()
        self._build_optimize_tab()
        self._build_about_tab()

        # 3. الشريط الإعلاني التعريفي الدائم للمطور (ظاهر في جميع الشاشات)
        promo_banner = tk.Frame(
            self.root, bg="#eff6ff", highlightbackground="#bfdbfe", highlightthickness=1, pady=8, padx=16
        )
        promo_banner.pack(fill="x", padx=16, pady=(0, 8))

        self.lbl_banner_dev = tk.Label(
            promo_banner, text="", bg="#eff6ff", fg="#1e3a8a", font=("Segoe UI", 9, "bold")
        )
        self.lbl_banner_dev.pack(side="left")

        links_box = tk.Frame(promo_banner, bg="#eff6ff")
        links_box.pack(side="right")

        lbl_gh_banner = tk.Label(
            links_box,
            text="github.com/dzopensource-lab",
            bg="#eff6ff",
            fg="#2563eb",
            font=("Segoe UI", 9, "bold underline"),
            cursor="hand2",
        )
        lbl_gh_banner.pack(side="left", padx=(0, 14))
        lbl_gh_banner.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/dzopensource-lab"))

        lbl_mail_banner = tk.Label(
            links_box,
            text="lionweb01@gmail.com",
            bg="#eff6ff",
            fg="#2563eb",
            font=("Segoe UI", 9, "bold underline"),
            cursor="hand2",
        )
        lbl_mail_banner.pack(side="left")
        lbl_mail_banner.bind("<Button-1>", lambda e: webbrowser.open("mailto:lionweb01@gmail.com"))

        # 4. شريط الحالة السفلي
        status_bar = tk.Frame(self.root, bg="#e2e8f0", height=26)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        tk.Label(
            status_bar,
            text="100% Offline  •  MIT Open Source  •  © Oussama Boudinar",
            bg="#e2e8f0",
            fg="#475569",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=16)

    def _build_merge_tab(self):
        self.merge_btn_row = tk.Frame(self.tab_merge, bg="#ffffff")
        self.merge_btn_row.pack(fill="x", pady=(0, 10))

        self.btn_add_files = HoverButton(
            self.merge_btn_row, bg_color="#dbeafe", hover_color="#bfdbfe", fg_color="#1e40af",
            font=("Segoe UI", 9, "bold"), padx=12, pady=6, command=self._on_add_merge_files
        )
        self.btn_move_up = HoverButton(
            self.merge_btn_row, bg_color="#e2e8f0", hover_color="#cbd5e1", fg_color="#0f172a",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, command=lambda: self._on_move_item(-1)
        )
        self.btn_move_down = HoverButton(
            self.merge_btn_row, bg_color="#e2e8f0", hover_color="#cbd5e1", fg_color="#0f172a",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, command=lambda: self._on_move_item(1)
        )
        self.btn_remove_item = HoverButton(
            self.merge_btn_row, bg_color="#fef3c7", hover_color="#fde68a", fg_color="#92400e",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, command=self._on_remove_selected
        )
        self.btn_clear_list = HoverButton(
            self.merge_btn_row, bg_color="#fee2e2", hover_color="#fecaca", fg_color="#991b1b",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, command=self._on_clear_merge_list
        )

        list_box_wrapper = tk.Frame(
            self.tab_merge, bg="#f8fafc", highlightbackground="#cbd5e1", highlightthickness=1
        )
        list_box_wrapper.pack(fill="both", expand=True, pady=(0, 12))

        scrollbar = ttk.Scrollbar(list_box_wrapper)
        scrollbar.pack(side="right", fill="y")

        self.listbox_merge = tk.Listbox(
            list_box_wrapper,
            bg="#f8fafc",
            fg="#1e293b",
            font=("Segoe UI", 10),
            bd=0,
            highlightthickness=0,
            selectbackground="#dbeafe",
            selectforeground="#1e40af",
            yscrollcommand=scrollbar.set,
        )
        self.listbox_merge.pack(fill="both", expand=True, padx=8, pady=8)
        scrollbar.config(command=self.listbox_merge.yview)

        self.btn_merge = HoverButton(
            self.tab_merge, bg_color="#2563eb", hover_color="#1d4ed8",
            font=("Segoe UI", 10, "bold"), pady=10, command=self._on_merge_save
        )
        self.btn_merge.pack(fill="x")

    def _build_split_tab(self):
        self.split_top_row = tk.Frame(self.tab_split, bg="#ffffff")
        self.split_top_row.pack(fill="x", pady=(0, 12))

        self.btn_select_split = HoverButton(
            self.split_top_row, bg_color="#e2e8f0", hover_color="#cbd5e1", fg_color="#0f172a",
            font=("Segoe UI", 9, "bold"), padx=14, pady=7, command=self._on_select_split_file
        )
        self.lbl_split_pages = ttk.Label(self.split_top_row, text="", style="Muted.TLabel")

        file_card = tk.Frame(self.tab_split, bg="#f8fafc", highlightbackground="#e2e8f0", highlightthickness=1, padx=12, pady=10)
        file_card.pack(fill="x", pady=(0, 20))

        self.lbl_split_file = ttk.Label(file_card, text="", style="FileTitle.TLabel")
        self.lbl_split_file.pack(fill="x")

        self.range_frame = tk.Frame(self.tab_split, bg="#ffffff")
        self.range_frame.pack(fill="x", pady=(0, 20))

        self.lbl_from_page = ttk.Label(self.range_frame, text="", font=("Segoe UI", 10, "bold"))
        self.var_from_page = tk.StringVar(value="1")
        self.entry_from = ttk.Entry(self.range_frame, textvariable=self.var_from_page, width=8, font=("Segoe UI", 11), justify="center")

        self.lbl_to_page = ttk.Label(self.range_frame, text="", font=("Segoe UI", 10, "bold"))
        self.var_to_page = tk.StringVar(value="1")
        self.entry_to = ttk.Entry(self.range_frame, textvariable=self.var_to_page, width=8, font=("Segoe UI", 11), justify="center")

        self.btn_split = HoverButton(
            self.tab_split, bg_color="#2563eb", hover_color="#1d4ed8",
            font=("Segoe UI", 10, "bold"), pady=10, command=self._on_split_save
        )
        self.btn_split.pack(fill="x", side="bottom")

    def _build_rotate_tab(self):
        self.rotate_top_row = tk.Frame(self.tab_rotate, bg="#ffffff")
        self.rotate_top_row.pack(fill="x", pady=(0, 12))

        self.btn_select_rotate = HoverButton(
            self.rotate_top_row, bg_color="#e2e8f0", hover_color="#cbd5e1", fg_color="#0f172a",
            font=("Segoe UI", 9, "bold"), padx=14, pady=7, command=self._on_select_rotate_file
        )

        file_card = tk.Frame(self.tab_rotate, bg="#f8fafc", highlightbackground="#e2e8f0", highlightthickness=1, padx=12, pady=10)
        file_card.pack(fill="x", pady=(0, 18))

        self.lbl_rotate_file = ttk.Label(file_card, text="", style="FileTitle.TLabel")
        self.lbl_rotate_file.pack(fill="x")

        self.lbl_rotate_angle = ttk.Label(self.tab_rotate, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_rotate_angle.pack(fill="x", pady=(0, 8))

        self.var_angle = tk.IntVar(value=90)
        self.rb_90 = tk.Radiobutton(self.tab_rotate, variable=self.var_angle, value=90, bg="#ffffff", activebackground="#ffffff", font=("Segoe UI", 10), cursor="hand2")
        self.rb_180 = tk.Radiobutton(self.tab_rotate, variable=self.var_angle, value=180, bg="#ffffff", activebackground="#ffffff", font=("Segoe UI", 10), cursor="hand2")
        self.rb_270 = tk.Radiobutton(self.tab_rotate, variable=self.var_angle, value=270, bg="#ffffff", activebackground="#ffffff", font=("Segoe UI", 10), cursor="hand2")

        self.rb_90.pack(anchor="w", pady=4)
        self.rb_180.pack(anchor="w", pady=4)
        self.rb_270.pack(anchor="w", pady=4)

        self.btn_rotate = HoverButton(
            self.tab_rotate, bg_color="#2563eb", hover_color="#1d4ed8",
            font=("Segoe UI", 10, "bold"), pady=10, command=self._on_rotate_save
        )
        self.btn_rotate.pack(fill="x", side="bottom")

    def _build_optimize_tab(self):
        self.opt_top_row = tk.Frame(self.tab_optimize, bg="#ffffff")
        self.opt_top_row.pack(fill="x", pady=(0, 12))

        self.btn_select_opt = HoverButton(
            self.opt_top_row, bg_color="#e2e8f0", hover_color="#cbd5e1", fg_color="#0f172a",
            font=("Segoe UI", 9, "bold"), padx=14, pady=7, command=self._on_select_opt_file
        )

        file_card = tk.Frame(self.tab_optimize, bg="#f8fafc", highlightbackground="#e2e8f0", highlightthickness=1, padx=12, pady=10)
        file_card.pack(fill="x", pady=(0, 18))

        self.lbl_opt_file = ttk.Label(file_card, text="", style="FileTitle.TLabel")
        self.lbl_opt_file.pack(fill="x")

        self.var_compress = tk.BooleanVar(value=True)
        self.chk_compress = tk.Checkbutton(
            self.tab_optimize, variable=self.var_compress, bg="#ffffff", activebackground="#ffffff",
            font=("Segoe UI", 10, "bold"), fg="#0f172a", cursor="hand2"
        )
        self.chk_compress.pack(anchor="w", pady=(0, 16))

        self.lbl_opt_pass = ttk.Label(self.tab_optimize, text="", font=("Segoe UI", 10))
        self.lbl_opt_pass.pack(fill="x", pady=(0, 6))

        self.var_opt_pass = tk.StringVar(value="")
        self.entry_opt_pass = ttk.Entry(self.tab_optimize, textvariable=self.var_opt_pass, width=32, font=("Segoe UI", 10), show="•")
        self.entry_opt_pass.pack(anchor="w")

        self.btn_optimize = HoverButton(
            self.tab_optimize, bg_color="#2563eb", hover_color="#1d4ed8",
            font=("Segoe UI", 10, "bold"), pady=10, command=self._on_optimize_save
        )
        self.btn_optimize.pack(fill="x", side="bottom")

    def _build_about_tab(self):
        info_card = tk.Frame(self.tab_about, bg="#f8fafc", highlightbackground="#e2e8f0", highlightthickness=1, padx=16, pady=12)
        info_card.pack(fill="x", pady=(0, 12))

        self.lbl_about_dev_title = ttk.Label(info_card, style="Muted.TLabel")
        self.lbl_about_dev_title.configure(background="#f8fafc")
        self.lbl_about_dev_title.pack(fill="x")

        self.lbl_dev_name = tk.Label(
            info_card, text="Oussama Boudinar", bg="#f8fafc", fg="#0f172a", font=("Segoe UI", 13, "bold")
        )
        self.lbl_dev_name.pack(fill="x", pady=(2, 8))

        self.lbl_about_gh_title = ttk.Label(info_card, style="Muted.TLabel")
        self.lbl_about_gh_title.configure(background="#f8fafc")
        self.lbl_about_gh_title.pack(fill="x")

        self.lbl_gh_link = tk.Label(
            info_card, text="https://github.com/dzopensource-lab", bg="#f8fafc", fg="#2563eb",
            font=("Segoe UI", 10, "underline"), cursor="hand2"
        )
        self.lbl_gh_link.pack(fill="x", pady=(2, 8))
        self.lbl_gh_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/dzopensource-lab"))

        self.lbl_about_email_title = ttk.Label(info_card, style="Muted.TLabel")
        self.lbl_about_email_title.configure(background="#f8fafc")
        self.lbl_about_email_title.pack(fill="x")

        self.lbl_email_link = tk.Label(
            info_card, text="lionweb01@gmail.com", bg="#f8fafc", fg="#2563eb",
            font=("Segoe UI", 10, "underline"), cursor="hand2"
        )
        self.lbl_email_link.pack(fill="x", pady=(2, 0))
        self.lbl_email_link.bind("<Button-1>", lambda e: webbrowser.open("mailto:lionweb01@gmail.com"))

        quote_box = tk.Frame(self.tab_about, bg="#eff6ff", highlightbackground="#bfdbfe", highlightthickness=1, padx=16, pady=10)
        quote_box.pack(fill="x", pady=(0, 10))

        self.lbl_quote = tk.Label(
            quote_box, text="", bg="#eff6ff", fg="#1e3a8a", font=("Segoe UI", 10, "italic"), wraplength=620
        )
        self.lbl_quote.pack(fill="x")

        self.lbl_license = ttk.Label(self.tab_about, style="Muted.TLabel", wraplength=640)
        self.lbl_license.pack(fill="x", side="bottom")

    def _on_lang_selected(self, event=None):
        lang_code = self.LANG_MAP.get(self.var_lang.get(), "fr")
        self.apply_language(lang_code)

    def apply_language(self, lang: str):
        self.current_lang = lang
        is_rtl = lang == "ar"
        side_primary = "right" if is_rtl else "left"
        side_secondary = "left" if is_rtl else "right"
        align = "e" if is_rtl else "w"
        justify = "right" if is_rtl else "left"

        self.root.title(self.t("app_title"))
        self.lbl_header.configure(text=self.t("app_title"))
        self.lbl_banner_dev.configure(text=self.t("banner_dev"))

        self.notebook.tab(0, text=self.t("tab_merge"))
        self.notebook.tab(1, text=self.t("tab_split"))
        self.notebook.tab(2, text=self.t("tab_rotate"))
        self.notebook.tab(3, text=self.t("tab_optimize"))
        self.notebook.tab(4, text=self.t("tab_about"))

        # تبويب الدمج
        for b in (self.btn_add_files, self.btn_move_up, self.btn_move_down, self.btn_remove_item, self.btn_clear_list):
            b.pack_forget()
        self.btn_add_files.configure(text=self.t("add_files"))
        self.btn_move_up.configure(text=self.t("move_up"))
        self.btn_move_down.configure(text=self.t("move_down"))
        self.btn_remove_item.configure(text=self.t("remove_selected"))
        self.btn_clear_list.configure(text=self.t("clear_list"))

        pad_main = (6, 0) if is_rtl else (0, 6)
        self.btn_add_files.pack(side=side_primary, padx=pad_main)
        self.btn_move_up.pack(side=side_primary, padx=pad_main)
        self.btn_move_down.pack(side=side_primary, padx=pad_main)
        self.btn_remove_item.pack(side=side_secondary, padx=(0, 6) if is_rtl else (6, 0))
        self.btn_clear_list.pack(side=side_secondary)
        self.btn_merge.configure(text=self.t("merge_btn"))

        # تبويب التقسيم
        self.btn_select_split.pack_forget()
        self.lbl_split_pages.pack_forget()
        self.btn_select_split.configure(text=self.t("select_pdf"))
        self.btn_select_split.pack(side=side_primary)
        self.lbl_split_pages.configure(
            text=self.t("page_count").format(count=self.split_total_pages) if self.split_file else ""
        )
        self.lbl_split_pages.pack(side=side_secondary)
        self.lbl_split_file.configure(
            text=Path(self.split_file).name if self.split_file else self.t("no_file_selected"), anchor=align
        )

        for w in (self.lbl_from_page, self.entry_from, self.lbl_to_page, self.entry_to):
            w.pack_forget()
        self.lbl_from_page.configure(text=self.t("from_page"))
        self.lbl_to_page.configure(text=self.t("to_page"))
        self.lbl_from_page.pack(side=side_primary, padx=(8, 0) if is_rtl else (0, 8))
        self.entry_from.pack(side=side_primary, padx=(24, 0) if is_rtl else (0, 24))
        self.lbl_to_page.pack(side=side_primary, padx=(8, 0) if is_rtl else (0, 8))
        self.entry_to.pack(side=side_primary)
        self.btn_split.configure(text=self.t("split_btn"))

        # تبويب التدوير
        self.btn_select_rotate.pack_forget()
        self.btn_select_rotate.configure(text=self.t("select_pdf"))
        self.btn_select_rotate.pack(side=side_primary)
        self.lbl_rotate_file.configure(
            text=Path(self.rotate_file).name if self.rotate_file else self.t("no_file_selected"), anchor=align
        )
        self.lbl_rotate_angle.configure(text=self.t("rotate_angle"), anchor=align)
        self.rb_90.configure(text=self.t("deg_90"))
        self.rb_180.configure(text=self.t("deg_180"))
        self.rb_270.configure(text=self.t("deg_270"))
        self.rb_90.pack_configure(anchor=align)
        self.rb_180.pack_configure(anchor=align)
        self.rb_270.pack_configure(anchor=align)
        self.btn_rotate.configure(text=self.t("rotate_btn"))

        # تبويب الضغط والحماية
        self.btn_select_opt.pack_forget()
        self.btn_select_opt.configure(text=self.t("select_pdf"))
        self.btn_select_opt.pack(side=side_primary)
        self.lbl_opt_file.configure(
            text=Path(self.optimize_file).name if self.optimize_file else self.t("no_file_selected"), anchor=align
        )
        self.chk_compress.configure(text=self.t("opt_compress_chk"))
        self.chk_compress.pack_configure(anchor=align)
        self.lbl_opt_pass.configure(text=self.t("opt_password_lbl"), anchor=align)
        self.entry_opt_pass.pack_configure(anchor=align)
        self.btn_optimize.configure(text=self.t("optimize_btn"))

        # تبويب الحقوق
        self.lbl_about_dev_title.configure(text=self.t("about_dev_label"), anchor=align)
        self.lbl_dev_name.configure(anchor=align)
        self.lbl_about_gh_title.configure(text=self.t("about_github_label"), anchor=align)
        self.lbl_gh_link.configure(anchor=align)
        self.lbl_about_email_title.configure(text=self.t("about_email_label"), anchor=align)
        self.lbl_email_link.configure(anchor=align)
        self.lbl_quote.configure(text=self.t("about_quote"), justify=justify, anchor=align)
        self.lbl_license.configure(text=self.t("about_license"), anchor=align)

    # --- أحداث الدمج والترتيب ---
    def _refresh_merge_listbox(self, select_idx: int | None = None):
        self.listbox_merge.delete(0, tk.END)
        for idx, f in enumerate(self.merge_files, start=1):
            self.listbox_merge.insert(tk.END, f"  {idx}.  📄  {Path(f).name}")
        if select_idx is not None and 0 <= select_idx < len(self.merge_files):
            self.listbox_merge.selection_set(select_idx)

    def _on_add_merge_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            self.merge_files.extend(files)
            self._refresh_merge_listbox()

    def _on_move_item(self, direction: int):
        sel = self.listbox_merge.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.merge_files):
            self.merge_files[idx], self.merge_files[new_idx] = self.merge_files[new_idx], self.merge_files[idx]
            self._refresh_merge_listbox(new_idx)

    def _on_remove_selected(self):
        sel = self.listbox_merge.curselection()
        if not sel:
            return
        idx = sel[0]
        self.merge_files.pop(idx)
        self._refresh_merge_listbox(min(idx, len(self.merge_files) - 1))

    def _on_clear_merge_list(self):
        self.merge_files.clear()
        self._refresh_merge_listbox()

    def _on_merge_save(self):
        if len(self.merge_files) < 2:
            messagebox.showwarning(self.t("error_title"), self.t("err_min_files"))
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], initialfile="merged.pdf")
        if not out:
            return
        try:
            merge_pdfs(self.merge_files, out)
            messagebox.showinfo(self.t("success_title"), self.t("success_msg").format(path=out))
        except Exception as exc:
            messagebox.showerror(self.t("error_title"), str(exc))

    # --- أحداث التقسيم ---
    def _on_select_split_file(self):
        f = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not f:
            return
        try:
            self.split_total_pages = get_pdf_page_count(f)
            self.split_file = f
            self.var_from_page.set("1")
            self.var_to_page.set(str(self.split_total_pages))
            self.apply_language(self.current_lang)
        except Exception as exc:
            messagebox.showerror(self.t("error_title"), str(exc))

    def _on_split_save(self):
        if not self.split_file:
            messagebox.showwarning(self.t("error_title"), self.t("err_no_file"))
            return
        try:
            start_p = int(self.var_from_page.get())
            end_p = int(self.var_to_page.get())
            if start_p < 1 or end_p > self.split_total_pages or start_p > end_p:
                raise ValueError()
        except ValueError:
            messagebox.showwarning(self.t("error_title"), self.t("err_invalid_range"))
            return

        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], initialfile="extracted.pdf")
        if not out:
            return
        try:
            split_pdf(self.split_file, start_p, end_p, out)
            messagebox.showinfo(self.t("success_title"), self.t("success_msg").format(path=out))
        except Exception as exc:
            messagebox.showerror(self.t("error_title"), str(exc))

    # --- أحداث التدوير ---
    def _on_select_rotate_file(self):
        f = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if f:
            self.rotate_file = f
            self.apply_language(self.current_lang)

    def _on_rotate_save(self):
        if not self.rotate_file:
            messagebox.showwarning(self.t("error_title"), self.t("err_no_file"))
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], initialfile="rotated.pdf")
        if not out:
            return
        try:
            rotate_pdf(self.rotate_file, self.var_angle.get(), out)
            messagebox.showinfo(self.t("success_title"), self.t("success_msg").format(path=out))
        except Exception as exc:
            messagebox.showerror(self.t("error_title"), str(exc))

    # --- أحداث الضغط والحماية ---
    def _on_select_opt_file(self):
        f = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if f:
            self.optimize_file = f
            self.apply_language(self.current_lang)

    def _on_optimize_save(self):
        if not self.optimize_file:
            messagebox.showwarning(self.t("error_title"), self.t("err_no_file"))
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], initialfile="optimized.pdf")
        if not out:
            return
        try:
            orig_kb, new_kb = optimize_and_protect_pdf(
                self.optimize_file, out, compress=self.var_compress.get(), password=self.var_opt_pass.get()
            )
            messagebox.showinfo(self.t("success_title"), self.t("opt_done_msg").format(orig=orig_kb, new=new_kb))
        except Exception as exc:
            messagebox.showerror(self.t("error_title"), str(exc))