import requests

url = "http://127.0.0.1:5000/api/hitung_total"

# Contoh data input lengkap
data_input = {
    "berat_buah": [3.5, 2.0, 1.0],   # list berat buah dalam kg
    "jarak": 10.0,
    "harga_bensin": 14500,
    "cuaca": 1,    # 0 = cerah, 1 = hujan misal
    "libur": 1,    # 0 = bukan libur, 1 = libur
    "total_harga_buah": 65000.0      # total harga buah (misal 3.5*10000 + 2*10000 + 1*10000)
}

response = requests.post(url, json=data_input)

if response.status_code == 200:
    hasil = response.json()
    print("Total Harga:", hasil['total_harga'])
else:
    print("Request gagal, status code:", response.status_code)
