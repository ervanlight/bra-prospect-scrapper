import streamlit as st
import requests
import pandas as pd
import time

# --- PENGATURAN HALAMAN ---
st.set_page_config(
    page_title="Bra Business Prospecting",
    page_icon="👙",
    layout="wide"
)

# --- FUNGSI UTAMA SCRAPING ---
def get_google_places(api_key, lat, lng, radius, keyword):
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    places = []
    params = {
        'location': f"{lat},{lng}",
        'radius': radius,
        'keyword': keyword,
        'key': api_key
    }

    # Loop untuk mengambil halaman selanjutnya (Pagination)
    while True:
        try:
            response = requests.get(base_url, params=params)
            results = response.json()

            if response.status_code != 200:
                return None, f"Error API: {results.get('error_message', 'Unknown Error')}"

            # Ambil data per toko
            for place in results.get('results', []):
                # Filter agar data lebih relevan
                nama = place.get('name')
                rating = place.get('rating', 0)
                alamat = place.get('vicinity')
                total_review = place.get('user_ratings_total', 0)
                place_id = place.get('place_id')
                types = place.get('types', [])
                
                # Buat link Google Maps
                maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

                places.append({
                    "Nama Bisnis": nama,
                    "Rating": rating,
                    "Jumlah Review": total_review,
                    "Alamat": alamat,
                    "Google Maps Link": maps_url,
                    "Kategori": ", ".join(types[:3]) # Ambil 3 kategori teratas
                })

            # Cek apakah ada halaman berikutnya (Next Page Token)
            next_page_token = results.get('next_page_token')
            if not next_page_token:
                break # Berhenti jika tidak ada halaman lagi
            
            # Wajib: Google butuh jeda waktu sebelum token halaman berikutnya valid
            time.sleep(2)
            params = {
                'pagetoken': next_page_token,
                'key': api_key
            }
            
        except Exception as e:
            return None, str(e)

    return places, None

# --- TAMPILAN WEB APP (UI) ---
st.title("👙 Bra & Lingerie Prospect Scraper")
st.markdown("Aplikasi pencari toko potensial untuk kanvasing produk bra berdasarkan radius.")

# -- Sidebar untuk Konfigurasi --
with st.sidebar:
    st.header("Pengaturan")
    
    # Cek apakah API Key ada di Secrets (Untuk keamanan)
    if 'GOOGLE_MAPS_API_KEY' in st.secrets:
        api_key = st.secrets['GOOGLE_MAPS_API_KEY']
        st.success("API Key terdeteksi dari sistem aman.")
    else:
        api_key = st.text_input("Masukkan Google Places API Key", type="password")
        st.warning("⚠️ Masukkan API Key Anda di sini.")

    st.divider()
    st.info("Tips: Gunakan keyword 'Lingerie', 'Underwear', atau 'Grosir Pakaian' untuk hasil maksimal.")

# -- Input Parameter --
col1, col2, col3 = st.columns(3)

with col1:
    lat_input = st.text_input("Latitude (Garis Lintang)", "-6.175392") # Default Monas
with col2:
    lng_input = st.text_input("Longitude (Garis Bujur)", "106.827153")
with col3:
    radius = st.number_input("Radius (Meter)", min_value=100, max_value=50000, value=1000, step=100)

keyword = st.text_input("Kata Kunci Pencarian", "Toko Pakaian Wanita")

# -- Tombol Eksekusi --
if st.button("🔍 Mulai Scraping Data", type="primary"):
    if not api_key:
        st.error("Mohon masukkan API Key terlebih dahulu di Sidebar samping kiri.")
    else:
        with st.spinner("Sedang menyisir lokasi... Mohon tunggu sebentar..."):
            data_hasil, error_msg = get_google_places(api_key, lat_input, lng_input, radius, keyword)
            
            if error_msg:
                st.error(error_msg)
            elif not data_hasil:
                st.warning("Tidak ditemukan toko di lokasi tersebut dengan keyword ini.")
            else:
                # -- Tampilkan Hasil --
                df = pd.DataFrame(data_hasil)
                st.success(f"Berhasil menemukan {len(df)} lokasi potensial!")
                
                # Tampilkan Tabel
                st.dataframe(df, use_container_width=True)
                
                # Tombol Download CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Data ke Excel (CSV)",
                    data=csv,
                    file_name=f"prospek_{keyword}_{radius}m.csv",
                    mime="text/csv"
                )
