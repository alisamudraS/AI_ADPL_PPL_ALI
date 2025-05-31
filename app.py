from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import datetime
import locale
import holidays  # Mengimpor modul holidays

# Inisialisasi Flask app
app = Flask(__name__)

# Set locale untuk format mata uang
locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')

# Membaca data CSV
buah_df = pd.read_csv('data/buah.csv')  # Membaca data buah
bensin_df = pd.read_csv('data/bensin.csv')  # Membaca data bensin
latihan_model_df = pd.read_csv('data/data.csv')  # Membaca data latihan model yang sudah dibuat

# Fungsi untuk melatih model regresi dengan Random Forest
def latih_model():
    # Mengambil fitur dan target dari data latihan
    X = latihan_model_df[['berat_buah', 'jarak', 'harga_bensin', 'cuaca', 'libur']]  # Fitur (5 input)
    y = latihan_model_df[['persentase_cuaca', 'persentase_libur']]  # Target (2 output: persentase cuaca dan libur)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)  # Melatih model dengan 5 fitur dan 2 target (persentase cuaca dan libur)
    return model

# Fungsi untuk menghitung biaya tambahan berdasarkan cuaca dan libur
def hitung_biaya_dengan_persen(berat_buah, jarak, harga_bensin, cuaca, libur, harga_transportasi, total_harga_buah):
    print(f"Jarak: {jarak}, Harga Bensin: {harga_bensin}, Cuaca: {cuaca}, Libur: {libur}")  # Debugging
    print(f"Berat Buah: {berat_buah}")  # Debugging
    
    if jarak >= 10:
        biaya_libur = 0 if libur == 0 else total_harga_buah * 0.03  # 3% dari total harga buah
        biaya_cuaca = total_harga_buah * (0.03 if cuaca == 1 else 0.01)  # 3% jika hujan, 1% jika cerah
    elif jarak < 10:
        # Jika jarak < 10 km, persentase dihitung menggunakan model AI
        total_berat = sum([float(berat) for berat in berat_buah])  # Menghitung total berat buah
        print(f"Total Berat Buah: {total_berat}")  # Debugging untuk total berat
        input_data = np.array([[total_berat, jarak, harga_bensin, cuaca, libur]])  # Pastikan 5 fitur
        print(f"Input untuk Model AI: {input_data}")  # Debugging untuk memastikan input data
        model = latih_model()  # Melatih model atau memuat model yang sudah disimpan
        
        # Prediksi persentase cuaca dan libur (hasil model adalah array dua dimensi)
        prediksi = model.predict(input_data)  # Memastikan hasil adalah array 2D
        persentase_cuaca = prediksi[0][0]  # Ambil persentase cuaca dari prediksi
        persentase_libur = prediksi[0][1]  # Ambil persentase libur dari prediksi
        
        print(f"Persentase Cuaca yang diprediksi oleh model: {persentase_cuaca}")  # Debugging output prediksi cuaca
        print(f"Persentase Libur yang diprediksi oleh model: {persentase_libur}")  # Debugging output prediksi libur

        # Cek apakah persentase valid
        if persentase_cuaca < 0 or persentase_cuaca > 100:
            raise ValueError(f"Persentase cuaca yang diprediksi invalid: {persentase_cuaca}")
        
        if persentase_libur < 0 or persentase_libur > 100:
            raise ValueError(f"Persentase libur yang diprediksi invalid: {persentase_libur}")

        # Menghitung biaya libur dan cuaca
        # Jika libur = 0, biaya_libur tetap 0, meskipun prediksi model ada
        biaya_libur = 0 if libur == 0 else total_harga_buah * (persentase_libur / 100)
        biaya_cuaca = total_harga_buah * (persentase_cuaca / 100)
    
    # Debugging: print total harga buah dan biaya
    print(f"Total Harga Buah: {total_harga_buah}")
    print(f"Biaya Libur: {biaya_libur}")
    print(f"Biaya Cuaca: {biaya_cuaca}")
    
    return biaya_libur, biaya_cuaca






# Fungsi untuk mengecek apakah hari libur
def cek_hari_libur(tgl_distribusi):
    # Menggunakan modul holidays untuk mengambil hari libur nasional Indonesia
    id_holidays = holidays.Indonesia(years=datetime.datetime.now().year)

    # Ubah string tanggal menjadi objek datetime
    tgl = datetime.datetime.strptime(tgl_distribusi, "%Y-%m-%d")

    # Cek apakah hari Minggu atau tanggal tersebut ada dalam hari libur Indonesia
    if tgl.weekday() == 6:  # 6 = Minggu
        return 1  # Hari Minggu adalah hari libur
    if tgl in id_holidays:  # Mengecek apakah tanggal tersebut adalah hari libur nasional
        return 1  # 1 berarti hari libur
    return 0  # 0 berarti bukan hari libur

# Define the currency formatting filter
@app.template_filter('locale_currency')
def locale_currency_filter(value):
    return locale.currency(value, grouping=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Ambil data buah dan bensin dari CSV
    buah_list = buah_df['nama_buah'].tolist()  # Daftar nama buah dari CSV
    bensin_list = bensin_df['nama_bensin'].tolist()  # Daftar nama bensin dari CSV

    if request.method == 'POST':
        # Mengambil inputan dari form
        berat_buah = list(map(float, request.form.getlist('berat[]')))  # Daftar berat buah
        buah = request.form.getlist('buah[]')  # Daftar buah
        jarak = float(request.form.get('jarak'))  # Mengubah jarak ke float
        bensin = request.form.get('bensin')
        tgl_distribusi = request.form.get('tgl')
        cuaca = request.form.get('cuaca')

        # Mengambil harga bensin dari bensin.csv
        harga_bensin = bensin_df[bensin_df['nama_bensin'] == bensin]['harga_per_liter'].values[0]

        # Mengecek apakah hari libur
        libur = cek_hari_libur(tgl_distribusi)  # 1 jika hari libur, 0 jika bukan

        # Ambil harga buah berdasarkan pilihan
        total_harga_buah = 0
        for buah_item, berat in zip(buah, berat_buah):
            harga_buah = buah_df[buah_df['nama_buah'] == buah_item]['harga_per_kg'].values[0]
            total_harga_buah += harga_buah * berat  # Menggunakan zip untuk mencocokkan buah dan berat

        # Tentukan cuaca, 1 untuk hujan, 0 untuk cerah
        cuaca_value = 1 if cuaca == 'Hujan' else 0

        # Menghitung ongkir (biaya pengiriman) menggunakan model AI
        konsumsi_bensin_per_km = 1 / 40  # 1 liter untuk 40 km
        harga_transportasi = harga_bensin * konsumsi_bensin_per_km * jarak  # Menghitung biaya transportasi per km

        # Menghitung biaya libur dan cuaca berdasarkan transportasi
        biaya_libur, biaya_cuaca = hitung_biaya_dengan_persen(berat_buah, jarak, harga_bensin, cuaca_value, libur, harga_transportasi, total_harga_buah)

        # Total harga dihitung secara manual
        total_harga = total_harga_buah + harga_transportasi + biaya_libur + biaya_cuaca

        return render_template('index.html', 
                               total_harga=total_harga,  # Pass raw number for total cost
                               total_harga_buah=total_harga_buah,  # Pass total fruit price
                               harga_transportasi=harga_transportasi,  # Pass raw number for transport cost
                               biaya_libur=biaya_libur,   # Pass raw number for holiday cost
                               biaya_cuaca=biaya_cuaca,   # Pass raw number for weather cost
                               buah_list=buah_list,
                               bensin_list=bensin_list)

    return render_template('index.html', total_harga=None, buah_list=buah_list, bensin_list=bensin_list)

if __name__ == '__main__':
    app.run(debug=True)
