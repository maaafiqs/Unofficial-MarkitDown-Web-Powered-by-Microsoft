# Unofficial MarkItDown Web & Desktop Studio (Powered by Microsoft)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Microsoft MarkItDown](https://img.shields.io/badge/Engine-Microsoft%20MarkItDown-0078D4?style=for-the-badge&logo=microsoft&logoColor=white)](https://github.com/microsoft/markitdown)
[![Flask](https://img.shields.io/badge/Web-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![CustomTkinter](https://img.shields.io/badge/Desktop-CustomTkinter-1f6aa5?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)

Aplikasi desktop & web modern yang intuitif untuk mengonversi dokumen **PDF, Microsoft Word (.docx), Excel (.xlsx), PowerPoint (.pptx), HTML, CSV, TXT, dll.** menjadi format **Markdown (.md)** bersih dan terstruktur secara instan.

Dirancang khusus untuk mengoptimalkan dokumen sebelum diunggah ke model AI (seperti **ChatGPT, Claude, Gemini, atau DeepSeek**), menghemat kuota token hingga **80%**, mencegah batasan *context window limit*, dan menjaga struktur tabel tetap presisi.

---

## 🌟 Fitur Utama

- ⚡ **Akselerasi Turbo (C++ PDFium Engine):** Konversi dokumen PDF super cepat (0.02 - 0.1 detik per dokumen), tanpa kendala lambat atau macet.
- 🤖 **Optimasi Token AI:** Menghapus sampah biner dan metadata visual dokumen mentah, sehingga token prompt hemat berlipat ganda.
- 🎨 **Antarmuka Futuristik & Responsif:** Desain modern dengan *glassmorphism*, dark/light mode toggle, dan animasi halus.
- 📄 **Dual Preview Mode:** Mode *Raw Markdown* untuk teks mentah dan *Tampilan Visual* yang di-render langsung via Marked.js.
- 📚 **Konversi Massal (Batch):** Unggah puluhan file sekaligus dan unduh semua hasil dalam satu arsip ZIP.
- 💻 **Dua Pilihan Platform:**
  - **Versi Web (Flask):** Akses lewat browser atau buka via smartphone dalam satu jaringan Wi-Fi.
  - **Versi Desktop (CustomTkinter):** Aplikasi Windows native modern lengkap dengan dukungan drag & drop.
- 🔗 **Integrasi Ekosistem:** Dilengkapi tombol kembali ke [Tulis Cek App](https://tuliscek-app.vercel.app/).

---

## 🚀 Cara Menjalankan

### 1. Versi Web (Browser)
Cukup **klik 2x** file:
```bash
Buka_MarkItDown_Web.bat
```
Server akan menyala otomatis dan membuka browser di `http://localhost:5000`.

### 2. Versi Desktop (Aplikasi Windows)
Cukup **klik 2x** file:
```bash
Buka_MarkItDown.vbs
```
*(Atau gunakan shortcut "MarkItDown Desktop" yang telah dibuat di layar Desktop Anda)*.

---

## 📦 Instalasi Manual (Dependencies)

Jika Anda menjalankan dari clone repositori:
```bash
git clone https://github.com/maaafiqs/Unofficial-MarkitDown-Web-Powered-by-Microsoft.git
cd Unofficial-MarkitDown-Web-Powered-by-Microsoft
pip install -r requirements.txt
```

Menjalankan server web:
```bash
python app.py
```
*(Atau `python web_app.py`)*

Menjalankan aplikasi desktop:
```bash
python desktop_app.py
```

---

## ☁️ Deploy ke Vercel

Aplikasi web ini sudah terkonfigurasi secara native untuk Vercel Serverless Functions (`api/index.py` dan `vercel.json`):
1. Import repository ini di dashboard [Vercel](https://vercel.com).
2. Biarkan setting build default (Framework Preset: **Other**).
3. Klik **Deploy**.
4. Aplikasi web Anda langsung online dan siap digunakan di seluruh dunia!

---

## 🛠️ Format yang Didukung

| Format | Ekstensi | Deskripsi |
| :--- | :--- | :--- |
| **PDF** | `.pdf` | Teks halaman demi halaman, pemisah paragraf, akselerasi PDFium C++ |
| **Word** | `.docx` | Heading 1-6, paragraf, daftar list, tabel bergaris |
| **Excel** | `.xlsx`, `.xls` | Tabel spreadsheet diubah menjadi tabel Markdown terstruktur |
| **PowerPoint** | `.pptx` | Judul slide, bullet point presentasi, catatan presenter |
| **HTML** | `.html`, `.htm` | Tag HTML dibersihkan menjadi Markdown murni |
| **Teks & Data** | `.txt`, `.csv`, `.tsv`, `.json`, `.xml` | Data baris/kolom dan teks terstruktur |
| **Arsip** | `.zip` | Membaca dokumen di dalam arsip ZIP |

---

## 👨‍💻 Pengembang & Kredit

- **Engine Inti:** Microsoft MarkItDown (`markitdown[all]`)
- **Dikelola & Dikembangkan oleh:** [Maaafiqs Dev](https://maaafiqs.web.id/)
- **Proyek Terkait:** [Tulis Cek App](https://tuliscek-app.vercel.app/)

---

## 📄 Lisensi
Didistribusikan di bawah lisensi MIT. Silakan gunakan dan kembangkan secara bebas.
