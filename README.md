# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Proyek ini menganalisis data e-commerce Olist (Brasil) periode Januari 2017 - Agustus 2018
untuk menjawab dua pertanyaan bisnis:

1. Berapa selisih rata-rata skor review antara order yang terlambat dan yang tepat waktu,
   dan di state mana persentase keterlambatannya paling tinggi?
2. Kategori produk mana yang masuk 10 besar revenue pada Januari-Agustus 2018, dan bagaimana
   pertumbuhannya dibandingkan periode yang sama di 2017?

Analisis lanjutan: analisis geospasial untuk memetakan keterlambatan per state.

## Struktur Folder

submission
├── dashboard
│   ├── main_data.csv
│   └── dashboard.py
├── data
│   └── (9 file CSV dataset Olist)
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt

- `data/` berisi dataset mentah.
- `notebook.ipynb` berisi seluruh proses analisis (wrangling, EDA, visualisasi, analisis lanjutan).
- `dashboard/main_data.csv` adalah data hasil cleaning dan penggabungan dari notebook, yang dipakai dashboard.
- `url.txt` berisi tautan dashboard di Streamlit Cloud.

## Cara Menjalankan Dashboard di Komputer

1. Pastikan Python sudah terpasang.
2. Buka terminal di folder `submission`, lalu pasang library:

   python -m pip install -r requirements.txt

3. Masuk ke folder dashboard dan jalankan:

   cd dashboard
   python -m streamlit run dashboard.py

4. Buka alamat yang tampil di terminal.

## Dashboard Online

Tautan dashboard ada di `url.txt`.
