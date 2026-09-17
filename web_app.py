import os
import sys
import io
import time
import zipfile
import tempfile
import warnings
from flask import Flask, request, jsonify, render_template, send_file
from markitdown import MarkItDown

# Redam peringatan ffmpeg/pydub
warnings.filterwarnings("ignore")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Maksimal upload 100MB
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Inisialisasi engine Microsoft MarkItDown
md = MarkItDown()

def get_text_stats(text: str):
    """Menghitung statistik teks Markdown."""
    chars = len(text)
    lines = len(text.splitlines()) if chars > 0 else 0
    words = len(text.split()) if chars > 0 else 0
    return {
        "characters": chars,
        "lines": lines,
        "words": words
    }

def fast_convert_document(file_path: str, ext: str) -> str:
    """
    Konversi dokumen berkecepatan tinggi:
    - Untuk PDF: Akselerasi menggunakan PDFium C++ engine (0.02 - 0.1 detik vs 30-60 detik pdfplumber).
    - Format lain (DOCX, XLSX, PPTX, HTML, CSV, TXT, JSON, dll.): Menggunakan engine Microsoft MarkItDown.
    """
    ext = (ext or "").lower()
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

    # Engine standar Microsoft MarkItDown
    result = md.convert(file_path)
    return result.text_content or ""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def server_status():
    return jsonify({
        "status": "online",
        "engine": "Microsoft MarkItDown (Turbo Accelerated)",
        "version": "1.0.0",
        "supported_formats": [
            "docx", "pdf", "pptx", "xlsx", "xls", "html", "htm", "csv", "tsv", "txt", "json", "xml", "zip", "wav", "mp3"
        ]
    })

@app.route("/api/convert", methods=["POST"])
def convert_single():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Tidak ada file yang diunggah."}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"success": False, "error": "Nama file kosong."}), 400

    original_filename = uploaded_file.filename
    _, ext = os.path.splitext(original_filename)

    start_time = time.time()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            uploaded_file.save(tmp)
            tmp_path = tmp.name

        file_size = os.path.getsize(tmp_path)
        # Konversi cepat dengan akselerasi C++ untuk PDF
        markdown_content = fast_convert_document(tmp_path, ext)
        elapsed = time.time() - start_time

        stats = get_text_stats(markdown_content)

        return jsonify({
            "success": True,
            "filename": original_filename,
            "size": file_size,
            "elapsed_seconds": round(elapsed, 2),
            "markdown": markdown_content,
            "stats": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "filename": original_filename,
            "error": str(e)
        }), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

@app.route("/api/convert-batch", methods=["POST"])
def convert_batch():
    files = request.files.getlist("files")
    if not files or len(files) == 0:
        return jsonify({"success": False, "error": "Tidak ada file yang dipilih untuk batch conversion."}), 400

    results = []
    total_start = time.time()

    for uploaded_file in files:
        if not uploaded_file.filename:
            continue

        original_filename = uploaded_file.filename
        _, ext = os.path.splitext(original_filename)
        tmp_path = None
        file_start = time.time()

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                uploaded_file.save(tmp)
                tmp_path = tmp.name

            file_size = os.path.getsize(tmp_path)
            md_text = fast_convert_document(tmp_path, ext)
            elapsed = time.time() - file_start

            results.append({
                "success": True,
                "filename": original_filename,
                "size": file_size,
                "elapsed": round(elapsed, 2),
                "markdown": md_text,
                "stats": get_text_stats(md_text)
            })
        except Exception as e:
            results.append({
                "success": False,
                "filename": original_filename,
                "error": str(e)
            })
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    total_elapsed = time.time() - total_start
    successful_count = sum(1 for r in results if r.get("success"))

    return jsonify({
        "success": True,
        "total_files": len(results),
        "successful_files": successful_count,
        "failed_files": len(results) - successful_count,
        "total_elapsed": round(total_elapsed, 2),
        "results": results
    })

@app.route("/api/download-zip", methods=["POST"])
def download_zip():
    data = request.get_json()
    if not data or "files" not in data or not isinstance(data["files"], list):
        return jsonify({"error": "Data file tidak valid"}), 400

    # Buat file zip di dalam memori (BytesIO)
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in data["files"]:
            fname = item.get("filename", "document.md")
            if not fname.endswith(".md"):
                fname += ".md"
            content = item.get("content", "")
            zf.writestr(fname, content.encode("utf-8"))

    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="MarkItDown_Hasil_Konversi.zip"
    )

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Server MarkItDown Web berjalan di http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

