"""
MarkItDown Web Studio - Backward Compatibility Entrypoint
Aplikasi utama sekarang berada di app.py untuk kompatibilitas otomatis Vercel & cloud hosting.
"""
from app import app, main

if __name__ == "__main__":
    main()
