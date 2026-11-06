import os
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import numpy as np

st.set_page_config(page_title='Dashboard E-Commerce', page_icon='🛒', layout='wide')


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(__file__), 'main_data.csv')
    return pd.read_csv(path, parse_dates=['tanggal_order'])


df = load_data()

# ---------- Sidebar: filter periode ----------
st.sidebar.header('Filter')
tgl_min = df['tanggal_order'].min().date()
tgl_max = df['tanggal_order'].max().date()
rentang = st.sidebar.date_input('Periode order', value=(tgl_min, tgl_max),
                                min_value=tgl_min, max_value=tgl_max)
st.sidebar.caption('Filter periode berlaku untuk ringkasan, keterlambatan, dan peta. '
                   'Bagian kategori produk selalu membandingkan Januari-Agustus 2018 dengan 2017.')

if len(rentang) != 2:
    st.info('Pilih tanggal awal dan tanggal akhir pada filter di sebelah kiri.')
    st.stop()

awal, akhir = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1]) + pd.Timedelta(days=1)
df_f = df[(df['tanggal_order'] >= awal) & (df['tanggal_order'] < akhir)]

if df_f.empty:
    st.warning('Tidak ada order pada periode yang dipilih.')
    st.stop()

# Satu baris per order untuk perhitungan keterlambatan dan skor review
order_unik = df_f.drop_duplicates('order_id')

# ---------- Judul ----------
st.title('🛒 Dashboard Analisis E-Commerce Olist')
st.caption('Order berstatus delivered, Januari 2017 - Agustus 2018. Revenue dihitung dari harga barang (tanpa ongkir), dalam BRL.')

# ---------- Ringkasan (KPI) ----------
skor_tepat = order_unik.loc[~order_unik['terlambat'], 'review_score'].mean()
skor_telat = order_unik.loc[order_unik['terlambat'], 'review_score'].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric('Total order', f"{order_unik['order_id'].nunique():,}")
k2.metric('Revenue (BRL)', f"{df_f['price'].sum():,.0f}")
k3.metric('Order terlambat', f"{order_unik['terlambat'].mean() * 100:.1f}%")
k4.metric('Skor order tepat waktu', '-' if pd.isna(skor_tepat) else f'{skor_tepat:.2f}')
k5.metric('Skor order terlambat', '-' if pd.isna(skor_telat) else f'{skor_telat:.2f}')

# ---------- Tab ----------
tab1, tab2, tab3 = st.tabs(['Keterlambatan & Review', 'Kategori Produk', 'Peta Keterlambatan'])

with tab1:
    # ----- Grafik 1: skor review tepat waktu vs terlambat -----
    st.subheader('Apakah order yang terlambat mendapat skor review lebih rendah?')

    ringkas = (order_unik.assign(status_kirim=order_unik['terlambat'].map({True: 'Terlambat', False: 'Tepat waktu'}))
               .groupby('status_kirim')['review_score'].mean()
               .reindex(['Tepat waktu', 'Terlambat']).dropna())
    warna = {'Tepat waktu': '#9AA5B1', 'Terlambat': '#D1495B'}

    fig, ax = plt.subplots(figsize=(6, 4.5))
    batang = ax.bar(ringkas.index, ringkas.values, color=[warna[i] for i in ringkas.index], width=0.55)
    for b, v in zip(batang, ringkas.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f'{v:.2f}', ha='center', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 5)
    ax.set_ylabel('Rata-rata skor review (skala 1-5)')
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    kolom_grafik, _ = st.columns([1, 1])
    with kolom_grafik:
        st.pyplot(fig)

    if len(ringkas) == 2:
        selisih = ringkas['Tepat waktu'] - ringkas['Terlambat']
        st.write(f'Order yang terlambat rata-rata mendapat skor **{selisih:.2f} poin lebih rendah** '
                 'dibanding order yang tiba tepat waktu.')
    else:
        st.info('Pada periode ini hanya ada satu kelompok (semua order tepat waktu atau semua terlambat), '
                'jadi perbandingan tidak bisa ditampilkan.')

    st.divider()

    # ----- Grafik 2: state dengan keterlambatan tertinggi -----
    st.subheader('Di state mana keterlambatannya paling tinggi?')
    min_order = st.slider('Minimal jumlah order per state (agar persentasenya stabil)',
                          min_value=10, max_value=500, value=100, step=10)

    per_state = (order_unik.groupby('customer_state')
                 .agg(total_order=('order_id', 'count'), order_terlambat=('terlambat', 'sum'))
                 .reset_index())
    per_state['persen_terlambat'] = per_state['order_terlambat'] / per_state['total_order'] * 100
    state_valid = per_state[per_state['total_order'] >= min_order]

    if state_valid.empty:
        st.info('Tidak ada state yang memenuhi batas minimal order. Turunkan batasnya.')
    else:
        top_state = state_valid.sort_values('persen_terlambat', ascending=False).head(10)
        rata_rata = order_unik['terlambat'].mean() * 100

        fig, ax = plt.subplots(figsize=(8, 5.5))
        warna_bar = ['#D1495B' if i < 3 else '#9AA5B1' for i in range(len(top_state))]
        ax.barh(top_state['customer_state'], top_state['persen_terlambat'], color=warna_bar)
        ax.invert_yaxis()
        for i, v in enumerate(top_state['persen_terlambat']):
            ax.text(v + 0.3, i, f'{v:.1f}%', va='center', fontsize=10)
        ax.axvline(rata_rata, color='black', linestyle='--', linewidth=1,
                   label=f'Rata-rata seluruh order ({rata_rata:.1f}%)')
        ax.legend(loc='lower right', frameon=False)
        ax.set_xlabel('Persentase order terlambat (%)')
        ax.set_ylabel('State')
        ax.set_xlim(0, top_state['persen_terlambat'].max() + 4)
        ax.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        st.caption(f'Menampilkan maksimal 10 state dengan minimal {min_order} order.')

with tab2:
    st.subheader('Kategori produk mana yang paling besar revenue-nya, dan bagaimana pertumbuhannya?')
    st.caption('Perbandingan selalu Januari-Agustus 2018 dengan Januari-Agustus 2017, jadi tidak mengikuti filter periode di sebelah kiri.')

    jumlah_kategori = st.slider('Jumlah kategori teratas yang ditampilkan', min_value=5, max_value=15, value=10)

    df_jan_agu = df[df['tanggal_order'].dt.month <= 8]
    rev = df_jan_agu.pivot_table(index='kategori_produk', columns=df_jan_agu['tanggal_order'].dt.year,
                                 values='price', aggfunc='sum', fill_value=0)
    rev.columns = [f'revenue_{c}' for c in rev.columns]

    total_2017, total_2018 = rev['revenue_2017'].sum(), rev['revenue_2018'].sum()
    pertumbuhan_total = (total_2018 - total_2017) / total_2017 * 100

    top = rev.sort_values('revenue_2018', ascending=False).head(jumlah_kategori).copy()
    top['pertumbuhan_persen'] = np.where(top['revenue_2017'] > 0,
                                         (top['revenue_2018'] - top['revenue_2017']) / top['revenue_2017'] * 100,
                                         np.nan)

    m1, m2, m3 = st.columns(3)
    m1.metric('Revenue Jan-Agu 2017 (BRL)', f'{total_2017:,.0f}')
    m2.metric('Revenue Jan-Agu 2018 (BRL)', f'{total_2018:,.0f}')
    m3.metric('Pertumbuhan total', f'{pertumbuhan_total:.0f}%')

    data_plot = top.sort_values('revenue_2018')   # terbesar berada di atas
    y = np.arange(len(data_plot))
    tinggi = 0.38

    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(y + tinggi / 2, data_plot['revenue_2017'] / 1000, height=tinggi, color='#B8C0CC', label='Jan-Agu 2017')
    ax.barh(y - tinggi / 2, data_plot['revenue_2018'] / 1000, height=tinggi, color='#2E6F9E', label='Jan-Agu 2018')

    for i, (rev18, growth) in enumerate(zip(data_plot['revenue_2018'], data_plot['pertumbuhan_persen'])):
        lambat = (not np.isnan(growth)) and growth < pertumbuhan_total
        teks_growth = 'baru' if np.isnan(growth) else f'+{growth:.0f}%'
        ax.text(rev18 / 1000 + 12, i - tinggi / 2, f'{rev18 / 1000:,.0f} rb  ({teks_growth})',
                va='center', fontsize=9.5, color='#D1495B' if lambat else '#1B1B1B',
                fontweight='bold' if lambat else 'normal')

    ax.set_yticks(y)
    ax.set_yticklabels(data_plot.index)
    ax.set_xlabel('Revenue (ribu BRL)')
    ax.set_title(f'Merah = tumbuh di bawah rata-rata total ({pertumbuhan_total:.0f}%)', fontsize=11)
    ax.set_xlim(0, data_plot['revenue_2018'].max() / 1000 * 1.3)
    ax.legend(loc='lower right', frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)

    with st.expander('Lihat tabel angka'):
        tabel = top.reset_index().rename(columns={'kategori_produk': 'Kategori', 'revenue_2017': 'Revenue 2017',
                                                  'revenue_2018': 'Revenue 2018', 'pertumbuhan_persen': 'Pertumbuhan (%)'})
        st.dataframe(tabel.round(1), hide_index=True, width='stretch')

with tab3:
    st.subheader('Bagaimana sebaran keterlambatan pengiriman di seluruh Brasil?')
    st.caption('Mengikuti filter periode di sebelah kiri. Warna = persentase order terlambat, ukuran = jumlah order. '
               'Posisi tiap state adalah rata-rata koordinat kode posnya (perkiraan kasar).')

    min_order_peta = st.slider('Minimal jumlah order per state (di bawahnya digambar sebagai lingkaran kosong)',
                               min_value=10, max_value=500, value=100, step=10, key='min_order_peta')

    peta = (order_unik.groupby('customer_state')
            .agg(total_order=('order_id', 'count'), order_terlambat=('terlambat', 'sum'),
                 lat=('state_lat', 'first'), lng=('state_lng', 'first'))
            .reset_index())
    peta['persen_terlambat'] = peta['order_terlambat'] / peta['total_order'] * 100

    cukup = peta['total_order'] >= min_order_peta
    ukuran = 60 + np.sqrt(peta['total_order']) * 5   # skala akar agar state kecil tetap terlihat

    if not cukup.any():
        st.info('Tidak ada state yang memenuhi batas minimal order. Turunkan batasnya.')
    else:
        fig, ax = plt.subplots(figsize=(9, 9))

        ax.scatter(peta.loc[~cukup, 'lng'], peta.loc[~cukup, 'lat'], s=ukuran[~cukup],
                   facecolors='none', edgecolors='#7A8594', linewidths=1.3,
                   label=f'Order < {min_order_peta} (tidak diperingkat)')

        sc = ax.scatter(peta.loc[cukup, 'lng'], peta.loc[cukup, 'lat'], s=ukuran[cukup],
                        c=peta.loc[cukup, 'persen_terlambat'], cmap='YlOrRd', vmin=0,
                        edgecolors='#555555', linewidths=0.6, alpha=0.9)

        for _, r in peta.iterrows():
            if r['total_order'] >= 3000:      # lingkaran besar: label di tengah
                ax.annotate(r['customer_state'], (r['lng'], r['lat']), ha='center', va='center',
                            fontsize=9, fontweight='bold')
            else:                              # lingkaran kecil: label digeser agar tidak menutupi
                ax.annotate(r['customer_state'], (r['lng'], r['lat']), xytext=(8, 6),
                            textcoords='offset points', fontsize=8.5, fontweight='bold')

        cbar = plt.colorbar(sc, ax=ax, shrink=0.6)
        cbar.set_label('Persentase order terlambat (%)')
        ax.set_xlabel('Bujur')
        ax.set_ylabel('Lintang')
        if (~cukup).any():
            ax.legend(loc='lower left', frameon=False)
        ax.set_aspect('equal')
        ax.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()

        kolom_peta, kolom_tabel = st.columns([3, 2])
        with kolom_peta:
            st.pyplot(fig)
        with kolom_tabel:
            st.markdown('**5 state dengan keterlambatan tertinggi**')
            tinggi5 = (peta[cukup].sort_values('persen_terlambat', ascending=False).head(5)
                       [['customer_state', 'total_order', 'persen_terlambat']]
                       .rename(columns={'customer_state': 'State', 'total_order': 'Total order',
                                        'persen_terlambat': 'Terlambat (%)'}))
            st.dataframe(tinggi5.round(1), hide_index=True, width='stretch')
