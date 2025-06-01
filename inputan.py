import requests

url = "http://127.0.0.1:5000/api/hitung_total"

# Contoh data input lengkap
data_input = {
  "berat_buah": [3.5, 2.0, 1.5],  # Berat buah dalam kg
  "jarak": 6,
  "harga_bensin": 14500,
  "cuaca": 1,
  "tanggal": "01-06-2025"
}

response = requests.post(url, json=data_input)

if response.status_code == 200:
    hasil = response.json()
    print("Total Harga:", hasil['total_harga'])
else:
    print("Request gagal, status code:", response.status_code)
