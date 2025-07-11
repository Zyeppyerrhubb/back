from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
import json
import os

app = Flask(__name__)
app.secret_key = "zyensecretkey"  # buat session login
CORS(app, supports_credentials=True)

DATA_FILE = 'pesanan.json'
PRODUK_FILE = 'produk.json'
USER_FILE = 'user.json'

def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"message": "❌ Username & password wajib diisi"}), 400

    users = load_json(USER_FILE)
    if any(u["username"] == username for u in users):
        return jsonify({"message": "❗ Username sudah terdaftar"}), 400

    users.append({"username": username, "password": password, "role": "user"})
    save_json(USER_FILE, users)
    return jsonify({"message": "✅ Akun berhasil dibuat"}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    users = load_json(USER_FILE)

    for user in users:
        if user["username"] == username and user["password"] == password:
            session["username"] = username
            session["role"] = user["role"]
            return jsonify({"message": "✅ Login berhasil", "role": user["role"]})
    
    return jsonify({"message": "❌ Username atau password salah"}), 401

@app.route("/api/auth/logout", methods=["GET"])
def logout():
    session.clear()
    return jsonify({"message": "✅ Logout berhasil"})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    if not data:
        return jsonify({"message": "❌ Data tidak valid"}), 400

    produk_list = load_json(PRODUK_FILE)
    produk_ditemukan = next((p for p in produk_list if p['nama'].lower() == data['nama_produk'].lower()), None)

    if not produk_ditemukan:
        return jsonify({"message": "❌ Produk tidak ditemukan"}), 404

    if produk_ditemukan['stok'] < data['jumlah']:
        return jsonify({"message": "❌ Stok tidak cukup"}), 400

    pesanan_list = load_json(DATA_FILE)
    data['id'] = str(uuid.uuid4())
    data['status'] = 'pending'
    
    # ✅ support user non-login
    data["username"] = session["username"] if "username" in session else "guest"

    pesanan_list.append(data)
    save_json(DATA_FILE, pesanan_list)

    return jsonify({"message": "✅ Pesanan diterima", "id": data['id']}), 200

@app.route('/api/pesanan-saya', methods=['GET'])
def pesanan_saya():
    if "username" not in session:
        return jsonify({"message": "🚫 Harus login terlebih dahulu"}), 401

    pesanan_list = load_json(DATA_FILE)
    user_pesanan = [p for p in pesanan_list if p.get("username") == session["username"]]
    return jsonify(user_pesanan), 200

@app.route('/api/admin/pesanan', methods=['GET'])
def get_pesanan():
    if session.get("role") != "admin":
        return jsonify({"message": "🚫 Akses ditolak"}), 403

    return jsonify(load_json(DATA_FILE)), 200

@app.route('/api/admin/pesanan/<id>', methods=['PUT'])
def update_status(id):
    if session.get("role") != "admin":
        return jsonify({"message": "🚫 Akses ditolak"}), 403

    pesanan_list = load_json(DATA_FILE)
    produk_list = load_json(PRODUK_FILE)

    for pesanan in pesanan_list:
        if pesanan['id'] == id:
            if pesanan['status'] == 'berhasil':
                return jsonify({"message": "❗ Sudah berhasil sebelumnya"}), 400

            pesanan['status'] = 'berhasil'
            for produk in produk_list:
                if produk['nama'].lower() == pesanan['nama_produk'].lower():
                    produk['stok'] -= pesanan['jumlah']
                    produk['stok'] = max(produk['stok'], 0)
                    save_json(PRODUK_FILE, produk_list)
                    break

            save_json(DATA_FILE, pesanan_list)
            return jsonify({"message": "✅ Status berhasil diperbarui & stok dikurangi"}), 200

    return jsonify({"message": "❌ Pesanan tidak ditemukan"}), 404

@app.route('/api/status/<id>', methods=['GET'])
def cek_status(id):
    pesanan_list = load_json(DATA_FILE)
    for pesanan in pesanan_list:
        if pesanan['id'] == id:
            return jsonify({"status": pesanan['status']}), 200
    return jsonify({"message": "❌ Pesanan tidak ditemukan"}), 404

@app.route('/api/produk', methods=['GET'])
def get_produk():
    return jsonify(load_json(PRODUK_FILE)), 200

@app.route('/api/admin/produk', methods=['POST'])
def tambah_produk():
    if session.get("role") != "admin":
        return jsonify({"message": "🚫 Akses ditolak"}), 403

    data = request.get_json()
    if not data or 'nama' not in data or 'harga' not in data or 'stok' not in data:
        return jsonify({"message": "❌ Data tidak lengkap"}), 400

    produk_list = load_json(PRODUK_FILE)
    for p in produk_list:
        if p['nama'].lower() == data['nama'].lower():
            return jsonify({"message": "❗ Produk sudah ada"}), 400

    produk_baru = {
        "nama": data['nama'],
        "harga": data['harga'],
        "stok": data['stok'],
        "gambar": data.get('gambar', '')
    }

    produk_list.append(produk_baru)
    save_json(PRODUK_FILE, produk_list)

    return jsonify({"message": "✅ Produk berhasil ditambahkan"}), 200

@app.route('/api/admin/produk/<nama>', methods=['PUT'])
def edit_produk(nama):
    if session.get("role") != "admin":
        return jsonify({"message": "🚫 Akses ditolak"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "❌ Data tidak dikirim"}), 400

    produk_list = load_json(PRODUK_FILE)
    for produk in produk_list:
        if produk['nama'].lower() == nama.lower():
            produk['nama'] = data.get('nama', produk['nama'])
            produk['harga'] = data.get('harga', produk['harga'])
            produk['stok'] = data.get('stok', produk['stok'])
            produk['gambar'] = data.get('gambar', produk.get('gambar', ''))
            save_json(PRODUK_FILE, produk_list)
            return jsonify({"message": "✅ Produk berhasil diedit"}), 200

    return jsonify({"message": "❌ Produk tidak ditemukan"}), 404

@app.route('/api/admin/produk/<nama>', methods=['DELETE'])
def hapus_produk(nama):
    if session.get("role") != "admin":
        return jsonify({"message": "🚫 Akses ditolak"}), 403

    produk_list = load_json(PRODUK_FILE)
    awal = len(produk_list)
    produk_list = [p for p in produk_list if p['nama'].lower() != nama.lower()]

    if len(produk_list) == awal:
        return jsonify({"message": "❌ Produk tidak ditemukan"}), 404

    save_json(PRODUK_FILE, produk_list)
    return jsonify({"message": "🗑️ Produk berhasil dihapus"}), 200

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
