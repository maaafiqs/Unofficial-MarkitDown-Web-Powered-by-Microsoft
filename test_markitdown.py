from markitdown import MarkItDown

# Inisialisasi converter
md = MarkItDown()

# Masukkan nama file yang ingin dikonversi (misal: dokumen.docx, file.pdf, data.xlsx)
path_file = "contoh.docx" 

try:
    result = md.convert(path_file)
    
    # Cetak hasil Markdown ke terminal
    print(result.text_content)

    # Opsional: Simpan ke file .md
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(result.text_content)
    print("\nKonversi berhasil disimpan ke output.md!")
    
except Exception as e:
    print(f"Terjadi error: {e}")