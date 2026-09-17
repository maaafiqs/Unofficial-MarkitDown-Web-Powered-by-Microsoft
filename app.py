import os
import sys
import time
import warnings
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# Sembunyikan peringatan pydub / ffmpeg jika ada
warnings.filterwarnings("ignore")

import customtkinter as ctk

# Cek dukungan Drag & Drop
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    class BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
    HAS_DND = True
except Exception as e:
    class BaseWindow(ctk.CTk):
        pass
    HAS_DND = False

from markitdown import MarkItDown

# Konfigurasi Tema CustomTkinter
ctk.set_appearance_mode("Dark")  # Pilihan: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

def format_file_size(bytes_size: int) -> str:
    """Format ukuran file dalam satuan byte ke KB/MB yang mudah dibaca."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"

def fast_convert_document(engine: MarkItDown, file_path: str) -> str:
    """Konversi dokumen dengan akselerasi C++ PDFium untuk file PDF agar secepat kilat."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        try:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(file_path)
            pages_text = []
            total_pages = len(doc)
            for i, page in enumerate(doc):
                textpage = page.get_textpage()
                raw_text = textpage.get_text_range()
                text = raw_text.strip() if raw_text else ""
                if text:
                    if total_pages > 1:
                        pages_text.append(f"## Halaman {i + 1}\n\n{text}")
                    else:
                        pages_text.append(text)
            result_text = "\n\n---\n\n".join(pages_text)
            if result_text.strip():
                return result_text
        except Exception:
            pass

    res = engine.convert(file_path)
    return res.text_content or ""


class MarkItDownDesktopApp(BaseWindow):
    def __init__(self):
        super().__init__()

        # Konfigurasi Jendela Utama
        self.title("MarkItDown Studio - Microsoft Document to Markdown")
        self.geometry("1100x740")
        self.minsize(920, 620)

        # Inisialisasi engine MarkItDown
        self.md_engine = MarkItDown()

        # State Aplikasi
        self.selected_file_path = None
        self.last_saved_output_path = None
        self.batch_files_list = []
        self.is_converting = False

        # Bangun Komponen Antarmuka
        self._create_header()
        self._create_main_tabs()
        self._create_statusbar()

    def _create_header(self):
        """Header atas dengan judul, branding, dan tombol pengubah tema."""
        header_frame = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color=("gray88", "#181824"))
        header_frame.pack(fill="x", side="top", padx=0, pady=0)

        # Bagian Kiri: Judul & Subjudul
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=10)

        main_title = ctk.CTkLabel(
            title_box,
            text="📑 MarkItDown Desktop Studio",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        main_title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Powered by Microsoft MarkItDown | Konversi Dokumen Cepat ke Markdown",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        subtitle.pack(anchor="w")

        # Bagian Kanan: Pemilih Tema & Bantuan
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right", padx=20, pady=10)

        self.theme_switch = ctk.CTkOptionMenu(
            right_box,
            values=["Dark", "Light", "System"],
            command=self._change_theme,
            width=105,
            height=30
        )
        self.theme_switch.set("Dark")
        self.theme_switch.pack(side="right", padx=5)

        theme_lbl = ctk.CTkLabel(right_box, text="Tema:", font=ctk.CTkFont(size=12))
        theme_lbl.pack(side="right", padx=5)

    def _change_theme(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)

    def _create_main_tabs(self):
        """Membuat Tabview untuk Konversi Tunggal, Konversi Batch, dan Info Format."""
        self.tabview = ctk.CTkTabview(self, corner_radius=8)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 5))

        self.tab_single = self.tabview.add("📄 Konversi File Tunggal")
        self.tab_batch = self.tabview.add("📚 Konversi Banyak File (Batch)")
        self.tab_about = self.tabview.add("ℹ️ Format & Panduan")

        self._setup_single_tab()
        self._setup_batch_tab()
        self._setup_about_tab()

    # ==========================================
    # TAB 1: KONVERSI FILE TUNGGAL
    # ==========================================
    def _setup_single_tab(self):
        # Layout 2 Kolom: Kiri (Input & Opsi) | Kanan (Editor & Preview Hasil)
        self.tab_single.grid_columnconfigure(0, weight=4, minsize=360)
        self.tab_single.grid_columnconfigure(1, weight=6)
        self.tab_single.grid_rowconfigure(0, weight=1)

        # --- PANEL KIRI ---
        left_panel = ctk.CTkFrame(self.tab_single, corner_radius=10)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        left_panel.grid_rowconfigure(4, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Area Drop Zone / Drag and Drop
        self.drop_zone = ctk.CTkFrame(
            left_panel,
            corner_radius=10,
            border_width=2,
            border_color=("#3B8ED0", "#1f6aa5"),
            fg_color=("gray92", "#1f2335")
        )
        self.drop_zone.pack(fill="x", padx=15, pady=(15, 10))

        drop_icon = ctk.CTkLabel(
            self.drop_zone,
            text="📥",
            font=ctk.CTkFont(size=38)
        )
        drop_icon.pack(pady=(15, 2))

        drop_title = ctk.CTkLabel(
            self.drop_zone,
            text="Tarik & Lepas File ke Sini",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        drop_title.pack(pady=(0, 2))

        drop_sub = ctk.CTkLabel(
            self.drop_zone,
            text="DOCX, PDF, PPTX, XLSX, HTML, CSV, TXT, dll.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60")
        )
        drop_sub.pack(pady=(0, 10))

        btn_select = ctk.CTkButton(
            self.drop_zone,
            text="📂 Pilih File dari Komputer",
            command=self._select_single_file,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=34
        )
        btn_select.pack(pady=(0, 15), padx=20, fill="x")

        # Aktifkan Drag and Drop jika didukung
        if HAS_DND:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind('<<Drop>>', self._on_single_file_drop)
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_single_file_drop)

        # Card Info File Terpilih
        self.file_info_frame = ctk.CTkFrame(left_panel, corner_radius=8, fg_color=("gray85", "#24283b"))
        self.file_info_frame.pack(fill="x", padx=15, pady=5)

        self.lbl_file_name = ctk.CTkLabel(
            self.file_info_frame,
            text="Belum ada file yang dipilih",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=310
        )
        self.lbl_file_name.pack(fill="x", padx=12, pady=(10, 2))

        self.lbl_file_meta = ctk.CTkLabel(
            self.file_info_frame,
            text="Pilih atau seret file dokumen untuk memulai.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
            anchor="w"
        )
        self.lbl_file_meta.pack(fill="x", padx=12, pady=(0, 10))

        # Opsi Konversi
        options_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        options_box.pack(fill="x", padx=15, pady=5)

        self.var_autosave = tk.BooleanVar(value=True)
        self.chk_autosave = ctk.CTkCheckBox(
            options_box,
            text="Simpan file .md otomatis di folder file asal",
            variable=self.var_autosave,
            font=ctk.CTkFont(size=12)
        )
        self.chk_autosave.pack(anchor="w", pady=4)

        self.var_autocopy = tk.BooleanVar(value=False)
        self.chk_autocopy = ctk.CTkCheckBox(
            options_box,
            text="Salin otomatis ke clipboard setelah selesai",
            variable=self.var_autocopy,
            font=ctk.CTkFont(size=12)
        )
        self.chk_autocopy.pack(anchor="w", pady=4)

        # Progress Bar & Tombol Konversi
        action_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        action_box.pack(fill="x", side="bottom", padx=15, pady=15)

        self.progress_single = ctk.CTkProgressBar(action_box, mode="indeterminate", height=10)
        self.progress_single.pack(fill="x", pady=(0, 10))
        self.progress_single.set(0)

        self.btn_convert_single = ctk.CTkButton(
            action_box,
            text="⚡ Konversi ke Markdown Sekarang",
            command=self._start_single_conversion,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        self.btn_convert_single.pack(fill="x", pady=(0, 6))

        btn_clear = ctk.CTkButton(
            action_box,
            text="Bersihkan / Reset",
            command=self._clear_single_tab,
            height=28,
            fg_color=("gray75", "#32364a"),
            hover_color=("gray65", "#414868")
        )
        btn_clear.pack(fill="x")

        # --- PANEL KANAN (PREVIEW & EDITOR) ---
        right_panel = ctk.CTkFrame(self.tab_single, corner_radius=10)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=5)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Toolbar Preview Atas
        toolbar = ctk.CTkFrame(right_panel, height=45, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        lbl_preview_title = ctk.CTkLabel(
            toolbar,
            text="📝 Hasil Markdown",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_preview_title.pack(side="left", padx=(0, 10))

        self.lbl_stats = ctk.CTkLabel(
            toolbar,
            text="0 karakter | 0 baris",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65")
        )
        self.lbl_stats.pack(side="left", padx=5)

        self.btn_open_folder = ctk.CTkButton(
            toolbar,
            text="📂 Buka Lokasi",
            command=self._open_output_folder,
            width=100,
            height=30,
            state="disabled"
        )
        self.btn_open_folder.pack(side="right", padx=(5, 0))

        self.btn_save_as = ctk.CTkButton(
            toolbar,
            text="💾 Simpan Markdown (.md)",
            command=self._save_markdown_as,
            width=165,
            height=30,
            state="disabled"
        )
        self.btn_save_as.pack(side="right", padx=5)

        self.btn_copy = ctk.CTkButton(
            toolbar,
            text="📋 Salin Teks",
            command=self._copy_to_clipboard,
            width=95,
            height=30,
            state="disabled"
        )
        self.btn_copy.pack(side="right", padx=5)

        # Area Teks Markdown
        self.txt_markdown = ctk.CTkTextbox(
            right_panel,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=8
        )
        self.txt_markdown.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.txt_markdown.bind("<KeyRelease>", self._update_text_stats)

    def _select_single_file(self):
        filetypes = [
            ("Semua File yang Didukung", "*.docx;*.pdf;*.pptx;*.xlsx;*.xls;*.html;*.htm;*.csv;*.tsv;*.txt;*.json;*.xml;*.zip;*.wav;*.mp3"),
            ("Microsoft Word (*.docx)", "*.docx"),
            ("Dokumen PDF (*.pdf)", "*.pdf"),
            ("Microsoft PowerPoint (*.pptx)", "*.pptx"),
            ("Microsoft Excel (*.xlsx, *.xls)", "*.xlsx;*.xls"),
            ("Halaman Web / HTML (*.html, *.htm)", "*.html;*.htm"),
            ("File Teks & Data (*.txt, *.csv, *.json, *.xml)", "*.txt;*.csv;*.tsv;*.json;*.xml"),
            ("Semua File (*.*)", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Pilih File Dokumen untuk Dikonversi", filetypes=filetypes)
        if filename:
            self._set_selected_file(filename)

    def _on_single_file_drop(self, event):
        """Menangani event drag & drop file ke jendela."""
        raw_data = event.data
        if not raw_data:
            return
        try:
            files = self.tk.splitlist(raw_data)
        except Exception:
            files = [raw_data.strip("{}")]

        if files:
            first_file = files[0]
            if os.path.isfile(first_file):
                self._set_selected_file(first_file)
            elif os.path.isdir(first_file):
                messagebox.showinfo("Folder Terdeteksi", "Untuk mengonversi seluruh isi folder, silakan buka tab 'Konversi Banyak File (Batch)'.")

    def _set_selected_file(self, filepath: str):
        filepath = os.path.abspath(filepath)
        self.selected_file_path = filepath
        fname = os.path.basename(filepath)
        size_str = format_file_size(os.path.getsize(filepath))
        ext = os.path.splitext(fname)[1].upper()

        self.lbl_file_name.configure(text=f"📄 {fname}")
        self.lbl_file_meta.configure(text=f"Tipe: {ext} | Ukuran: {size_str}\nLokasi: {os.path.dirname(filepath)}")
        self.set_status(f"File dipilih: {fname} ({size_str})")

    def _start_single_conversion(self):
        if not self.selected_file_path:
            messagebox.showwarning("Peringatan", "Silakan pilih file dokumen terlebih dahulu!")
            return

        if not os.path.exists(self.selected_file_path):
            messagebox.showerror("Error", f"File tidak ditemukan:\n{self.selected_file_path}")
            return

        if self.is_converting:
            return

        self.is_converting = True
        self.btn_convert_single.configure(state="disabled", text="⏳ Sedang Mengonversi...")
        self.progress_single.start()
        self.set_status(f"Sedang mengonversi {os.path.basename(self.selected_file_path)}...")

        threading.Thread(target=self._worker_single_conversion, daemon=True).start()

    def _worker_single_conversion(self):
        start_time = time.time()
        file_path = self.selected_file_path
        error_msg = None
        markdown_result = ""

        try:
            markdown_result = fast_convert_document(self.md_engine, file_path)
        except Exception as e:
            error_msg = str(e)

        elapsed = time.time() - start_time
        self.after(0, lambda: self._finish_single_conversion(markdown_result, error_msg, elapsed, file_path))

    def _finish_single_conversion(self, markdown_text: str, error_msg: str, elapsed: float, file_path: str):
        self.progress_single.stop()
        self.progress_single.set(0)
        self.btn_convert_single.configure(state="normal", text="⚡ Konversi ke Markdown Sekarang")
        self.is_converting = False

        if error_msg:
            self.set_status(f"Gagal mengonversi file: {error_msg}")
            messagebox.showerror("Konversi Gagal", f"Terjadi kesalahan saat mengonversi file:\n\n{error_msg}")
            return

        self.txt_markdown.delete("1.0", "end")
        self.txt_markdown.insert("1.0", markdown_text)
        self._update_text_stats()

        self.btn_copy.configure(state="normal")
        self.btn_save_as.configure(state="normal")

        saved_msg = ""
        if self.var_autosave.get():
            try:
                base_name = os.path.splitext(file_path)[0]
                out_path = f"{base_name}.md"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(markdown_text)
                self.last_saved_output_path = out_path
                self.btn_open_folder.configure(state="normal")
                saved_msg = f" | Otomatis disimpan ke: {os.path.basename(out_path)}"
            except Exception as e:
                saved_msg = f" | Gagal simpan otomatis: {e}"

        if self.var_autocopy.get():
            self._copy_to_clipboard(silent=True)
            saved_msg += " (Tersalin ke clipboard)"

        self.set_status(f"✅ Selesai dalam {elapsed:.2f} detik!{saved_msg}")

    def _update_text_stats(self, event=None):
        content = self.txt_markdown.get("1.0", "end-1c")
        chars = len(content)
        lines = len(content.splitlines()) if chars > 0 else 0
        self.lbl_stats.configure(text=f"{chars:,} karakter | {lines:,} baris")

    def _copy_to_clipboard(self, silent=False):
        content = self.txt_markdown.get("1.0", "end-1c")
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        self.update()
        if not silent:
            self.set_status("📋 Teks Markdown berhasil disalin ke clipboard!")
            messagebox.showinfo("Disalin", "Markdown berhasil disalin ke clipboard!")

    def _save_markdown_as(self):
        content = self.txt_markdown.get("1.0", "end-1c")
        if not content:
            messagebox.showwarning("Kosong", "Tidak ada konten Markdown untuk disimpan.")
            return

        default_name = "output.md"
        if self.selected_file_path:
            base = os.path.splitext(os.path.basename(self.selected_file_path))[0]
            default_name = f"{base}.md"

        target_file = filedialog.asksaveasfilename(
            title="Simpan File Markdown",
            defaultextension=".md",
            initialfile=default_name,
            filetypes=[("Markdown Document (*.md)", "*.md"), ("Semua File (*.*)", "*.*")]
        )
        if target_file:
            try:
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.last_saved_output_path = target_file
                self.btn_open_folder.configure(state="normal")
                self.set_status(f"File berhasil disimpan ke: {target_file}")
                messagebox.showinfo("Berhasil", f"File berhasil disimpan ke:\n{target_file}")
            except Exception as e:
                messagebox.showerror("Gagal Menyimpan", f"Error: {e}")

    def _open_output_folder(self):
        target = self.last_saved_output_path or self.selected_file_path
        if not target:
            return
        folder = os.path.dirname(os.path.abspath(target))
        if os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Tidak dapat membuka folder: {e}")

    def _clear_single_tab(self):
        self.selected_file_path = None
        self.last_saved_output_path = None
        self.lbl_file_name.configure(text="Belum ada file yang dipilih")
        self.lbl_file_meta.configure(text="Pilih atau seret file dokumen untuk memulai.")
        self.txt_markdown.delete("1.0", "end")
        self._update_text_stats()
        self.btn_copy.configure(state="disabled")
        self.btn_save_as.configure(state="disabled")
        self.btn_open_folder.configure(state="disabled")
        self.set_status("Siap digunakan.")

    # ==========================================
    # TAB 2: KONVERSI MASSAL (BATCH)
    # ==========================================
    def _setup_batch_tab(self):
        self.tab_batch.grid_columnconfigure(0, weight=1)
        self.tab_batch.grid_rowconfigure(1, weight=1)

        # Kontrol Atas
        top_ctrl = ctk.CTkFrame(self.tab_batch, corner_radius=8)
        top_ctrl.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10))

        btn_add_files = ctk.CTkButton(
            top_ctrl,
            text="➕ Tambah Banyak File...",
            command=self._batch_add_files,
            height=32
        )
        btn_add_files.pack(side="left", padx=10, pady=10)

        btn_add_dir = ctk.CTkButton(
            top_ctrl,
            text="📁 Tambah 1 Folder Penuh...",
            command=self._batch_add_directory,
            height=32
        )
        btn_add_dir.pack(side="left", padx=5, pady=10)

        btn_clear_list = ctk.CTkButton(
            top_ctrl,
            text="🧹 Bersihkan Antrean",
            command=self._batch_clear_all,
            fg_color=("gray75", "#32364a"),
            hover_color=("gray65", "#414868"),
            height=32
        )
        btn_clear_list.pack(side="left", padx=5, pady=10)

        self.lbl_queue_count = ctk.CTkLabel(
            top_ctrl,
            text="0 file dalam antrean",
            font=ctk.CTkFont(weight="bold")
        )
        self.lbl_queue_count.pack(side="right", padx=15)

        # Frame List Antrean
        self.scroll_batch = ctk.CTkScrollableFrame(self.tab_batch, label_text="Daftar Dokumen yang Akan Dikonversi")
        self.scroll_batch.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)
        self.scroll_batch.grid_columnconfigure(0, weight=1)

        # Kontrol Bawah
        bottom_frame = ctk.CTkFrame(self.tab_batch, corner_radius=8)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(10, 5))

        out_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        out_row.pack(fill="x", padx=15, pady=(10, 5))

        lbl_out = ctk.CTkLabel(out_row, text="Folder Hasil:")
        lbl_out.pack(side="left", padx=(0, 10))

        self.entry_batch_out = ctk.CTkEntry(
            out_row,
            placeholder_text="Biarkan kosong untuk menyimpan di folder yang sama dengan file asal"
        )
        self.entry_batch_out.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse_out = ctk.CTkButton(
            out_row,
            text="Jelajahi...",
            width=80,
            command=self._batch_browse_out_dir
        )
        btn_browse_out.pack(side="right")

        action_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(5, 12))

        self.progress_batch = ctk.CTkProgressBar(action_row, mode="determinate", height=12)
        self.progress_batch.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.progress_batch.set(0)

        self.lbl_batch_progress_text = ctk.CTkLabel(action_row, text="0 / 0 file selesai")
        self.lbl_batch_progress_text.pack(side="left", padx=(0, 15))

        self.btn_start_batch = ctk.CTkButton(
            action_row,
            text="🚀 Mulai Konversi Batch",
            command=self._start_batch_conversion,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        self.btn_start_batch.pack(side="right")

    def _batch_add_files(self):
        filetypes = [
            ("Semua File yang Didukung", "*.docx;*.pdf;*.pptx;*.xlsx;*.xls;*.html;*.htm;*.csv;*.tsv;*.txt;*.json;*.xml;*.zip"),
            ("Semua File (*.*)", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Pilih Beberapa File Sekaligus", filetypes=filetypes)
        if files:
            for f in files:
                self._add_file_to_batch_queue(f)

    def _batch_add_directory(self):
        folder = filedialog.askdirectory(title="Pilih Folder yang Berisi Dokumen")
        if not folder:
            return

        supported_exts = {".docx", ".pdf", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".csv", ".tsv", ".txt", ".json", ".xml", ".zip"}
        added = 0
        for root, _, filenames in os.walk(folder):
            for name in filenames:
                ext = os.path.splitext(name)[1].lower()
                if ext in supported_exts:
                    full_p = os.path.join(root, name)
                    self._add_file_to_batch_queue(full_p)
                    added += 1

        if added == 0:
            messagebox.showinfo("Tidak Ada File", "Tidak ditemukan file dokumen yang didukung di folder tersebut.")
        else:
            self.set_status(f"Berhasil menambahkan {added} file dari folder ke antrean.")

    def _add_file_to_batch_queue(self, file_path: str):
        file_path = os.path.abspath(file_path)
        if any(item["path"] == file_path for item in self.batch_files_list):
            return

        item = {
            "path": file_path,
            "status": "Menunggu",
            "row_frame": None,
            "status_label": None
        }

        row = ctk.CTkFrame(self.scroll_batch, corner_radius=6, height=36)
        row.pack(fill="x", padx=5, pady=3)
        row.pack_propagate(False)

        fname = os.path.basename(file_path)
        size_str = format_file_size(os.path.getsize(file_path))

        lbl_name = ctk.CTkLabel(row, text=f"{fname} ({size_str})", anchor="w", font=ctk.CTkFont(size=12))
        lbl_name.pack(side="left", padx=10)

        lbl_status = ctk.CTkLabel(row, text="⏳ Menunggu", text_color="gray60", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_status.pack(side="right", padx=10)

        item["row_frame"] = row
        item["status_label"] = lbl_status

        self.batch_files_list.append(item)
        self.lbl_queue_count.configure(text=f"{len(self.batch_files_list)} file dalam antrean")

    def _batch_clear_all(self):
        if self.is_converting:
            messagebox.showwarning("Peringatan", "Tunggu hingga konversi selesai!")
            return
        for item in self.batch_files_list:
            item["row_frame"].destroy()
        self.batch_files_list.clear()
        self.lbl_queue_count.configure(text="0 file dalam antrean")
        self.progress_batch.set(0)
        self.lbl_batch_progress_text.configure(text="0 / 0 file selesai")

    def _batch_browse_out_dir(self):
        d = filedialog.askdirectory(title="Pilih Folder Tujuan Penyimpanan Markdown")
        if d:
            self.entry_batch_out.delete(0, "end")
            self.entry_batch_out.insert(0, d)

    def _start_batch_conversion(self):
        if not self.batch_files_list:
            messagebox.showwarning("Kosong", "Belum ada file dalam antrean konversi.")
            return

        if self.is_converting:
            return

        self.is_converting = True
        self.btn_start_batch.configure(state="disabled", text="⏳ Memproses...")
        self.progress_batch.set(0)

        threading.Thread(target=self._worker_batch_conversion, daemon=True).start()

    def _worker_batch_conversion(self):
        total = len(self.batch_files_list)
        custom_out_dir = self.entry_batch_out.get().strip()
        if custom_out_dir and not os.path.exists(custom_out_dir):
            try:
                os.makedirs(custom_out_dir, exist_ok=True)
            except Exception:
                custom_out_dir = None

        success_count = 0
        fail_count = 0

        for i, item in enumerate(self.batch_files_list):
            fpath = item["path"]
            self.after(0, lambda it=item: it["status_label"].configure(text="🔄 Memproses...", text_color="#3B8ED0"))

            try:
                content = fast_convert_document(self.md_engine, fpath)
                base = os.path.splitext(os.path.basename(fpath))[0]
                if custom_out_dir:
                    out_path = os.path.join(custom_out_dir, f"{base}.md")
                else:
                    out_path = os.path.splitext(fpath)[0] + ".md"

                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)

                success_count += 1
                self.after(0, lambda it=item: it["status_label"].configure(text="✅ Selesai", text_color="#4ade80"))
            except Exception as e:
                fail_count += 1
                self.after(0, lambda it=item: it["status_label"].configure(text="❌ Gagal", text_color="#f87171"))

            progress_ratio = (i + 1) / total
            self.after(0, lambda r=progress_ratio, curr=i+1, t=total: (
                self.progress_batch.set(r),
                self.lbl_batch_progress_text.configure(text=f"{curr} / {t} file ({int(r*100)}%)")
            ))

        self.after(0, lambda: self._finish_batch_conversion(success_count, fail_count, total, custom_out_dir))

    def _finish_batch_conversion(self, success: int, fail: int, total: int, out_dir: str):
        self.btn_start_batch.configure(state="normal", text="🚀 Mulai Konversi Batch")
        self.is_converting = False
        msg = f"Konversi batch selesai!\n\nBerhasil: {success} file\nGagal: {fail} file\nTotal: {total} file"
        self.set_status(f"Konversi batch selesai: {success} berhasil, {fail} gagal.")
        
        if messagebox.askyesno("Selesai", f"{msg}\n\nApakah Anda ingin membuka folder hasil konversi?"):
            target_folder = out_dir if (out_dir and os.path.exists(out_dir)) else (os.path.dirname(self.batch_files_list[0]["path"]) if self.batch_files_list else "")
            if target_folder and os.path.exists(target_folder):
                try:
                    os.startfile(target_folder)
                except Exception:
                    pass

    # ==========================================
    # TAB 3: FORMAT & PANDUAN
    # ==========================================
    def _setup_about_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_about, label_text="Panduan & Format Dokumen yang Didukung")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        scroll.grid_columnconfigure(0, weight=1)

        formats = [
            ("📄 Microsoft Word (.docx)", "Mengonversi paragraf, tabel, heading, teks tebal/miring, dan daftar item ke format Markdown standar."),
            ("📑 Dokumen PDF (.pdf)", "Mengekstrak teks halaman, format paragraf, dan struktur dokumen PDF secara bersih."),
            ("📊 Microsoft Excel (.xlsx, .xls)", "Mengubah sheet dan tabel spreadsheet menjadi tabel Markdown yang rapi dan terstruktur."),
            ("📽️ Microsoft PowerPoint (.pptx)", "Mengekstrak slide presentasi, judul presentasi, bullet points, dan catatan slide."),
            ("🌐 Halaman Web (.html, .htm)", "Membersihkan tag HTML dan mengubah struktur website menjadi Markdown yang mudah dibaca."),
            ("📋 File Data & Teks (.csv, .tsv, .txt, .json, .xml)", "Mengonversi data terstruktur dan teks biasa langsung menjadi format Markdown."),
            ("📦 Arsip ZIP (.zip)", "Membaca dan mengonversi file dokumen yang berada di dalam paket ZIP."),
            ("🎙️ File Audio & Gambar (.mp3, .wav, .jpg, .png)", "Mendukung pembacaan metadata dan transkripsi audio/OCR jika dependensi tambahan dikonfigurasi.")
        ]

        for title, desc in formats:
            card = ctk.CTkFrame(scroll, corner_radius=8)
            card.pack(fill="x", padx=10, pady=6)

            lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            lbl_t.pack(fill="x", padx=12, pady=(8, 2))

            lbl_d = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12), text_color=("gray40", "gray70"), anchor="w", wraplength=700)
            lbl_d.pack(fill="x", padx=12, pady=(0, 8))

        tip_frame = ctk.CTkFrame(scroll, corner_radius=8, fg_color=("gray85", "#1f2335"))
        tip_frame.pack(fill="x", padx=10, pady=(15, 10))

        tip_title = ctk.CTkLabel(tip_frame, text="💡 Tips Praktis:", font=ctk.CTkFont(size=13, weight="bold"))
        tip_title.pack(anchor="w", padx=12, pady=(10, 4))

        tip_text = (
            "1. Anda bisa langsung men-drag file dari File Explorer ke jendela aplikasi ini.\n"
            "2. Hasil konversi dapat diedit langsung di panel pratinjau sebelum disimpan atau disalin.\n"
            "3. Gunakan tombol 'Buka Lokasi' untuk langsung membuka folder tempat file Markdown tersimpan di Windows Explorer.\n"
            "4. Untuk mengonversi puluhan dokumen sekaligus, gunakan tab 'Konversi Banyak File (Batch)'."
        )
        lbl_tip = ctk.CTkLabel(tip_frame, text=tip_text, font=ctk.CTkFont(size=12), justify="left")
        lbl_tip.pack(anchor="w", padx=12, pady=(0, 10))

    # ==========================================
    # STATUS BAR
    # ==========================================
    def _create_statusbar(self):
        self.statusbar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color=("gray90", "#14151f"))
        self.statusbar.pack(fill="x", side="bottom")

        self.lbl_status = ctk.CTkLabel(
            self.statusbar,
            text="Siap digunakan.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray65"),
            anchor="w"
        )
        self.lbl_status.pack(side="left", padx=15, pady=2)

        ver_lbl = ctk.CTkLabel(
            self.statusbar,
            text="Microsoft MarkItDown | Dikelola oleh Maaafiqs Dev (maaafiqs.web.id)",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60")
        )
        ver_lbl.pack(side="right", padx=15, pady=2)

    def set_status(self, text: str):
        self.lbl_status.configure(text=text)


if __name__ == "__main__":
    app = MarkItDownDesktopApp()
    app.mainloop()
