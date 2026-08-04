import streamlit as st
from pypdf import PdfReader
import pandas as pd
import re

# Pengaturan Halaman Streamlit
st.set_page_config(
    page_title="PDF Multi-File Word Detector",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Deteksi Kata Kunci PDF & Ekspor Tabel Excel")
st.write("Unggah satu atau beberapa file PDF, masukkan kata kunci, dan dapatkan tabel rekapitulasi yang siap dicopy/di-paste ke Excel.")

# Sidebar untuk Pengaturan
st.sidebar.header("⚙️ Pengaturan Pencarian")
case_sensitive = st.sidebar.checkbox("Peka Huruf Besar/Kecil (Case Sensitive)", value=False)
exact_match = st.sidebar.checkbox("Kata Utuh Sahaja / Exact Word Match (contoh: 'erp' bukan 'interpretasi')", value=True)
max_snippets = st.sidebar.number_input("Maksimal Cuplikan per Kata per Halaman", min_value=1, max_value=5, value=2)

# 1. Upload Multiple File PDF
uploaded_files = st.file_uploader(
    "Unggah satu atau beberapa file PDF di sini", 
    type=["pdf"], 
    accept_multiple_files=True
)

# 2. Input Banyak Kata Kunci
input_keywords = st.text_input(
    "Masukkan kata/frasa kunci (pisahkan dengan koma):", 
    placeholder="Contoh: erp, laporan, tanggal, total bayar..."
)

if uploaded_files and input_keywords:
    # Memproses daftar kata kunci
    keywords = [kw.strip() for kw in input_keywords.split(",") if kw.strip()]
    
    if not keywords:
        st.warning("Masukkan setidaknya satu kata kunci yang valid.")
    else:
        flags = 0 if case_sensitive else re.IGNORECASE
        
        table_data = []
        all_file_details = {}

        with st.spinner("Sedang memproses dan menganalisis semua file PDF..."):
            for uploaded_file in uploaded_files:
                file_name = uploaded_file.name
                reader = PdfReader(uploaded_file)
                
                word_counts = {kw: 0 for kw in keywords}
                file_details = {}
                total_all_words_in_file = 0  # Penampung total seluruh kata dalam PDF

                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Menghitung total kata keseluruhan pada halaman ini
                    page_words = len(text.split())
                    total_all_words_in_file += page_words
                    
                    for kw in keywords:
                        if exact_match:
                            pattern = re.compile(r'\b' + re.escape(kw) + r'\b', flags)
                        else:
                            pattern = re.compile(re.escape(kw), flags)
                            
                        matches = list(pattern.finditer(text))
                        
                        if matches:
                            count = len(matches)
                            word_counts[kw] += count
                            
                            # Mengambil cuplikan teks
                            snippets = []
                            for match in matches[:max_snippets]:
                                start = max(0, match.start() - 35)
                                end = min(len(text), match.end() + 35)
                                snippet = text[start:end].replace("\n", " ").strip()
                                snippets.append(f"...{snippet}...")
                            
                            if page_num not in file_details:
                                file_details[page_num] = {}
                            
                            file_details[page_num][kw] = {
                                "count": count,
                                "snippets": snippets
                            }

                total_matched_words = sum(word_counts.values())
                
                # Susun struktur kolom tabel
                row = {"Nama File": file_name}
                for kw in keywords:
                    row[kw] = word_counts[kw]
                row["Total Word"] = total_matched_words
                row["Total All Words"] = total_all_words_in_file  # Kolom Paling Akhir
                
                table_data.append(row)
                all_file_details[file_name] = file_details

        # Buat DataFrame Pandas
        df = pd.DataFrame(table_data)

        st.markdown("---")
        
        # 3. TAMPILAN TABEL REKAPITULASI
        st.subheader("📋 Tabel Rekapitulasi Kemunculan Kata")
        st.caption("💡 **Tips Copy ke Excel:** Anda bisa langsung memblok sel pada tabel interaktif di bawah dan menekan **Ctrl+C / Cmd+C**, lalu tempel (**Ctrl+V**) di Microsoft Excel / Google Sheets.")

        # Menampilkan Tabel Interaktif Streamlit
        st.dataframe(df, use_container_width=True)

        # 4. TEKS TABEL TSV (CLIPBOARD SUPPORT EXCEL)
        st.subheader("✂️ Teks Clipboard (Format Tab-Separated)")
        st.caption("💡 Klik tombol icon **Copy** di pojok kanan atas kotak di bawah, lalu lakukan **Paste (Ctrl+V)** langsung ke Microsoft Excel.")
        
        # Konversi dataframe ke format TSV (Tab Separated Values)
        tsv_data = df.to_csv(sep="\t", index=False)
        st.code(tsv_data, language="text")

        st.markdown("---")
        
        # 5. RINCIAN DETAIL PER FILE & HALAMAN
        st.subheader("📌 Rincian Letak Halaman & Cuplikan Teks per File")
        
        for file_name, file_details in all_file_details.items():
            with st.expander(f"📁 **File: {file_name}**"):
                if file_details:
                    for page_num, kw_data in file_details.items():
                        st.markdown(f"📖 **Halaman {page_num}**")
                        for kw, data in kw_data.items():
                            st.markdown(f"- **Kata `{kw}`** *(ditemukan {data['count']} kali):*")
                            for snip in data["snippets"]:
                                if exact_match:
                                    highlight_pattern = re.compile(r'\b(' + re.escape(kw) + r')\b', flags)
                                else:
                                    highlight_pattern = re.compile(r'(' + re.escape(kw) + r')', flags)
                                    
                                highlighted = highlight_pattern.sub(r"**:\1:**", snip)
                                st.write(f"  - {highlighted}")
                else:
                    st.write("Tidak ada kata kunci yang ditemukan pada file ini.")

elif uploaded_files and not input_keywords:
    st.info("Silakan masukkan kata kunci pada kolom di atas (pisahkan dengan koma).")