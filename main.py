from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = 'pesanan.json'
PRODUK_FILE = 'produk.json'

# 🔄 Load data pesanan
def load_pesanan():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# 💾 Simpan data pesanan
def save_pesanan(pesanan_list):
    with open(DATA_FILE, 'w') as f:
        json.dump(pesanan_list, f, indent=2)

# 🔄 Load data produk
def load_produk():
    if not os.path.exists(PRODUK_FILE):
        return []
    with open(PRODUK_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# 💾 Simpan data produk
def save_produk(produk_list):
    with open(PRODUK_FILE, 'w') as f:
        json.dump(produk_list, f, indent=2)

# ✅ POST /api/checkout
@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    if not data:
        return jsonify({"message": "❌ Data tidak valid"}), 400

    produk_list = load_produk()
    produk_ditemukan = None

    for p in produk_list:
        if p['nama'].lower() == data['nama_produk'].lower():
            produk_ditemukan = p
            break

    if not produk_ditemukan:
        return jsonify({"message": "❌ Produk tidak ditemukan"}), 404

    if produk_ditemukan['stok'] < data['jumlah']:
        return jsonify({"message": "❌ Stok tidak cukup"}), 400

    pesanan_list = load_pesanan()
    if 'id' not in data:
        data['id'] = str(uuid.uuid4())

    data['status'] = 'pending'
    pesanan_list.append(data)
    save_pesanan(pesanan_list)

    return jsonify({"message": "✅ Pesanan diterima", "id": data['id']}), 200

# 📦 GET /api/admin/pesanan
@app.route('/api/admin/pesanan', methods=['GET'])
def get_pesanan():
    return jsonify(load_pesanan()), 200

# 🔁 PUT /api/admin/pesanan/<id>
@app.route('/api/admin/pesanan/<id>', methods=['PUT'])
def update_status(id):
    pesanan_list = load_pesanan()
    produk_list = load_produk()
    updated = False

    for pesanan in pesanan_list:
        if pesanan['id'] == id:
            if pesanan['status'] == 'berhasil':
                return jsonify({"message": "❗ Sudah berhasil sebelumnya"}), 400

            pesanan['status'] = 'berhasil'
            # kurangi stok
            for produk in produk_list:
                if produk['nama'].lower() == pesanan['nama_produk'].lower():
                    produk['stok'] -= pesanan['jumlah']
                    if produk['stok'] < 0:
                        produk['stok'] = 0
                    save_produk(produk_list)
                    break

            updated = True
            break

    if updated:
        save_pesanan(pesanan_list)
        return jsonify({"message": "✅ Status berhasil diperbarui & stok dikurangi"}), 200
    else:
        return jsonify({"message": "❌ Pesanan tidak ditemukan"}), 404

# ✅ GET /api/status/<id>
@app.route('/api/status/<id>', methods=['GET'])
def cek_status(id):
    pesanan_list = load_pesanan()
    for pesanan in pesanan_list:
        if pesanan['id'] == id:
            return jsonify({"status": pesanan['status']}), 200
    return jsonify({"message": "❌ Pesanan tidak ditemukan"}), 404

# ✅ GET /api/produk
@app.route('/api/produk', methods=['GET'])
def get_produk():
    return jsonify(load_produk()), 200

# ✅ POST /api/admin/produk
@app.route('/api/admin/produk', methods=['POST'])
def tambah_produk():
    data = request.get_json()
    if not data or 'nama' not in data or 'harga' not in data or 'stok' not in data:
        return jsonify({"message": "❌ Data tidak lengkap"}), 400

    produk_list = load_produk()

    # cek biar nama produk ga dobel
    for p in produk_list:
        if p['nama'].lower() == data['nama'].lower():
            return jsonify({"message": "❗ Produk sudah ada"}), 400

    produk_baru = {
        "nama": data['nama'],
        "harga": data['harga'],
        "stok": data['stok'],
        "gambar": data.get('gambar', '')  # default kosong kalau gak dikirim
    }

    produk_list.append(produk_baru)
    save_produk(produk_list)

    return jsonify({"message": "✅ Produk berhasil ditambahkan"}), 200

# ✏️ PUT /api/admin/produk/<nama>
@app.route('/api/admin/produk/<nama>', methods=['PUT'])
def edit_produk(nama):
    data = request.get_json()
    if not data:
        return jsonify({"message": "❌ Data tidak dikirim"}), 400

    produk_list = load_produk()
    updated = False

    for produk in produk_list:
        if produk['nama'].lower() == nama.lower():
            produk['nama'] = data.get('nama', produk['nama'])
            produk['harga'] = data.get('harga', produk['harga'])
            produk['stok'] = data.get('stok', produk['stok'])
            produk['gambar'] = data.get('gambar', produk.get('gambar', ''))
            updated = True
            break

    if updated:
        save_produk(produk_list)
        return jsonify({"message": "✅ Produk berhasil diedit"}), 200
    else:
        return jsonify({"message": "❌ Produk tidak ditemukan"}), 404

# ❌ DELETE /api/admin/produk/<nama>
@app.route('/api/admin/produk/<nama>', methods=['DELETE'])
def hapus_produk(nama):
    produk_list = load_produk()
    awal = len(produk_list)

    produk_list = [p for p in produk_list if p['nama'].lower() != nama.lower()]

    if len(produk_list) == awal:
        return jsonify({"message": "❌ Produk tidak ditemukan"}), 404

    save_produk(produk_list)
    return jsonify({"message": "🗑️ Produk berhasil dihapus"}), 200
# 🎨 Halaman Utama
@app.route('/')
def index():
    return '''
    <html>
      <head>
        <title>ZYEN STORE API</title>
        <style>
          body {
            background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
            color: white;
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            padding-top: 100px;
          }
          h1 {
            font-size: 40px;
            margin-bottom: 10px;
          }
          p {
            font-size: 18px;
            margin-top: 0;
          }
          .tag {
            margin-top: 40px;
            font-size: 14px;
            color: #ccc;
          }
        </style>
      </head>
      <body>
        <h1>🔥 ZYEN STORE API AKTIF 🔥</h1>
        <p>Semua sistem backend berjalan dengan lancar</p>
        <div class="tag">Dibuat oleh <strong>@Zyen</strong></div>
      </body>
    </html>
    '''

# 🚀 Jalankan server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)