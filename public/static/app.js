/**
 * MarkItDown Web Studio - Client JavaScript
 * Modern, responsive interactions for document-to-markdown conversion
 */

document.addEventListener("DOMContentLoaded", () => {
  // State variables
  let currentSingleFile = null;
  let currentMarkdownText = "";
  let currentFilename = "document.md";
  let batchQueue = []; // array of { file, status, markdown, elapsed }

  // DOM Elements - Theme & Tabs
  const htmlEl = document.documentElement;
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const tabBtns = [
    { btn: document.getElementById("tabBtnSingle"), panel: document.getElementById("tabSingle") },
    { btn: document.getElementById("tabBtnBatch"), panel: document.getElementById("tabBatch") },
    { btn: document.getElementById("tabBtnDocs"), panel: document.getElementById("tabDocs") }
  ];

  // DOM Elements - Single File Mode
  const singleDropzone = document.getElementById("singleDropzone");
  const singleFileInput = document.getElementById("singleFileInput");
  const selectedFileCard = document.getElementById("selectedFileCard");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const fileMetaDisplay = document.getElementById("fileMetaDisplay");
  const fileExtBadge = document.getElementById("fileExtBadge");
  const btnRemoveFile = document.getElementById("btnRemoveFile");
  const btnConvertSingle = document.getElementById("btnConvertSingle");
  const btnResetSingle = document.getElementById("btnResetSingle");
  const conversionProgress = document.getElementById("conversionProgress");
  const progressStatusLabel = document.getElementById("progressStatusLabel");

  // DOM Elements - Preview & Results
  const btnViewRaw = document.getElementById("btnViewRaw");
  const btnViewRendered = document.getElementById("btnViewRendered");
  const rawMarkdownEditor = document.getElementById("rawMarkdownEditor");
  const renderedMarkdownView = document.getElementById("renderedMarkdownView");
  const resultStats = document.getElementById("resultStats");
  const btnCopyMarkdown = document.getElementById("btnCopyMarkdown");
  const btnDownloadMarkdown = document.getElementById("btnDownloadMarkdown");

  // DOM Elements - Batch Mode
  const batchDropzone = document.getElementById("batchDropzone");
  const batchFileInput = document.getElementById("batchFileInput");
  const batchTableBody = document.getElementById("batchTableBody");
  const queueCounterText = document.getElementById("queueCounterText");
  const btnBatchStart = document.getElementById("btnBatchStart");
  const btnBatchClear = document.getElementById("btnBatchClear");
  const btnDownloadBatchZip = document.getElementById("btnDownloadBatchZip");

  // DOM Elements - Toast
  const toastNotification = document.getElementById("toastNotification");
  const toastMessage = document.getElementById("toastMessage");

  // ==========================================
  // 1. THEME TOGGLING
  // ==========================================
  const savedTheme = localStorage.getItem("markitdown_theme") || "dark";
  htmlEl.setAttribute("data-theme", savedTheme);

  themeToggleBtn.addEventListener("click", () => {
    const current = htmlEl.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    htmlEl.setAttribute("data-theme", next);
    localStorage.setItem("markitdown_theme", next);
  });

  // ==========================================
  // 2. TAB SWITCHING
  // ==========================================
  tabBtns.forEach(({ btn, panel }) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(t => {
        t.btn.classList.remove("active");
        t.btn.setAttribute("aria-selected", "false");
        t.panel.classList.remove("active");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      panel.classList.add("active");
    });
  });

  // ==========================================
  // 2B. COLLAPSIBLE AI TOKEN EXPLANATION CARD
  // ==========================================
  const aiTokenCard = document.getElementById("aiTokenCard");
  const aiCardHeader = document.getElementById("aiCardHeader");
  const aiCardBody = document.getElementById("aiCardBody");
  const btnToggleAiExplain = document.getElementById("btnToggleAiExplain");
  const toggleAiText = document.getElementById("toggleAiText");

  function setAiExplanationCollapsed(collapsed) {
    if (!aiTokenCard || !aiCardBody) return;
    if (collapsed) {
      aiTokenCard.classList.add("collapsed");
      aiCardBody.classList.add("collapsed");
      if (toggleAiText) toggleAiText.textContent = "Buka Penjelasan";
      if (btnToggleAiExplain) btnToggleAiExplain.setAttribute("aria-expanded", "false");
      localStorage.setItem("ai_explain_collapsed", "true");
    } else {
      aiTokenCard.classList.remove("collapsed");
      aiCardBody.classList.remove("collapsed");
      if (toggleAiText) toggleAiText.textContent = "Tutup Penjelasan";
      if (btnToggleAiExplain) btnToggleAiExplain.setAttribute("aria-expanded", "true");
      localStorage.setItem("ai_explain_collapsed", "false");
    }
  }

  // Restore saved state (default is open/expanded)
  const isAiExplainCollapsed = localStorage.getItem("ai_explain_collapsed") === "true";
  if (isAiExplainCollapsed) {
    setAiExplanationCollapsed(true);
  }

  if (btnToggleAiExplain) {
    btnToggleAiExplain.addEventListener("click", (e) => {
      e.stopPropagation();
      const currentlyCollapsed = aiCardBody.classList.contains("collapsed");
      setAiExplanationCollapsed(!currentlyCollapsed);
    });
  }

  if (aiCardHeader) {
    aiCardHeader.addEventListener("click", () => {
      const currentlyCollapsed = aiCardBody.classList.contains("collapsed");
      setAiExplanationCollapsed(!currentlyCollapsed);
    });
  }

  // ==========================================
  // 3. UTILITIES
  // ==========================================
  function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  function getFileExtension(filename) {
    const parts = filename.split(".");
    return parts.length > 1 ? parts.pop().toUpperCase() : "FILE";
  }

  function showToast(msg) {
    toastMessage.textContent = msg;
    toastNotification.classList.remove("hidden");
    setTimeout(() => {
      toastNotification.classList.add("hidden");
    }, 3200);
  }

  function updateStats(text) {
    const chars = text.length;
    const lines = text ? text.split("\n").length : 0;
    resultStats.innerHTML = `<span>${chars.toLocaleString()} karakter</span> • <span>${lines.toLocaleString()} baris</span>`;
  }

  // ==========================================
  // 4. SINGLE FILE SELECTION & DROP
  // ==========================================
  function setSingleFile(file) {
    if (!file) return;
    currentSingleFile = file;
    currentFilename = file.name;

    const ext = getFileExtension(file.name);
    fileExtBadge.textContent = ext.slice(0, 4);
    fileNameDisplay.textContent = file.name;
    fileMetaDisplay.textContent = `${formatBytes(file.size)} • Format .${ext.toLowerCase()}`;

    singleDropzone.classList.add("hidden");
    selectedFileCard.classList.remove("hidden");
    btnConvertSingle.removeAttribute("disabled");
  }

  function clearSingleFile() {
    currentSingleFile = null;
    singleFileInput.value = "";
    selectedFileCard.classList.add("hidden");
    singleDropzone.classList.remove("hidden");
    btnConvertSingle.setAttribute("disabled", "true");
  }

  singleFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      setSingleFile(e.target.files[0]);
    }
  });

  singleDropzone.addEventListener("click", () => singleFileInput.click());

  // Drag & Drop Events for Single Dropzone
  ["dragenter", "dragover"].forEach(eventName => {
    singleDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      singleDropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    singleDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      singleDropzone.classList.remove("dragover");
    });
  });

  singleDropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSingleFile(e.dataTransfer.files[0]);
    }
  });

  btnRemoveFile.addEventListener("click", clearSingleFile);
  btnResetSingle.addEventListener("click", () => {
    clearSingleFile();
    rawMarkdownEditor.value = "";
    currentMarkdownText = "";
    updateStats("");
    btnCopyMarkdown.setAttribute("disabled", "true");
    btnDownloadMarkdown.setAttribute("disabled", "true");
    renderedMarkdownView.innerHTML = `<div class="empty-state-notice"><p>Belum ada konten dokumen. Silakan unggah dan konversi dokumen Anda.</p></div>`;
  });

  // ==========================================
  // 5. CONVERSION LOGIC (SINGLE FILE)
  // ==========================================
  btnConvertSingle.addEventListener("click", async () => {
    if (!currentSingleFile) return;

    btnConvertSingle.setAttribute("disabled", "true");
    conversionProgress.classList.remove("hidden");
    progressStatusLabel.textContent = `Mengonversi ${currentSingleFile.name}...`;

    const formData = new FormData();
    formData.append("file", currentSingleFile);

    try {
      const response = await fetch("/api/convert", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Gagal mengonversi file");
      }

      currentMarkdownText = data.markdown || "";
      rawMarkdownEditor.value = currentMarkdownText;
      updateStats(currentMarkdownText);

      // Render ke tampilan visual HTML jika marked.js aktif
      renderMarkdownHtml(currentMarkdownText);

      // Aktifkan tombol copy & download
      btnCopyMarkdown.removeAttribute("disabled");
      btnDownloadMarkdown.removeAttribute("disabled");

      showToast(`Konversi berhasil dalam ${data.elapsed_seconds} detik!`);
    } catch (err) {
      alert(`Terjadi kesalahan konversi:\n${err.message}`);
    } finally {
      btnConvertSingle.removeAttribute("disabled");
      conversionProgress.classList.add("hidden");
    }
  });

  // ==========================================
  // 6. VIEW MODES & LIVE EDITOR
  // ==========================================
  function renderMarkdownHtml(mdText) {
    if (typeof marked !== "undefined" && marked.parse) {
      renderedMarkdownView.innerHTML = marked.parse(mdText);
    } else {
      renderedMarkdownView.innerHTML = `<pre><code>${mdText}</code></pre>`;
    }
  }

  btnViewRaw.addEventListener("click", () => {
    btnViewRaw.classList.add("active");
    btnViewRendered.classList.remove("active");
    rawMarkdownEditor.classList.remove("hidden");
    renderedMarkdownView.classList.add("hidden");
  });

  btnViewRendered.addEventListener("click", () => {
    btnViewRendered.classList.add("active");
    btnViewRaw.classList.remove("active");
    // Render teks terbaru dari editor (jika user mengubah teks secara manual)
    renderMarkdownHtml(rawMarkdownEditor.value);
    renderedMarkdownView.classList.remove("hidden");
    rawMarkdownEditor.classList.add("hidden");
  });

  rawMarkdownEditor.addEventListener("input", (e) => {
    updateStats(e.target.value);
    currentMarkdownText = e.target.value;
  });

  // Copy to Clipboard
  btnCopyMarkdown.addEventListener("click", async () => {
    const textToCopy = rawMarkdownEditor.value;
    if (!textToCopy) return;

    try {
      await navigator.clipboard.writeText(textToCopy);
      showToast("Teks Markdown berhasil disalin ke clipboard!");
    } catch (err) {
      // Fallback
      rawMarkdownEditor.select();
      document.execCommand("copy");
      showToast("Teks disalin ke clipboard!");
    }
  });

  // Download .md File
  btnDownloadMarkdown.addEventListener("click", () => {
    const textToSave = rawMarkdownEditor.value;
    if (!textToSave) return;

    let targetName = currentFilename;
    const lastDot = targetName.lastIndexOf(".");
    if (lastDot !== -1) {
      targetName = targetName.substring(0, lastDot);
    }
    targetName += ".md";

    const blob = new Blob([textToSave], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = targetName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast(`File ${targetName} berhasil diunduh!`);
  });

  // ==========================================
  // 7. BATCH CONVERSION LOGIC
  // ==========================================
  function renderBatchTable() {
    if (batchQueue.length === 0) {
      batchTableBody.innerHTML = `
        <tr class="empty-row">
          <td colspan="6">Belum ada file dalam antrean. Seret file ke area di atas.</td>
        </tr>
      `;
      queueCounterText.textContent = "0 file dalam antrean";
      btnBatchStart.setAttribute("disabled", "true");
      btnDownloadBatchZip.classList.add("hidden");
      return;
    }

    queueCounterText.textContent = `${batchQueue.length} file dalam antrean`;
    btnBatchStart.removeAttribute("disabled");

    let html = "";
    batchQueue.forEach((item, index) => {
      let statusBadge = "";
      if (item.status === "pending") {
        statusBadge = `<span class="badge-status badge-pending">Menunggu</span>`;
      } else if (item.status === "processing") {
        statusBadge = `<span class="badge-status badge-processing">Memproses...</span>`;
      } else if (item.status === "success") {
        statusBadge = `<span class="badge-status badge-success">Selesai</span>`;
      } else {
        statusBadge = `<span class="badge-status badge-error">Gagal</span>`;
      }

      const elapsedStr = item.elapsed ? `${item.elapsed}s` : "-";
      const actionBtn = item.markdown ? 
        `<button class="btn-action" onclick="window.downloadSingleBatchItem(${index})" title="Unduh file dokumen Markdown (.md)">Unduh Markdown (.md)</button>` : 
        `<span style="color: var(--text-muted); font-size: 0.8rem;">-</span>`;

      html += `
        <tr>
          <td>${index + 1}</td>
          <td><strong>${item.file.name}</strong></td>
          <td>${formatBytes(item.file.size)}</td>
          <td>${statusBadge}</td>
          <td>${elapsedStr}</td>
          <td>${actionBtn}</td>
        </tr>
      `;
    });

    batchTableBody.innerHTML = html;

    const hasCompleted = batchQueue.some(i => i.status === "success");
    if (hasCompleted) {
      btnDownloadBatchZip.classList.remove("hidden");
    }
  }

  function addFilesToBatch(files) {
    Array.from(files).forEach(f => {
      // Hindari duplikasi nama
      if (!batchQueue.some(item => item.file.name === f.name && item.file.size === f.size)) {
        batchQueue.push({
          file: f,
          status: "pending",
          markdown: "",
          elapsed: null,
          error: null
        });
      }
    });
    renderBatchTable();
  }

  batchDropzone.addEventListener("click", () => batchFileInput.click());

  batchFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      addFilesToBatch(e.target.files);
    }
  });

  ["dragenter", "dragover"].forEach(eventName => {
    batchDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      batchDropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    batchDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      batchDropzone.classList.remove("dragover");
    });
  });

  batchDropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToBatch(e.dataTransfer.files);
    }
  });

  btnBatchClear.addEventListener("click", () => {
    batchQueue = [];
    batchFileInput.value = "";
    renderBatchTable();
  });

  btnBatchStart.addEventListener("click", async () => {
    if (batchQueue.length === 0) return;

    btnBatchStart.setAttribute("disabled", "true");
    btnBatchClear.setAttribute("disabled", "true");

    const formData = new FormData();
    batchQueue.forEach(item => {
      formData.append("files", item.file);
      item.status = "processing";
    });
    renderBatchTable();

    try {
      const res = await fetch("/api/convert-batch", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || "Gagal konversi batch");
      }

      data.results.forEach((resItem, idx) => {
        if (batchQueue[idx]) {
          if (resItem.success) {
            batchQueue[idx].status = "success";
            batchQueue[idx].markdown = resItem.markdown;
            batchQueue[idx].elapsed = resItem.elapsed;
          } else {
            batchQueue[idx].status = "error";
            batchQueue[idx].error = resItem.error;
          }
        }
      });

      renderBatchTable();
      showToast(`Batch selesai! ${data.successful_files} berhasil, ${data.failed_files} gagal.`);
    } catch (err) {
      alert(`Error saat konversi batch: ${err.message}`);
    } finally {
      btnBatchStart.removeAttribute("disabled");
      btnBatchClear.removeAttribute("disabled");
    }
  });

  // Unduh semua hasil batch sebagai ZIP
  btnDownloadBatchZip.addEventListener("click", async () => {
    const successFiles = batchQueue.filter(i => i.status === "success" && i.markdown);
    if (successFiles.length === 0) return;

    const filesPayload = successFiles.map(i => {
      let base = i.file.name;
      const lastDot = base.lastIndexOf(".");
      if (lastDot !== -1) base = base.substring(0, lastDot);
      return {
        filename: `${base}.md`,
        content: i.markdown
      };
    });

    try {
      const response = await fetch("/api/download-zip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: filesPayload })
      });

      if (!response.ok) throw new Error("Gagal membuat zip");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "MarkItDown_Hasil_Konversi.zip";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showToast("Arsip ZIP berhasil diunduh!");
    } catch (err) {
      alert(`Gagal mengunduh ZIP: ${err.message}`);
    }
  });

  // Global helper to download single item from batch table
  window.downloadSingleBatchItem = function (index) {
    const item = batchQueue[index];
    if (!item || !item.markdown) return;

    let base = item.file.name;
    const lastDot = base.lastIndexOf(".");
    if (lastDot !== -1) base = base.substring(0, lastDot);
    const fname = `${base}.md`;

    const blob = new Blob([item.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fname;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`File ${fname} berhasil diunduh!`);
  };

  // Check server health
  fetch("/api/status")
    .then(r => r.json())
    .then(data => {
      const statusText = document.getElementById("serverStatusText");
      if (data && data.status === "online") {
        statusText.textContent = "Server Online";
      }
    })
    .catch(() => {
      const statusText = document.getElementById("serverStatusText");
      statusText.textContent = "Offline";
    });
});
