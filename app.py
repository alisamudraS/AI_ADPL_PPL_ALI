from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import datetime
import holidays

app = Flask(__name__)

latihan_model_df = pd.read_csv('data.csv')

def latih_model():
    X = latihan_model_df[['berat_buah', 'jarak', 'harga_bensin', 'cuaca', 'libur']]
    y = latihan_model_df[['persentase_cuaca', 'persentase_libur']]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

model = latih_model()

def cek_hari_libur(tgl_distribusi):
    id_holidays = holidays.Indonesia(years=datetime.datetime.now().year)
    tgl = datetime.datetime.strptime(tgl_distribusi, "%d-%m-%Y")
    if tgl.weekday() == 6:  # Minggu
        return 1
    if tgl in id_holidays:
        return 1
    return 0

def hitung_biaya_dengan_persen(berat_buah, jarak, harga_bensin, cuaca, libur, harga_transportasi, total_harga_buah):
    if jarak >= 10:
        biaya_libur = 0 if libur == 0 else total_harga_buah * 0.03
        biaya_cuaca = total_harga_buah * (0.03 if cuaca == 1 else 0.01)
    else:
        total_berat = sum([float(berat) for berat in berat_buah])
        input_data = np.array([[total_berat, jarak, harga_bensin, cuaca, libur]])
        prediksi = model.predict(input_data)
        persentase_cuaca = prediksi[0][0]
        persentase_libur = prediksi[0][1]
        biaya_libur = 0 if libur == 0 else total_harga_buah * (persentase_libur / 100)
        biaya_cuaca = total_harga_buah * (persentase_cuaca / 100)
    return biaya_libur, biaya_cuaca

def hitung_harga_transportasi(jarak, harga_bensin):
    konsumsi_bensin_per_km = 1 / 40
    return jarak * harga_bensin * konsumsi_bensin_per_km

@app.route('/api/hitung_total', methods=['POST'])
def api_hitung_total():
    data = request.json
    berat_buah = data.get('berat_buah')
    jarak = float(data.get('jarak'))
    harga_bensin = float(data.get('harga_bensin'))
    cuaca = int(data.get('cuaca'))
    tgl_distribusi = data.get('tanggal')  # input tanggal dalam format 'dd-mm-yyyy'

    # Cek hari libur berdasarkan tanggal
    libur = cek_hari_libur(tgl_distribusi)

    # Hitung total harga buah (pakai asumsi 10.000/kg seperti biasa)
    total_harga_buah = 0
    for berat in berat_buah:
        total_harga_buah += float(berat) * 10000

    harga_transportasi = hitung_harga_transportasi(jarak, harga_bensin)

    biaya_libur, biaya_cuaca = hitung_biaya_dengan_persen(
        berat_buah, jarak, harga_bensin, cuaca, libur, harga_transportasi, total_harga_buah)

    total_harga = total_harga_buah + harga_transportasi + biaya_libur + biaya_cuaca

    return jsonify({'total_harga': total_harga})

if __name__ == '__main__':
    app.run(debug=True)
