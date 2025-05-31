from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import datetime
import locale
import holidays

app = Flask(__name__)

locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')

buah_df = pd.read_csv('data/buah.csv')
bensin_df = pd.read_csv('data/bensin.csv')
latihan_model_df = pd.read_csv('data/data.csv')

def latih_model():
    X = latihan_model_df[['berat_buah', 'jarak', 'harga_bensin', 'cuaca', 'libur']]
    y = latihan_model_df[['persentase_cuaca', 'persentase_libur']]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

model = latih_model()

def hitung_biaya_dengan_persen(berat_buah, jarak, harga_bensin, cuaca, libur, harga_transportasi, total_harga_buah):
    # (logika asli kamu tidak saya ubah, hanya dikopi di sini)
    if jarak >= 10:
        biaya_libur = 0 if libur == 0 else total_harga_buah * 0.03
        biaya_cuaca = total_harga_buah * (0.03 if cuaca == 1 else 0.01)
    elif jarak < 10:
        total_berat = sum([float(berat) for berat in berat_buah])
        input_data = np.array([[total_berat, jarak, harga_bensin, cuaca, libur]])
        prediksi = model.predict(input_data)
        persentase_cuaca = prediksi[0][0]
        persentase_libur = prediksi[0][1]
        biaya_libur = 0 if libur == 0 else total_harga_buah * (persentase_libur / 100)
        biaya_cuaca = total_harga_buah * (persentase_cuaca / 100)
    return biaya_libur, biaya_cuaca

def cek_hari_libur(tgl_distribusi):
    id_holidays = holidays.Indonesia(years=datetime.datetime.now().year)
    tgl = datetime.datetime.strptime(tgl_distribusi, "%Y-%m-%d")
    if tgl.weekday() == 6:
        return 1
    if tgl in id_holidays:
        return 1
    return 0

# Tambah route API POST untuk terima input JSON dan return total_harga saja
@app.route('/api/hitung_total', methods=['POST'])
def api_hitung_total():
    data = request.json
    # Data input di sini harus dikirim dalam JSON dengan key sesuai
    berat_buah = data.get('berat_buah')  # Harus berupa list [float, float, ...]
    jarak = float(data.get('jarak'))
    harga_bensin = float(data.get('harga_bensin'))
    cuaca = int(data.get('cuaca'))
    libur = int(data.get('libur'))

    # Hitung total harga buah sama seperti logika asli kamu
    total_harga_buah = 0
    # Karena di sini berat_buah dikirim langsung, tanpa nama buah, kita pakai asumsi harga 10.000/kg saja
    # Jika kamu ingin harga berbeda per buah, ini perlu input nama buah juga
    for berat in berat_buah:
        total_harga_buah += berat * 10000  # sesuai asumsi kamu

    konsumsi_bensin_per_km = 1 / 40
    harga_transportasi = harga_bensin * konsumsi_bensin_per_km * jarak

    biaya_libur, biaya_cuaca = hitung_biaya_dengan_persen(
        berat_buah, jarak, harga_bensin, cuaca, libur, harga_transportasi, total_harga_buah)

    total_harga = total_harga_buah + harga_transportasi + biaya_libur + biaya_cuaca

    # Kembalikan hasil dalam JSON hanya total_harga
    return jsonify({'total_harga': total_harga})

# Jangan ubah route index dan logika lain kamu, tetap jalan seperti biasa

if __name__ == '__main__':
    app.run(debug=True)
