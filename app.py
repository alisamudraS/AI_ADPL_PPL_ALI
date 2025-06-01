from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import datetime
import subprocess
import csv
import os
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
    if tgl.weekday() == 6:
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

def append_data_to_csv(data_row, csv_path='datalatihreal.csv'):
    # Jika file belum ada, buat header terlebih dahulu
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['berat_buah', 'jarak', 'harga_bensin', 'cuaca', 'libur', 'persentase_cuaca', 'persentase_libur']
            writer.writerow(header)
    # Append data row
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data_row)

def git_commit_and_push(csv_path='datalatihreal.csv'):
    try:
        subprocess.run(['git', 'add', csv_path], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update datalatihreal.csv with new input data'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")

@app.route('/api/hitung_total', methods=['POST'])
def api_hitung_total():
    data = request.json
    berat_buah = data.get('berat_buah')  # list berat buah
    jarak = float(data.get('jarak'))
    harga_bensin = float(data.get('harga_bensin'))
    cuaca = int(data.get('cuaca'))
    tanggal = data.get('tanggal')  # format 'dd-mm-yyyy'

    # Cek hari libur otomatis dari tanggal
    libur = cek_hari_libur(tanggal)

    # Hitung total harga buah (asumsi harga 10.000/kg)
    total_harga_buah = sum(float(b) * 10000 for b in berat_buah)

    harga_transportasi = hitung_harga_transportasi(jarak, harga_bensin)

    biaya_libur, biaya_cuaca = hitung_biaya_dengan_persen(
        berat_buah, jarak, harga_bensin, cuaca, libur, harga_transportasi, total_harga_buah)

    total_harga = total_harga_buah + harga_transportasi + biaya_libur + biaya_cuaca

    # Prediksi persentase cuaca dan libur untuk simpan di csv
    if jarak < 10:
        input_model = np.array([[sum(float(b) for b in berat_buah), jarak, harga_bensin, cuaca, libur]])
        prediksi = model.predict(input_model)[0]
        persentase_cuaca, persentase_libur = prediksi[0], prediksi[1]
    else:
        # Kalau jarak >= 10, pakai persentase default
        persentase_cuaca = 0.03 if cuaca == 1 else 0.01
        persentase_libur = 0.03 if libur == 1 else 0.0

    # Data yang akan ditambahkan ke CSV
    data_row = [
        sum(float(b) for b in berat_buah),
        jarak,
        harga_bensin,
        cuaca,
        libur,
        persentase_cuaca,
        persentase_libur
    ]

    append_data_to_csv(data_row)
    git_commit_and_push()

    return jsonify({'total_harga': total_harga})

if __name__ == '__main__':
    app.run(debug=True)
